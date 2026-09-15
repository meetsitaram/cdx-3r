# CDX-3R elbow

Hinge. One revolute axis through the epicondyles. Two cables (flex / extend). McMaster sheave on a 3/4 in shaft. Printed forks and cuffs.

This is **not** certified. 5 kg garage. 15 kg only after you swap in 1/8 in wire rope and stop treating PETG as structure.

## Physics

\[
\tau = T \cdot r
\]

Pitch radius \(r = 38.1\,\mathrm{mm}\) (McMaster 3434T121, 3 in pitch).

Lever from elbow axis to crate ≈ 0.35 m (forearm 260 mm + half hand).

| Crate | Moment at elbow | Cable tension |
|---|---|---|
| 5 kg (garage) | 17 N·m | 450 N |
| 15 kg (target) | 51 N·m | 1350 N |

Jagwire 1.5 mm stainless is a **5 kg** cable. Breaking load is roughly 1.8–2.5 kN; working load should stay well under that. For 15 kg buy 1/8 in 7×19 and keep the same sheave (groove is oversized, that is fine).

Antagonist: flexor pulls, extensor slacks. Do not run one cable and a rubber band if you want to set a crate down under control.

## Human numbers (edit `../params.json`)

| | mm |
|---|---|
| Upper arm, shoulder axis → elbow axis | 290 |
| Forearm, elbow axis → wrist | 260 |
| Hand | 90 |
| Elbow width (epicondyle to epicondyle) | 80 |
| Forearm cuff ID (skin + 8 mm foam) | 95 |
| Upper-arm cuff ID | 105 |
| ROM | 0–135° flexion |
| Work pose | 90° |

Measure the wearer. Change the JSON. Rebuild.

## Buy (do not print)

| Qty | Part | Why | Link |
|---|---|---|---|
| 1 | McMaster **3434T121** sheave, 3.5 in OD, 3/4 in bore, 1550 lb | Joint radius and the only rated groove | [3434T121](https://www.mcmaster.com/3434T121/) |
| 1 | 3/4 in × 100 mm precision shaft | Elbow axis | [1346K17](https://www.mcmaster.com/1346K17/) |
| 2 | 3/4 in retaining rings | Shaft retention | McMaster 97633A170 family |
| 2 | 25 mm OD × 1 mm wall tube, 150 mm stubs | Upper arm + forearm spars | McMaster 89995K31 family |
| 1 | Jagwire 1.5 mm stainless + 5 mm housing kit | Garage cable | Jagwire Mountain Pro |
| 8 | M4 heat-set inserts | Forks and hub | [94180A351](https://www.mcmaster.com/94180A351/) |
| 8 | M4 × 16 SHCS | Sandwich bolts | McMaster 91290A152 family |
| 2 | 25 mm webbing + cam lock | Cuffs | any pack strap |
| 1 | 8 mm EVA foam sheet | Inside cuffs | |

Optional load upgrade: 1/8 in 7×19 stainless, McMaster 3461T44. Same printed parts.

## Print (PETG or PA12-CF)

| File | Material | Notes |
|---|---|---|
| `print_fork_lateral.stl` | PETG, 5 walls, 40 % gyroid | Flat on bed, 0.2 mm |
| `print_fork_medial.stl` | same | Mirror. Heat-set M4 from the outside |
| `print_forearm_hub.stl` | PA12-CF preferred | Clamps 25 mm tube, keys to sheave |
| `print_cuff_forearm.stl` | PETG | Split C, foam inside |
| `print_cuff_upper.stl` | PETG | Sits ~80 mm proximal of axis |
| `print_bowden_anchor.stl` ×2 | PETG | 5 mm ferrule seat, M5 clamp |
| `print_hard_stop.stl` | PETG | 0° and 135° faces |
| `print_drum.stl` | **prototype only** | Use if the McMaster sheave is late. Not for 15 kg |

Do not print `ref_sheave.stl`. That is the COTS envelope.

## Assemble

1. Heat-set M4 inserts in both forks.
2. Slide sheave onto shaft. Snap rings outboard of forks.
3. Bolt forks around the 25 mm upper-arm tube. Axis must line up with the epicondyles, not float 40 mm off the joint.
4. Clamp forearm hub to the 25 mm forearm tube. Two M4 through the sheave web if you drill it; otherwise friction plates on both faces.
5. Foam + straps. You should be able to doff without tools.
6. Seat 5 mm ferrules in the two Bowden anchors. Flexor wraps the sheave inferior; extensor superior.
7. Hard stop must hit **before** the anatomical end-stop. The suit does not get to hyperextend you.

## OpenSCAD

```bash
openscad cad/elbow/cdx-3r-elbow.scad
```

`part = "assembly";` or `"fork_l"`, `"fork_r"`, `"hub"`, `"drum"`, `"cuff_forearm"`, `"cuff_upper"`, `"bowden"`, `"stop"`.

## Rebuild STLs

```bash
python3 cad/elbow/build_stl.py
```
