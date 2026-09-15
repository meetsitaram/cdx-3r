export const NAV = [
  { id: "system", label: "System" },
  { id: "physics", label: "Physics" },
  { id: "cables", label: "Cables" },
  { id: "motion", label: "Motion" },
  { id: "cad", label: "Build" },
  { id: "safety", label: "Safety" },
  { id: "gallery", label: "Gallery" },
  { id: "cost", label: "Cost" },
  { id: "sponsor", label: "Sponsor" },
] as const;

export const STATS = [
  { k: "Designation", v: "CDX-3R" },
  { k: "Kinematics", v: "3 revolute" },
  { k: "Side", v: "Right arm" },
  { k: "Target load", v: "15–20 kg" },
  { k: "Pack voltage", v: "48 V" },
  { k: "Release", v: "Left-hand T-handle" },
] as const;

export const GALLERY = [
  {
    src: "/gallery/hero.jpg",
    title: "Whole suit",
    caption: "Carbon-titanium pack, Bowden run, armored right arm, crate in the mech hand.",
  },
  {
    src: "/gallery/first-person.jpg",
    title: "Operator view",
    caption: "First-person look down the armored arm while holding a load.",
  },
  {
    src: "/gallery/pack.jpg",
    title: "Pack internals",
    caption: "Three winch modules, clutch/brake stack, battery sled, cable comb.",
  },
  {
    src: "/gallery/winch.jpg",
    title: "Winch module",
    caption: "The one live bench unit sponsors should actually see spin.",
  },
  {
    src: "/gallery/shoulder.jpg",
    title: "Shoulder pulleys",
    caption: "Dual sheaves — flexion and abduction planes, cables only pull.",
  },
  {
    src: "/gallery/elbow.jpg",
    title: "Elbow",
    caption: "Antagonist pair wrapping a circular pulley at the joint.",
  },
  {
    src: "/gallery/side.jpg",
    title: "Three axes",
    caption: "Shoulder flexion, shoulder abduction, elbow. Wrist stays passive plating.",
  },
  {
    src: "/gallery/estop.jpg",
    title: "E-stop pull",
    caption: "Left hand on the red T-handle. One yank dumps clutch and brake.",
  },
] as const;

export const MOTION = [
  {
    src: "/gallery/lift-3r.mp4",
    poster: "/gallery/lift-3r.jpg",
    title: "Coordinated 3R lift",
    caption:
      "Load path: hip → chest. Shoulder flexion first (upper arm rotates on the sheave), then elbow flexion (forearm closes on the pulley). Wrist plating does not move.",
    featured: true,
  },
  {
    src: "/gallery/shoulder-motion.mp4",
    poster: "/gallery/shoulder.jpg",
    title: "Shoulder flexion",
    caption: "Dual sheaves. Cables only pull. The glenohumeral flexion plane raises the crate.",
    featured: false,
  },
  {
    src: "/gallery/elbow-motion.mp4",
    poster: "/gallery/elbow.jpg",
    title: "Elbow flexion",
    caption: "Antagonist pair wraps the circular pulley. One side pays in, the other pays out.",
    featured: false,
  },
  {
    src: "/gallery/lift.mp4",
    poster: "/gallery/first-person.jpg",
    title: "Operator view",
    caption: "Looking down the arm while the elbow pulley turns and the crate comes up.",
    featured: false,
  },
] as const;

export const BOM = [
  { item: "3× BLDC + planetary gearbox", low: "$600", high: "$2,500" },
  { item: "3× motor drivers (ODrive-class)", low: "$450", high: "$800" },
  { item: "Clutches + disc brakes", low: "$300", high: "$900" },
  { item: "48 V battery sled + BMS", low: "$250", high: "$700" },
  { item: "Bowden housing, inners, ferrules", low: "$80", high: "$200" },
  { item: "Pulleys, bearings, hard stops", low: "$200", high: "$600" },
  { item: "Harness, cuffs, armor plates", low: "$400", high: "$2,000" },
  { item: "Controllers, sensors, wiring", low: "$350", high: "$1,200" },
] as const;

