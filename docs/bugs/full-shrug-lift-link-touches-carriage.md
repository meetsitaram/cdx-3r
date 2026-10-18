# Full shrug: lower lift link touches the carriage

**Where:** lift link lower vs lift carriage (10)  
**Status:** open (small) — listed in `collision_check.MOTION_KNOWN` (only these poses and parts pass; remove the entry when fixed)

| | |
|---|---|
| What | At the full 60 mm shrug the lower lift link overlaps the carriage by 20 mm³: a light touch at the end of travel. |
| How found | Motion sweep (`motion_check.txt`). |
| Cost | — (the carriage is printed but a touch at the end stop may be acceptable as the stop itself). |
| Root cause | Lift link and carriage clearance only checked at rest. |
| Fix | Open: decide whether this is the intended end stop (then allow it in `collision_check.ALLOWED` with that reason) or relieve the link by ~1 mm. |
| What catches it now | `motion_check.txt`. |
