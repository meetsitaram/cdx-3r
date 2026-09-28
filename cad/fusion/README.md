# CDX-3R in Autodesk Fusion

Fusion models built from this repo's CAD, and the scripts that build them. Scripts run inside
Fusion (Fusion MCP or Utilities > Scripts and Add-Ins); units are mm.

## Models (`models/`)

| File | What |
|---|---|
| `cdx-3r-elbow-concepts.f3d` | Current elbow design (concept B): PVC-pipe arm units (3 rear pipes, 2 self-tapping screws per pipe joint, forearm tapering to the wrist), two-sided 6806 bearing joint with bolted axles (pilot + 3 × M3), M3 covers, elbow shells, hyperextension ledge and 135° flexion stop, side-opening wrist cuff, rounded skin-side edges, fit coupons, and all bought hardware modelled. Repeated features are patterns / mirrors of one seed. Built by `concepts.py`. |
| `cdx-3r-full-arm.f3d` | The whole existing CDX-3R (elbow, shoulder, backpack, system, armor, wearer) rebuilt as Fusion solids from `cad/*/build_stl.py`, plus the imported reference STLs. Built by `build.py`. |

Open with Fusion: File > Open > Open from my computer.

## Scripts

- `concepts.py` - the elbow concept. Edit `P` at the top (arm sizes, pipes, bearing, axle, screws,
  cuff, stops) and run `concepts.main()`; it rebuilds and re-runs the collision sweeps (elbow
  0-135°, cuff 0-100° at elbow 0° and 90°). The stop, pipe-path, hardware-fit and soft-tissue
  checks used during design are in the session notes of the test-print READMEs.
  `export_stls()` writes the test-print set.
- `build.py` + `fxlib.py`, `elbow.py`, `mech.py`, `armor.py` - the full-arm rebuild, one stage per
  subsystem; `check` compares every part with its reference mesh (all 114 layers within 0.85 mm).

Runner (Fusion MCP / script):

```python
import sys, importlib
sys.path.insert(0, r'<repo>\cad\fusion')
import fxlib, concepts
for m in (fxlib, concepts): importlib.reload(m)
def run(context): concepts.main(('B',))
```

Test prints: `prints/elbow-test-v9/` is current (see its README). Earlier folders are kept for
reference; each README says what changed.
