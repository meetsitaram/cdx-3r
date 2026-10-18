# Shoulder + back system, print set v3 (Bambu P1S)

Back frame, shoulder girdle (tower, lift, SCARA arms), shoulder hinges, upper-arm link and the chained shoulder rest,
fitted to the exoarm2 body scan. Built by `cad/fusion/shoulder.py`, `girdle_b.py` and `shoulder_rest.py` (Fusion
document **CDX-3R shoulder + back**). The elbow is unchanged: print it from `prints/elbow-test-v10/`. Assembly:
`docs/ASSEMBLY.md`. Hardware: `BOM.md`.

Every STL is one solid in the design frame: use **Lay on Face** in Bambu Studio for the orientation below. Every part
fits the 256 mm bed. Settings: PETG, 0.2 mm layers, 4–5 walls, 5 top/bottom, 40 % gyroid (100 % for the pulleys and
spacers).

**Print first:** `prints/elbow-test-v10/00_fit_coupon_bearing_pockets.stl` if the 608 / 6806 fits are unknown, then
the back frame (01–05) so you can assemble as you go.

| File | Qty | Size (mm) | ~g | Orientation / supports | vs v2 |
|---|---|---|---|---|---|
| `01_bottom_node_R.stl` | 1 | 188 × 92 × 36 | 286 | back face down (splice side); strap tabs stand up | same as v2 |
| `02_bottom_node_L.stl` | 1 | 188 × 92 × 36 | 286 | back face down, as R | same as v2 |
| `03_bottom_node_splice_plate.stl` | 1 | 100 × 74 × 42 | 60 | U-channel, open side up | same as v2 |
| `04_mid_node.stl` | 1 | 212 × 70 × 42 | 174 | back face down; support the angled diagonal socket | **changed**: right beam/diagonal sockets gone |
| `05_top_node.stl` | 1 | 211 × 70 × 43 | 174 | back face down; support the angled beam socket | **changed**: right end is the tower tenon |
| `06_shoulder_block_L.stl` | 1 | 150 × 80 × 69 | 426 | rear face down (pocket axis vertical) | same as v2 (left only: battery mount) |
| `07_shoulder_tower.stl` | 1 | 203 × 167 × 66 | 245 | upright, node end on the bed | new |
| `08_lift_link_upper.stl` | 1 | 131 × 60 × 26 | 74 | flat on a cheek face | new |
| `09_lift_link_lower.stl` | 1 | 131 × 60 × 26 | 74 | flat on a cheek face | new |
| `10_lift_carriage.stl` | 1 | 114 × 97 × 63 | 144 | upright, root plate on the bed; supports under the front cheek's lower end and the strut fork | new |
| `11_scara_link1_tray.stl` | 1 | 106 × 62 × 22 | 41 | outer face down | new |
| `12_scara_link1_lid.stl` | 1 | 106 × 62 × 8 | 23 | outer face down | new |
| `13_scara_link2_tray.stl` | 1 | 109 × 47 × 22 | 41 | outer face down | new |
| `14_scara_link2_lid.stl` | 1 | 109 × 47 × 8 | 23 | outer face down | new |
| `15_end_plate_housing.stl` | 1 | 77 × 69 × 62 | 99 | on the housing's front face (E nut pocket opens upward) | new |
| `16_pulley_P0.stl` | 1 | 22 × 22 × 8 | 2 | flat | new |
| `17_pulley_PA.stl` | 1 | 22 × 22 × 8 | 2 | flat | new |
| `18_pulley_PB.stl` | 1 | 22 × 22 × 8 | 2 | flat | new |
| `19_pulley_P2.stl` | 1 | 22 × 22 × 8 | 2 | flat | new |
| `20_spacer_thick_x8.stl` | 8 | 11 × 11 × 4 | 1 | flat | new |
| `21_spacer_thin_x5.stl` | 5 | 11 × 11 × 1 | 0 | flat | new |
| `22_abduction_sleeve.stl` | 1 | 69 × 30 × 30 | 34 | on end (bore vertical) | same as v2 |
| `23_yoke.stl` | 1 | 165 × 112 × 88 | 154 | flexion housing axis vertical; support the root boss | same as v2 |
| `24_flexion_sleeve.stl` | 1 | 40 × 40 × 25 | 23 | on end | same as v2 |
| `25_upper_arm_link.stl` | 1 | 187 × 125 × 97 | 249 | outer (spoked) plate down; support the fork gap and pipe head | **changed** since v2 |
| `26_rest_bracket.stl` | 1 | 89 × 57 × 21 | 13 | flat, tower side down | new |
| `27_rest_root_arm.stl` | 1 | 90 × 85 × 51 | 29 | on edge, hinge-pin axis vertical; brim | new |
| `28_rest_blade_1.stl` | 1 | 79 × 56 × 51 | 19 | on edge, pin axis vertical; brim | new |
| `29_rest_blade_2.stl` | 1 | 84 × 67 × 49 | 24 | on edge, pin axis vertical; brim | new |
| `30_rest_blade_3.stl` | 1 | 101 × 82 × 66 | 35 | on edge, pin axis vertical; brim | new |

Total about **2.8 kg** at 60 % effective fill. Already printed v2? Skip the parts marked "same as v2" and reprint
04, 05 and 25. The v2 `Abduction_mount_block_R` is no longer used (the tower replaces it).

## Notes

- **Hidden nuts:** the tower, carriage, end plate and arm link have hex pockets for nuts that go in before the next
  part closes over them: see the ⚠ steps in `docs/ASSEMBLY.md`.
- **Strut forks** (tower and carriage ears): the 4.5 mm slot takes the strut's flat eyelet. If the eyelet is thicker
  than 4 mm, file the slot.
- **Pulleys** are 35-tooth GT2 for the 200 mm closed belts at 65 mm centres: 100 % infill, 0.12 mm layers if the teeth
  come out soft.
- **Inserts:** every insert hole is Ø4.0 × 7 mm for ruthex RX-M3 × 5.7.
