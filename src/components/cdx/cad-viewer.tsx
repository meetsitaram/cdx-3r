import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { ELBOW_SWATCHES } from "@/lib/cdx";

const LAYERS = {
  worn: [
    "arm",
    "cuff_upper",
    "cuff_forearm",
    "lateral",
    "medial",
    "sheave",
    "screw",
    "nylock",
    "bearing",
    "anchor",
    "stop",
  ],
  brace: [
    "cuff_upper",
    "cuff_forearm",
    "lateral",
    "medial",
    "sheave",
    "screw",
    "nylock",
    "bearing",
    "anchor",
    "stop",
  ],
} as const;

const SOLO = [
  { id: "print_fork_lateral", label: "Lateral plate", file: "/cad/elbow/print_fork_lateral.stl", color: 0xc8ccd4 },
  { id: "print_fork_medial", label: "Medial plate", file: "/cad/elbow/print_fork_medial.stl", color: 0x6b7380 },
  { id: "print_cuff_forearm", label: "Cuff", file: "/cad/elbow/print_cuff_forearm.stl", color: 0x7eb8c9 },
  { id: "ref_sheave", label: "Sheave", file: "/cad/elbow/ref_sheave_DO_NOT_PRINT.stl", color: 0xc4a35a },
  { id: "ref_608", label: "608-2RS", file: "/cad/elbow/ref_608_DO_NOT_PRINT.stl", color: 0xe07a3d },
  { id: "ref_screw", label: "Shoulder screw", file: "/cad/elbow/ref_shoulder_screw_DO_NOT_PRINT.stl", color: 0x2a2c30 },
] as const;

type View = "worn" | "brace" | (typeof SOLO)[number]["id"];

function hexToInt(hex: string) {
  return parseInt(hex.replace("#", ""), 16);
}

export function CadViewer() {
  const host = useRef<HTMLDivElement>(null);
  const [part, setPart] = useState<View>("worn");
  const [status, setStatus] = useState("Loading STL…");

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
      const layerNames = part === "worn" ? LAYERS.worn : part === "brace" ? LAYERS.brace : null;

      if (layerNames) {
        const swatch = Object.fromEntries(ELBOW_SWATCHES.map((s) => [s.id, s.hex]));
        for (const name of layerNames) {
          const geo = await loader.loadAsync(`/cad/elbow/asm/${name}.stl`);
          if (dead) {
            geo.dispose();
            return;
          }
          geo.computeVertexNormals();
          const hex = swatch[name] ?? "#8aa0a8";
          const mat = new THREE.MeshStandardMaterial({
            color: hexToInt(hex),
            metalness: name === "sheave" || name === "screw" ? 0.7 : 0.2,
            roughness: name === "sheave" ? 0.35 : 0.55,
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
        const spec = SOLO.find((p) => p.id === part) ?? SOLO[0];
        const geo = await loader.loadAsync(spec.file);
        if (dead) {
          geo.dispose();
          return;
        }
        geo.computeVertexNormals();
        geo.center();
        const mat = new THREE.MeshStandardMaterial({
          color: spec.color,
          metalness: spec.id.startsWith("ref_") ? 0.7 : 0.2,
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
  }, [part]);

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
        {SOLO.map((p) => (
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
