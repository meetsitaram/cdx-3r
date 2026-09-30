# Shoulder + back system, print set v2 (Bambu P1S)

This is the back frame, shoulder hinges and upper-arm link, fitted to the exoarm2 body scan. The parts are built by
`cad/fusion/shoulder.py`; the model is `cad/fusion/models/cdx-3r-shoulder-back.f3d` (Fusion document
**CDX-3R shoulder + back**). Every part fits the P1S bed (256 mm). Each STL is one watertight solid, exported in the
design frame, so place it with Lay on Face in Bambu Studio. Bought parts are in `BOM.md` at the repo root.

The left-side frame parts are Fusion mirror features of the right side (the plane is the body midline).

## Parts

| File | Qty | Size (mm) | ~g PETG | Orientation / notes |
|---|---|---|---|---|
| `Upper-arm_link.stl` | 1 | 200 × 164 × 93 | 267 | Outer (spoked) plate flat on the bed. Supports under the round-top inner plate, the curved brace wall and the pipe head. One piece: flexion fork + pipe head + brace wall. |
| `Yoke.stl` | 1 | 197 × 88 × 65 | 154 | Flexion housing axis vertical (round 6808 pockets); support the root boss. |
| `Flexion_axle_sleeve.stl` | 1 | Ø40 × 25 | 23 | On end. Goes through both 6808s. |
| `Abduction_sleeve.stl` | 1 | Ø30 × 69 | 34 | On end. Goes through both 6806s in the right mount block. |
| `Abduction_mount_block_R.stl`, `_L.stl` | 1 + 1 | 150 × 80 × 69 | 426 each | Rear face down (bearing axis vertical). L is empty until there is a left arm (battery mount spot). |
| `Top_node.stl` | 1 | 241 × 70 × 43 | 214 | Back face down; support the two angled beam sockets. |
| `Mid_node.stl` | 1 | 244 × 72 × 39 | 191 | Back face down; support the two angled diagonal sockets. |
| `Bottom_node_R.stl`, `_L.stl` | 1 + 1 | 188 × 92 × 36 | 289 each | Back face down (strap tabs stand up). |
| `Bottom_node_splice_plate.stl` | 1 | 100 × 74 × 42 | 60 | U-channel; open side up. |

The total is about 2.6 kg. Suggested settings: PETG, 0.2 mm layers, 4 walls, 5 top/bottom layers, 40 % gyroid.
Print `prints/elbow-test-v10/00_fit_coupon_bearing_pockets.stl` first if bearing fits are unknown.

## What changed since v1

- The shoulder flexion hinge uses **6808-2RS** bearings with a Ø88 hub (the same size as the elbow). The link is a two-sided fork on an M8 × 55 through-bolt with a printed Ø40 sleeve, and has spoked windows that show the bearing.
- The upper-arm link is one piece: the pipe head (3 blind sockets for the upper-arm PVC pipes, 127.5 mm long) and
  a curved brace wall up to the link. The link stops the arm swinging back at about −25°.
- The abduction hinge uses a printed Ø30 sleeve through 2 × 6806 and an M8 × 100 through-bolt (no printed axle).
- The bottom-node splice is a U-channel held by 8 × M3 × 8 into M3 heat-set inserts.
- The strap tabs are 10 mm thick, with flared bases.
- Pipe screws: **#4 × 3/8" pan-head self-tapping** through the Ø3.2 holes (Ø6.5 head counterbores where the wall is thick).
- Insert holes (splice) are Ø4.0 × 7 mm deep for **ruthex RX-M3 × 5.7** inserts.
- The load-lifter stays are gone: the backbone pipes (2 × 412 mm) end inside the top node.

## Assembly

1. Heat-set 8 × ruthex M3 × 5.7 inserts (flush) into the bottom-node halves. Bolt on the splice channel (8 × M3 × 8).
2. Push the backbone pipes into the bottom node, then slide on the mid and top nodes. Fit the beams and diagonals to the
   mount blocks. Drive the pipe screws.
3. Press 2 × 6806 into the right mount block. Pass the abduction sleeve through, set the yoke root against the front
   bearing, and fit the M8 × 100 from the yoke side, with the fender washer and nyloc behind the block.
4. Press 2 × 6808 into the yoke housing. Fit the flexion sleeve, place the link fork over the housing, drop the nyloc into the
   hex pocket in the outer plate, and fit the M8 × 55 from the arm side.
5. Push the upper-arm pipes (from the elbow's upper-arm piece) into the pipe head sockets and drive 2 screws per pipe.
6. Thread the webbing: the shoulder straps and the waist strap (see `BOM.md`).

## Checks (Fusion + body scan)

- No interference between any bodies, hardware included.
- Flexion running gap 2 mm; abduction running gap 1 mm.
- Rest pose (arm 20° abducted): every part at least 9 mm from the body, except the pipe head's inner face (3.5 mm, like the other
  arm rings).
- Shoulder abduction 20–60° × flexion −20° to 120°: at least 8 mm to the torso and 16 mm to the fixed frame.

## Not in v2 yet

- Dedicated stop pads (abduction 60°; flexion 120° / −25°). The backward stop currently comes from link-to-yoke contact.
- A battery mount on the left block.
