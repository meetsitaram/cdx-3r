# **Open (to investigate):** end plate ceiling and E bolt under the arm's tipping load

**Where:** shoulder girdle: SCARA end plate (`15_end_plate_housing`), joint E (M8 × 55 + captive nyloc)
**Status:** open, noted 25 Oct for later. Not fixed, not stress-tested.

| | |
|---|---|
| What | The arm hangs on the exo about at the shoulder joint, **~156 mm ahead of E**, so its weight also tries to tip the end plate about E's bolt. The captive nut is held by a **4 mm** ceiling. A rough hand check: 50 N at the arm (arm resting in the straps + the exo below E) is a 7.8 N·m tipping moment; if the nut's edge alone resists it, the ceiling bends to ~49 MPa (**safety factor ~0.9**, printed PETG ~45 MPa along the layers). An 8 mm ceiling would be ~12 MPa (SF ~3.7). The same moment bends the M8 bolt (A2-70) to ~290 MPa if the bolt alone carries it (SF ~1.5). At the 150 N peak case both are well over. |
| How found | User, looking at the end plate in the slicer: "this piece looks too thin to hold the whole thing between the bolt and nut". |
| Why nothing caught it | The only girdle stress study (docs/stress, 18 Oct) hung 150 N straight on the end plate (no lever to the arm), glued every contact, and ran on the old end plate (open nut pocket). No automatic strength check covers the girdle. |
| To do | 1. Stress study of the girdle with the load at the arm line (156 mm lever) and contacts that can open at nut/bolt seats; also the other SCARA joints (C, S0) and the carriage nut seat (see [carriage-nut-seat-overstressed](carriage-nut-seat-overstressed.md)). 2. Then decide: ceiling 8 mm (cheap: the slot moves 4 mm lower, the M8 × 55 still reaches), a stronger bolt (8.8 / 12.9 steel), or a longer grip of the bolt in the plate. 3. Add an automatic hand-calc check (a draft exists: ceiling bending under the nut's pry, bolt bending; it fails the 4 mm ceiling at SF 0.9 and passes 8 mm at 3.7). |
| What catches it now | Nothing yet. |
