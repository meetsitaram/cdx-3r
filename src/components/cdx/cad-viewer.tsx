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

const PACK_WORN = [
  "torso",
  "frame",
  "sled",
  "battery",
  "motor",
  "s1",
  "spreader",
  "xt90",
  "bullet",
  "bulkhead",
  "housing",
  "cable_el",
  "cable_flex",
  "cable_abd",
  "strap",
] as const;

const KITS = {
  elbow: {
    prefix: "/cad/elbow",
    worn: ELBOW_WORN,
    brace: ELBOW_WORN.filter((n) => n !== "arm"),
    fallback: "/cad/elbow/assembly_worn.stl",
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
    fallback: "/cad/shoulder/assembly_worn.stl",
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
  backpack: {
    prefix: "/cad/backpack",
    worn: PACK_WORN,
    brace: PACK_WORN.filter((n) => n !== "torso"),
    fallback: "/cad/backpack/assembly_worn.stl",
    swatches: {
      torso: "#e7d3c0",
      frame: "#f2f4f7",
      sled: "#94a3b8",
      battery: "#14532d",
      motor: "#111215",
      s1: "#16a34a",
      spreader: "#cbd5e1",
      xt90: "#f97316",
      bullet: "#eab308",
      bulkhead: "#22c55e",
      housing: "#1f2937",
      cable_el: "#38bdf8",
      cable_flex: "#e879f9",
      cable_abd: "#818cf8",
      strap: "#78716c",
    },
    ghost: new Set(["torso"]),
    solo: [
      { id: "ref_battery", label: "Hailong", file: "/cad/backpack/ref_battery_DO_NOT_PRINT.stl", color: 0x14532d },
      { id: "ref_motor", label: "D6374", file: "/cad/backpack/ref_motor_DO_NOT_PRINT.stl", color: 0x111215 },
      { id: "ref_planetary", label: "10:1", file: "/cad/backpack/ref_planetary_DO_NOT_PRINT.stl", color: 0x64748b },
      { id: "ref_s1", label: "ODrive S1", file: "/cad/backpack/ref_s1_DO_NOT_PRINT.stl", color: 0x16a34a },
      { id: "print_drum", label: "Drum", file: "/cad/backpack/print_drum.stl", color: 0xffc93c },
      { id: "print_bulkhead", label: "Bulkhead", file: "/cad/backpack/print_bulkhead.stl", color: 0x22c55e },
    ],
  },
  system: {
    prefix: "/cad/system",
    worn: [
      "human",
      "saddle",
      "yoke",
      "beam",
      "belt",
      "park",
      "strap",
      "ferrule",
      "housing",
      "cable_el",
      "cable_flex",
      "cable_abd",
      "pk_frame",
      "pk_battery",
      "pk_motor",
      "pk_bulkhead",
      "sh_sheave_flex",
      "sh_sheave_abd",
      "sh_cuff",
      "el_cuff_upper",
      "el_cuff_forearm",
      "el_sheave",
      "el_lateral",
    ],
    brace: [
      "saddle",
      "yoke",
      "beam",
      "belt",
      "park",
      "pk_frame",
      "pk_battery",
      "pk_motor",
      "sh_sheave_flex",
      "sh_sheave_abd",
      "el_sheave",
      "el_lateral",
    ],
    fallback: "/cad/system/assembly_worn.stl",
    swatches: {
      human: "#f3c6a5",
      saddle: "#f59e0b",
      yoke: "#e2e8f0",
      beam: "#94a3b8",
      belt: "#78716c",
      park: "#f97316",
      strap: "#a8a29e",
      ferrule: "#22c55e",
      housing: "#1f2937",
      cable_el: "#38bdf8",
      cable_flex: "#e879f9",
      cable_abd: "#818cf8",
      pk_frame: "#f2f4f7",
      pk_battery: "#14532d",
      pk_motor: "#111215",
      pk_s1: "#16a34a",
      pk_bulkhead: "#22c55e",
      sh_sheave_flex: "#ffc93c",
      sh_sheave_abd: "#f97316",
      sh_cuff: "#5ee0ff",
      el_cuff_upper: "#12b5d4",
      el_cuff_forearm: "#5ee0ff",
      el_sheave: "#ffc93c",
      el_lateral: "#f2f4f7",
    },
    ghost: new Set(["human"]),
    solo: [
      { id: "print_saddle", label: "Saddle", file: "/cad/system/print_saddle.stl", color: 0xf59e0b },
      { id: "print_yoke", label: "Yoke", file: "/cad/system/print_yoke.stl", color: 0xe2e8f0 },
      { id: "print_ua_beam", label: "UA beam", file: "/cad/system/print_ua_beam.stl", color: 0x94a3b8 },
      { id: "print_hip_belt", label: "Hip belt", file: "/cad/system/print_hip_belt.stl", color: 0x78716c },
      { id: "print_park_rest", label: "Cradle", file: "/cad/system/print_park_rest.stl", color: 0xf97316 },
    ],
  },
} as const;

type Kit = keyof typeof KITS;

function hexToInt(hex: string) {
  return parseInt(hex.replace("#", ""), 16);
}

async function loadThree() {
  const THREE = await import("three");
  try {
    const { OrbitControls } = await import("three/addons/controls/OrbitControls.js");
    const { STLLoader } = await import("three/addons/loaders/STLLoader.js");
    return { THREE, OrbitControls, STLLoader };
  } catch {
    const { OrbitControls } = await import("three/examples/jsm/controls/OrbitControls.js");
    const { STLLoader } = await import("three/examples/jsm/loaders/STLLoader.js");
    return { THREE, OrbitControls, STLLoader };
  }
}

export function CadViewer({ kit = "elbow" }: { kit?: Kit }) {
  const spec = KITS[kit];
  const host = useRef<HTMLDivElement>(null);
  const [part, setPart] = useState("worn");
  const [status, setStatus] = useState("Loading STL…");

  useEffect(() => {
    const el = host.current;
    if (!el) return;
    let dead = false;
    let started = false;
    let renderer: import("three").WebGLRenderer | undefined;
    let controls: InstanceType<typeof import("three/examples/jsm/controls/OrbitControls.js").OrbitControls> | undefined;
    let frame = 0;
    const disposers: Array<() => void> = [];

    const boot = async () => {
      if (dead || started) return;
      if (el.clientWidth < 16 || el.clientHeight < 16) return;
      started = true;
      setStatus("Loading STL…");

      const { THREE, OrbitControls, STLLoader } = await loadThree();
      if (dead) return;

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x121214);
      const camera = new THREE.PerspectiveCamera(42, 1, 0.5, 8000);
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      el.innerHTML = "";
      el.appendChild(renderer.domElement);

      scene.add(new THREE.AmbientLight(0xffffff, 0.4));
      const key = new THREE.DirectionalLight(0xffffff, 1.15);
      key.position.set(160, 200, 120);
      const fill = new THREE.DirectionalLight(0x7eb8c9, 0.45);
      fill.position.set(-100, 40, -140);
      scene.add(key, fill);

      controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;

      const resize = () => {
        if (!el || !renderer) return;
        const w = Math.max(el.clientWidth, 16);
        const h = Math.max(el.clientHeight, 16);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h, false);
      };
      resize();

      const loader = new STLLoader();
      const group = new THREE.Group();
      const layerNames = part === "worn" ? spec.worn : part === "brace" ? spec.brace : null;
      let loaded = 0;

      const addGeo = (
        geo: import("three").BufferGeometry,
        color: number,
        extra?: { metal?: boolean; ghost?: boolean },
      ) => {
        geo.computeVertexNormals();
        const mat = new THREE.MeshStandardMaterial({
          color,
          metalness: extra?.metal ? 0.7 : 0.18,
          roughness: extra?.metal ? 0.35 : 0.55,
          transparent: extra?.ghost ?? false,
          opacity: extra?.ghost ? 0.42 : 1,
          depthWrite: !extra?.ghost,
        });
        group.add(new THREE.Mesh(geo, mat));
        disposers.push(() => {
          geo.dispose();
          mat.dispose();
        });
      };

      if (layerNames) {
        const results = await Promise.allSettled(
          layerNames.map(async (name) => {
            const geo = await loader.loadAsync(`${spec.prefix}/asm/${name}.stl`);
            return { name, geo };
          }),
        );
        if (dead) return;
        for (const r of results) {
          if (r.status !== "fulfilled") continue;
          const { name, geo } = r.value;
          addGeo(geo, hexToInt((spec.swatches as Record<string, string>)[name] ?? "#8aa0a8"), {
            metal: name.includes("sheave") || name === "screw",
            ghost: spec.ghost.has(name as never),
          });
          loaded += 1;
        }
        if (loaded === 0) {
          const geo = await loader.loadAsync(spec.fallback);
          if (dead) {
            geo.dispose();
            return;
          }
          geo.center();
          addGeo(geo, 0x8aa0a8);
          loaded = 1;
        }
      } else {
        const solo = spec.solo.find((p) => p.id === part) ?? spec.solo[0];
        const geo = await loader.loadAsync(solo.file);
        if (dead) {
          geo.dispose();
          return;
        }
        geo.center();
        addGeo(geo, solo.color, { metal: solo.id.includes("sheave") });
        loaded = 1;
      }

      scene.add(group);
      if (layerNames) {
        const box = new THREE.Box3().setFromObject(group);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3()).length() || 180;
        group.position.sub(center);
        if (kit === "system") camera.position.set(size * 0.9, size * 0.18, size * 0.4);
        else camera.position.set(size * 0.55, size * 0.4, size * 0.75);
      } else {
        const box = new THREE.Box3().setFromObject(group);
        const r = box.getSize(new THREE.Vector3()).length() || 80;
        camera.position.set(r * 0.8, r * 0.55, r * 0.9);
      }
      controls.target.set(0, 0, 0);
      controls.update();
      setStatus(loaded ? "Drag to orbit · scroll to zoom" : "Could not load STL");

      const tick = () => {
        if (dead) return;
        controls?.update();
        renderer?.render(scene, camera);
        frame = requestAnimationFrame(tick);
      };
      tick();
    };

    const ro = new ResizeObserver(() => {
      void boot();
      if (!renderer || !el) return;
      const w = Math.max(el.clientWidth, 16);
      const h = Math.max(el.clientHeight, 16);
      renderer.setSize(w, h, false);
    });
    ro.observe(el);
    void boot();

    return () => {
      dead = true;
      cancelAnimationFrame(frame);
      ro.disconnect();
      disposers.forEach((d) => d());
      controls?.dispose();
      renderer?.dispose();
      renderer?.domElement.remove();
    };
  }, [part, kit, spec]);

  return (
    <div className="mb-4">
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
        <div ref={host} className="h-[460px] w-full" />
        <div className="border-t border-border px-4 py-2 font-mono text-[11px] tracking-[0.14em] text-subtle uppercase">
          {status}
        </div>
      </div>
    </div>
  );
}
