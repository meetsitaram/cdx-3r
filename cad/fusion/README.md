# CDX-3R in Autodesk Fusion

Fusion models built from this repo's CAD, and the scripts that build them. Scripts run inside
Fusion (Fusion MCP or Utilities > Scripts and Add-Ins); units are mm.

## Models (`models/`)

| File | What |
|---|---|
| `cdx-3r-elbow-concepts.f3d` | Current elbow design (concept B): PVC-pipe arm units (3 rear pipes, 2 self-tapping screws per pipe joint, forearm tapering to the wrist), two-sided 6806 bearing joint with bolted axles (pilot + 3 × M3), M3 covers, elbow shells, hyperextension ledge and 135° flexion stop, side-opening wrist cuff, rounded skin-side edges, fit coupons, and all bought hardware modelled. Repeated features are patterns / mirrors of one seed. Built by `concepts.py`. |
| `cdx-3r-shoulder-back.f3d` | Shoulder + back system on the exoarm2 body scan: PVC back frame (mirrored L/R), strap anchors, split bottom node with U-channel splice, abduction mount blocks (2 x 6806, M8 through-bolt), yoke, one-piece upper-arm link (6808 fork hinge, spoked hub, pipe head + brace wall), all hardware, the elbow (copied, posed at the scanned 12 deg), scan reference and harness illustration. Built by `shoulder.py`. |
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

Test prints: `prints/elbow-test-v10/` and `prints/shoulder-back-v2/` are current (see its README). Earlier folders are kept for
reference; each README says what changed.

Shoulder + back (`shoulder.py`): run `main()` (frame), then `main2()` (moving side), `place_elbow()`, `add_harness()`
and `show_reference_smooth()`; `export_print(dir)` writes the print set. Rebuilding the frame removes the arm side, so
always run `main2()` after `main()`. Keep each call short (the MCP call times out on very long runs). Lessons learned
building both are in `LESSONS.md`; the body-scan pipeline is in `cad/scan/`; bought parts are in `BOM.md` at the repo root.
