# Elbow test print v10

This is elbow concept B, built by `cad/fusion/concepts.py` (model `cad/fusion/models/cdx-3r-elbow-concepts.f3d`). Hardware
is in `BOM.md` at the repo root. It pairs with `prints/shoulder-back-v2/`.

## Changes since v9

- **The upper-arm far ring (`07`) is removed.** The upper-arm pipes now run from the elbow's near ring straight into the
  pipe head on the shoulder's upper-arm link. The upper-arm pipes are **127.5 mm** long (the forearm pipes stay 184.8 mm).
- **Axles `03`:** the screw heads sit 1 mm deeper, so all small screws are **M3 × 8** (no more M3 × 10).
- **Covers `04`:** spoked, with an open Ø38.5 centre and 6 windows, so the bearing and axle show. They still hold the bearing's outer ring.
- `01`, `02`, `05` and `06` are unchanged in shape (re-exported). `01` has the same few mesh defects as in v9. Bambu Studio
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

Only `03` and `04` need reprinting if you already have v9 printed. The v9 `07` far ring is no longer used.
