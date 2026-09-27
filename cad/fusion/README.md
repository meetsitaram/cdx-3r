# CDX-3R in Autodesk Fusion

Fusion models built from this repo's CAD, and the scripts that build them. Scripts run inside
Fusion (Fusion MCP or Utilities > Scripts and Add-Ins); units are mm.

## Models (`models/`)

| File | What |
|---|---|
| `cdx-3r-elbow-concepts.f3d` | Current elbow design (concept B): PVC-pipe arm units, two-sided 6806 bearing joint, elbow shells, hyperextension ledge and 135 deg flexion stop, side-opening wrist cuff, fit coupons. Built by `concepts.py`. |
| `cdx-3r-full-arm.f3d` | The whole existing CDX-3R (elbow, shoulder, backpack, system, armor, wearer) rebuilt as Fusion solids from `cad/*/build_stl.py`, plus the imported reference STLs. Built by `build.py`. |

Open with Fusion: File > Open > Open from my computer.

## Scripts

- `concepts.py` - the elbow concept. Edit `P` at the top (arm sizes, pipes, bearing, door/cuff, stops)
  and run `concepts.main()`; it rebuilds and re-runs the checks: elbow sweep 0-135 deg,
  cuff sweep, hyperextension and flexion stops. `export_stls()` writes the test-print set.
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

Test prints: `prints/elbow-test-v5/` (see its README).
