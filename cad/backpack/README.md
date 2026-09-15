# CDX-3R backpack

Three winches. One Hailong 48 V. Cable bulkhead at the top.

## Buy (real)

| Qty | Part | Why |
|---|---|---|
| 3 | [ODrive S1](https://shop.odriverobotics.com/products/odrive-s1) $149 | One axis each. 12–48 V, 40 A. |
| 3 | [D6374 150 kV](https://shop.odriverobotics.com/products/odrive-custom-motor-d6374-150kv) $119 | 10 mm shaft, 8 mm rear for encoder. |
| 3 | PLE60 10:1 planetary (14 mm out) | Drum torque. 10 mm in matches D6374. |
| 3 | [CUI AMT212](https://www.cuisensors.com/) on the rear 8 mm | ODrive S1 encoder. |
| 1 | Hailong 48 V 13 Ah (367×90×111 mm) | ~4 kg, XT90. E-bike down-tube pack. |
| 2 | XT90 | Battery to bus. |
| 6 | M5×0.8 barrel adjusters + 5 mm Jagwire ferrules | Bulkhead. Antagonist pair per axis. |
| 6 | 608-2RS [6455K44](https://www.mcmaster.com/6455K44/) | Drum support. |

## Gears

Printed drum, 20 mm pitch radius, on the 14 mm planetary output.

| Joint | Cable T (5 kg) | Drum τ | Motor τ after 10:1 |
|---|---|---|---|
| Elbow | 450 N | 9 N·m | 0.9 N·m — D6374 is fine |
| Shoulder flex | 840 N | 17 N·m | 1.7 N·m — peak ok |
| Shoulder abd | same order | same | same |

15 kg at the shoulder is **not** this gearbox. That needs 1/8 in rope and a bigger reducer.

## Print

Frame, Hailong sled, 3 drums, bulkhead plate. Do not print motors, S1, battery, planetaries.