export const COST_TIERS = [
  {
    id: "garage",
    name: "Garage prototype",
    range: "$3k–$6k",
    blurb: "Three cheap winches, printed cuffs, no pretty armor. Proves torque. Will not look like the renders.",
    parts: "$1.8k–$3k",
    labor: "$1k–$3k (you)",
  },
  {
    id: "serious",
    name: "Serious one-off",
    range: "$8k–$18k",
    blurb: "Real metals, brakes and clutches, wearable harness. 20 kg class. Not pretty, not a costume.",
    parts: "$4k–$8k",
    labor: "$4k–$10k",
  },
  {
    id: "render",
    name: "Render-level suit",
    range: "$25k–$50k",
    blurb: "Carbon/titanium, fitted armor, safety review. Looks like the concept. Do not promise this on a $5k budget.",
    parts: "$8k–$15k",
    labor: "$15k–$35k",
  },
  {
    id: "lookalike",
    name: "Look-alike only",
    range: "$400–$3.5k",
    blurb: "Shape, paint, LEDs. Photographs like the machine. Cannot carry a crate. Use only as a booth shell.",
    parts: "$250–$1.2k",
    labor: "You, or $1.2k–$3.5k commissioned",
  },
] as const;

export const SPONSOR_SPLIT = [
  { piece: "Exterior armor, pack, cables, LEDs", real: "Look-alike, high finish", why: "Photos and booth" },
  { piece: "One elbow or shoulder winch on a bench", real: "Real, instrumented", why: "Proves τ = T × r" },
  { piece: "Full 30 kg worn lift", real: "Not yet", why: "Injury risk and money sink" },
] as const;

export const CAD_STAGES = [
  { n: "01", name: "Elbow", status: "Done", blurb: "Hinge, McMaster sheave, printed forks and cuffs." },
  { n: "02", name: "Shoulder", status: "Done", blurb: "Flexion (lateral) + abduction (posterior)." },
  { n: "03", name: "Backpack", status: "Done", blurb: "3× D6374 + 10:1, Hailong 48 V, 3× ODrive S1." },
  { n: "04", name: "Connect", status: "Now", blurb: "One system. Saddle + hip belt take the weight, not the biceps." },
  { n: "05", name: "Armor", status: "Last", blurb: "Plates on the structure. Straps. Not costume first." },
] as const;

export const ELBOW_HUMAN = [
  { k: "Upper arm", v: "290 mm", d: "Shoulder axis to elbow axis" },
  { k: "Forearm", v: "260 mm", d: "Elbow axis to wrist" },
  { k: "Hand", v: "90 mm", d: "Adds to crate lever" },
  { k: "Elbow width", v: "80 mm", d: "Epicondyle to epicondyle" },
  { k: "Forearm cuff ID", v: "95 mm", d: "Skin + 8 mm foam" },
  { k: "ROM", v: "0–135°", d: "Hard stop before anatomy" },
] as const;

export const ELBOW_PHYSICS = [
  { k: "τ = T × r", v: "r = 38.1 mm", d: "3 in pitch, McMaster 3434T121" },
  { k: "5 kg garage", v: "17 N·m → 450 N", d: "Jagwire 1.5 mm is in this band" },
  { k: "15 kg target", v: "51 N·m → 1350 N", d: "1/8 in 7×19. Same printed forks." },
] as const;

export const ELBOW_BUY = [
  {
    qty: "1",
    item: "McMaster 3434T121 sheave",
    why: "3.5 in OD, 3/4 in bore, sleeve bearing inside, 1550 lb. $25.",
    href: "https://www.mcmaster.com/3434T121/",
  },
  {
    qty: "1",
    item: "McMaster 91273A274 shoulder screw",
    why: "3/4 in × 1.5 in 18-8. Head traps the sheave against the plate.",
    href: "https://www.mcmaster.com/91273A274/",
  },
  {
    qty: "1",
    item: "McMaster 90640A125 nylock 3/4-10",
    why: "On the inside of the lateral plate.",
    href: "https://www.mcmaster.com/90640A125/",
  },
  {
    qty: "2",
    item: "McMaster 91083A033 washer 3/4 in",
    why: "One under the head, one under the nut.",
    href: "https://www.mcmaster.com/91083A033/",
  },
  {
    qty: "2",
    item: "McMaster 6455K44 608-2RS",
    why: "8×22×7 mm sealed. Cable fairleads. Press into printed cups.",
    href: "https://www.mcmaster.com/6455K44/",
  },
  {
    qty: "2",
    item: "McMaster 91290A194 M8×25 SHCS",
    why: "Through each 608 into an M8 heat-set.",
    href: "https://www.mcmaster.com/91290A194/",
  },
  {
    qty: "2",
    item: "McMaster 94180A411 M8 heat-set",
    why: "In the lateral plate, under each idler.",
    href: "https://www.mcmaster.com/94180A411/",
  },
  {
    qty: "8",
    item: "McMaster 94180A351 M4 heat-set",
    why: "Cuffs and plate joints.",
    href: "https://www.mcmaster.com/94180A351/",
  },
] as const;

