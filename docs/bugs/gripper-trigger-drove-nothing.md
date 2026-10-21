# Gripper trigger was not connected to anything

**Where:** gripper prototype 2: trigger → cable → pusher lever → drive pin → gears
**Status:** fixed in the model (not printed yet)

| | |
|---|---|
| What | The trigger, its horn, the pusher lever and the gears were all modelled, but no wire joined the horn to the pusher. The trigger drove nothing. |
| How found | User review: "the trigger is not connected to anything yet". |
| Cost | A review round. |
| Root cause | I checked the chain only in my head (`_chain` computes the motion). Nothing in the model checks that each link physically touches the next. |
| Fix | The inner wire is modelled from the horn, along a channel in the arm, through the housing and the cable stop, into the pusher lever. The pusher bears on the steel head of the drive pin. |
| What catches it now | `design_rules.py`, **chains**: for each declared drive chain (in its pose: head slid forward), consecutive links must touch: trigger → wire → pusher → drive pin → gear R → gear L → fingers. Proven on the old model: it failed at trigger → wire (20.8 mm) and wire → pusher (9.5 mm). |
