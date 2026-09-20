import { Group, Matrix4, Quaternion, Vector3, ArrowHelper } from "three";
import type { Mesh, BufferGeometry } from "three";

export type Pose = { shoulderAbduction: number; shoulderFlexion: number; elbowFlexion: number };
export type Joint = {
  id: string; parent: string; key: keyof Pose; label: string;
  origin: [number, number, number]; axis: [number, number, number];
  rest: number; min: number; max: number;
};
type Flexible = {
  fromLink: string; toLink: string; path?: number[][]; weights?: number[];
  coordinate?: number; start?: number; end?: number;
};
export type MotionManifest = {
  version: number; joints: Joint[]; bindings: Record<string, string>;
  flexible: Record<string, Flexible>; rest: Pose;
  landmarks: Record<string, [number, number, number]>;
};
export const REST_POSE: Pose = { shoulderAbduction: 0, shoulderFlexion: 0, elbowFlexion: 90 };
export const POSES: { label: string; pose: Pose }[] = [
  { label: "Work pose", pose: REST_POSE },
  { label: "Arm down", pose: { shoulderAbduction: 0, shoulderFlexion: 0, elbowFlexion: 0 } },
  { label: "Reach", pose: { shoulderAbduction: 10, shoulderFlexion: 65, elbowFlexion: 25 } },
  { label: "Side lift", pose: { shoulderAbduction: 50, shoulderFlexion: 0, elbowFlexion: 75 } },
];
const finite = (n: unknown): n is number => typeof n === "number" && Number.isFinite(n);
const vec = (v: unknown): v is [number, number, number] => Array.isArray(v) && v.length === 3 && v.every(finite);

export function readMotion(value: unknown, names: string[]): MotionManifest {
  const m = value as MotionManifest;
  if (!m || m.version !== 1 || !Array.isArray(m.joints) || m.joints.length !== 3 || !m.bindings || !m.flexible || !m.rest) throw new Error("Missing joint rig");
  const links = new Set(["base"]);
  const keys = new Set<string>();
  for (const j of m.joints) {
    if (!j || typeof j.id !== "string" || links.has(j.id) || !links.has(j.parent) || !(j.key in REST_POSE) || keys.has(j.key) ||
        typeof j.label !== "string" || !vec(j.origin) || !vec(j.axis) || Math.abs(Math.hypot(...j.axis) - 1) > 1e-6 ||
        ![j.rest, j.min, j.max, m.rest[j.key]].every(finite) || j.min > j.rest || j.rest > j.max || m.rest[j.key] !== j.rest) throw new Error("Invalid joint rig");
    links.add(j.id); keys.add(j.key);
  }
  if (names.some((name) => !links.has(m.bindings[name]))) throw new Error("Unassigned assembly layer");
  for (const [name, f] of Object.entries(m.flexible)) {
    if (!(name in m.bindings) || !links.has(f.fromLink) || !links.has(f.toLink)) throw new Error("Invalid cable binding");
    if (f.path) {
      if (!f.path.length || !f.path.every(vec) || f.weights?.length !== f.path.length || !f.weights.every((w) => finite(w) && w >= 0 && w <= 1)) throw new Error("Invalid cable route");
    } else if (![0, 1, 2].includes(f.coordinate ?? -1) || !finite(f.start) || !finite(f.end) || f.start === f.end) throw new Error("Invalid cable blend");
  }
  if (!m.landmarks || !Object.values(m.landmarks).every(vec)) throw new Error("Invalid arm landmarks");
  return m;
}

export function clampPose(m: MotionManifest, pose: Pose): Pose {
  const result = { ...m.rest };
  for (const j of m.joints) result[j.key] = Math.max(j.min, Math.min(j.max, finite(pose[j.key]) ? pose[j.key] : j.rest));
  return result;
}

