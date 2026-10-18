# Shoulder-rest bracket hung on one screw and a 1.7 mm wall

**Where:** shoulder rest bracket (26) on the shoulder tower (07)  
**Status:** fixed in the model; towers already printed get a drilled hole

![before and after](img/rest-bracket-attachment.png)

| | |
|---|---|
| What | The rest bracket turns on a Ø16 boss on the tower's front plate. The only thing holding it on, against the straps pulling forward, was **one M6 screw** through the bracket's arc slot into a nut in a pocket, with **1.7 mm** of plastic between the nut and the plate face. The angle was held by friction alone. |
| How found | The user, after a **9 h print of the tower**: "how is the rest bracket holding onto the tower, given that it will be pulled forward by tight straps?" Nothing in the pipeline asked that question. |
| Cost | One 9 h tower print could have been redone; instead that tower gets a **retrofit**: drill Ø6.5 through the boss and front plate, M6 × 30 into a captive nut in a printed 30 mm backer inside the tower (its back plate has no material around the bolt line, so no through-bolt). New prints have the hole, the back pad and the through-bolt. |
| Root cause | We checked that parts fit and print, never that each joint can carry its load. The MuJoCo sim treats the bracket as welded to the tower, so it could not show this. |
| Fix | An **M6 x 65 socket head** through the bracket, the boss, the front plate, the tower's hollow and its back plate; a printed Ø24 x 3 washer at each end (31); 2 M6 nuts jammed at the back; a printed crush tube (32) between the tower's two plates, so tightening can't squeeze them together (the bolt is threaded near its tip only, so no nut can sit behind the front plate). Both plates share the load, and the clamp holds the angle. The slot screw is gone. |
| What catches it now | `fastener_check.py` (every bought screw must have ≥ 3 mm of material or a nut at its tip; runs before every export and in the pre-commit hook). It catches screws that hold *nothing*. It does **not** judge whether a wall is strong enough: that needs a load check (see README, "next tests"). |

**Note on the diagnosis:** at first I told you the old screw ended "in thin air". That was wrong: see [false-thin-air-diagnosis](false-thin-air-diagnosis.md). The old joint held, just weakly.
