# Gripper collar could not go on the carrier

**Where:** gripper prototype 3: collar on the carrier's hub
**Status:** fixed in the model (collar re-exported; the printed carrier is unchanged)

| | |
|---|---|
| What | The collar's bore (radius 26.4 mm) was smaller than the carrier's nose (27.5 mm), and the bridge closes off the hub's other end. The collar could not be put on at all. The guide also fitted the claws first, which would have blocked the nose anyway. |
| How found | User, assembling the printed parts: "i can't slide the collar into the carrier". |
| Cost | A collar reprint. The carrier (a long print) was kept: the collar was redesigned around it. |
| Root cause | Every check looked at the finished assembly (collisions, motion, fasteners). None checked that a part can be brought to its place, so a part trapped by its neighbours passed. |
| Fix | Collar bore 27.8 mm, clear of the nose. Three pads inside the bore centre it on the hub (0.3 mm play); they sit at the claw angles, so on the way on they pass through the nose's claw slots. New build order: collar on, pushed 7 mm past its seat, claws into their slots, collar forward over the claw tails. |
| What catches it now | `gripper3.insertion_rules` (in `design_rules.txt`), driven by `INSERTION`: each part, in the guide's order, slides in along its path 1 mm at a time and must not cut into a part already on. Proven on the old collar: blocked 17 mm out (1171 mm³ into the nose). It also showed the claws can't go in with the collar at its seat, which set the new order. Add a row to `INSERTION` for every new part that slides or drops into place. |
