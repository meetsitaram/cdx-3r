# Servo horn coupler sat on the horn's centre screw

**Where:** elbow servo v1: `03_servo_horn_coupler` on the XL430-W250-T horn
**Status:** fixed in the model (reprint `03_servo_horn_coupler` only)

| | |
|---|---|
| What | The XL430's horn is held on by a centre screw whose head (with its washer) stands proud of the horn face. The coupler's flat back landed on that head, so it couldn't sit flat on the horn and its 2 M2.5 screws couldn't pull it down. |
| How found | User, while fitting the printed parts (27 Oct): "we will need a small hole in the middle for that screw". |
| Cost | A reprint of the coupler (small). |
| Root cause | The horn was modelled from Robotis' STEP as a plain disc; the centre screw isn't in it, so nothing in the model was in the coupler's way. The collision sweeps also skip the coupler/horn pair, because both turn with the forearm (same part). |
| Fix | The horn's centre screw head is now modelled (Ø5 × 2 mm, a generous guess: measure if it ever matters) and the coupler has a Ø7 hole through its middle, which clears it and lets a screwdriver reach it. |
| What catches it now | `concepts.horn_fit()`: an interference check between the coupler and everything on the horn's face, run on every build of the elbow; it raises if anything reaches into the coupler. Proven on the old coupler (centre hole off): it failed. |
| Lesson | A bought part's STEP can leave out its screws. Before mating to a bought part, check its photos for anything standing proud of the face. |
