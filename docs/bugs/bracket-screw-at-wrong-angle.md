# Rest lock screw at 90° while its slot was at 50°

**Where:** Shoulder rest bracket + tower  
**Status:** fixed

| | |
|---|---|
| What | `bracket_bolts()` placed the screw, tower hole and nut trap at 90°, the slot was cut at `phi` = 50°: the screw sat on the strut ear. |
| How found | Interference sweep with all hardware. |
| Cost | None printed. |
| Root cause | The same position was computed in two places from different numbers. |
| Fix | One function gives the position to the cut, the hardware and the mating part. (Since [rest-bracket-attachment](rest-bracket-attachment.md) the slot lock is gone.) |
| What catches it now | `collision_check.py` (every body of the assembly, hardware included) before every export. |
