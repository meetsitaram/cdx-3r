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

Clips are muted, six seconds, H.264. Click play if they do not autoplay.

**Worn carry** — two steps with the crate.

<video src="https://github.com/meetsitaram/cdx-3r/raw/main/public/gallery/walk.mp4" controls muted loop playsinline width="100%"></video>

[Play worn carry](https://github.com/meetsitaram/cdx-3r/raw/main/public/gallery/walk.mp4)

**Elbow flexion** — first-person lift.

<video src="https://github.com/meetsitaram/cdx-3r/raw/main/public/gallery/lift.mp4" controls muted loop playsinline width="100%"></video>

[Play elbow flexion](https://github.com/meetsitaram/cdx-3r/raw/main/public/gallery/lift.mp4)

**Bench winch** — spool, clutch, brake.

<video src="https://github.com/meetsitaram/cdx-3r/raw/main/public/gallery/spool.mp4" controls muted loop playsinline width="100%"></video>

[Play bench winch](https://github.com/meetsitaram/cdx-3r/raw/main/public/gallery/spool.mp4)

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

## Layout

| Path | What |
|---|---|
| `src/routes/index.tsx` | The site |
| `src/lib/cdx.ts` | Specs, gallery, BOM, cost tiers |
| `public/gallery/` | Stills and motion clips |
