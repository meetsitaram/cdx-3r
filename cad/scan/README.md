# Body scan → exo layout (exoarm2)

These scripts turn the exoarm2 Gaussian-splat body scan into a clean body mesh, lay out the exo on it and check clearances.
The working copy (with the large scan meshes) lives in `C:\Users\PC\projects\exoarm2-scan`. `cad/fusion/shoulder.py`
reads `exoarm2-scan/out/...` from there. This folder is the versioned copy of the scripts plus `layout/layout.json` (the
landmarks and frame points the Fusion model is built from).

The frame is mm, X forward, Y up, Z right; floor at Y = 0. Tools need Python 3.12 with numpy, scipy, open3d, trimesh, manifold3d,
shapely, scikit-image and matplotlib.

| Script | What |
|---|---|
| `splat.cs` | C# SPZ decoder/renderer (no Python needed) |
| `body.py` | splat → body point cloud, levelled and yaw-aligned (`body_pts.ply`) |
| `solid.py` / `mesh.py` | watertight body solid (voxel close + fill + marching cubes) |
| `landmarks.py` / `sections.py` | slice measurements and section plots (shoulder GH, elbow, wrist) |
| `layout.py` | layout + distance fields; rest pose (20° abduction); writes `layout.json` |
| `trim.py` | Fusion reference meshes (torso hips → neck without head/left arm; right arm to wrist) |
| `harness.py` | webbing + buckles illustration routed over the torso |
| `check_fusion.py` | clearance of the Fusion-exported parts to the body + shoulder ROM sweep |
| `com.py` | mass and centre of mass |
| `rest.py`, `study_ua.py`, `render.py`, `viewer.py`, `fmcp.py` | shoulder-rest study (dropped), upper-arm study, renders, three.js viewer, a direct Fusion MCP client (fallback only) |
