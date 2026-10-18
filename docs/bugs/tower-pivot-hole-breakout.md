# Tower pivot hole broke out of the back plate's slanted edge

**Where:** shoulder tower (07), while fixing [rest-bracket-attachment](rest-bracket-attachment.md)  
**Status:** fixed

| | |
|---|---|
| What | The new Ø6.6 pivot hole exited the back plate right at its slanted edge, leaving a 0.02 mm film. |
| How found | `print_validate.py` failed the exported tower. |
| Cost | None (caught before export was accepted). |
| Root cause | A hole placed from the front without checking the material on the far side. |
| Fix | A round pad (washer Ø + 2 mm) on the back plate around the hole. |
| What catches it now | `print_validate.py`, on every export and in the pre-commit hook. It worked as intended here. |
