# Gripper collar: the tail-pin cheeks broke off

**Where:** gripper 3, `06_gripper_collar`: the pairs of cheeks that hold each claw tail's M3 pin
**Status:** fixed in the model (reprint `06_gripper_collar`; tail pins become M3 × 25)

| | |
|---|---|
| What | The skirt of the collar is cut into pairs of cheeks, one pair either side of each claw tail. The tail's pin runs through a slot in both cheeks. The cheeks were 4 mm wide, with only **2 mm** of plastic outside the pin slot and **2.3 mm** in front of it. Several snapped off at the slot, straight along the layer lines (the collar prints standing up, so the pin pulls across the layers). |
| How found | User, first print (27 Oct): "that was such a weak point". |
| Cost | A collar reprint. |
| Root cause | The cheeks were sized for the claws and pins to fit and clear each other, never for strength. The design rules check the collar's side lugs under load, but nothing looked at the plastic left round the tail pin slots. The print check's wall measure did flag the collar as the thinnest part (1.6 mm, 5th percentile), but that is only a warning. |
| Fix | Cheeks 6 mm wide (from 4). The skirt reaches out to a 40 mm radius (from 36), leaving 6 mm outside the slot. It runs 1.5 mm further forward, leaving 3.8 mm in front of the pin, with a round relief that clears the claw's root. The tail pins become M3 × 25. A closed outer ring was considered and dropped: the claws and pins go in from outside, so the cheeks have to stay open. |
| What catches it now | `gripper3.tail_cheek_rules()` in `design_rules.txt`: plastic outside and in front of the pin slot ≥ 3.5 mm, cheek width ≥ 5.5 mm. Proven on the old collar: all three failed (2.0, 2.3 and 4.0 mm). |
| Lesson | Every slot or hole that carries a load gets a ligament rule: plastic on each side of it, as built. |