export const ELBOW_PRINT = [
  { file: "print_fork_lateral.stl", note: "Upper-arm plate. Bowden housing stops here." },
  { file: "print_fork_distal.stl", note: "Forearm plate. Bolts to the sheave. Rotates." },
  { file: "print_fork_medial.stl", note: "Medial hinge. No sheave. Completes the yoke." },
  { file: "print_cuff_forearm.stl", note: "C-cuff. Arm goes through. Foam inside." },
  { file: "print_cuff_upper.stl", note: "Same, ~95 mm proximal of the axis." },
  { file: "print_bowden_anchor.stl", note: "Print two. On the lateral plate, not on the cuff ID." },
  { file: "print_hard_stop.stl", note: "Hits before your elbow does." },
  { file: "print_idler_cup.stl", note: "Optional spare cups. Already on the lateral plate." },
  { file: "print_drum.stl", note: "Only if 3434T121 is late. Not 15 kg." },
] as const;

export const ELBOW_PREVIEWS = [
  { src: "/cad/elbow/preview/worn.png?v=4", title: "Worn — cables up to the shoulder" },
  { src: "/cad/elbow/preview/assembly.png?v=4", title: "Brace only" },
  { src: "/cad/elbow/preview/sheave.png?v=2", title: "Buy — 3434T121 sheave" },
  { src: "/cad/elbow/preview/bearing.png?v=2", title: "Buy — 608-2RS" },
  { src: "/cad/elbow/preview/screw.png?v=2", title: "Buy — 3/4 in shoulder screw" },
  { src: "/cad/elbow/preview/fork.png?v=2", title: "Print — lateral plate" },
  { src: "/cad/elbow/preview/hub.png?v=2", title: "Print — medial plate" },
  { src: "/cad/elbow/preview/cuff.png?v=2", title: "Print — cuff (arm goes through)" },
  { src: "/cad/elbow/preview/anchor.png?v=2", title: "Print — Bowden anchor" },
  { src: "/cad/elbow/preview/stop.png?v=2", title: "Print — hard stop" },
] as const;

export const ELBOW_SWATCHES = [
  { id: "arm", label: "Ghost arm", hex: "#f3c6a5" },
  { id: "cuff_upper", label: "Upper cuff", hex: "#12b5d4" },
  { id: "cuff_forearm", label: "Forearm cuff", hex: "#5ee0ff" },
  { id: "lateral", label: "Upper-arm plate", hex: "#f2f4f7" },
  { id: "distal", label: "Forearm plate", hex: "#cbd5e1" },
  { id: "medial", label: "Medial plate", hex: "#4b5568" },
  { id: "sheave", label: "3434T121 sheave", hex: "#ffc93c" },
  { id: "housing", label: "Bowden housing", hex: "#1f2937" },
  { id: "cable_flex", label: "Flexor inner", hex: "#e879f9" },
  { id: "cable_ext", label: "Extensor inner", hex: "#818cf8" },
  { id: "clamp", label: "Cable clamp on sheave", hex: "#fb7185" },
  { id: "anchor", label: "Housing ferrule (stops here)", hex: "#22c55e" },
  { id: "bearing", label: "608 fairlead", hex: "#ff6a1a" },
] as const;

export const SHOULDER_PHYSICS = [
  { k: "Flexion sheave", v: "Lateral · gold", d: "3434T121, ML axis, like the elbow" },
  { k: "Abduction sheave", v: "Posterior · orange", d: "3434T121, AP axis, toward the pack" },
  { k: "5 kg at 0.65 m", v: "32 N·m → 840 N", d: "Longer lever than the elbow. Jagwire is tight." },
  { k: "15 kg at 0.65 m", v: "96 N·m → 2500 N", d: "1/8 in 7×19. Not PETG." },
] as const;

