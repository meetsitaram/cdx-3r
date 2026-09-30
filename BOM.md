# CDX-3R bill of materials: parts to buy

This is for one right arm (elbow concept B) plus the shoulder and back system, as of 2026-09-29. Quantities come
from the current CAD: `cad/fusion/concepts.py` (elbow) and `cad/fusion/shoulder.py` (shoulder + back). Print
details are in `prints/elbow-test-v10/` and `prints/shoulder-back-v2/`.
The last column is what a future **left arm** would add; the frame and harness are shared.

Buy extra of the small parts (see the fastener notes).

## Bearings

| Item | Spec | Right arm + back | Where | + Left arm |
|---|---|---|---|---|
| Deep-groove ball bearing | **6806-2RS**, 30 × 42 × 7 mm, sealed | **4** | elbow 2 (upper-arm housings); shoulder abduction 2 (right mount block) | 4 |
| Deep-groove ball bearing | **6808-2RS**, 40 × 52 × 7 mm, sealed | **2** | shoulder flexion (yoke housing: the shoulder carries the whole arm) | 2 |

## Fasteners

**Small screws are two kinds:** **M3 × 8 socket head** machine screws into M3 heat-set inserts, and **#4 × 3/8" pan-head
self-tapping screws** straight into the PVC pipes. Where a wall is thicker, the head sits in a Ø6.5 counterbore, so the
screw always reaches. The two hinge bolts are M8 socket heads.

