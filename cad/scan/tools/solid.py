"""body_pts.ply -> watertight solid body (voxel close + slice fill + marching cubes)."""
from pathlib import Path
import numpy as np
import open3d as o3d
import trimesh
from scipy import ndimage as ndi
from skimage import measure

OUT = Path(__file__).resolve().parent.parent / 'out'
VOX = 5.0   # mm

P = np.asarray(o3d.io.read_point_cloud(str(OUT / 'body_pts.ply')).points)
lo = P.min(0) - 40; hi = P.max(0) + 40
shape = np.ceil((hi - lo) / VOX).astype(int)
g = np.zeros(shape, bool)
ijk = ((P - lo) / VOX).astype(int)
g[tuple(ijk.T)] = True
print('grid', shape, 'occupied', g.sum())


def ball(r):
    x = np.arange(-r, r + 1)
    return (x[:, None, None] ** 2 + x[None, :, None] ** 2 + x[None, None, :] ** 2) <= r * r


# close gaps in the shell (sparse splat regions), 3D
s = ndi.binary_dilation(g, ball(3))
# fill each horizontal slice (Y is axis 1) -> solid cross-sections
for j in range(s.shape[1]):
    s[:, j, :] = ndi.binary_fill_holes(s[:, j, :])
# fill along the other axes too (armpit / crotch pockets)
for i in range(s.shape[0]):
    s[i] = ndi.binary_fill_holes(s[i])
s = ndi.binary_erosion(s, ball(3), border_value=0)   # undo the dilation
s = ndi.binary_opening(s, ball(1))
lab, n = ndi.label(s)
s = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
f = ndi.gaussian_filter(s.astype(float), 1.2)
v, faces, _, _ = measure.marching_cubes(f, 0.5)
v = v * VOX + lo
m = trimesh.Trimesh(v, faces)
trimesh.smoothing.filter_taubin(m, iterations=10)
if m.volume < 0: m.invert()
print('solid: %d faces, watertight %s, volume %.1f L' % (len(m.faces), m.is_watertight, m.volume / 1e6))
m.export(OUT / 'body_solid_full.stl')
d = m.simplify_quadric_decimation(face_count=40000)
print('decimated: %d faces, watertight %s' % (len(d.faces), d.is_watertight))
d.export(OUT / 'body_solid.stl'); d.export(OUT / 'body_solid.obj')
np.savez_compressed(OUT / 'body_vox.npz', s=s, lo=lo, vox=VOX)
