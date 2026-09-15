import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

const PARTS = [
  { id: "worn", label: "Worn", file: "/cad/elbow/assembly_worn.stl", color: 0x8aa0a8 },
  { id: "assembly_preview", label: "Brace", file: "/cad/elbow/assembly_preview.stl", color: 0x8aa0a8 },
  { id: "print_fork_lateral", label: "Lateral plate", file: "/cad/elbow/print_fork_lateral.stl", color: 0x7eb8c9 },
  { id: "print_fork_medial", label: "Medial plate", file: "/cad/elbow/print_fork_medial.stl", color: 0x7eb8c9 },
  { id: "print_cuff_forearm", label: "Cuff", file: "/cad/elbow/print_cuff_forearm.stl", color: 0x7eb8c9 },
  { id: "print_drum", label: "Drum", file: "/cad/elbow/print_drum.stl", color: 0x9aa3ad },
  { id: "print_bowden_anchor", label: "Anchor", file: "/cad/elbow/print_bowden_anchor.stl", color: 0x7eb8c9 },
  { id: "ref_sheave", label: "Sheave (buy)", file: "/cad/elbow/ref_sheave_DO_NOT_PRINT.stl", color: 0xc4a35a },
] as const;

export function CadViewer() {
  const host = useRef<HTMLDivElement>(null);
  const [part, setPart] = useState<(typeof PARTS)[number]["id"]>("worn");
  const [status, setStatus] = useState("Loading STL…");

  useEffect(() => {
    const el = host.current;
    if (!el) return;
    let dead = false;
    let renderer: import("three").WebGLRenderer | undefined;
    let controls: import("three/examples/jsm/controls/OrbitControls.js").OrbitControls | undefined;
    let frame = 0;
    let ro: ResizeObserver | undefined;
    let geoDispose: (() => void) | undefined;
    const spec = PARTS.find((p) => p.id === part) ?? PARTS[0];

    (async () => {
      const THREE = await import("three");
      const { OrbitControls } = await import("three/examples/jsm/controls/OrbitControls.js");
      const { STLLoader } = await import("three/examples/jsm/loaders/STLLoader.js");
      if (dead || !el) return;

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x121214);

      const camera = new THREE.PerspectiveCamera(42, 1, 0.5, 4000);
      camera.position.set(180, 140, 220);

      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      el.innerHTML = "";
      el.appendChild(renderer.domElement);

      const key = new THREE.DirectionalLight(0xffffff, 1.1);
      key.position.set(120, 180, 90);
      const fill = new THREE.DirectionalLight(0x7eb8c9, 0.35);
      fill.position.set(-80, 40, -120);
      scene.add(key, fill, new THREE.AmbientLight(0xffffff, 0.35));

      controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.08;

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

      const geo = await new STLLoader().loadAsync(spec.file);
      if (dead) {
        geo.dispose();
        return;
      }
      geo.computeVertexNormals();
      geo.center();
      const mat = new THREE.MeshStandardMaterial({
        color: spec.color,
        metalness: spec.id === "ref_sheave" ? 0.75 : 0.25,
        roughness: spec.id === "ref_sheave" ? 0.35 : 0.55,
      });
      scene.add(new THREE.Mesh(geo, mat));
      geoDispose = () => {
        geo.dispose();
        mat.dispose();
      };

      geo.computeBoundingSphere();
      const r = geo.boundingSphere?.radius ?? 80;
      camera.position.set(r * 1.6, r * 1.1, r * 1.8);
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
      geoDispose?.();
      controls?.dispose();
      renderer?.dispose();
      renderer?.domElement.remove();
    };
  }, [part]);

  return (
    <div className="mb-10">
      <div className="mb-3 flex flex-wrap gap-2">
        {PARTS.map((p) => (
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
