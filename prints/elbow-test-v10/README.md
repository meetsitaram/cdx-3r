# Elbow test print v10

This is elbow concept B, built by `cad/fusion/concepts.py` (model `cad/fusion/models/cdx-3r-elbow-concepts.f3d`). Hardware
is in `BOM.md` at the repo root. It pairs with `prints/shoulder-back-v2/`.

## Changes since v9

- **The upper-arm far ring (`07`) is removed.** The upper-arm pipes now run from the elbow's near ring straight into the
  pipe head on the shoulder's upper-arm link. The upper-arm pipes are **127.5 mm** long (the forearm pipes stay 184.8 mm).
- **Axles `03`:** the screw heads sit 1 mm deeper, so all small screws are **M3 × 8** (no more M3 × 10).
- **Covers `04`:** spoked, with an open Ø38.5 centre and 6 windows, so the bearing and axle show. They still hold the bearing's outer ring.
- **Insert holes are Ø4.0 × 7 mm deep** for ruthex RX-M3 × 5.7 inserts (forearm hubs `02`, housings `01`).
- Pipe screws: #4 × 3/8" pan-head self-tapping, 2 per joint, through the Ø3.2 holes.
- **Wrist cuff latch (`05`, `06`, +X side):** Ø5.2 holes for a Ø5 × 30 mm ball-lock quick-release pin; the hinge side stays Ø4.2 for the Ø4 × 25 dowel.
- `01`, `02`, `05` and `06` are otherwise unchanged in shape (re-exported). `01` has the same few mesh defects as in v9. Bambu Studio
  repairs them on import; the v9 print was fine.

## Parts

| File | Qty | Notes |
|---|---|---|
| `00_fit_coupon_pipe_holes.stl` / `00_fit_coupon_bearing_pockets.stl` | 1 each | quick fit tests |
| `01_upper_arm_elbow_piece.stl` | 1 | ring face down; tree supports in the bearing pockets |
| `02_forearm_elbow_piece.stl` | 1 | ring face down |
| `03_bearing_axle_print2.stl` | 2 | flat, pilot up; 3 × M3 × 8 each into the forearm hub inserts |
| `04_bearing_cover_print2.stl` | 2 | flat; 6 × M3 × 8 each |
| `05_wrist_ring.stl` | 1 | flat |
| `06_wrist_cuff.stl` | 1 | flat |

Already printed v9? It still works: press the 5.7 mm inserts flush into the 5.5 mm holes (or run a 4 mm drill to
~7 mm first), and use **M3 × 10** in the v9 axles (their head pocket is 1 mm shallower). Reprint `03` and `04` only if
you want the spoked covers and M3 × 8 everywhere. The v9 `07` far ring is no longer used.
