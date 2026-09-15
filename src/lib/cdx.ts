export const NAV = [
  { id: "system", label: "System" },
  { id: "physics", label: "Physics" },
  { id: "cables", label: "Cables" },
  { id: "motion", label: "Motion" },
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
    src: "/gallery/walk.mp4",
    poster: "/gallery/hero.jpg",
    title: "Worn carry",
    caption: "Two steps with the crate. The 3R suit holds — it does not swing a 7-axis wrist.",
  },
  {
    src: "/gallery/lift.mp4",
    poster: "/gallery/first-person.jpg",
    title: "Elbow flexion",
    caption: "First-person: one revolute axis closing. Cables tighten, then hold.",
  },
  {
    src: "/gallery/spool.mp4",
    poster: "/gallery/winch.jpg",
    title: "Bench winch",
    caption: "The module sponsors should see spin: spool, clutch, brake, known load path.",
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
