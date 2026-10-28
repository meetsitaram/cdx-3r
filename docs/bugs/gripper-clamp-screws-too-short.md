# Gripper pipe clamps: the thumb screws could not clamp

**Where:** gripper 3, base: the 2 pipe clamp screws (top of the base, into inserts, tip on the middle pipe)
**Status:** fixed (no reprint): M3 × 12 socket head instead of the M3 × 10 thumb screws; user is using long wood screws for now

| | |
|---|---|
| What | From the top of the base to the pipe is 9.25 mm, so a 10 mm screw could reach only 0.75 mm past the pipe's surface before its head landed on the base: almost no clamping travel. The model even drew the screw 9.25 mm long, tip just touching the pipe. |
| How found | User, fitting the base (27 Oct). |
| Root cause | No rule for clamp travel; the screw was drawn to fit the gap, not its real length. |
| What catches it now | `gripper3.clamp_rules()`: the screw's real length must reach ≥ 1.5 mm past the pipe. Proven on the M3 × 10: failed (0.75 mm); M3 × 12 passes (2.75 mm). |
| Note | The screw is on the top of the pipe, away from the arm: the pipe is always between its tip and the skin, and the clip is open on the arm side. |
