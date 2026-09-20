import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { BufferGeometry, Float32BufferAttribute, Group, Mesh, MeshBasicMaterial, Vector3 } from "three";
import { clampPose, createMotionRig, poseTransforms, readMotion, REST_POSE, POSES } from "./cad-motion.ts";

const manifest = JSON.parse(readFileSync(new URL("../../public/cad/system/asm/colors.json", import.meta.url), "utf8"));
const motion = readMotion(manifest.motion, Object.keys(manifest.layers));
const near = (a: Vector3, b: Vector3) => assert.ok(a.distanceTo(b) < 1e-4, `${a.toArray()} != ${b.toArray()}`);
const point = (name: string, pose = REST_POSE) => new Vector3(...motion.landmarks[name]).applyMatrix4(poseTransforms(motion, pose)[name === "wrist" ? "forearm" : name === "elbow" ? "upper" : "shoulder"]);

test("exported rig owns every layer and rejects incomplete or invalid rigs", () => {
  assert.equal(Object.keys(motion.bindings).length, Object.keys(manifest.layers).length);
  assert.equal(motion.bindings.ar_ua_trim, "upper");
  assert.equal(motion.bindings.ar_fa_trim, "forearm");
  assert.equal(motion.bindings.sh_anchor_abd, "base");
  const invalid = structuredClone(motion); delete invalid.bindings.ar_fa;
  assert.throws(() => readMotion(invalid, Object.keys(manifest.layers)));
  const badAxis = structuredClone(motion); badAxis.joints[0].axis = [0, 0, 0];
  assert.throws(() => readMotion(badAxis, Object.keys(manifest.layers)));
});

test("rest pose leaves all world-coordinate layers exactly in place", () => {
  for (const matrix of Object.values(poseTransforms(motion, REST_POSE))) near(new Vector3(80, -230, 75).applyMatrix4(matrix), new Vector3(80, -230, 75));
});

test("elbow zero extends down, ninety reaches forward, and shoulder signs lift forward and outboard", () => {
  const ua = -motion.landmarks.elbow[1]; const fa = motion.landmarks.wrist[0];
  near(point("wrist", { ...REST_POSE, elbowFlexion: 0 }), new Vector3(0, -ua - fa, 0));
  near(point("wrist"), new Vector3(fa, -ua, 0));
  near(point("elbow", { ...REST_POSE, shoulderFlexion: 90 }), new Vector3(ua, 0, 0));
  const side = point("elbow", { ...REST_POSE, shoulderAbduction: 60 });
  assert.ok(side.z > 0); assert.ok(side.y > -ua);
});

test("combined joint sweeps preserve segment lengths and the common elbow pivot", () => {
  for (let a = 0; a <= 60; a += 15) for (let s = 0; s <= 90; s += 15) for (let e = 0; e <= 135; e += 15) {
    const pose = { shoulderAbduction: a, shoulderFlexion: s, elbowFlexion: e };
    const shoulder = point("shoulder", pose), elbow = point("elbow", pose), wrist = point("wrist", pose);
    assert.ok(Math.abs(shoulder.distanceTo(elbow) + motion.landmarks.elbow[1]) < 1e-6);
    assert.ok(Math.abs(elbow.distanceTo(wrist) - motion.landmarks.wrist[0]) < 1e-6);
    near(new Vector3(...motion.landmarks.elbow).applyMatrix4(poseTransforms(motion, pose).forearm), elbow);
  }
});

test("scene hierarchy matches analytic transforms, including a centered viewer root", () => {
  const root = new Group(); root.position.set(-60, 100, 40);
  const rig = createMotionRig(root, motion);
  const meshes: { name: string; mesh: Mesh; p: Vector3 }[] = [];
  for (const name of ["ar_ua", "ar_fa", "ar_fa_trim", "ar_deltoid", "sh_anchor_abd", "pk_frame", "ghost_forearm"]) {
    const p = new Vector3(50, -150, 70);
    const mesh = new Mesh(new BufferGeometry(), new MeshBasicMaterial());
    rig.add(name, mesh); meshes.push({ name, mesh, p });
  }
  for (const { pose } of POSES) {
    rig.update(pose, true, true); root.updateMatrixWorld(true);
    for (const { name, mesh, p } of meshes) near(mesh.localToWorld(p.clone()), p.clone().applyMatrix4(poseTransforms(motion, pose)[motion.bindings[name]]).add(root.position));
  }
  rig.update(REST_POSE, false, false);
  assert.equal(meshes[0].mesh.visible, false); assert.equal(meshes[5].mesh.visible, true);
  rig.dispose();
});

test("flexible routing keeps pack ends fixed and moving ends on their assigned link without drift", () => {
  const root = new Group(); const rig = createMotionRig(root, motion);
  const spec = motion.flexible.housing_0;
  const first = new Vector3(...spec.path![0]); const last = new Vector3(...spec.path!.at(-1)!);
  const geo = new BufferGeometry(); geo.setAttribute("position", new Float32BufferAttribute([...first.toArray(), ...last.toArray(), ...last.clone().addScalar(.1).toArray()], 3));
  rig.add("housing_0", new Mesh(geo, new MeshBasicMaterial()));
  for (const { pose } of [...POSES, ...POSES]) {
    rig.update(pose, true, false);
    near(new Vector3().fromBufferAttribute(geo.getAttribute("position"), 0), first);
    near(new Vector3().fromBufferAttribute(geo.getAttribute("position"), 1), last.clone().applyMatrix4(poseTransforms(motion, pose).upper));
  }
  rig.dispose(); geo.dispose();
});

test("out-of-range and nonfinite input is bounded before transforms", () => {
  assert.deepEqual(clampPose(motion, { shoulderAbduction: -40, shoulderFlexion: 999, elbowFlexion: NaN }), { shoulderAbduction: 0, shoulderFlexion: 90, elbowFlexion: 90 });
});
