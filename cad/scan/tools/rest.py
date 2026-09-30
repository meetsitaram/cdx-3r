"""Printable right shoulder rest from the body scan (2 mm field, smooth outline, slots + holes).

Shell: inner face `pad` mm off the skin (room for foam), `t` mm thick, rolled rim.  Outline is a
rounded rectangle in plan (X fwd, Z right) - medial edge clear of the neck, lateral edge inside
the acromion so the shoulder joints swing past.  Features: two M5 rear holes (frame top node),
one M5 rear-lateral hole (abduction mount block strut), 25 mm webbing slot at the front edge.
Output: out/print/R_shoulder_rest.stl (world frame) and a copy laid flat for printing.
"""
from pathlib import Path
import json
import numpy as np
import trimesh
from scipy import ndimage as ndi
from skimage import measure

OUT = Path(__file__).resolve().parent.parent / 'out'
PR = OUT / 'print'; PR.mkdir(exist_ok=True)
lay = json.load(open(OUT / 'layout' / 'layout.json'))
GH = np.array(lay['landmarks']['GH']); MID_Z = lay['landmarks']['MID_Z']

R = dict(pad=15., t=6., vox=2.0,
         x=(-150., 55.), z=(MID_Z + 70., GH[2] - 20.), y_min=1325., y_max=1450., corner=30.,
         slot=(27., 4.5), hole=5.5, axle_clear=38.)

torso = trimesh.load(OUT / 'layout' / 'body_torso.stl')
lo = np.array([R['x'][0] - 40, R['y_min'] - 60, R['z'][0] - 40])
hi = np.array([R['x'][1] + 40, 1500., R['z'][1] + 40])
n = np.ceil((hi - lo) / R['vox']).astype(int)
g = np.stack(np.meshgrid(*[lo[i] + (np.arange(n[i]) + .5) * R['vox'] for i in range(3)], indexing='ij'), -1)
# inside/outside of the torso on the fine grid (ray-free: winding via contains is slow; use voxelized fill)
vg = torso.voxelized(R['vox']).fill()
inside = np.zeros(n, bool)
pts = vg.points
ijk = np.floor((pts - lo) / R['vox']).astype(int)
ok = np.all((ijk >= 0) & (ijk < n), 1)
inside[tuple(ijk[ok].T)] = True
inside = ndi.binary_closing(inside, iterations=2)
d = ndi.distance_transform_edt(~inside) * R['vox']
d = ndi.gaussian_filter(d, 1.0)

# plan outline: rounded rectangle, smooth edge via signed distance in (X, Z)
X, Y, Z = g[..., 0], g[..., 1], g[..., 2]
cx, cz = np.mean(R['x']), np.mean(R['z'])
hx, hz, rc = (R['x'][1] - R['x'][0]) / 2, (R['z'][1] - R['z'][0]) / 2, R['corner']
qx, qz = np.abs(X - cx) - (hx - rc), np.abs(Z - cz) - (hz - rc)
plan = np.hypot(np.maximum(qx, 0), np.maximum(qz, 0)) + np.minimum(np.maximum(qx, qz), 0) - rc   # <0 inside
# keep clear of the abduction axle / yoke root (axis X through GH), behind the shoulder
r_ax = np.hypot(Y - GH[1], Z - GH[2])
axle_clear = np.where(X < -95, R['axle_clear'] - r_ax, -10.)
field = np.maximum.reduce([R['pad'] - d, d - (R['pad'] + R['t']), plan, R['y_min'] - Y, Y - R['y_max'], axle_clear])      # <0 = solid
field = np.pad(field, 2, constant_values=10.)
v, f, _, _ = measure.marching_cubes(-field, 0.0, spacing=(R['vox'],) * 3)
m = trimesh.Trimesh(v + lo + R['vox'] / 2 - 2 * R['vox'], f)
m.merge_vertices(); m.fix_normals()
m = max(m.split(only_watertight=False), key=lambda p: len(p.faces))
trimesh.smoothing.filter_taubin(m, iterations=8)
if m.volume < 0: m.invert()
print('shell: %d faces, watertight %s, volume %.0f cm3' % (len(m.faces), m.is_watertight, m.volume / 1e3))


def local(p):
    """point on the shell mid-surface nearest p, and its outward normal"""
    c, _, tri = trimesh.proximity.closest_point(m, [p])
    return c[0], m.face_normals[tri[0]]


def cutter_hole(p, d_, L=30.):
    c, nrm = local(p)
    return trimesh.creation.cylinder(d_ / 2, L, sections=32,
                                     transform=trimesh.geometry.align_vectors([0, 0, 1], nrm) @ np.eye(4)) \
        .apply_translation(c)


def cutter_slot(p, along, w, h, L=30.):
    c, nrm = local(p)
    a = along - nrm * (along @ nrm); a /= np.linalg.norm(a); b = np.cross(nrm, a)
    T = np.eye(4); T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = b, a, nrm, c
    return trimesh.creation.box((w, h, L), transform=T)


V = m.vertices
rear = V[V[:, 0] < V[:, 0].min() + 25]
hole_pts = [local(rear[np.argmin(np.abs(rear[:, 2] - z))]) for z in (MID_Z + 70, MID_Z + 120)]
holes = [cutter_hole(rear[np.argmin(np.abs(rear[:, 2] - z))], R['hole']) for z in (MID_Z + 70, MID_Z + 120)]
blat = V[np.argmin(V[:, 0] - 0.8 * V[:, 2])] + np.array([15, -5, -15])
hole_pts.append(local(blat))
holes.append(cutter_hole(blat, R['hole']))
front = V[np.argmax(V[:, 0] - 0.4 * V[:, 1])] + np.array([-14, 4, 0])
slot = cutter_slot(front, np.array([0, 0, 1.]), R['slot'][0], R['slot'][1])
part = m.difference(trimesh.util.concatenate(holes + [slot]), engine='manifold')
print('rest: %d faces, watertight %s, %.0f g PETG (100%% infill est.)' % (len(part.faces), part.is_watertight,
                                                                         part.volume / 1e3 * 1.27))
part.export(PR / 'R_shoulder_rest_world.stl')
# print orientation: skin side down is concave; print outer (convex) side down on supports? no:
# lay it on its outer face -> the skin face stays smooth.  Stable pose = trimesh's lowest-CoM pose.
T = part.compute_stable_poses(n_samples=4)[0][0]
flat = part.copy().apply_transform(T)
flat.apply_translation(-flat.bounds[0])
flat.export(PR / 'R_shoulder_rest.stl')
print('print bbox mm', np.round(flat.extents, 1))
json.dump(dict(params=R, bbox=flat.extents.tolist(), print_transform=T.tolist(),
               holes=[dict(p=c.tolist(), n=nn.tolist()) for c, nn in hole_pts],
               slot=dict(p=local(front)[0].tolist(), n=local(front)[1].tolist())),
          open(PR / 'R_shoulder_rest.json', 'w'), indent=1)
