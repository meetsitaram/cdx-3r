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

## Physics

Pitch radius r = 38.1 mm (3434T121). Lever ≈ 0.35 m.

| Crate | τ | Cable T |
|---|---|---|
| 5 kg garage | 17 N·m | 450 N — Jagwire |
| 15 kg | 51 N·m | 1350 N — 1/8 in 7×19 |

## Human (edit `../params.json`)

290 / 260 / 90 mm · cuff ID 105 / 95 mm · ROM 0–135°.

## Buy / print

Same BOM. New prints: `print_fork_lateral.stl` (the plate the sheave bolts to), `print_fork_medial.stl` (yoke). Do not print `ref_arm_ghost` or `ref_sheave`.
