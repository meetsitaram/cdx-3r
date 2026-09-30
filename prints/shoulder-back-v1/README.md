# Shoulder + back system, test print v1 (Bambu P1S)

> **Superseded by `prints/shoulder-back-v2/`.** Kept for history.

Back frame, shoulder hinge mounts and right-arm shoulder mechanism, fitted to the exoarm2 body scan.
Built by `cad/fusion/shoulder.py`; Fusion document **CDX-3R shoulder + back** (project my-projects).
Every part fits the P1S bed (256 × 256 × 256 mm) with at least 11 mm to spare.

Left-side parts are Fusion mirror features of the right side (plane = body midline), so edits to the
right-side features update the left automatically.

## Printed parts

Orient the parts on the plate as listed. The STLs are exported in the design frame, so use Lay on Face in Bambu Studio.

| File | Qty | Size (mm) | ~g | Orientation |
|---|---|---|---|---|
| `Top_node.stl` | 1 | 242 × 70 × 44 | 210 | back face down; support the two angled beam sockets |
| `Mid_node.stl` | 1 | 245 × 73 × 40 | 193 | back face down; support the two angled diagonal sockets |
| `Bottom_node_R.stl`, `Bottom_node_L.stl` | 1 + 1 | 188 × 92 × 36 | 285 each | back face down (strap tabs stand up) |
| `Bottom_node_splice_plate.stl` | 1 | 100 × 56 × 6 | 25 | flat |
| `Abduction_mount_block_R.stl`, `_L.stl` | 1 + 1 | 150 × 80 × 69 | 428 each | rear face down: bearing axis vertical, so the pockets print round |
| `Yoke.stl` | 1 | 190 × 68 × 66 | 133 | flexion-housing axis vertical; support the root boss |
| `Abduction_axle.stl` | 1 | 100 × 50 × 50 | 59 | flange down, shaft up |
| `Upper-arm_link.stl` | 1 | 153 × 56 × 44 | 66 | plate flat, flexion axle up |

Total is about 2.1 kg PETG (the estimate assumes 60 % effective fill). Suggested settings: PETG, 0.2 mm layers, 4 walls,
5 top/bottom layers, 40 % gyroid. The bearing pockets and the axle bore are nominal (Ø42.2 / Ø34 / Ø30);
print a fit coupon from `prints/elbow-test-v9/00_fit_coupon_bearing_pockets.stl` first if the P1S
runs tight.

## Bought parts

| Item | Qty | Notes |
|---|---|---|
| PVC pipe 21.5 OD / 15.5 ID | 2 × 483, 2 × 102, 2 × 131 mm | backbone, upper beam, diagonal (L + R) |
| 6806-2RS bearing (30 × 42 × 7) | 4 | abduction (2, right mount block) + shoulder flexion (2, yoke). The left block stays empty until a left arm |
| M3 × 10 socket head + M3 heat-set insert (Ø4 × 5.5) | 3 | abduction axle flange to yoke |
| M3 × 8 + washer Ø36 (printed or steel) | 2 | axle retainers: abduction axle rear end, flexion axle inner end |
| M4 × 12 + M4 heat-set insert (Ø5.7 × 8) | 4 | splice plate to bottom node halves |
| M4 × 16 | 2 | upper-arm link foot to the far-ring lug (lug not built yet, see below) |
| 25 mm webbing | ~2 m | shoulder straps (top tabs → over shoulder → under arm → bottom tabs) |
| 25 mm ladder-lock | 2 | shoulder strap adjusters |
| 38 mm webbing + 38 mm side-release buckle | ~1.2 m + 1 | waist strap through the two side tabs |

## Assembly

1. Heat-set the M4 inserts in both bottom-node halves. Bolt the splice plate across the seam on the back face.
2. Push the backbone pipes into the bottom node. Slide the mid and top nodes on; the backbone passes through them and
   continues up as the load-lifter stays.
3. Fit the upper beams and diagonals between the nodes and the mount blocks (sockets 25–30 mm deep).
4. Press 2 × 6806 into the right mount block (front and rear pockets). Pass the abduction axle through from the front,
   seat the yoke root in its flange pocket, fit 3 × M3 into the yoke inserts, then fit the rear retainer screw and washer.
5. Press 2 × 6806 into the yoke's flexion housing. Insert the upper-arm link's axle from outside, then fit the inner
   retainer.
6. Thread the webbing: the shoulder straps go from the top tabs over the shoulders and down under the arms to the bottom tabs.
   The waist strap runs through the side tabs and buckles at the front.

## Checks (against the body scan, `exoarm2-scan/tools/check_fusion.py`)

- No interference between any of the 16 bodies (Fusion interference analysis).
- Rest pose (arm 12° abducted): at least 9.7 mm from the body. The closest part is the bottom node at the hips.
- Shoulder abduction 12–60° × flexion −20–120°: at least 10 mm to the torso and at least 19 mm to the fixed frame.
- Centre of mass: about 96 mm right of the spine with the right arm fitted. A battery in or at the left mount block balances it
  (1 kg there brings it to about 24 mm).

## Not in v1 yet

- Hard stops: abduction 60°, flexion −20° / 120°.
- Far-ring lug for the upper-arm link foot (the far ring is in the elbow document).
- Self-tapping screw holes in the pipe sockets (v1 relies on a tight fit or glue).
- Lighter mount blocks (hollow + ribbed, about −200 g each).
- The rigid shoulder rest was dropped: the backpack straps and hip belt carry the frame
  (the STL is kept at `exoarm2-scan/out/print`).
