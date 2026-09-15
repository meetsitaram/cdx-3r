# CDX-3R elbow

The arm goes **through the cuffs**. The sheave does **not**.

This is an orthopedic-brace layout, not a pulley stuffed inside the elbow.

```
 medial plate                         lateral plate + SHEAVE
     |                                        |
     |     [ upper cuff  ○ arm ○ ]            |
     |______________ hinge axis ______________|
     |     [ forearm cuff ○ arm ○ ]           |
```

- Origin = anatomical flexion axis (through the epicondyles).
- Cuffs: C-rings, open medial, straps. Inner volume is the wearer.
- Lateral plate: sagittal, outboard of the cuff OD. McMaster sheave lives here.
- Medial plate: light hinge only. No through-bolt through flesh.
- 90° work pose in the assembly: upper arm −X, forearm +Y.

## Attach the real hardware

Stack, outboard → inboard:

1. **91273A274** 3/4 in shoulder screw (head outboard)
2. 3/4 in washer
3. **3434T121** sheave (sleeve bearing already in it)
4. Lateral plate (printed) — 19.2 mm hole
5. 3/4 in washer
6. **90640A125** nylock

Cable fairleads: press **6455K44** (608-2RS) into the two printed cups on the plate. **M8×25** through the bore into an M8 heat-set.

Same 3/4 in hole takes **3434T157** (sealed ball, ~$133) if you want to upgrade the sheave later. Do not reprint.

## Physics

Pitch radius r = 38.1 mm (3434T121). Lever ≈ 0.35 m.

| Crate | τ | Cable T |
|---|---|---|
| 5 kg garage | 17 N·m | 450 N — Jagwire |
| 15 kg | 51 N·m | 1350 N — 1/8 in 7×19 |

## Human (edit `../params.json`)

290 / 260 / 90 mm · cuff ID 105 / 95 mm · ROM 0–135°.

## Buy / print

See the site **Build** list. Do not print `ref_*` files.
