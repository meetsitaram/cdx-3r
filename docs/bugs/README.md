# Bugs

One file per design bug found and fixed. Each says what went wrong, what it cost, why, the fix, and **what test now
catches it** (or that nothing does yet). Name the file after what went wrong (`what-broke.md`, no numbers);
add a row at the bottom of the table (rows are in the order found).

| Bug | Cost | Caught now by |
|---|---|---|
| [Assembly animations showed an impossible build](assembly-animations-impossible-order.md) | review rounds | review rule only |
| [Strut modelled with ball ends; bought one has eyelets](strut-ball-ends-vs-eyelets.md) | redesign | rule only |
| [Carriage auto-oriented on its side, supports in holes](carriage-printed-on-its-side.md) | slicing round | `orient_stls.py` + hook |
| [Carriage 0.05 mm film, nut seat cut away, crescent](carriage-thin-film-and-crescent.md) | rebuilds | `print_validate.py` |
| [Fix reported but not made (boss lip)](carriage-boss-lip-claimed-fixed.md) | a round, trust | rule: show the diff |
| [Carriage base on a 0.6 mm boss](carriage-flat-base.md) | — | rule only |
| [Carriage web hit link-1 screw heads](link1-lid-screws-vs-web.md) | — | `collision_check.py` |
| [Servo coupler sat on the horn's centre screw](servo-coupler-on-horn-screw.md) | coupler reprint | `concepts.horn_fit()` |
| [Rest screw at 90°, slot at 50°](bracket-screw-at-wrong-angle.md) | — | `collision_check.py` |
| [Docs: backbone 583 mm, model 568 mm](stale-backbone-length.md) | — | rule only |
| [**Rest bracket held by one screw and a 1.7 mm wall**](rest-bracket-attachment.md) | **9 h print → drill a hole** | `fastener_check.py` (partly) |
| [My false "thin air" diagnosis of the bracket bug](false-thin-air-diagnosis.md) | near reprint | rule: test known-good/bad |
| [Tower pivot hole broke out of the back plate](tower-pivot-hole-breakout.md) | none | `print_validate.py` |
| [The new pivot bolt ran into the rest's hinge](pivot-bolt-hits-rest-hinge.md) | design round | `collision_check.py` |
| [**Open:** arm raised past ~80° swings into the shoulder rest](raised-arm-hits-shoulder-rest.md) | — | motion sweep |
| [**Open:** full shrug, lift link touches carriage (20 mm³)](full-shrug-lift-link-touches-carriage.md) | — | motion sweep |
| [**Open:** lift carriage over-stressed under an M8 pivot nut (FEA, 150 N)](carriage-nut-seat-overstressed.md) | — | stress study (manual) |
| [Gripper cable housing hung in thin air](gripper-cable-housing-in-thin-air.md) | review round | `design_rules.py` floating |
| [Gripper trigger was not connected to anything](gripper-trigger-drove-nothing.md) | review round | `design_rules.py` chains |
| [Gripper damper "gear" was a plain disc](gripper-damper-gear-was-a-disc.md) | review round | `design_rules.py` meshes |
| [Gripper drive pin and trigger horn too weak to print](gripper-weak-printed-drive-pin.md) | review round | `design_rules.py` strength |
| [Gripper trigger cable could not be threaded](gripper-cable-could-not-be-threaded.md) | review round | `design_rules.py` cables |
| [Gripper collar could not go on the carrier](gripper-collar-could-not-go-on.md) | collar reprint | `gripper3.insertion_rules` |
| [**SCARA end plate hung below the nut meant to hold it**](end-plate-hung-below-its-nut.md) | end plate reprint | `fastener_check.py` THREAD / HELD / JOINTS |
| [**Open (to investigate):** end plate ceiling and E bolt under the arm's tipping load](end-plate-tipped-by-the-arm.md) | — | nothing yet (stress study to do) |

## Tests that gate every export

`checks.run_all(<set>)` in Fusion on the assembly (also the first step of every export): `fastener_check.py` (screws
bite), `collision_check.py` (no part or bolt inside another) and its motion sweep (the same through 22 poses of the
girdle and arm), and `design_rules.py` on each mechanism module (floating parts, drive chains, gear meshes, strength of
slender printed features). Reports land in `prints/<set>/`, stamped with a hash of the model code; the pre-commit hook
(`checks.py --verify`) refuses any commit touching model code or prints unless every report says `failing 0` and has
the current stamp. Offline: `print_validate.py` (no film, one shell) and orientation.

## Next tests (would have caught the bracket bug before printing)

1. **Load path check:** every part must connect to the frame through named joints; each joint lists the load it carries
   (from MuJoCo) and its capacity (screw size, wall under the nut, bearing area). Fail when load > capacity / 3.
2. **MuJoCo joint forces:** model each attachment as its own weld with a force sensor; run the strap cases; write the
   peak force per joint to a table the load path check reads.
3. **Fusion Simulation (Static Stress)** for the few joints near their limit, with the MuJoCo forces as loads.
4. **Physical pull test** of a printed joint with a luggage scale before a long print.