export function poseTransforms(m: MotionManifest, pose: Pose): Record<string, Matrix4> {
  const safe = clampPose(m, pose);
  const matrices: Record<string, Matrix4> = { base: new Matrix4() };
  for (const j of m.joints) {
    const p = new Vector3(...j.origin);
    const rotation = new Matrix4().makeRotationAxis(new Vector3(...j.axis), (safe[j.key] - j.rest) * Math.PI / 180);
    const local = new Matrix4().makeTranslation(p.x, p.y, p.z).multiply(rotation).multiply(new Matrix4().makeTranslation(-p.x, -p.y, -p.z));
    matrices[j.id] = matrices[j.parent].clone().multiply(local);
  }
  return matrices;
}

function skinWeight(f: Flexible, p: Vector3) {
  if (f.path && f.weights) {
    let nearest = 0; let distance = Infinity;
    f.path.forEach((v, i) => {
      const d = (p.x - v[0]) ** 2 + (p.y - v[1]) ** 2 + (p.z - v[2]) ** 2;
      if (d < distance) { nearest = i; distance = d; }
    });
    return f.weights[nearest];
  }
  const t = Math.max(0, Math.min(1, (p.getComponent(f.coordinate!) - f.start!) / (f.end! - f.start!)));
  return t * t * (3 - 2 * t);
}

/** Each rigid mesh stays in its source world pose until parented at its axle. */
export function createMotionRig(root: Group, m: MotionManifest) {
  const nodes: Record<string, Group> = { base: root };
  const origins: Record<string, Vector3> = { base: new Vector3() };
  const axes: ArrowHelper[] = [];
  const meshes: { name: string; mesh: Mesh }[] = [];
  const skins: { geometry: BufferGeometry; rest: Float32Array; weights: Float32Array; spec: Flexible }[] = [];
  for (const [index, j] of m.joints.entries()) {
    const node = new Group(); node.name = j.id;
    const origin = new Vector3(...j.origin);
    node.position.copy(origin).sub(origins[j.parent]);
    nodes[j.parent].add(node); nodes[j.id] = node; origins[j.id] = origin;
    const arrow = new ArrowHelper(new Vector3(...j.axis), new Vector3(), 85, [0xf78b59, 0x64d9f5, 0xb2e57c][index], 12, 6);
    arrow.visible = false; node.add(arrow); axes.push(arrow);
  }
  return {
    add(name: string, mesh: Mesh) {
      mesh.name = name; meshes.push({ name, mesh });
      const f = m.flexible[name];
      if (f) {
        const position = mesh.geometry.getAttribute("position");
        const rest = new Float32Array(position.array);
        const weights = new Float32Array(position.count);
        const p = new Vector3();
        for (let i = 0; i < position.count; i++) weights[i] = skinWeight(f, p.fromArray(rest, i * 3));
        skins.push({ geometry: mesh.geometry, rest, weights, spec: f }); root.add(mesh);
      } else {
        const link = m.bindings[name];
        mesh.position.copy(origins[link]).negate(); nodes[link].add(mesh);
      }
    },
    update(pose: Pose, shells: boolean, showAxes: boolean) {
      const safe = clampPose(m, pose);
      for (const j of m.joints) nodes[j.id].quaternion.copy(new Quaternion().setFromAxisAngle(new Vector3(...j.axis), (safe[j.key] - j.rest) * Math.PI / 180));
      for (const { name, mesh } of meshes) mesh.visible = !name.startsWith("ar_") || shells;
      axes.forEach((axis) => { axis.visible = showAxes; });
      const matrices = poseTransforms(m, safe); const p = new Vector3(); const a = new Vector3(); const b = new Vector3();
      for (const skin of skins) {
        const position = skin.geometry.getAttribute("position");
        for (let i = 0; i < position.count; i++) {
          p.fromArray(skin.rest, i * 3);
          a.copy(p).applyMatrix4(matrices[skin.spec.fromLink]); b.copy(p).applyMatrix4(matrices[skin.spec.toLink]);
          a.lerp(b, skin.weights[i]); position.setXYZ(i, a.x, a.y, a.z);
        }
        position.needsUpdate = true; skin.geometry.computeVertexNormals(); skin.geometry.computeBoundingSphere();
      }
    },
    dispose() { axes.forEach((a) => a.dispose()); },
  };
}
