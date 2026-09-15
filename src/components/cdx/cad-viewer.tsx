import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { ELBOW_SWATCHES, SHOULDER_SWATCHES } from "@/lib/cdx";

const ELBOW_WORN = [
  "arm",
  "cuff_upper",
  "cuff_forearm",
  "lateral",
  "distal",
  "medial",
  "sheave",
  "screw",
  "nylock",
  "bearing",
  "anchor",
  "housing",
  "cable_flex",
  "cable_ext",
  "clamp",
  "stop",
] as const;

const SHOULDER_WORN = [
  "torso",
  "arm",
  "cuff",
  "scapula",
  "abd_yoke",
  "flex_yoke",
  "sheave_flex",
  "sheave_abd",
  "screw",
  "bearing",
  "anchor",
  "comb",
  "housing",
  "cable_flex",
  "cable_abd",
  "cable_elbow",
  "clamp",
  "stop",
] as const;

const SHOULDER_COLORS: Record<string, string> = {
  torso: "#e7d3c0",
  arm: "#f3c6a5",
  cuff: "#5ee0ff",
  scapula: "#f2f4f7",
  abd_yoke: "#94a3b8",
  flex_yoke: "#cbd5e1",
  sheave_flex: "#ffc93c",
  sheave_abd: "#f97316",
  screw: "#111215",
  bearing: "#ff6a1a",
  cups: "#f2f4f7",
  anchor: "#22c55e",
  comb: "#14b8a6",
  housing: "#1f2937",
  cable_flex: "#e879f9",
  cable_abd: "#818cf8",
  cable_elbow: "#38bdf8",
  clamp: "#fb7185",
  stop: "#facc15",
};

const KITS = {
  elbow: {
    prefix: "/cad/elbow",
    worn: ELBOW_WORN,
    brace: ELBOW_WORN.filter((n) => n !== "arm"),
    swatches: Object.fromEntries(ELBOW_SWATCHES.map((s) => [s.id, s.hex])),
    ghost: new Set(["arm"]),
    solo: [
      { id: "print_fork_lateral", label: "Lateral plate", file: "/cad/elbow/print_fork_lateral.stl", color: 0xf2f4f7 },
      { id: "print_cuff_forearm", label: "Cuff", file: "/cad/elbow/print_cuff_forearm.stl", color: 0x5ee0ff },
      { id: "ref_sheave", label: "Sheave", file: "/cad/elbow/ref_sheave_DO_NOT_PRINT.stl", color: 0xffc93c },
      { id: "ref_608", label: "608-2RS", file: "/cad/elbow/ref_608_DO_NOT_PRINT.stl", color: 0xff6a1a },
    ],
  },
  shoulder: {
    prefix: "/cad/shoulder",
    worn: SHOULDER_WORN,
    brace: SHOULDER_WORN.filter((n) => n !== "arm" && n !== "torso"),
    swatches: { ...SHOULDER_COLORS, ...Object.fromEntries(SHOULDER_SWATCHES.map((s) => [s.id, s.hex])) },
    ghost: new Set(["arm", "torso"]),
    solo: [
      { id: "print_scapula", label: "Scapula", file: "/cad/shoulder/print_scapula.stl", color: 0xf2f4f7 },
      { id: "print_flex_yoke", label: "Flex yoke", file: "/cad/shoulder/print_flex_yoke.stl", color: 0xcbd5e1 },
      { id: "print_deltoid_cuff", label: "Deltoid cuff", file: "/cad/shoulder/print_deltoid_cuff.stl", color: 0x5ee0ff },
      { id: "ref_sheave_flex", label: "Flexion sheave", file: "/cad/shoulder/ref_sheave_flex_DO_NOT_PRINT.stl", color: 0xffc93c },
      { id: "ref_sheave_abd", label: "Abduction sheave", file: "/cad/shoulder/ref_sheave_abd_DO_NOT_PRINT.stl", color: 0xf97316 },
      { id: "print_cable_comb", label: "Comb", file: "/cad/shoulder/print_cable_comb.stl", color: 0x14b8a6 },
    ],
  },
} as const;

type Kit = keyof typeof KITS;

function hexToInt(hex: string) {
  return parseInt(hex.replace("#", ""), 16);
}

