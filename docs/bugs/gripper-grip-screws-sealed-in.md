# Gripper grip: the 4 screw heads were sealed inside the grip

**Where:** gripper 3, `03_gripper_grip` to the carrier's bridge (4 × M3 × 12 into inserts)
**Status:** fixed in the model (reprint the grip as two parts: `03_gripper_grip` + `03b_gripper_grip_sleeve`)

| | |
|---|---|
| What | The screw heads sat in pockets 8–13 mm under the grip's top, with 100 mm of solid grip below them: no way to get a screw or a key in. |
| How found | User, fitting the printed grip (27 Oct): "There is no place for me to insert and tighten them". |
| Cost | A grip reprint. |
| Root cause | The fastener check asked whether each screw bites (grip, THREAD, HELD) but never whether a hand can reach it. A long channel from below would have needed a long hex driver (long screwdrivers are Phillips). |
| Fix | User's call: the grip is now a top plate with a cross-shaped post (two 7 mm blades between the 4 screws; the heads sit in pockets open below, a normal L key reaches them), and a sleeve, the full grip, that slides up over the post (0.25 mm per side, relief at its mouth) and is held by one M3 × 8 up through its floor into an insert in the post's foot. |
| What catches it now | `fastener_check` **ACCESS**: 15 mm straight out from every screw head must be free of printed parts, except parts fitted after it (`FITTED_AFTER`). Proven on the old grip: all 4 screws failed ("in the way 1 mm out from the head"). Across the whole assembly it also found the servo coupler/axle screws (covered by parts fitted after them, by design) and the shoulder rest's pivot bolt (open: `rest-pivot-head-under-root-arm.md`). |
