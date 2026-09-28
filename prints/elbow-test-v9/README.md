# Elbow test print v9 (current)

Concept B elbow from `cad/fusion/concepts.py`, right arm, all sizes in mm.
Goal: check that the PVC pipes push into the rings and lock with screws, and that the elbow
turns smoothly on its two 6806 bearings.

## What's new in v9

- **Skin-side edges rounded.** Every edge on the inside of the rings, the elbow shells and the
  wrist cuff (the surfaces around your arm) has a 1.5 mm round, where 1.5 mm fits, otherwise
  1.0 mm or a small chamfer. That includes the bore edge of each ring and the rim of the
  upper-arm shell behind the elbow. The hyperextension ledge's steps are rounded 1 mm.
  Rounded before the pipe holes are drilled, so nothing creeps into a hole. Re-checked:
  pipe paths clear, hardware clear, both stops unchanged.

## v8 changes (still included)

- **Axle fixed: it now fits through the bearing.** In v7 the axle had a thin 0.5 mm shoulder
  (Ø32.5) at its inner end, wider than the bearing's Ø30 bore, so it could not be pushed
  through the bearing, and the thin flange would have snapped. The axle is now a plain Ø30
  stub with its Ø16 pilot; the 0.5 mm inner-ring shoulder is a raised ring on the forearm hub
  face instead, backed by the whole hub. Changed: `02` forearm elbow piece, `03` axle.

## v7 changes (still included)

- **All M3.** The axle bolts to the forearm hub with 3 × M3 × 10 (heads sunk in the axle) into
  M3 heat-set inserts; the covers use 6 × M3 × 8 into M3 inserts in the housing. v6 had no
  holes in the housing for the cover screws; v7 does.
- **Pipe screws.** Every pipe joint has 2 radial holes (Ø3.2, 13 mm apart along the pipe) for
  small self-tapping pan-head screws that go straight into the PVC, no insert: #4 × 3/8" or
  M3 × 10 self-tapping. Drill a 2.2 mm pilot into the pipe through each hole once the pipe is in.
- Changed since v6: `01`, `02`, `03`, `04` (hole pattern only), `05`, `07`.

## 0. Fit coupons first (about 30 min each)

| File | What to try |
|---|---|
| `00_fit_coupon_pipe_holes.stl` | Push a PVC pipe (21.5 OD) into each hole: 21.7 / 21.9 / 22.1 / 22.3, marked 1-4 dots. The parts use **21.9**. |
| `00_fit_coupon_bearing_pockets.stl` | Press a 6806 into each pocket from the top: 41.9 / 42.05 / 42.2, marked 1-3 dots. The parts use **42.05**. |

If another size fits better, say which and the parts get re-exported before the long prints.

## 1. Parts

| File | Qty | Print orientation | Notes |
|---|---|---|---|
| `01_upper_arm_elbow_piece.stl` | 1 | Ring face down; the shell rises, bearing housings on top | Tree supports inside the two Ø42 pockets only |
| `02_forearm_elbow_piece.stl` | 1 | Ring face down | Rear stop ledge is a 45° staircase: no support needed |
| `03_bearing_axle_print2.stl` | 2 | Flat on its outer face, pilot up | 3 × M3 to the forearm hub |
| `04_bearing_cover_print2.stl` | 2 | Flat | 6 × M3 into the housing |
| `05_wrist_ring.stl` | 1 | Flat | Back half of the wrist ring; 3 leaning pipe holes; cuff knuckles |
| `06_wrist_cuff.stl` | 1 | Flat | Front half; swings open sideways |
| `07_upper_arm_far_ring.stl` | 1 | Flat | Top ring of the upper arm |

Settings: PETG (or ASA), 0.2 mm layers, 5 walls, 5 top/bottom, 40 % gyroid.
The wrist ring's 80 mm bore and the upper arm's 120 mm bore are placeholders until measured.

## 2. Hardware (one elbow)

| Item | Qty | Where |
|---|---|---|
| 6806-2RS bearing (30 × 42 × 7) | 2 | upper-arm housings |
| M3 × 10 socket head | 6 | axles to forearm hubs |
| M3 × 8 socket head | 12 | covers to housings |
| M3 heat-set insert, 4 long (4.0 mm hole) | 18 | 6 in the forearm hubs, 12 in the housings |
| #4 × 3/8" (or M3 × 10) self-tapping pan head | 24 | 2 per pipe joint, into the PVC |
| 4 mm pin, about 25 long | 1 | wrist cuff hinge (inner side) |
| 4 mm quick-release pin | 1 | wrist cuff latch (outer side) |
| PVC pipe 21.5 OD | 6 | 3 per arm segment |

## 3. Assembly

1. Heat-set the inserts: 3 in each forearm hub face, 6 around each upper-arm housing.
2. Press a bearing into each upper-arm housing, from the inside face.
3. Set the forearm piece inside the upper-arm piece, hubs just inside the bearings.
4. From outside, push an axle through each bearing so its pilot drops into the hub recess;
   screw it down with 3 × M3 × 10.
5. Screw the covers on with 6 × M3 × 8.
6. Rotate: straight (hard stop at the back, about 1° past straight) to 135° (hard stop at the
   hubs) with no rubbing.
7. Push the pipes through the far rings into the elbow-end rings until they seat in the shell,
   drill the 2.2 mm pilots through the screw holes, and drive the pipe screws.

## Checks done in Fusion

- Elbow 0-135° and wrist cuff 0-100° (elbow at 0° and 90°): no collisions.
- Every screw, insert and bearing sits in its hole without touching printed plastic.
- Pipes: a pipe-sized cylinder slid along each pipe's axis through both rings meets 0.0 mm³ of plastic.
- Stops: flexion contact at 135°, hyperextension at about 1° past straight.
- Nothing on the forearm comes within 4.8 mm of the upper arm at full fold.
- Section views in `sections/`.

## How the model is built

Repeated features are modelled once and patterned in Fusion: one pipe (and its ring hole and
2 screw holes) circular-patterned to 3; one axle screw + insert patterned to 3; one cover
screw + insert patterned to 6; the whole lateral bearing set (axle, bearing, cover, screws)
mirrored to the medial side. Editing a seed feature in Fusion updates its copies.
