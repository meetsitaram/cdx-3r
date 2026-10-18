# The new pivot bolt ran into the rest's hinge

**Where:** shoulder rest: bracket (26), root arm (27), the M6 x 65 pivot bolt from [rest-bracket-attachment](rest-bracket-attachment.md)  
**Status:** fixed

| | |
|---|---|
| What | The fix for 010 put an M6 x 65 bolt through the bracket's pivot. The pivot sits right under the root arm's hinge: the bolt head and front washer went 308 + 107 mm³ into the root arm's knuckle, and the bolt passed through the clevis pin. There was 1.8 mm between the bracket and the knuckle. |
| How found | The user, looking at the model in Fusion ("looks like the bolt will be colliding with the rest piece"). |
| Cost | No print (bracket and root arm weren't printed yet). One design round. |
| Root cause | The fix was checked for grip (fastener test) and printability, but nothing checked collisions: the only interference check was a one-off sweep in an old concept script, not part of the export. |
| Fix | The root hinge moved 10 mm forward (x −176 → −166, `shoulder_rest_layout.py`): bracket arms 10 mm longer, root arm 10 mm shorter; blades unchanged. Head + washer now have 2.8 mm clearance to the knuckle, and the root arm can swing ±90° before anything touches. |
| What catches it now | **`collision_check.py`**: Fusion's interference analysis on every body of the assembly (printed parts and hardware), 9 s. Runs before every export; the pre-commit hook requires `collision_check.txt` to say `failing 0`. Intended overlaps (R-clip through its pin, self-tapping screws, the strut's own parts) are listed with a reason. Calibrated: it reports this bug on the old version and passes the fixed one. Its first version reported 0 on the bad model too (results come back without their assembly path, so every pair looked like one part) — caught by testing it on the known-bad case first, per [false-thin-air-diagnosis](false-thin-air-diagnosis.md). |
