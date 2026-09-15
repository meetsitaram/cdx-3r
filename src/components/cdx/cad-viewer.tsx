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

const PACK_WORN = [
  "torso",
  "frame",
  "sled",
  "battery",
  "motor",
  "s1",
  "spreader",
  "xt90",
  "bulkhead",
  "cable_el",
  "cable_flex",
  "cable_abd",
  "strap",
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
      bulkhead: "#22c55e",
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
      "ar_ua",
      "ar_fa",
      "ar_deltoid",
      "ar_bezel",
      "ar_sheave",
      "ar_scapula",
      "ar_pack",
      "ar_lid",
      "ar_led",
    ],
    brace: ["saddle", "yoke", "beam", "belt", "park", "pk_frame", "pk_battery", "pk_motor", "sh_sheave_flex", "el_sheave"],
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
      pk_bulkhead: "#22c55e",
      sh_sheave_flex: "#ffc93c",
      sh_sheave_abd: "#f97316",
      sh_cuff: "#5ee0ff",
      el_cuff_upper: "#12b5d4",
      el_cuff_forearm: "#5ee0ff",
      el_sheave: "#ffc93c",
      el_lateral: "#f2f4f7",
      ar_ua: "#1f2328",
      ar_fa: "#252a31",
      ar_deltoid: "#1c2024",
      ar_bezel: "#8a9199",
      ar_sheave: "#c5cad3",
      ar_scapula: "#2a3038",
      ar_pack: "#16191d",
      ar_lid: "#1a1e24",
      ar_led: "#3b82f6",
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
  armor: {
    prefix: "/cad/armor",
    worn: ["ghost_ua", "ghost_fa", "ghost_deltoid", "ghost_frame", "ua", "fa", "deltoid", "bezel", "sheave", "scapula", "pack", "lid", "led", "screw"],
    brace: ["ua", "fa", "deltoid", "bezel", "sheave", "scapula", "pack", "lid", "led"],
    fallback: "/cad/armor/assembly_worn.stl",
    swatches: {
      ghost_ua: "#5ee0ff",
      ghost_fa: "#5ee0ff",
      ghost_deltoid: "#5ee0ff",
      ghost_frame: "#94a3b8",
      ua: "#1f2328",
      fa: "#252a31",
      deltoid: "#1c2024",
      bezel: "#8a9199",
      sheave: "#c5cad3",
      scapula: "#2a3038",
      pack: "#16191d",
      lid: "#1a1e24",
      led: "#3b82f6",
      screw: "#c5cad3",
    },
    ghost: new Set(["ghost_ua", "ghost_fa", "ghost_deltoid", "ghost_frame"]),
    solo: [
      { id: "print_fairing_ua", label: "Bicep plate", file: "/cad/armor/print_fairing_ua.stl", color: 0x1f2328 },
      { id: "print_fairing_fa", label: "Forearm dish", file: "/cad/armor/print_fairing_fa.stl", color: 0x252a31 },
      { id: "print_fairing_deltoid", label: "Deltoid window", file: "/cad/armor/print_fairing_deltoid.stl", color: 0x1c2024 },
      { id: "print_fairing_scapula", label: "Yoke dish", file: "/cad/armor/print_fairing_scapula.stl", color: 0x2a3038 },
      { id: "print_fairing_pack_tub", label: "Pack plate", file: "/cad/armor/print_fairing_pack_tub.stl", color: 0x16191d },
      { id: "print_fairing_pack_lid", label: "Drum bezels", file: "/cad/armor/print_fairing_pack_lid.stl", color: 0x1a1e24 },
    ],
  },
} as const;

type Kit = keyof typeof KITS;

function hexToInt(hex: string) {
  return parseInt(hex.replace("#", ""), 16);
}

async function loadThree() {
  const THREE = await import("three");
  const ctl = await import("three/examples/jsm/controls/OrbitControls.js");
  const OrbitControls = ctl.OrbitControls;
  if (!OrbitControls) throw new Error("OrbitControls missing");
  return { THREE, OrbitControls };
}

