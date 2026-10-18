# Carriage: 0.05 mm film, cut-away nut seat, crescent wall

**Where:** 10_lift_carriage  
**Status:** fixed

| | |
|---|---|
| What | A clearance cut started 0.05 mm off the cheek face (a film that cannot print); in code it started at the cheek's inner face (cut the nut's seat away); a round well into the strut ear left a wall thinning to zero. |
| How found | User, from slicer previews ("left over thin region", "inner ring so thin it might not print"). |
| Cost | None printed. Several rebuilds. |
| Root cause | Cuts offset by a small amount, and a range variable meaning the inner face used as the outer one. |
| Fix | Cuts start exactly on the face they clear; a flat chord instead of a crescent. |
| What catches it now | `print_validate.py` (thin films fail, edges only warn), run after every export and in the pre-commit hook. Proven: the old carriage fails, the fixed one passes. |