export const SHOULDER_BUY = [
  {
    qty: "2",
    item: "McMaster 3434T121 sheave",
    why: "One flexion (lateral), one abduction (posterior)",
    href: "https://www.mcmaster.com/3434T121/",
  },
  {
    qty: "2",
    item: "McMaster 91273A274 shoulder screw",
    why: "3/4 in × 1.5 in. Same stack as the elbow.",
    href: "https://www.mcmaster.com/91273A274/",
  },
  {
    qty: "4",
    item: "McMaster 6455K44 608-2RS",
    why: "Fairleads on both sheaves",
    href: "https://www.mcmaster.com/6455K44/",
  },
] as const;

export const SHOULDER_PRINT = [
  { file: "print_scapula.stl", note: "Scapula pad. Pack straps bolt here." },
  { file: "print_abd_yoke.stl", note: "Abduction yoke. Carries the flexion sheave." },
  { file: "print_flex_yoke.stl", note: "Flexion yoke. Beam toward the elbow." },
  { file: "print_deltoid_cuff.stl", note: "Deltoid C-cuff. Arm goes through." },
  { file: "print_cable_comb.stl", note: "Elbow Bowden passes. Does not wrap the shoulder." },
] as const;

export const SHOULDER_PREVIEWS = [
  { src: "/cad/shoulder/preview/worn.png", title: "Worn — 2R shoulder" },
  { src: "/cad/shoulder/preview/assembly.png", title: "Brace only" },
  { src: "/cad/shoulder/preview/flex.png", title: "Buy — flexion sheave (lateral)" },
  { src: "/cad/shoulder/preview/abd.png", title: "Buy — abduction sheave (posterior)" },
  { src: "/cad/shoulder/preview/scapula.png", title: "Print — scapula pad" },
  { src: "/cad/shoulder/preview/yoke.png", title: "Print — flexion yoke" },
  { src: "/cad/shoulder/preview/cuff.png", title: "Print — deltoid cuff" },
  { src: "/cad/shoulder/preview/comb.png", title: "Print — elbow cable comb" },
] as const;

export const SHOULDER_SWATCHES = [
  { id: "sheave_flex", label: "Flexion sheave", hex: "#ffc93c" },
  { id: "sheave_abd", label: "Abduction sheave", hex: "#f97316" },
  { id: "cable_flex", label: "Flexion inner", hex: "#e879f9" },
  { id: "cable_abd", label: "Abduction inner", hex: "#818cf8" },
  { id: "cable_elbow", label: "Elbow pass-through", hex: "#38bdf8" },
  { id: "comb", label: "Comb", hex: "#14b8a6" },
  { id: "cuff", label: "Deltoid cuff", hex: "#5ee0ff" },
] as const;

export const PACK_PHYSICS = [
  { k: "Drum r", v: "20 mm", d: "Printed, on the 14 mm planetary output" },
  { k: "Elbow 5 kg", v: "9 N·m → 0.9 N·m", d: "After 10:1. D6374 is fine." },
  { k: "Shoulder 5 kg", v: "17 N·m → 1.7 N·m", d: "Peak. Not 15 kg." },
  { k: "Bus", v: "48 V · 3× S1", d: "Hailong 13 Ah. XT90." },
] as const;

export const PACK_BUY = [
  {
    qty: "3",
    item: "ODrive S1",
    why: "One axis each. 12–48 V, 40 A continuous with heat spreader.",
    href: "https://shop.odriverobotics.com/products/odrive-s1",
  },
  {
    qty: "3",
    item: "ODrive D6374 150 kV",
    why: "10 mm shaft, 8 mm rear for AMT212. 4 mm bullets included.",
    href: "https://shop.odriverobotics.com/products/odrive-custom-motor-d6374-150kv",
  },
  {
    qty: "3",
    item: "PLE60 10:1 planetary",
    why: "10 mm in, 14 mm out. Matches D6374. Drum bolts here.",
    href: "https://www.omc-stepperonline.com/",
  },
  {
    qty: "3",
    item: "CUI AMT212 encoder",
    why: "On the D6374 rear 8 mm. Talks to S1.",
    href: "https://www.cuidevices.com/product/motion/rotary-encoders/incremental/modular/amt21-series",
  },
  {
    qty: "1",
    item: "Hailong 48 V 13 Ah",
    why: "367×90×111 mm, ~4 kg, XT90. E-bike down-tube pack.",
    href: "https://yosepower.com/products/48v-13ah-down-tube-hailong1-2-battery-lithium-ion-accu-e-bike-electric-bicycle-bottle-new-black-diy",
  },
  {
    qty: "6",
    item: "M5 barrel adjusters + Jagwire 5 mm ferrules",
    why: "Bulkhead. Antagonist pair per axis.",
    href: "https://www.jagwire.com/",
  },
  {
    qty: "6",
    item: "McMaster 6455K44 608-2RS",
    why: "Drum support, same as the arm fairleads.",
    href: "https://www.mcmaster.com/6455K44/",
  },
] as const;