| Item | Spec | Qty | Where | + Left arm | Buy |
|---|---|---|---|---|---|
| Socket head cap screw | **M3 × 8** (ISO 4762), 304 stainless | **26** | into M3 inserts: elbow axles 6 (heads 4.2 mm deep in the axle), elbow covers 12, bottom-node splice channel 8 (2 mm counterbores) | 18 | [Fgruh 720 pcs M3 kit, M3 × 6–30 (has 25 × M3 × 8: use one M3 × 10 for the 26th)](https://www.amazon.com/dp/B0FG2BRXL3) |
| Heat-set insert | **ruthex RX-M3 × 5.7**, brass, Ø4.0 hole | **26** | elbow: 6 in the forearm hubs, 12 around the housings; splice: 8 in the bottom-node halves | 18 | [ruthex M3 × 5.7, 100 pcs](https://www.amazon.com/dp/B08BCRZZS3) |
| Self-tapping pan-head screw | **#4 × 3/8"** (2.9 × 9.5 mm), Phillips, 304 stainless, pointed | **48** | into the PVC pipes: elbow 18, link pipe head 6, frame 24 | 24 | [#4 × 3/8" Phillips pan head self-tapping, 304 stainless black oxide, 100 pcs](https://www.amazon.com/Phillips-Self-Tapping-Stainless-Corrosion-Resistant/dp/B0F9FP5DV4) |
| Socket head cap screw | **M8 × 100** (ISO 4762 / DIN 912, head Ø13 × 8), 304 stainless. **Not flat/countersunk head**: it sits in a flat Ø14.5 counterbore | 1 | shoulder abduction hinge: yoke root → sleeve through both bearings → washer + nut behind the mount block | 1 | [M8 × 100 socket head cap screws, 304 stainless, 10 pcs](https://amazon.com/Socket-Screws-10-Piece-Stainless-Thread/dp/B01H5MD9YO) |
| Socket head cap screw | **M8 × 55** (ISO 4762 / DIN 912, head Ø13 × 8), 304 stainless. M8 × 50 is too short (the clamp stack is 52.5 mm) | 1 | shoulder flexion hinge: through the printed Ø40 sleeve in the 6808s; head sunk flush on the arm side of the link fork, nut captured in the outer plate | 1 | [M8-1.25 × 55 socket head, 304 stainless, 10 pcs](https://www.amazon.com/M8-1-25-Socket-Screws-Stainless-Machine/dp/B07L346K4H) |
| Hex nut | **M8-1.25**, DIN 934, 304 stainless (13 mm AF × 6.5 mm) | 2 | flexion: drops into the 8 mm hex pocket in the link (can't turn); abduction: behind the mount block, **with blue threadlocker** (or use a nyloc) | 2 | [Juvielich M8-1.25 hex nut, 304, 25 pcs](https://www.amazon.com/Stainless-Fasteners-Replacement-M8-1-25mm-Hexagonal/dp/B0CZQNB22Q) · optional nyloc: [Bolt Base M8 A2 nyloc, 25 pcs](https://www.amazon.com/Bolt-Base-Stainless-Insert-Nylock/dp/B00U92NLXC) |
| Fender washer | M8, 30 mm OD | 1 | behind the abduction mount block, under the nut | 1 | [Bolt MC fender washers M8 × 30 mm OD](https://www.amazon.com/Bolt-Hardware-Fender-Washers-M8FW-30-STL/dp/B005UGHPDE) |
| Dowel pin | **Ø4 × 25 mm**, 304 stainless | 1 | elbow: wrist-cuff hinge (inner side), through the 25 mm knuckle stack (Ø4.2 bores); a drop of CA glue at one end so it cannot slide out (or use an M4 × 30 + nyloc instead) | 1 | [uxcell 4 × 25 mm, 10 pcs](https://www.amazon.com/uxcell-Stainless-Support-Fasten-Elements/dp/B07M63LW8M) · [Antrader 4 × 25 mm, 50 pcs](https://www.amazon.com/Antrader-Dowel-Stainless-Cylindrical-Locating/dp/B07GKRKX2Y) |
| Ball-lock quick-release pin | **Ø4 mm, usable length ~30 mm** (balls must clear the far face of the 25 mm stack), stainless, with lanyard | 1 | elbow: wrist-cuff latch (outer side) | 1 | [Ball-lock quick-release pins, choose 4 mm × 30 mm](https://www.amazon.com/Quick-Release-Pins-Stainless-Self-Locking/dp/B0GLNMSTFW) |

**Pipe screws:** seat the pipe, then drive the #4 self-tapping screw through the Ø3.2 hole. The printed hole centres
the point, and the screw cuts its own thread in the PVC, usually with no pilot needed. If one skates on the round pipe,
drill a 2 mm pilot through the hole. Snug is enough: over-tightening strips the thin pipe wall. 3/8" is the right
length: about 7 mm of plastic + PVC wall before the thread bites, and the tip ends inside the hollow pipe.

**Inserts:** all insert holes are Ø4.0 × 7 mm deep for the ruthex RX-M3 × 5.7 (elbow v10, shoulder-back v2). Parts
already printed from elbow v9 have 5.5 mm holes: press the insert flush (or run a 4 mm drill to ~7 mm first), and use
**M3 × 10** in the v9 axles.

## PVC pipe (21.5 mm OD / 15.5 mm ID)

| Piece | Cut length | Qty | Where |
|---|---|---|---|
| Upper-arm pipe | 127.5 mm | 3 | elbow near ring → upper-arm link pipe head |
| Forearm pipe | 184.8 mm (leans 5.9° toward the wrist) | 3 | elbow near ring → wrist ring |
| Backbone | 412 mm | 2 | bottom node → top node (ends flush inside it) |
| Upper beam | 101.6 mm | 2 | top node → mount block (L + R) |
| Diagonal | 130.6 mm | 2 | mid node → mount block (L + R) |

The total is about 2.23 m; **buy 3 m** (cuts plus saw kerf and spares). A left arm adds 3 × 127.5 + 3 × 184.8 mm.

## Harness (camping-pack style)

| Item | Spec | Qty | Where |
|---|---|---|---|
| Webbing | 25 mm nylon | ~2 m | 2 shoulder straps: top tabs → over the shoulders → under the arms → bottom tabs |
| Ladder-lock buckle | 25 mm | 2 | shoulder-strap adjusters |
| Webbing | 38 mm nylon | ~1.2 m | waist strap through the two side tabs |
| Side-release buckle | 38 mm | 1 | waist strap, front |
| Hook-and-loop strap *(optional)* | 25 mm | ~1 m | arm retention across the open front of the pipe head / rings |
| Foam padding *(optional)* | 10 mm closed-cell, self-adhesive | ~0.2 m² | shoulder straps, waist strap, skin-side ring faces |

## Filament

| Item | Qty | Notes |
|---|---|---|
| PETG | ~3 kg | shoulder + back ~2.1 kg (60 % effective fill), elbow set ~0.6 kg, plus fit coupons and reprints |

## Not included yet

- Actuation and power (motors, winches, cables, battery, controller): the back pack is still a placeholder box.
  The battery should sit at the left mount block to balance the right arm (see `prints/shoulder-back-v2/README.md`).
- Shoulder hard stops (abduction 60°, flexion −20 / 120°): not modelled yet; they may add small screws.
