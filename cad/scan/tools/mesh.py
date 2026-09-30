"""body_pts.ply (mm, CDX-3R world) -> Poisson body mesh + landmark measurements."""
from pathlib import Path
import json
import numpy as np
import open3d as o3d
import trimesh
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent.parent / 'out'

pc = o3d.io.read_point_cloud(str(OUT / 'body_pts.ply'))
P = np.asarray(pc.points)
pc.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=25, max_nn=40))
N = np.asarray(pc.normals)
# outward = away from the nearest "bone" line: torso axis (vertical through slice
# centroid) or, for arm points, the arm's own slice centroid.
out = np.zeros_like(P)
for y0 in np.arange(P[:, 1].min(), P[:, 1].max() + 20, 20):
    m = (P[:, 1] >= y0) & (P[:, 1] < y0 + 20)
    if not m.any(): continue
    Q = P[m][:, [0, 2]]
    # split slice into blobs by Z gaps (arms vs torso) at ~15 mm
    order = np.argsort(Q[:, 1]); z = Q[order, 1]
    cuts = np.where(np.diff(z) > 15)[0]
    idx = np.where(m)[0][order]
    for seg in np.split(np.arange(len(z)), cuts + 1):
        c = Q[order][seg].mean(0)
        d = P[idx[seg]][:, [0, 2]] - c
        out[idx[seg], 0] = d[:, 0]; out[idx[seg], 2] = d[:, 1]
flip = (N * out).sum(1) < 0
N[flip] *= -1
pc.normals = o3d.utility.Vector3dVector(N)

mesh, dens = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pc, depth=9, scale=1.1)
dens = np.asarray(dens)
mesh.remove_vertices_by_mask(dens < np.quantile(dens, 0.06))
# keep only surface near real points
V = np.asarray(mesh.vertices)
tree = o3d.geometry.KDTreeFlann(pc)
far = np.array([np.sqrt(tree.search_knn_vector_3d(v, 1)[2][0]) > 18 for v in V])
mesh.remove_vertices_by_mask(far)
mesh = mesh.filter_smooth_taubin(10)
mesh.remove_degenerate_triangles(); mesh.remove_unreferenced_vertices()
tm = trimesh.Trimesh(np.asarray(mesh.vertices), np.asarray(mesh.triangles))
parts = tm.split(only_watertight=False)
tm = max(parts, key=lambda p: len(p.faces))
print('poisson mesh %d faces, watertight=%s' % (len(tm.faces), tm.is_watertight))
tm.export(OUT / 'body_full.ply')
light = tm.simplify_quadric_decimation(face_count=30000)
light.export(OUT / 'body_30k.stl'); light.export(OUT / 'body_30k.obj')
print('decimated %d faces' % len(light.faces))

fig = plt.figure(figsize=(16, 8))
for k, (el, az, t) in enumerate([(0, 0, 'front'), (0, 90, 'right side'), (0, 180, 'back'), (25, 45, 'iso')]):
    ax = fig.add_subplot(1, 4, k + 1, projection='3d')
    v = light.vertices
    ax.plot_trisurf(v[:, 0], v[:, 2], v[:, 1], triangles=light.faces, color='#c9b8a8', lw=0, shade=True)
    ax.view_init(el, az); ax.set_box_aspect(np.ptp(v[:, [0, 2, 1]], 0)); ax.set_title(t); ax.axis('off')
plt.tight_layout(); plt.savefig(OUT / 'body_mesh.png', dpi=80)
