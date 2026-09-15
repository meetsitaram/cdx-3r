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
    why: "Rated 1550 lb groove, 3/4 in bore",
    href: "https://www.mcmaster.com/3434T121/",
  },
  {
    qty: "1",
    item: "3/4 in × 100 mm shaft",
    why: "Elbow axis",
    href: "https://www.mcmaster.com/1346K17/",
  },
  {
    qty: "2",
    item: "25 mm OD tube stubs",
    why: "Upper arm + forearm spars",
    href: "https://www.mcmaster.com/89995K31/",
  },
  {
    qty: "1",
    item: "Jagwire 1.5 mm + 5 mm housing",
    why: "Garage flexor / extensor",
    href: "https://www.jagwire.com/",
  },
  {
    qty: "8",
    item: "M4 heat-set inserts",
    why: "Forks and hub",
    href: "https://www.mcmaster.com/94180A351/",
  },
] as const;

export const ELBOW_PRINT = [
  { file: "print_fork_lateral.stl", note: "PETG, 5 walls, flat on bed" },
  { file: "print_fork_medial.stl", note: "Mirror. Inserts from the outside" },
  { file: "print_forearm_hub.stl", note: "PA12-CF if you have it" },
  { file: "print_cuff_forearm.stl", note: "C-cuff, foam inside" },
  { file: "print_cuff_upper.stl", note: "~80 mm proximal of the axis" },
  { file: "print_bowden_anchor.stl", note: "Print two. 5 mm ferrule seat" },
  { file: "print_hard_stop.stl", note: "Hits before your elbow does" },
  { file: "print_drum.stl", note: "Only if the McMaster sheave is late. Not 15 kg" },
] as const;

export const ELBOW_PREVIEWS = [
  { src: "/cad/elbow/preview/assembly.png", title: "Assembly" },
  { src: "/cad/elbow/preview/sheave.png", title: "Buy — sheave" },
  { src: "/cad/elbow/preview/fork.png", title: "Print — fork" },
  { src: "/cad/elbow/preview/hub.png", title: "Print — hub" },
  { src: "/cad/elbow/preview/cuff.png", title: "Print — cuff" },
  { src: "/cad/elbow/preview/drum.png", title: "Print — drum" },
  { src: "/cad/elbow/preview/anchor.png", title: "Print — anchor" },
  { src: "/cad/elbow/preview/stop.png", title: "Print — stop" },
] as const;
