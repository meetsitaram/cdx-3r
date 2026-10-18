# Arm raised high swings into the shoulder rest

**Where:** yoke, upper-arm link, flexion sleeve (moving) vs rest blades 1–3 and pads (fixed to the tower)  
**Status:** open: found by the motion sweep, needs a design decision — listed in `collision_check.MOTION_KNOWN` (only these poses and parts pass; remove the entry when fixed)

| | |
|---|---|
| What | Raising the arm out to the side past about 75° (abduction +55° from the 20° rest) is clear; from +65° the yoke enters rest blade 2 (4.4 cm³), and at the +75° stop (arm at 95°) yoke, upper-arm link and flexion parts overlap blades 1–3 by up to 16 cm³ (worst with the shoulder pulled in). With a shrug at the same time (+60 mm) it's clear. |
| How found | `collision_check.sweep` (motion_check.txt): the first check that moves the parts. Static checks and the renders (which only went to +55°) never saw it. |
| Cost | Nothing printed yet for the rest blades. |
| Root cause | The rest was laid out on the shoulder at rest; nobody checked the arm's swept volume against it. |
| Fix | Open. Options: limit abduction to +55° (an end stop) unless shrugging; or shape/shorten the blades where the yoke passes; or move the rest further back. |
| What catches it now | `motion_check.txt` (22 poses: shrug, down, reach, squeeze, in/out, abduction 25–75°, flexion −20…120° and combinations), part of `checks.run_all` and required by the pre-commit hook. |
