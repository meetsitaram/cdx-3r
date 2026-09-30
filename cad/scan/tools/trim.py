"""Trim the scan reference meshes for Fusion: torso keeps hips..neck (no head, no helmet chin, no left arm),
right arm stops just past the wrist (no fingers)."""
from pathlib import Path
import json
import numpy as np
import trimesh

LAY = Path(__file__).resolve().parent.parent / 'out' / 'layout'
info = json.load(open(LAY / 'layout.json'))
GH = np.array(info['landmarks']['GH']); WR = np.array(info['landmarks']['WR']); MID_Z = info['landmarks']['MID_Z']
f = np.array(info['derived']['f']); rest = info['params']['rest_abd']
Y_LO, Y_HI = 900., 1460.
CHIN = dict(x0=45., y0=1395., half_w=90.)
HAND_KEEP = 30.                                           # mm past the wrist centre


def abduct(p, deg):
    t = np.radians(deg); c, s = np.cos(t), np.sin(t); q = np.atleast_2d(p) - GH
    return GH + np.c_[q[:, 0], q[:, 1] * c + q[:, 2] * s, -q[:, 1] * s + q[:, 2] * c]


m = trimesh.load(LAY / 'body_torso.stl'); n0 = len(m.faces)
m = m.slice_plane([0, Y_LO, 0], [0, 1, 0], cap=True).slice_plane([0, Y_HI, 0], [0, -1, 0], cap=True)
chin = trimesh.creation.box(bounds=[[CHIN['x0'], CHIN['y0'], MID_Z - CHIN['half_w']], [400, 1600, MID_Z + CHIN['half_w']]])
l_arm = trimesh.creation.box(bounds=[[-400, 0, -600], [400, 1340, -235]])   # left arm, below the shoulder
m = m.difference(chin, engine='manifold').difference(l_arm, engine='manifold')
m = max(m.split(only_watertight=False), key=lambda p: len(p.faces))
m.export(LAY / 'body_torso_trim.stl')
print('torso %d -> %d faces, watertight %s' % (n0, len(m.faces), m.is_watertight))

a = trimesh.load(LAY / 'body_arm.stl'); a0 = len(a.faces)
fp = abduct(GH + f, rest)[0] - GH                          # forearm direction in the rest pose
cut = abduct(WR, rest)[0] + fp * HAND_KEEP
a = a.slice_plane(cut, -fp, cap=True)
a = max(a.split(only_watertight=False), key=lambda p: len(p.faces))
a.export(LAY / 'body_arm_trim.stl')
print('arm %d -> %d faces, lowest Y %.0f, watertight %s' % (a0, len(a.faces), a.bounds[0, 1], a.is_watertight))

# ---- fill the arm-gap tunnels: re-voxelize, close narrow gaps, fill holes slice-wise on all axes ----
from scipy import ndimage as ndi
from skimage import measure
P = 4.0
vg = m.voxelized(P).fill()
g = vg.matrix.copy()
g = np.pad(g, 6)
ball = lambda r: (np.add.reduce(np.indices((2 * r + 1,) * 3) - r) ** 2 if False else
                  (sum((np.indices((2 * r + 1,) * 3)[i] - r) ** 2 for i in range(3)) <= r * r))
g = ndi.binary_closing(g, ball(4))
for ax in range(3):
    g = np.moveaxis(np.array([ndi.binary_fill_holes(s) for s in np.moveaxis(g, ax, 0)]), 0, ax)
v, f_, _, _ = measure.marching_cubes(ndi.gaussian_filter(g.astype(float), 1.0), 0.5)
T = vg.transform
v = (v - 6) @ T[:3, :3].T + T[:3, 3]
t2 = trimesh.Trimesh(v, f_)
trimesh.smoothing.filter_taubin(t2, iterations=10)
if t2.volume < 0: t2.invert()
t2 = t2.slice_plane([0, Y_LO, 0], [0, 1, 0], cap=True).slice_plane([0, Y_HI, 0], [0, -1, 0], cap=True)
t2 = t2.simplify_quadric_decimation(face_count=15000)
t2.vertices -= t2.vertex_normals * 2.5                    # undo the voxel-fill inflation (~P/2 + blur)
t2.export(LAY / 'body_torso_trim.stl')
print('torso refilled: %d faces, watertight %s, volume %.1f L (was %.1f L)' % (len(t2.faces), t2.is_watertight,
                                                                              t2.volume / 1e6, m.volume / 1e6))
