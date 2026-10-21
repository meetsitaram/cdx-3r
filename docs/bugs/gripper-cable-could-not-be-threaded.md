# Gripper trigger cable could not be threaded

**Where:** gripper prototype 2, the trigger wire's path through the handle arm
**Status:** fixed in the model (not printed yet)

| | |
|---|---|
| What | The wire ran from the trigger's horn back through a closed channel inside the arm, then turned 90° inside the solid plastic to exit the side. You can't push a stiff 1.5 mm brake wire round a hidden corner. Neither wire end had a nipple or clamp to hold it. |
| How found | User question after the previous fix: "how will I get the wire through the solid material?" |
| Cost | A review round; the arm would have been printed with an unusable channel. |
| Root cause | The model checked that the wire touched each link (`chains`), not that a person could fit it. |
| Fix | The housing lies in a pocket open on the arm's side and seats on a 4.5 mm wall. The wire's only walled-in runs are straight: the hole through that wall, the cable stop at the front, and the pusher lever's hole. The horn's wire slot is open at the top, and the U-turn (needed because the horn moves forward when squeezed) happens in the flexible housing outside the arm, on a 20 mm radius. Ends: the cable's barrel nipple behind the horn; a solderless screw nipple behind the pusher lever, which also sets the tension. The wire runs level from the cable stop into the pusher. |
| What catches it now | `design_rules.py`, **cables**: rays square to the route find where the wire is walled in by printed material (within 15 mm all round). Every walled-in run must be straight (≤ 10°), and each end must sit at a nipple. Proven on the old model: "enclosed 56 mm, bends 90 deg inside" and both ends unanchored. |

**How to fit it:** drop the barrel nipple into place behind the horn and lay the wire in the horn's slot. Push the wire through the wall hole into the housing, seated in the side pocket. Run the housing round its loop to the cable stop, and the wire through the stop and the pusher lever. Put on the screw nipple, pull out the slack and tighten its grub screw.
