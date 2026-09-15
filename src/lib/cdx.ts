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
  { n: "01", name: "Elbow", status: "Now", blurb: "Hinge, McMaster sheave, printed forks and cuffs." },
  { n: "02", name: "Shoulder", status: "Next", blurb: "Flexion + abduction sheaves. Same cable rules." },
  { n: "03", name: "Backpack", status: "After", blurb: "Three winches, Hailong 48 V, ODrive S1." },
  { n: "04", name: "Connect", status: "After", blurb: "Bowden runs, comb, system hard stops." },
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
  { file: "print_fork_lateral.stl", note: "Lateral plate. Sheave bolts here, outside the cuff." },
  { file: "print_fork_medial.stl", note: "Medial hinge. No sheave. Completes the yoke." },
  { file: "print_cuff_forearm.stl", note: "C-cuff. Arm goes through. Foam inside." },
  { file: "print_cuff_upper.stl", note: "Same, ~95 mm proximal of the axis." },
  { file: "print_bowden_anchor.stl", note: "Print two. On the lateral plate, not on the cuff ID." },
  { file: "print_hard_stop.stl", note: "Hits before your elbow does." },
  { file: "print_idler_cup.stl", note: "Optional spare cups. Already on the lateral plate." },
  { file: "print_drum.stl", note: "Only if 3434T121 is late. Not 15 kg." },
] as const;

export const ELBOW_PREVIEWS = [
  { src: "/cad/elbow/preview/worn.png?v=2", title: "Worn — arm through, sheave outboard" },
  { src: "/cad/elbow/preview/assembly.png?v=2", title: "Brace only" },
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
  { id: "lateral", label: "Lateral plate", hex: "#f2f4f7" },
  { id: "medial", label: "Medial plate", hex: "#4b5568" },
  { id: "sheave", label: "3434T121 sheave", hex: "#ffc93c" },
  { id: "screw", label: "Shoulder screw", hex: "#111215" },
  { id: "bearing", label: "608-2RS", hex: "#ff6a1a" },
  { id: "nylock", label: "Nylock", hex: "#ef4444" },
  { id: "anchor", label: "Bowden anchor", hex: "#22c55e" },
  { id: "stop", label: "Hard stop", hex: "#facc15" },
] as const;
