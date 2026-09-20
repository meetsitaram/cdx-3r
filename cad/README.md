# CDX-3R CAD — piece by piece

Not a 7-axis arm. Three revolute joints, right side.

| Order | Stage | Status |
|---|---|---|
| 1 | **Elbow** — hinge, antagonist sheave, cuffs | `elbow/` |
| 2 | **Shoulder** — flexion (lateral) + abduction (posterior) | `shoulder/` |
| 3 | **Backpack** — 3 winches, Hailong 48 V, ODrive S1 | `backpack/` |
| 4 | **Connect** — one system, saddle + hip belt take the weight | `system/` |
| 4 | Connect — Bowden runs, cable comb, hard stops as a system | after pack |
| 5 | **Armor** — circular window around the sheave | `armor/` |

**Rule:** metal takes the load. Print the fixtures that hold the metal.

Open `elbow/` first. Do not print the whole suit.

## Current revision

[Revision B — rebuilt shells](armor/README.md) adds segmented shoulder armor,
tapered arm panels and a passive wrist collar, with a synchronized full assembly.

```bash
python -m pip install -r cad/requirements.txt
python -B cad/build.py
python -B -m unittest discover -s cad/tests -v
python -B cad/render_previews.py
```

The scripts work from this checkout without `/workspace` paths. STL units are mm.
Both local and public exports are produced from the same normalized meshes.
`cad/render_mesh.py` renders the actual STL surfaces locally with a depth buffer.
