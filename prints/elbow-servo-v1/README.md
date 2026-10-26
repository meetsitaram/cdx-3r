# Elbow servo v1: Dynamixel XL430-W250-T on the elbow

Replaces the **outer (lateral) bearing cover** of elbow test print v10 with a case for an XL430-W250-T, so the elbow
no longer swings freely: the forearm turns the servo's horn. Built by `servo_side()` in `cad/fusion/concepts.py`
(sizes from Robotis' STEP in the koch-v1-1 repo, `hardware/follower/STEP/Robotis_DYNAMIXEL_XL430_W250_T.STEP`).

**Unchanged and reused:** both elbow pieces (`01`, `02` of v10), the inner (medial) axle and cover, both 6806
bearings, the outer axle's 3 × M3 × 8 and the hub inserts, and the 6 inserts the old cover screwed into.

## Parts

| File | Qty | Print | Notes |
|---|---|---|---|
| `01_servo_case.stl` | 1 | plate down, as exported | the servo drops into its pocket; 6 × M3 × 12 into the old cover's inserts |
| `02_servo_strap.stl` | 1 | flat | across the back of the servo, 2 × M3 × 8 into inserts in the case walls |
| `03_servo_horn_coupler.stl` | 1 | flat, pegs up | 2 × M2.5 × 6 into the horn; its 3 pegs drop into the axle |
| `04_servo_axle_lateral.stl` | 1 | flat, pilot up | replaces the **outer** `03_bearing_axle`: same screws, deeper screw pockets (the pegs go in above the heads), Ø36 flange outside the bearing |

Hardware: the XL430-W250-T with its horn, 2 × M2.5 × 6 socket head, 6 × M3 × 12 socket head, 2 × M3 × 8 socket
head, 2 ruthex M3 inserts (case walls). Every part passes the checks in this folder.

## Assembly

1. Take off the old outer cover (6 screws) and the old outer axle (3 screws). The forearm stays on the inner axle.
2. **Servo axle:** in through the bearing from outside, pilot into the hub, 3 × M3 × 8 back into the same inserts.
3. **Case:** 2 inserts into the tops of its side walls. Case plate on the housing, 6 × M3 × 12 into the old cover's
   inserts (do these before the servo goes in: two of them sit under it).
4. **Coupler on the horn:** turn the servo to its centre position (in the Dynamixel Wizard), then screw the coupler
   onto the horn with 2 × M2.5 × 6 through the counterbored holes.
5. Put the forearm at the angle you want to call centre. Drop the servo into the case, horn first, turning the
   forearm a little until the 3 pegs fall into the axle's screw pockets.
6. Strap across the back, 2 × M3 × 8. The cable end of the case is open (towards the shoulder).

## Before you power it

- **Don't force an unpowered XL430.** Its gearbox is 258:1. Pushing the elbow hard with the servo off, or against
  a stalled servo, can strip its gears. Run it powered in current-based position mode (Operating Mode 5) with a low
  current limit, or as a soft spring (low P gain), so your arm can always move it.
- It needs 12 V and a U2D2 (or another TTL bus adapter), as on the Koch arm.
- Holding torque is about 1.4 N m at stall: enough to stop the elbow swinging, not to lift a heavy load.
