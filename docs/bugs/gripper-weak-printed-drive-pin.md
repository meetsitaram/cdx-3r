# Gripper drive pin and trigger horn too weak to print

**Where:** gripper prototype 2: the tab on gear R's drive arm, and the trigger's horn
**Status:** fixed in the model (not printed yet)

| | |
|---|---|
| What | **Drive pin:** the tab the pusher pushes was a printed Ø6 pin hanging 20 mm off a thin 7 × 6 mm arm. The gear prints flat, so the pin stands upright and the push loads it across its layers: safety factor 2.1. **Trigger horn:** a 6 × 4 mm horn carries the cable pull (~78 N on a hard squeeze): safety factor 0.8. |
| How found | User review flagged the drive pin: "looks weak for a 3d printed part and can break off". The new strength rule also found the horn. |
| Cost | A review round; the horn would have snapped on the first hard squeeze. |
| Root cause | No load check on small printed features. The stress studies covered only the shoulder parts. |
| Fix | The drive arm is 10 mm wide and runs past the pin. The pin is a steel M4 × 20 screw, head down: the pusher bears on the steel head, and the shank goes up through the arm into a nyloc. The horn is 10 × 8 mm (safety factor 4.3). |
| What catches it now | `design_rules.py`, **strength**: the declared slender features (trigger lever and horn, pusher lever, drive arm, drive pin) are checked as cantilevers under the loads of a hard squeeze (40 N at the finger, carried down the chain). Their sections come from the build parameters, so making a part thinner fails here first. It uses PETG yield along or across layers (45 / 30 MPa) and requires a safety factor ≥ 3. Proven on the old model: both failures above. |
