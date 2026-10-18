# Carriage web hit link-1 lid screw heads

**Where:** Carriage + link 1  
**Status:** fixed

| | |
|---|---|
| What | The carriage's front web collided with the lid screw heads of link 1. |
| How found | Assembly interference sweep. |
| Cost | None printed. |
| Root cause | The web was sized without the hardware in the collision check. |
| Fix | Web lifted 3.5 mm. |
| What catches it now | `collision_check.py` (every body of the assembly, hardware included) before every export. |