export function CadViewer({ kit = "elbow" }: { kit?: Kit }) {
  const spec = KITS[kit];
  const host = useRef<HTMLDivElement>(null);
  const [part, setPart] = useState<string>("worn");
  const [status, setStatus] = useState("Loading STL…");

  useEffect(() => {
    setPart("worn");
    setStatus("Loading STL…");
  }, [kit]);

  useEffect(() => {
    const el = host.current;
    if (!el) return;
    let dead = false;
    let renderer: import("three").WebGLRenderer | undefined;
    let controls: import("three/examples/jsm/controls/OrbitControls.js").OrbitControls | undefined;
    let frame = 0;
    let ro: ResizeObserver | undefined;
    const disposers: Array<() => void> = [];

    (async () => {
      const THREE = await import("three");
      const { OrbitControls } = await import("three/examples/jsm/controls/OrbitControls.js");
      const { STLLoader } = await import("three/examples/jsm/loaders/STLLoader.js");
      if (dead || !el) return;

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x121214);
      const camera = new THREE.PerspectiveCamera(42, 1, 0.5, 4000);
      renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      el.innerHTML = "";
      el.appendChild(renderer.domElement);

      const key = new THREE.DirectionalLight(0xffffff, 1.15);
      key.position.set(120, 180, 90);
      const fill = new THREE.DirectionalLight(0x7eb8c9, 0.4);
      fill.position.set(-80, 40, -120);
      scene.add(key, fill, new THREE.AmbientLight(0xffffff, 0.32));

      controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;

      const resize = () => {
        if (!el || !renderer) return;
        const w = el.clientWidth;
        const h = el.clientHeight;
        camera.aspect = w / Math.max(h, 1);
        camera.updateProjectionMatrix();
        renderer.setSize(w, h, false);
      };
      resize();
      ro = new ResizeObserver(resize);
      ro.observe(el);

      const loader = new STLLoader();
      const group = new THREE.Group();
      const layerNames = part === "worn" ? spec.worn : part === "brace" ? spec.brace : null;

      if (layerNames) {
        for (const name of layerNames) {
          const geo = await loader.loadAsync(`${spec.prefix}/asm/${name}.stl`);
          if (dead) {
            geo.dispose();
            return;
          }
          geo.computeVertexNormals();
          const ghost = spec.ghost.has(name as never);
          const mat = new THREE.MeshStandardMaterial({
            color: hexToInt(spec.swatches[name] ?? "#8aa0a8"),
            metalness: name.includes("sheave") || name === "screw" ? 0.7 : 0.2,
            roughness: name.includes("sheave") ? 0.35 : 0.55,
            transparent: ghost,
            opacity: ghost ? 0.42 : 1,
            depthWrite: !ghost,
          });
          group.add(new THREE.Mesh(geo, mat));
          disposers.push(() => {
            geo.dispose();
            mat.dispose();
          });
        }
        scene.add(group);
        const box = new THREE.Box3().setFromObject(group);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3()).length() || 120;
        group.position.sub(center);
        camera.position.set(size * 0.55, size * 0.4, size * 0.7);
      } else {
        const solo = spec.solo.find((p) => p.id === part) ?? spec.solo[0];
        const geo = await loader.loadAsync(solo.file);
        if (dead) {
          geo.dispose();
          return;
        }
        geo.computeVertexNormals();
        geo.center();
        const mat = new THREE.MeshStandardMaterial({
          color: solo.color,
          metalness: solo.id.includes("sheave") ? 0.7 : 0.2,
          roughness: 0.45,
        });
        group.add(new THREE.Mesh(geo, mat));
        scene.add(group);
        geo.computeBoundingSphere();
        const r = geo.boundingSphere?.radius ?? 80;
        camera.position.set(r * 1.6, r * 1.1, r * 1.8);
        disposers.push(() => {
          geo.dispose();
          mat.dispose();
        });
      }

      controls.target.set(0, 0, 0);
      controls.update();
      setStatus("Drag to orbit · scroll to zoom");

      const tick = () => {
        if (dead) return;
        controls?.update();
        renderer?.render(scene, camera);
        frame = requestAnimationFrame(tick);
      };
      tick();
    })().catch((err) => {
      if (!dead) setStatus(err instanceof Error ? err.message : "Could not load STL");
    });

    return () => {
      dead = true;
      cancelAnimationFrame(frame);
      ro?.disconnect();
      disposers.forEach((d) => d());
      controls?.dispose();
      renderer?.dispose();
      renderer?.domElement.remove();
    };
  }, [part, kit, spec]);

  return (
    <div className="mb-10">
      <div className="mb-3 flex flex-wrap gap-2">
        {(["worn", "brace"] as const).map((id) => (
          <button
            key={id}
            type="button"
            onClick={() => {
              setStatus("Loading STL…");
              setPart(id);
            }}
            className={cn(
              "rounded-full border px-3 py-1 font-mono text-[11px] tracking-[0.14em] uppercase",
              part === id
                ? "border-accent bg-accent/15 text-accent"
                : "border-border bg-surface text-muted hover:text-fg",
            )}
          >
            {id}
          </button>
        ))}
        {spec.solo.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => {
              setStatus("Loading STL…");
              setPart(p.id);
            }}
            className={cn(
              "rounded-full border px-3 py-1 font-mono text-[11px] tracking-[0.14em] uppercase",
              part === p.id
                ? "border-accent bg-accent/15 text-accent"
                : "border-border bg-surface text-muted hover:text-fg",
            )}
          >
            {p.label}
          </button>
        ))}
      </div>
      <div className="overflow-hidden rounded-lg border border-border bg-elevated">
        <div ref={host} className="h-[420px] w-full" />
        <div className="border-t border-border px-4 py-2 font-mono text-[11px] tracking-[0.14em] text-subtle uppercase">
          {status}
        </div>
      </div>
    </div>
  );
}
