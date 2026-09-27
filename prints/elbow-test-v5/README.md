# Elbow test print v5  (current; replaces v4)

**v5 vs v4:** fixes the pipe holes. In v4 the rounded edges were added after the holes were
drilled, which left a thin fin inside each leaning (forearm) pipe hole, the one you spotted in
the slicer. Now the edges are rounded first, every hole is drilled last, and each hole is
checked by sliding a pipe-sized cylinder along the pipe's own axis through both rings:
0.0 mm3 of plastic in the way, for all 6 pipes. At the elbow-end rings the pipe now seats in a
3 mm pocket in the shell. Section views: `sections/4_*` and `sections/5_*`.
**v4 vs v3:** same elbow parts (01-04 are byte-identical to v3), plus the wrist and upper-arm
far rings so you can test the whole forearm/upper-arm fit:
- `05_wrist_ring.stl` - back half of the wrist ring, 3 leaning pipe holes, cuff knuckles (print flat)
- `06_wrist_cuff.stl` - front half; swings open sideways (print flat)
- `07_upper_arm_far_ring.stl` - the upper arm's top ring (print flat)
Cuff hardware: 1 x 4 mm pin (hinge, inner side) + 1 x 4 mm quick-release pin (latch, outer side),
about 25 mm long. The wrist ring's 80 mm bore is a placeholder until the wrist is measured.
**v3 vs v2 (safety changes):**
- **Flexion hard stop.** The upper-arm piece now has a stop block on each hub (the hub discs
  grew to 88 mm across to carry them). The forearm shell's edge meets the blocks at 135 deg,
  so the joint physically cannot fold further. The rear ledge still stops it about 1 deg past
  straight.
- **Nothing hard on the front of the forearm near the elbow.** At full fold that area presses
  on the biceps, so the door's elbow end and its pipe are gone. The forearm's elbow-end ring is
  the back half only; close the front with a soft strap. The wrist keeps a hinged front clasp
  (not part of this elbow test set).
- Checked in Fusion: pipes sit exactly on their hole axes (0.000 mm offset, 0.2 mm gap all
  round); no forearm hardware comes within 4.8 mm of the upper arm from 90 to 135 deg.
  Section views are in `sections/`.
## 0. Fit coupons first (about 30 min each)

| File | What to try |
|---|---|
| `00_fit_coupon_pipe_holes.stl` | Push a PVC pipe (21.5 OD) into each hole. Holes are 21.7 / 21.9 / 22.1 / 22.3, marked 1-4 dots. The parts use **21.9**. |
| `00_fit_coupon_bearing_pockets.stl` | Press a 6806 bearing into each pocket (from the top). Pockets are 41.9 / 42.05 / 42.2, marked 1-3 dots. The parts use **42.05**. |

If a different hole or pocket fits best, change `pipe_clear` or the pocket size in
`concepts.py` (or tell Claude) and re-export before printing the big parts.
Note: in the upper-arm piece the bearing pocket prints on its side, so it may come
out slightly tighter than on the coupon.

## 1. Parts

| File | Qty | Print orientation | Notes |
|---|---|---|---|
| `01_upper_arm_elbow_piece.stl` | 1 | 160 x 132 x 109 mm; Ring face down (the flat face farthest from the hubs); the shell rises, the bearing housings are on top | Tree supports inside the two Ã˜42 bearing pockets only |
| `02_forearm_elbow_piece.stl` | 1 | Ring face down, same way | The rear stop ledge is a 45Â° staircase: no support needed |
| `03_bearing_axle_print2.stl` | 2 | Flat on a round face | M8 bolt goes through it |
| `04_bearing_cover_print2.stl` | 2 | Flat | 6 Ã— M3 + centre M8 hole |

In the slicer use "Place on face" / "Lay on face" to set the orientations above.

Settings: PETG (or ASA); 0.2 mm layers; 5 walls; 5 top/bottom; 40 % gyroid.
PLA works for a fit test but gets brittle and creeps under steady load.

## 2. Hardware

- 2 Ã— 6806-2RS bearing (30 Ã— 42 Ã— 7)
- 2 Ã— M8 bolt, about 30 mm, + 2 Ã— M8 nyloc + washers (through axle and forearm hub)
- 12 Ã— M3 Ã— 8 screws for the covers (M3 heat-set inserts in the housings are better)
- PVC pipe 21.5 OD, 3 stubs per piece to test the fit

## 3. Assembly

1. Press one bearing into each housing of the upper-arm piece, from the inside face.
2. Set the forearm piece inside the upper-arm piece so its two hubs sit just inside the housings.
3. From outside, push an axle through each bearing onto the forearm hub; bolt with M8 through the axle and hub.
4. Screw the covers on.
5. Rotate: it should swing from straight (hard stop at the back, about 1Â° past straight)
   to about 135Â° with no rubbing.
6. Push pipe stubs into the ring holes; they bottom out on the shell below the ring.




