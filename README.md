# CDX-3R

Cable-driven right-arm exoskeleton. **3R** = three revolute axes on the right arm (shoulder flexion, shoulder abduction, elbow flexion). Wrist plating is passive.

This repo is the design portal: architecture, physics, cable drive, motion clips, safety, gallery, cost, and sponsor kit.

> Concept design. Not a certified build. Structural analysis, e-stop testing, and battery safety review still required.

## Run locally

```bash
npm install
npm run dev
```

Then open [http://localhost:8080](http://localhost:8080).

```bash
npm run build
```

## Layout

| Path | What |
|---|---|
| `src/routes/index.tsx` | The site |
| `src/lib/cdx.ts` | Specs, gallery, BOM, cost tiers |
| `public/gallery/` | Stills and motion clips |

## Kinematics

Not a 7-DOF industrial arm.

1. Shoulder flexion
2. Shoulder abduction
3. Elbow flexion

Motors live in the backpack. Bowden cables run over the right shoulder. Left hand stays free for the T-handle e-stop.
