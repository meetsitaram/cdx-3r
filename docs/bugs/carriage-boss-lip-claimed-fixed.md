# Carriage boss lip: reported fixed, but the fix was not in the code

**Where:** 10_lift_carriage  
**Status:** fixed

| | |
|---|---|
| What | I told the user the boss lip was already fixed; it was not. |
| How found | The next slicer preview still showed it. |
| Cost | Lost trust and one more round. |
| Root cause | A fix was reported from memory without checking the diff. |
| Fix | Fixed for real (boss removed; a printed root spacer instead). |
| What catches it now | Rule: show the diff line before reporting a fix. `print_validate` would also flag the lip if it left a film. |
