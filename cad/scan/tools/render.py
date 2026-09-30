"""Render meshes (mm, X fwd, Y up, Z right) with flat shading; all faces depth-sorted together.
python render.py out.png mesh1.stl[|color] mesh2.stl[|color] ..."""
import sys
import numpy as np
import trimesh
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.colors import to_rgb

VIEWS = [(5, 0, 'front'), (5, -90, 'right side'), (5, 180, 'back'), (20, -45, 'front-right'),
         (20, -135, 'back-right'), (80, 0, 'top')]


def render(out, items, views=VIEWS, max_faces=40000, crop=None, dpi=90, size=4):
    tris, cols, nrm = [], [], []
    for m, col in items:
        if isinstance(m, str):
            m = trimesh.load(m, force='mesh')
        if crop is not None:
            keep = np.all((m.triangles_center >= crop[0]) & (m.triangles_center <= crop[1]), 1)
            if not keep.any(): continue
            m = m.submesh([np.where(keep)[0]], append=True)
        if len(m.faces) > max_faces:
            m = m.simplify_quadric_decimation(face_count=max_faces)
        tris.append(m.triangles); nrm.append(m.face_normals)
        cols.append(np.tile(to_rgb(col), (len(m.faces), 1)))
    T = np.vstack(tris)[:, :, [0, 2, 1]] * [1, -1, 1]; N = np.vstack(nrm)[:, [0, 2, 1]] * [1, -1, 1]; Cc = np.vstack(cols)
    lo = T.reshape(-1, 3).min(0); hi = T.reshape(-1, 3).max(0)
    light = np.array([0.5, 0.4, -0.6]); light /= np.linalg.norm(light)
    fig = plt.figure(figsize=(size * len(views), size * 2))
    for k, (el, az, t) in enumerate(views):
        ax = fig.add_subplot(1, len(views), k + 1, projection='3d')
        sh = 0.35 + 0.65 * np.abs(N @ light)
        ax.add_collection3d(Poly3DCollection(T, facecolors=np.clip(Cc * sh[:, None], 0, 1), linewidths=0))
        ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
        ax.set_box_aspect(hi - lo); ax.view_init(el, az); ax.set_title(t); ax.axis('off')
    plt.tight_layout(); plt.savefig(out, dpi=dpi); plt.close(fig)


if __name__ == '__main__':
    items = []
    for a in sys.argv[2:]:
        p, _, c = a.partition('|')
        items.append((p, c or '#c9b8a8'))
    render(sys.argv[1], items)
