# Elbow test print v6 (current)

Concept B elbow from `cad/fusion/concepts.py`, right arm, all sizes in mm.
Goal: check that the PVC pipes push into the rings and that the elbow turns smoothly on its
two 6806 bearings.

## What's new in v6: axle bolted to the forearm (option A)

- The bearing axle is a flanged stub bolted to the forearm hub, like a wheel on its hub.
  A Ø16 × 3 pilot on the axle drops into a recess in the hub; it centres the axle and takes the
  load in shear. 3 × M4 screws, heads sunk into the axle, clamp it into heat-set inserts in the hub.
- A 0.5 mm shoulder on the axle (Ø32.5) is the only thing touching the bearing, on its inner
  ring. The hub face is relieved 1 mm so it can't rub the outer ring or seal.
- The housing's retaining lip hole is Ø39.5, so it touches only the bearing's outer ring.
- Changed since v5: `01`, `02`, `03`. The others are unchanged apart from re-export.

## 0. Fit coupons first (about 30 min each)

| File | What to try |
|---|---|
| `00_fit_coupon_pipe_holes.stl` | Push a PVC pipe (21.5 OD) into each hole: 21.7 / 21.9 / 22.1 / 22.3, marked 1-4 dots. The parts use **21.9**. |
| `00_fit_coupon_bearing_pockets.stl` | Press a 6806 into each pocket from the top: 41.9 / 42.05 / 42.2, marked 1-3 dots. The parts use **42.05**. |

If another size fits better, say which and the parts get re-exported before the long prints.
In the upper-arm piece the pockets print on their side, so they may come out slightly tighter
than on the coupon.

## 1. Parts

| File | Qty | Print orientation | Notes |
|---|---|---|---|
| `01_upper_arm_elbow_piece.stl` | 1 | Ring face down; the shell rises, bearing housings on top | 160 × 132 × 109. Tree supports inside the two Ø42 pockets only |
| `02_forearm_elbow_piece.stl` | 1 | Ring face down | Rear stop ledge is a 45° staircase: no support needed |
| `03_bearing_axle_print2.stl` | 2 | Flat on its outer face, pilot up | 3 × M4 to the forearm hub |
| `04_bearing_cover_print2.stl` | 2 | Flat | 6 × M3 into the housing |
| `05_wrist_ring.stl` | 1 | Flat | Back half of the wrist ring; 3 leaning pipe holes; cuff knuckles |
| `06_wrist_cuff.stl` | 1 | Flat | Front half; swings open sideways |
| `07_upper_arm_far_ring.stl` | 1 | Flat | Top ring of the upper arm |

Settings: PETG (or ASA), 0.2 mm layers, 5 walls, 5 top/bottom, 40 % gyroid.
The wrist ring's 80 mm bore and the upper arm's 120 mm bore are placeholders until measured.

## 2. Hardware (one elbow)

- 2 × 6806-2RS bearing (30 × 42 × 7)
- 6 × M4 × 12 socket head screws + 6 × M4 heat-set inserts (axles to forearm hub)
- 12 × M3 × 8 screws + 12 × M3 heat-set inserts (covers)
- Wrist cuff: 1 × 4 mm pin about 25 mm (hinge, inner side) + 1 × 4 mm quick-release pin (latch, outer side)
- PVC pipe 21.5 OD: 3 per arm segment

## 3. Assembly

1. Heat-set the inserts: 3 × M4 in each forearm hub face, 6 × M3 around each upper-arm housing.
2. Press a bearing into each upper-arm housing, from the inside face.
3. Set the forearm piece inside the upper-arm piece, hubs just inside the bearings.
4. From outside, push an axle through each bearing so its pilot drops into the hub recess;
   screw it down with 3 × M4.
5. Screw the covers on.
6. Rotate: straight (hard stop at the back, about 1° past straight) to 135° (hard stop at the
   hubs) with no rubbing.
7. Push the pipes through the far rings into the elbow-end rings until they seat in the shell.

## Checks done in Fusion

- Elbow 0-135° and wrist cuff 0-100° (elbow at 0° and 90°): no collisions.
- Pipes: sliding a pipe-sized cylinder along each pipe's axis through both rings meets
  0.0 mm³ of plastic, for all 6 pipes.
- Stops: flexion contact at 135°, hyperextension at about 1° past straight.
- Nothing on the forearm comes within 4.8 mm of the upper arm at full fold.
- Section views in `sections/`.
