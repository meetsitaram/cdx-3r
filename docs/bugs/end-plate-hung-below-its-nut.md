# SCARA end plate hung below the nut meant to hold it

**Where:** shoulder girdle: SCARA link 2 → end plate + abduction housing, joint E (M8 × 55 + nyloc)
**Status:** fixed in the model (end plate re-exported: reprint `15_end_plate_housing`, plus one more thin spacer)

| | |
|---|---|
| What | The E nyloc sat in a hex pocket that was **open at the top** of the end plate. Tightening the bolt pulls the nut up, out of the pocket, so the clamp stack ended at the nut and the end plate hung underneath it: nothing held it on, and the arm's weight would pull it off. The pocket only stopped the nut turning. |
| How found | User, in a section view: "this piece is just hanging in there … screw from up just goes inside and sits there". |
| Cost | A reprint of the end plate housing. |
| Root cause | `fastener_check` only asked whether there is plastic round the screw's tip, and there was (the plain hole below the nut). Nothing checked that each part is **between** the head and the nut, or that every machine screw ends in a nut or insert. The MuJoCo sim couldn't see it either: its joints are hand-written ideal hinges that can't come apart. |
| Fix | The nut is captive **inside** the plate, under a 4 mm ceiling: it slides in from the front through a slot as wide as the nut and stops in the slot's V end, centred on the bolt (no lining up); a 5 mm hole from the back pushes it out. Tightening now clamps the end plate up against link 2. A 1 mm spacer (the 7th thin spacer) sits between the plate and link 2's bearing. |
| What catches it now | `fastener_check.py`, three new rules, in `fastener_check.txt` on every export: **THREAD** (a machine screw ends in a modelled nut or insert), **HELD** (every printed part a fastener passes is between its head and the nut's far face), **JOINTS** (every joint in `cad/sim/exo_sim.py` is made by the hardware listed in `cad/fusion/sim_joints.json`: the bolt passes, the parts it should clamp are in its stack, each bearing is on the stack and held by its part). Proven on the old model: HELD failed ("end plate reached only beyond the nut, 49..63 mm, nut ends at 47") and joint q3 failed. `exo_sim.py` refuses to run with a joint missing from `sim_joints.json`. The same rules found three gripper screws whose nuts were only named, not modelled (fold hinge, trigger pivot: needed M3 × 35, pull pin: needed M3 × 25). |