async function stlGeometry(THREE: typeof import("three"), url: string) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`STL ${res.status}`);
  const buf = await res.arrayBuffer();
  if (buf.byteLength < 84) throw new Error("STL too small");
  const view = new DataView(buf);
  const n = view.getUint32(80, true);
  if (n <= 0 || n > 5_000_000) throw new Error("Bad STL");
  const pos = new Float32Array(n * 9);
  let o = 84;
  for (let i = 0; i < n; i++) {
    o += 12;
    for (let k = 0; k < 9; k++, o += 4) pos[i * 9 + k] = view.getFloat32(o, true);
    o += 2;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  geo.computeVertexNormals();
  return geo;
}

const STILL: Record<Kit, string> = {
  elbow: "/cad/elbow/preview/worn.png",
  shoulder: "/cad/shoulder/preview/worn.png",
  backpack: "/cad/backpack/preview/worn.png",
  system: "/cad/system/preview/worn.png",
  armor: "/cad/armor/preview/worn.png",
};

export function CadViewer({ kit = "elbow" }: { kit?: Kit }) {
  const spec = KITS[kit];
  const host = useRef<HTMLDivElement>(null);
  const [part, setPart] = useState("worn");
  const [status, setStatus] = useState("Still loaded. Tap Load 3D to orbit.");
  const [live, setLive] = useState(false);

  useEffect(() => {
    if (!live) return;
    const el = host.current;
    if (!el) return;
    let dead = false;
    let renderer: import("three").WebGLRenderer | undefined;
    let controls: InstanceType<typeof import("three/examples/jsm/controls/OrbitControls.js").OrbitControls> | undefined;
    let frame = 0;
    const disposers: Array<() => void> = [];

    const fail = (err: unknown) => {
      if (!dead) setStatus(err instanceof Error ? err.message : "Could not load STL");
    };

    const boot = async () => {
      if (dead) return;
      if (el.clientWidth < 16) {
        window.setTimeout(() => void boot().catch(fail), 80);
        return;
      }
      setStatus("Loading STL…");
      const { THREE, OrbitControls } = await loadThree();
      if (dead) return;

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x121214);
      const camera = new THREE.PerspectiveCamera(42, 1, 0.5, 8000);
      const canvas = document.createElement("canvas");
      const gl =
        canvas.getContext("webgl2", { alpha: false, antialias: false, powerPreference: "low-power" }) ||
        canvas.getContext("webgl", { alpha: false, antialias: false, powerPreference: "low-power" });
      if (!gl) {
        setStatus("WebGL blocked here — use the still");
        return;
      }
      renderer = new THREE.WebGLRenderer({ canvas, context: gl as WebGLRenderingContext, antialias: false });
      renderer.setPixelRatio(1);
      el.replaceChildren(renderer.domElement);

      scene.add(new THREE.AmbientLight(0xffffff, 0.55));
      const key = new THREE.DirectionalLight(0xffffff, 1.05);
      key.position.set(160, 200, 120);
      scene.add(key);

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

      const group = new THREE.Group();
      scene.add(group);

      const addMesh = (g: import("three").BufferGeometry, color: number, ghost = false, metal = false) => {
        const m = new THREE.MeshStandardMaterial({
          color,
          metalness: metal ? 0.65 : 0.2,
          roughness: metal ? 0.35 : 0.52,
          transparent: ghost,
          opacity: ghost ? 0.4 : 1,
          depthWrite: !ghost,
        });
        group.add(new THREE.Mesh(g, m));
        disposers.push(() => {
          g.dispose();
          m.dispose();
        });
      };

      const frameCam = () => {
        const box = new THREE.Box3().setFromObject(group);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3()).length() || 180;
        group.position.set(0, 0, 0);
        group.position.sub(center);
        camera.position.set(-size * 0.55, size * 0.22, size * 0.72);
        controls?.target.set(0, 0, 0);
        controls?.update();
      };

      const layerNames = part === "worn" ? spec.worn : part === "brace" ? spec.brace : null;
      const url = layerNames ? spec.fallback : (spec.solo.find((p) => p.id === part) ?? spec.solo[0]).file;
      const geo = await stlGeometry(THREE, url);
      if (dead) {
        geo.dispose();
        return;
      }
      if (!layerNames) geo.center();
      const solo = spec.solo.find((p) => p.id === part);
      addMesh(geo, solo && !layerNames ? solo.color : 0x9aa8ae);
      frameCam();
      setStatus("Drag to orbit · colors loading…");

      const tick = () => {
        if (dead) return;
        controls?.update();
        renderer?.render(scene, camera);
        frame = requestAnimationFrame(tick);
      };
      tick();

      if (!layerNames) {
        setStatus("Drag to orbit · pinch to zoom");
        return;
      }

      let colored = 0;
      const grey = group.children[0];
      for (const name of layerNames) {
        if (dead) return;
        try {
          const g = await stlGeometry(THREE, `${spec.prefix}/asm/${name}.stl`);
          addMesh(
            g,
            hexToInt((spec.swatches as Record<string, string>)[name] ?? "#8aa0a8"),
            spec.ghost.has(name as never),
            name.includes("sheave"),
          );
          colored += 1;
          if (colored === 1 && grey) group.remove(grey);
        } catch {
          /* keep going */
        }
      }
      if (colored > 0) frameCam();
      setStatus("Drag to orbit · pinch to zoom");
    };

    void boot().catch(fail);
    return () => {
      dead = true;
      cancelAnimationFrame(frame);
      disposers.forEach((d) => d());
      controls?.dispose();
      renderer?.dispose();
      renderer?.domElement.remove();
    };
  }, [live, part, kit, spec]);

  return (
    <div className="mb-4">
      <div className="mb-3 flex flex-wrap gap-2">
        {(["worn", "brace"] as const).map((id) => (
          <button
            key={id}
            type="button"
            onClick={() => setPart(id)}
            className={cn(
              "rounded-full border px-3 py-1 font-mono text-[11px] tracking-[0.14em] uppercase",
              part === id ? "border-accent bg-accent/15 text-accent" : "border-border bg-surface text-muted hover:text-fg",
            )}
          >
            {id}
          </button>
        ))}
        {spec.solo.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => setPart(p.id)}
            className={cn(
              "rounded-full border px-3 py-1 font-mono text-[11px] tracking-[0.14em] uppercase",
              part === p.id ? "border-accent bg-accent/15 text-accent" : "border-border bg-surface text-muted hover:text-fg",
            )}
          >
            {p.label}
          </button>
        ))}
        <button
          type="button"
          onClick={() => {
            setLive(true);
            setStatus("Loading STL…");
          }}
          className={cn(
            "rounded-full border px-3 py-1 font-mono text-[11px] tracking-[0.14em] uppercase",
            live ? "border-accent bg-accent/15 text-accent" : "border-border bg-surface text-muted hover:text-fg",
          )}
        >
          Load 3D
        </button>
      </div>
      <div className="overflow-hidden rounded-lg border border-border bg-elevated">
        <div className="relative w-full" style={{ height: 460 }}>
          <img src={STILL[kit]} alt="" className="absolute inset-0 h-full w-full object-contain" />
          {live ? <div ref={host} className="absolute inset-0" /> : null}
        </div>
        <div className="border-t border-border px-4 py-2 font-mono text-[11px] tracking-[0.14em] text-subtle uppercase">
          {status}
        </div>
      </div>
    </div>
  );
}

export function LazyCadViewer({
  kit,
  startOpen = false,
  label,
}: {
  kit: Kit;
  startOpen?: boolean;
  label: string;
}) {
  const [open, setOpen] = useState(startOpen);
  return (
    <details
      open={startOpen}
      onToggle={(e) => setOpen((e.currentTarget as HTMLDetailsElement).open)}
      className="mb-8 rounded-lg border border-border bg-surface p-4"
    >
      <summary className="cursor-pointer font-mono text-xs tracking-[0.18em] text-muted uppercase">{label}</summary>
      <div className="mt-4">{open ? <CadViewer kit={kit} /> : null}</div>
    </details>
  );
}
