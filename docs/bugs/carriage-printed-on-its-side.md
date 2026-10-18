# Lift carriage printed on its side: supports inside the holes

**Where:** Print set, 10_lift_carriage  
**Status:** fixed

| | |
|---|---|
| What | Bambu auto-orient laid the carriage on its side; tree supports grew into the pivot tunnels and the S0 bore. My orientation advice also named the wrong face. |
| How found | User, in the slicer. |
| Cost | One slicing round; no print lost. |
| Root cause | STLs were exported in the design frame and the orientation in the README was a guess. |
| Fix | `orient_stls.py` picks the print-up direction (with an override table) and every STL ships pre-rotated; tunnels got 45° teardrop points on the top side only. |
| What catches it now | `export_prints.export` always orients; the pre-commit hook orients any STL that isn't. |