export const PACK_PRINT = [
  { file: "print_frame.stl", note: "Pack shell. Straps bolt to the sides." },
  { file: "print_sled.stl", note: "Hailong dovetail. Battery slides in." },
  { file: "print_drum.stl", note: "Print three. 20 mm pitch radius." },
  { file: "print_bulkhead.stl", note: "Six M5 barrels. Housing stops here." },
] as const;

export const PACK_PREVIEWS = [
  { src: "/cad/backpack/preview/worn.png", title: "Worn — pack on the back" },
  { src: "/cad/backpack/preview/assembly.png", title: "Pack only" },
  { src: "/cad/backpack/preview/battery.png", title: "Buy — Hailong 48 V" },
  { src: "/cad/backpack/preview/motor.png", title: "Buy — D6374" },
  { src: "/cad/backpack/preview/gear.png", title: "Buy — 10:1 planetary" },
  { src: "/cad/backpack/preview/s1.png", title: "Buy — ODrive S1" },
  { src: "/cad/backpack/preview/drum.png", title: "Print — winch drum" },
  { src: "/cad/backpack/preview/bulkhead.png", title: "Print — cable bulkhead" },
] as const;

export const PACK_SWATCHES = [
  { id: "battery", label: "Hailong 48 V", hex: "#14532d" },
  { id: "motor", label: "D6374 + gearbox", hex: "#111215" },
  { id: "s1", label: "ODrive S1", hex: "#16a34a" },
  { id: "xt90", label: "XT90", hex: "#f97316" },
  { id: "bulkhead", label: "M5 barrels", hex: "#22c55e" },
  { id: "cable_el", label: "Elbow pair", hex: "#38bdf8" },
  { id: "cable_flex", label: "Flexion pair", hex: "#e879f9" },
  { id: "cable_abd", label: "Abduction pair", hex: "#818cf8" },
] as const;

export const SYSTEM_PHYSICS = [
  { k: "Exo mass path", v: "Saddle + belt", d: "Not the cuffs. Not the biceps." },
  { k: "Saddle", v: "Trapezius / acromion", d: "Amber pad. This is where it sits." },
  { k: "Park rest", v: "Forearm shelf", d: "Red. Rest pose. Arm can leave the cuffs." },
  { k: "UA beam", v: "Lateral tube", d: "GH to elbow. Outside the arm." },
] as const;

export const SYSTEM_PRINT = [
  { file: "print_saddle.stl", note: "Shoulder saddle. Exo rests here." },
  { file: "print_yoke.stl", note: "Pack to saddle. Load path." },
  { file: "print_ua_beam.stl", note: "Lateral upper-arm beam. Not through flesh." },
  { file: "print_hip_belt.stl", note: "Pack weight to the hips." },
  { file: "print_park_rest.stl", note: "Forearm sits here in rest. Biceps idle." },
] as const;

export const SYSTEM_PREVIEWS = [
  { src: "/cad/system/preview/worn.png", title: "Worn — full system" },
  { src: "/cad/system/preview/loadpath.png", title: "Load path — saddle + park" },
  { src: "/cad/system/preview/saddle.png", title: "Print — shoulder saddle" },
  { src: "/cad/system/preview/yoke.png", title: "Print — pack yoke" },
  { src: "/cad/system/preview/beam.png", title: "Print — UA beam" },
  { src: "/cad/system/preview/belt.png", title: "Print — hip belt" },
  { src: "/cad/system/preview/park.png", title: "Print — park rest" },
] as const;

export const SYSTEM_SWATCHES = [
  { id: "saddle", label: "Shoulder saddle", hex: "#f59e0b" },
  { id: "park", label: "Park rest", hex: "#ef4444" },
  { id: "yoke", label: "Pack yoke", hex: "#e2e8f0" },
  { id: "beam", label: "UA beam", hex: "#94a3b8" },
  { id: "belt", label: "Hip belt", hex: "#78716c" },
] as const;
