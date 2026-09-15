# CDX-3R

Cable-driven right-arm exoskeleton. **3R** = three revolute axes on the right arm (shoulder flexion, shoulder abduction, elbow flexion). Wrist plating is passive.

![CDX-3R holding a crate](public/gallery/hero.jpg)

This repo is the design portal: architecture, physics, cable drive, motion clips, safety, gallery, cost, and sponsor kit.

> Concept design. Not a certified build. Structural analysis, e-stop testing, and battery safety review still required.

## The machine

Motors in the backpack. Bowden cables over the right shoulder. Three powered revolute joints. Left hand stays free for the T-handle.

![Side view — three axes](public/gallery/side.jpg)

| Operator view | Pack internals |
|---|---|
| ![Looking down the armored arm](public/gallery/first-person.jpg) | ![Three winch modules in the backpack](public/gallery/pack.jpg) |

| Shoulder pulleys | Elbow antagonist |
|---|---|
| ![Shoulder sheaves](public/gallery/shoulder.jpg) | ![Elbow pulley](public/gallery/elbow.jpg) |

| Bench winch | E-stop |
|---|---|
| ![Winch module](public/gallery/winch.jpg) | ![Left hand on the red T-handle](public/gallery/estop.jpg) |

## Motion

These clips show the **two lift joints** turning under load. Not a walk-around.

**Coordinated 3R lift** — shoulder flexion, then elbow flexion. Crate from hip to chest. Wrist does not move.

<video src="https://github.com/meetsitaram/cdx-3r/raw/main/public/gallery/lift-3r.mp4" controls muted loop playsinline width="100%"></video>

[Play coordinated lift](https://github.com/meetsitaram/cdx-3r/raw/main/public/gallery/lift-3r.mp4)

**Shoulder flexion** — dual sheaves rotate, cables only pull.

<video src="https://github.com/meetsitaram/cdx-3r/raw/main/public/gallery/shoulder-motion.mp4" controls muted loop playsinline width="100%"></video>

[Play shoulder](https://github.com/meetsitaram/cdx-3r/raw/main/public/gallery/shoulder-motion.mp4)

**Elbow flexion** — antagonist pair wraps the pulley as the forearm closes.

<video src="https://github.com/meetsitaram/cdx-3r/raw/main/public/gallery/elbow-motion.mp4" controls muted loop playsinline width="100%"></video>

[Play elbow](https://github.com/meetsitaram/cdx-3r/raw/main/public/gallery/elbow-motion.mp4)

**Operator view** — looking down the arm as the crate comes up.

<video src="https://github.com/meetsitaram/cdx-3r/raw/main/public/gallery/lift.mp4" controls muted loop playsinline width="100%"></video>

[Play operator view](https://github.com/meetsitaram/cdx-3r/raw/main/public/gallery/lift.mp4)

## Kinematics

Not a 7-DOF industrial arm.

1. Shoulder flexion
2. Shoulder abduction
3. Elbow flexion

## Run locally

```bash
npm install
npm run dev
```

Open [http://localhost:8080](http://localhost:8080).

```bash
npm run build
```

## CAD

Piece by piece. **Elbow is first.**

- [cad/README.md](cad/README.md) — order of work
- [cad/elbow/](cad/elbow/) — McMaster sheave, printable forks/cuffs, physics
Open the site **Build** section — orbit the STLs in the browser. Or:

- STL → PrusaSlicer / Bambu / Blender
- `.scad` → [OpenSCAD](https://openscad.org/)


Do not print `ref_sheave_DO_NOT_PRINT.stl`. Buy [3434T121](https://www.mcmaster.com/3434T121/).


| Path | What |
|---|---|
| `src/routes/index.tsx` | The site |
| `src/lib/cdx.ts` | Specs, gallery, BOM, cost tiers |
| `public/gallery/` | Stills and motion clips |
