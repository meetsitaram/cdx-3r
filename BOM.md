# CDX-3R bill of materials: parts to buy

This is for one right arm (elbow concept B) plus the shoulder and back system, as of 2026-10-17. Quantities come
from the current CAD: `cad/fusion/concepts.py` (elbow), `cad/fusion/shoulder.py`, `girdle_b.py` and
`shoulder_rest.py` (shoulder + back). Print details are in `prints/elbow-test-v10/` and `prints/shoulder-back-v3/`.
The last column is what a future **left arm** would add; the frame and harness are shared.

Buy extra of the small parts (see the fastener notes).

## Shopping list: new for the v3 shoulder girdle + rest

Everything else comes from packs already on this list.

| ☐ | Item | Pack | Need | Link |
|---|---|---|---|---|
| ☐ | 608-2RS bearings | 20 pcs | 16 | [SHKI 608-2RS](https://www.amazon.com/dp/B09PKD8QZZ) |
| ☐ | GT2 6 mm closed belt loop, 200 mm | 10 pcs | 2 | [Zeelo GT2 200 mm](https://www.amazon.com/dp/B0BZNTT5T4) |
| ☐ | Gas strut 180 / 120 mm, 22 N, eyelet ends | 2 pcs | 1 | [Motoforti 7" 22 N](https://www.amazon.com/dp/B0DHVV6QZW) |
| ☐ | M6 × 16 socket head cap screw (5 mm hex key) | 40 pcs | 3 | [MewuDecor M6 × 16 socket head, 304](https://www.amazon.com/dp/B07HR6PPX8) |
| ☐ | M6 × 65 socket head (5 mm key), shoulder rest pivot; 2 M6 nuts from the pack below | 10 pcs | 1 | [uxcell M6 × 65, stainless](https://www.amazon.com/uxcell-M6x65mm-Stainless-Socket-Screws/dp/B01BBP4VU2) |
| ✓ | M6 × 30 socket head: **only** for towers printed before 18 Oct (rest-bracket retrofit) | 10 pcs | 1 | ordered 18 Oct: [uxcell M6 × 30, 304](https://www.amazon.com/clp/B019ETH8YI) |
| ☐ | M8 × 75 socket head, 304, fully threaded (SCARA elbow bolt; replaces cutting an M8 × 100) | any small pack | 1 | [Amazon search](https://www.amazon.com/s?k=M8-1.25+x+75mm+socket+head+cap+screw+304+stainless+full+thread) |
| ☐ | M6 hex nut | 50 pcs | 3 | [M6 hex nuts](https://www.amazon.com/dp/B0CZQRH3L2) |
| ☐ | Clevis pin M6 × 70 + R-clip | 6 pcs | 4 | [M6 × 70 clevis pins](https://www.amazon.com/dp/B0FJWVWFBY) |
| ☐ | ½" adhesive neoprene foam | 12" × 54" sheet | 9 pads | [MYFULLY ½" foam](https://www.amazon.com/dp/B0BTRWTXN4) |
| ☐ | Adhesive hook-and-loop, 2" | 27 ft | 9 pads | [Navona 2" hook-and-loop](https://www.amazon.com/dp/B0CNQ2MP8V) |

Also check stock of: PETG (~4 kg total, see Filament), ½" PVC (3 m), M8 × 55 (7 used), M8 nylocs (9), ruthex inserts
(38) and M3 × 8 / M3 × 12 screws.

## Bearings

| | Item | Spec | Right arm + back | Where | + Left arm | Buy |
|---|---|---|---|---|---|---|
| <img src="https://m.media-amazon.com/images/I/51X2MKd+kkL._SS64_.jpg" width="48"> | Deep-groove ball bearing | **6806-2RS**, 30 × 42 × 7 mm, sealed | **4** | elbow 2 (upper-arm housings); shoulder abduction 2 (right mount block) | 4 | [uxcell 6806-2RS, 2-pack](https://www.amazon.com/uxcell-6806-2RS-Bearing-30x42x7mm-Bearings/dp/B07TV2HVZ3) |
| <img src="https://m.media-amazon.com/images/I/61ULw0csEoL._SS64_.jpg" width="48"> | Deep-groove ball bearing | **6808-2RS**, 40 × 52 × 7 mm, sealed | **2** | shoulder flexion (yoke housing: the shoulder carries the whole arm) | 2 | [XIKE 6808-2RS 40 × 52 × 7, 10 pcs](https://www.amazon.com/XIKE-6808-2RS-Bearings-40x52x7mm-Pre-Lubricated/dp/B09D2VY3BK) |

## Fasteners

**Small screws are two kinds:** **M3 × 8 socket head** machine screws into M3 heat-set inserts, and **#4 × 3/8" pan-head
self-tapping screws** straight into the PVC pipes. Where a wall is thicker, the head sits in a Ø6.5 counterbore, so the
screw always reaches. The two hinge bolts are M8 socket heads.

| | Item | Spec | Qty | Where | + Left arm | Buy |
|---|---|---|---|---|---|---|
| <img src="https://m.media-amazon.com/images/I/81gWELi+t-L._SS64_.jpg" width="48"> | Socket head cap screw | **M3 × 8** (ISO 4762), 304 stainless | **26** | into M3 inserts: elbow axles 6 (heads 4.2 mm deep in the axle), elbow covers 12, bottom-node splice channel 8 (2 mm counterbores) | 18 | [Fgruh 720 pcs M3 kit, M3 × 6–30 (has 25 × M3 × 8: use one M3 × 10 for the 26th)](https://www.amazon.com/dp/B0FG2BRXL3) |
| <img src="https://m.media-amazon.com/images/I/717sikDXLoL._SS64_.jpg" width="48"> | Heat-set insert | **ruthex RX-M3 × 5.7**, brass, Ø4.0 hole | **26** | elbow: 6 in the forearm hubs, 12 around the housings; splice: 8 in the bottom-node halves | 18 | [ruthex M3 × 5.7, 100 pcs](https://www.amazon.com/dp/B08BCRZZS3) |
| <img src="https://m.media-amazon.com/images/I/41nNcy4BttL._SS64_.jpg" width="48"> | Self-tapping pan-head screw | **#4 × 3/8"** (2.9 × 9.5 mm), Phillips, 304 stainless, pointed | **48** | into the PVC pipes: elbow 18, link pipe head 6, frame 24 | 24 | [#4 × 3/8" Phillips pan head self-tapping, 304 stainless black oxide, 100 pcs](https://www.amazon.com/Phillips-Self-Tapping-Stainless-Corrosion-Resistant/dp/B0F9FP5DV4) |
| <img src="https://m.media-amazon.com/images/I/81eRRQ84F+L._SS64_.jpg" width="48"> | Socket head cap screw | **M8 × 100** (ISO 4762 / DIN 912, head Ø13 × 8), 304 stainless. **Not flat/countersunk head**: it sits in a flat Ø14.5 counterbore | 1 | shoulder abduction hinge: yoke root → sleeve through both bearings → washer + nut behind the mount block | 1 | [YIIFLY M8-1.25 × 100 socket head cap screws, 304 (A2-70), 8 pcs](https://www.amazon.com/YIIFLY-M8x1-25-Stainless-Machine-Quantity/dp/B0G6YVL3SZ) |
| <img src="https://m.media-amazon.com/images/I/71YDpuW7B+L._SS64_.jpg" width="48"> | Socket head cap screw | **M8 × 55** (ISO 4762 / DIN 912, head Ø13 × 8), 304 stainless. M8 × 50 is too short (the clamp stack is 52.5 mm) | 1 | shoulder flexion hinge: through the printed Ø40 sleeve in the 6808s; head sunk flush on the arm side of the link fork, nut captured in the outer plate | 1 | [M8-1.25 × 55 socket head, 304 stainless, 10 pcs](https://www.amazon.com/M8-1-25-Socket-Screws-Stainless-Machine/dp/B07L346K4H) |
| <img src="https://m.media-amazon.com/images/I/71WBREb9hWL._SS64_.jpg" width="48"> | Nyloc nut | **M8-1.25**, nylon-insert lock nut (DIN 985, 13 mm AF × ~8 mm), 304 stainless | 2 | flexion: drops into the 8 mm hex pocket in the link (can't turn); abduction: behind the mount block, on the fender washer | 2 | [Vifmy M8-1.25 nyloc, 304 (A2-70), 90 pcs](https://www.amazon.com/Vifmy-M8-1-25mm-Locknuts-Stainless-Standard/dp/B0CPJH281Y) |
| <img src="https://m.media-amazon.com/images/I/51hU57u8SNL._SS64_.jpg" width="48"> | Fender washer | M8, **32 mm OD** × 1.2 mm, 304 stainless. **Not 30 mm**: a 30 mm washer is the same size as the 6806 bore and slips into the bearing. Over 33 mm it rubs the bearing's fixed outer ring | 1 | behind the abduction mount block, under the nyloc: clamps the rear 6806 inner ring and the sleeve end | 1 | [M8 × 32 mm OD fender washer, 304, 1.2 mm, 50 pcs](https://www.amazon.com/dp/B0GSLW9F7G) |
| <img src="https://m.media-amazon.com/images/I/61j7q-TA-uL._SS64_.jpg" width="48"> | Dowel pin | **Ø4 × 25 mm**, 304 stainless | 1 | elbow: wrist-cuff hinge (inner side), through the 25 mm knuckle stack (Ø4.2 bores); a drop of CA glue at one end so it cannot slide out (or use an M4 × 30 + nyloc instead) | 1 | [uxcell 4 × 25 mm dowel pin, 304, chamfered ends, 10 pcs](https://www.amazon.com/uxcell-Stainless-Chamfered-Support-Elements/dp/B0BCFKNDMQ) |
| <img src="https://m.media-amazon.com/images/I/61hUlaKe6xL._CR0,0,1500,1000_SS64_.jpg" width="48"> | Neodymium magnet | **Ø10 × 2 mm** round | 4 | elbow: wrist-cuff latch side (**design pending**: a magnet-assisted snap latch will replace the old quick-release pin; the Ø5.2 latch holes in the current `05`/`06` are not used) | 4 | [Neodymium magnets Ø10 × 2 mm, 100 pcs](https://www.amazon.com/dp/B0FBR9Z39L) |

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
| Upper-arm pipe | 127 mm | 3 | elbow near ring → upper-arm link pipe head |
| Forearm pipe | 185 mm (leans 5.9° toward the wrist) | 3 | elbow near ring → wrist ring |
| Backbone | 412 mm | 2 | bottom node → top node (ends flush inside it). **v3b girdle: left only**, see below |
| Upper beam | 102 mm | 2 | top node → mount block (L + R). **v3b girdle: left only** (101.6 → 102) |
| Diagonal | 131 mm | 2 | mid node → mount block (L + R). **v3b girdle: left only** |
| Backbone R, v3b girdle | 568 mm | 1 | bottom node → up through the top node into the shoulder tower (replaces the right 412 mm backbone) |

## Shoulder girdle v3b + shoulder rest (right): hardware (in design, from the Fusion model)

Counts are for the right side. The girdle replaces the right abduction mount block, beam and diagonal. Everything not
marked **new** comes from packs already on this list.

| Item | Qty | Where | Order |
|---|---|---|---|
| 608-2RS bearing, 8 × 22 × 7 | 16 | lift links 8 (2 per pivot), SCARA links 8 | **new**: [SHKI 608-2RS, 20 pcs](https://www.amazon.com/dp/B09PKD8QZZ) |
| M8 × 55 socket head + M8 nyloc | 6 | 4 lift pivots; S0 (nyloc locked in the carriage, bolt from below); E (nyloc locked in the end plate, bolt from the top of link 2) | same pack as the flexion bolt (10 pcs: 7 used here + flexion) |
| M8 × **75** socket head (full thread) + M8 nyloc | 1 | C, the SCARA elbow spool | **new**: buy as M8-1.25 × 75, socket head, 304 stainless, fully threaded ([Amazon search](https://www.amazon.com/s?k=M8-1.25+x+75mm+socket+head+cap+screw+304+stainless+full+thread)); no cutting |
| M3 × 8 socket head + ruthex M3 insert | 4 + 4 | saddle → top node | M3 kit + ruthex pack |
| M6 × 16 socket head (head Ø10 × 6, 5 mm hex key) + M6 hex nut | 2 + 2 | the 2 gas-strut eyelet forks; each nut sits in a hex pocket in the plate | **new**: [MewuDecor M6 × 16 socket head, 304](https://www.amazon.com/dp/B07HR6PPX8) + [M6 hex nuts, 50 pcs](https://www.amazon.com/dp/B0CZQRH3L2) |
| M3 × 12 socket head + ruthex M3 insert | 8 + 8 | SCARA link lids | M3 kit (6–30 mm) + ruthex pack |
| #4 × 3/8" pipe screw | 2 | shoulder tower → right backbone (counterbored) | pipe screw pack |
| Clevis pin **M6 × 70** with R-clip | 4 | shoulder rest hinges: one size for all 4 joints (every hinge is 64 mm wide) | **new**: [M6 × 70 clevis pins + R-clips, 6 pcs](https://www.amazon.com/dp/B0FJWVWFBY) |
| GT2 6 mm closed belt loop, **200 mm** | 2 | one in each SCARA link (printed 35-tooth pulleys at 65 mm centres) | **new**: [Zeelo GT2 200 mm closed loop, 10 pcs](https://www.amazon.com/dp/B0BZNTT5T4) |
| Gas strut, **180 mm** extended / **120 mm** compressed, **22 N**, flat **eyelet** ends (hole ~6 mm, assumed; check on arrival) | 1 (2-pack) | eyelet in a printed fork on the tower ear → carriage ear (120–177 mm over drop 20 → shrug 60). 22 N from the MuJoCo strap test (`cad/sim/exo_sim.py`): 15–25 N gives the lowest strap forces; 100 N doubled them | **new**: [Motoforti 7" 22 N, 2 pcs](https://www.amazon.com/dp/B0DHVV6QZW) |
| Side-release buckle 25 mm | 1 | front end of the shoulder rest | strap kit (6 buckles) |
| Foam ½" (12.7 mm) + adhesive hook-and-loop | 3 + 6 pads | under the 3 blades; 2 per frame node on the body side | **new**: [MYFULLY ½" × 12" × 54" adhesive neoprene](https://www.amazon.com/dp/B0BTRWTXN4) + [Navona 2" × 27 ft adhesive hook-and-loop](https://www.amazon.com/dp/B0CNQ2MP8V) |

No M5 parts, no washers, no hex-head bolts: every M8 nyloc that would be hard to reach sits in a printed hex pocket.

Straps on the arm: **two** on the upper-arm pipes (about 30 % and 75 % of the way from shoulder to elbow) + the wrist cuff. With one upper-arm strap the exo can pivot around it and its shoulder drifts ~5 cm off yours (MuJoCo test).

Printed small parts: 4 GT2 35-tooth pulleys (P0, PA, PB, P2, 8 mm wide), 8 inner-ring spacers Ø11 / 8.4 × 4 mm, 6 spacers Ø11 × 1 mm (one is the carriage's root spacer on link 1).

The total is about 2.15 m; **buy 3 m** (cuts plus saw kerf and spares). A left arm adds 3 × 127 + 3 × 185 mm.

## Harness (camping-pack style)

**One webbing size: 1" (25.4 mm)** everywhere. All six strap tabs on the frame have 26 mm slots. Tri-glides adjust length like ladder-locks.

| | Item | Spec | Qty used | Where | Buy |
|---|---|---|---|---|---|
| <img src="https://m.media-amazon.com/images/I/81QQGzCsKJL._SS64_.jpg" width="48"> | 1" strap kit | 25 mm (1") nylon webbing + side-release buckles + tri-glides | ~3.7 m webbing (6 yd in the kit), 2 buckles, 3 tri-glides | 2 shoulder straps (top tabs → over the shoulders → under the arms → bottom tabs), sternum strap, waist strap (through the two side tabs, buckled at the front) | [BEYOURD 1" set: 6 yd, 6 buckles, 12 tri-glides](https://www.amazon.com/BEYOURD-Buckles-Straps-Set-Adjustable/dp/B08LD8CJ8D) |
|  | Strap pads *(optional)* | slip-on / hook-and-loop strap covers for 1" webbing (e.g. car-seat or backpack shoulder-strap pads) | 2–3 | shoulder straps, waist strap | |
|  | Hook-and-loop strap *(optional)* | 25 mm | ~1 m | arm retention across the open front of the pipe head / rings | |
|  | Foam padding *(optional)* | thin closed-cell, self-adhesive | small sheet | skin-side faces of the arm rings / pipe head, if they rub | |

## Gripper prototype 3 (fold-up, 3 fin-ray claws): hardware (Fusion doc "CDX-3R gripper 3", prints/gripper3-v1)

**To buy** (all Prime eligible, checked on Amazon 20 Oct 2026: Prime delivery in 1 to 2 days):

| ☐ | Item | Qty used | Pick |
|---|---|---|---|
| ☐ | M3 nyloc nut (304) | 5 | [BinifiMux M3 nylock, 100 pcs](https://www.amazon.com/dp/B075ZZW7VL) |
| ☐ | M3 × 35 socket head (trigger pivot: through both grip cheeks and the trigger, nyloc outside) | 1 | (see the note under the table) |
| ☐ | Index plunger M8-1.25, 5 mm pin, pull ring (screws into a 6.8 mm hole, its own lock nut outside) | 1 | [Bitray spring plunger M8-1.25-5, 4 pcs](https://www.amazon.com/dp/B0DFP11V6C) |
| ☐ | Extension spring, 1.2 mm wire × ~10 mm OD × 45 mm, hook ends | 1 | [Keadic 100 pcs stainless extension spring kit (has 1.2 × 10 × 45)](https://www.amazon.com/dp/B0D9H4VB5T) |
| ☐ | TPU 95A filament, 1.75 mm | ~60 g | [SUNLU TPU 95A, 1 kg](https://www.amazon.com/dp/B0BXNWK6NS) |

**From stock** (already ordered for the shoulder):

| Item | Qty | Where | From |
|---|---|---|---|
| ruthex M3 × 5.7 heat-set insert | 12 | claw pivots (3, pressed in from outside the dome), grip (4), grip post foot (1), pipe clamps (2), Y-link pins (2) | ruthex 100-pack (38 used by the shoulder) |
| M3 × 12 socket head | 8 | grip to bridge (4), Y-link pins into the collar (2), pipe clamps (2: a 10 mm thumb screw only just reaches the pipe) | Fgruh M3 kit |
| M3 × 8 socket head | 1 | grip sleeve onto the grip post (from below) | from the shoulder's M3 × 8 |
| M3 × 25 socket head | 4 | trigger pull pin (1) and claw tail pins (3), each + nyloc (the trigger and the collar's cheek pairs are about 19 mm across: a 20 mm screw leaves nothing for the nut) | Fgruh M3 kit |
| M3 × 30 socket head | 3 | claw pivots (into inserts) | Fgruh M3 kit |
| M8 × 55 socket head + M8 nyloc | 1 + 1 | fold hinge: head on the plunger side, nyloc on the other | M8 × 55 pack (2 spare) + Vifmy nylocs |
| Hook-and-loop | 2 dots, 22 mm | stowed rest: one on the bridge top, one on the base pad | cut from the Navona 2" roll |

Every screw here ends in a nut or an insert (the screw check fails one that doesn't, 25 Oct). M3 × 35 is longer than
most kits: buy a small pack if yours stops at 30. If the Fgruh kit lacks 12, 25 or 30 mm: [VIGRUE M3 kit, 4–30 mm](https://www.amazon.com/dp/B083SGJ7BD) (Prime).
Spring: hook it in the link hole farthest from the hub (45 mm between hooks); if the trigger feels too stiff, use
the middle (40 mm) hole.

**Prints** (`prints/gripper3-v1`, oriented, checked):

| File | Material | Qty | Note |
|---|---|---|---|
| 01_gripper_base | PETG | 1 | stands at a tilt; supports on |
| 02_gripper_carrier | PETG | 1 | on its side; tree supports under the hub and dome |
| 03_gripper_grip | PETG | 1 | |
| 04_gripper_trigger | PETG | 1 | lies on its straight back edge |
| 05_gripper_y_link | PETG | 1 | |
| 06_gripper_collar | PETG | 1 | |
| 07_gripper_claw_TPU_x3 | TPU 95A | 3 | flat; slow (20–30 mm/s) |

## Elbow servo (prints/elbow-servo-v1)

A Dynamixel XL430-W250-T in a case on the elbow's outer side, instead of the outer bearing cover.

| Item | Qty | Where | From |
|---|---|---|---|
| Dynamixel XL430-W250-T, with its horn | 1 | elbow, outer side | Koch arm parts |
| U2D2 (or another TTL adapter) + 12 V supply | 1 | to run it | Koch arm parts |
| M2.5 × 6 socket head | 2 | horn coupler to the horn | M2.5 kit (Robotis horn screws are M2.5) |
| M3 × 12 socket head | 6 | case into the old cover's inserts | Fgruh M3 kit |
| M3 × 8 socket head + ruthex M3 insert | 2 + 2 | strap | stock |

## Filament

| Item | Qty | Notes |
|---|---|---|
| PETG | ~4 kg | shoulder + back v3 ~2.8 kg (60 % effective fill), elbow set ~0.6 kg, gripper 3 ~0.4 kg (600 g solid, 60 % effective fill, plus supports), plus fit coupons and reprints |
| TPU 95A | ~60 g | gripper 3 claws (see above) |

## Not included yet

- Actuation and power (motors, winches, cables, battery, controller): the back pack is still a placeholder box.
  The battery should sit at the left mount block to balance the right arm (see `prints/shoulder-back-v2/README.md`).
- Shoulder hard stops (abduction 60°, flexion −20 / 120°): not modelled yet; they may add small screws.
