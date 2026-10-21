# Gripper cable housing hung in thin air

**Where:** gripper prototype 2, the trigger cable along the handle arm
**Status:** fixed in the model (not printed yet)

| | |
|---|---|
| What | The brake-cable housing ran from near the arm's side to near the pusher lever, ending in mid-air at both ends: 1 mm off the arm, nothing at the front. A housing only works when both ends push against a stop. The return spring's coil also floated around its post, with no spool. |
| How found | User review of the model: "what is that white piece hanging on by itself in thin air?" |
| Cost | A review round; it would have been a non-working trigger. |
| Root cause | No check asked whether a part is held by anything. The collision check only reports parts that overlap, so a part that touches nothing passes it. |
| Fix | The housing sits squarely on the arm's side face at the back and on a printed cable stop at the front. The wire is modelled end to end. A printed spool carries the coil. |
| What catches it now | `design_rules.py`, **floating**: every body must touch another (within 0.3 mm) and link back to the rail base through touching parts. It runs in `checks.run_all` and the pre-commit hook (`design_rules.txt`). Proven on the old model: it flagged the housing. |
