"""exoarm2 splat -> clean body point cloud + watertight-ish body mesh, in the
CDX-3R world frame (mm, X forward, Y up, Z outboard/right).

Stage 1 (this file): decode SPZ v3, crop the person, drop floor/outliers,
level + yaw-align, write body_pts.ply and body_floor.json (transform), plus
check renders.  Mesh + landmarks: mesh.py.
"""
import gzip, json, sys
from pathlib import Path
import numpy as np
import open3d as o3d
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / 'out'; OUT.mkdir(exist_ok=True)


def read_spz(path):
    raw = gzip.decompress(Path(path).read_bytes())
    magic, ver, n = np.frombuffer(raw[:12], '<u4')
    sh_deg, fb = raw[12], raw[13]
    assert magic == 0x5053474E and ver in (2, 3), (hex(magic), ver)
    o = 16
    p = np.frombuffer(raw[o:o + 9 * n], np.uint8).reshape(n, 3, 3).astype(np.int32); o += 9 * n
    v = p[..., 0] | (p[..., 1] << 8) | (p[..., 2] << 16)
    v = np.where(v & 0x800000, v - (1 << 24), v)
    xyz = v / float(1 << fb)
    a = np.frombuffer(raw[o:o + n], np.uint8) / 255.; o += n
    c = np.frombuffer(raw[o:o + 3 * n], np.uint8).reshape(n, 3) / 255.; o += 3 * n
    rgb = np.clip(0.5 + 0.282095 * (c - 0.5) / 0.15, 0, 1)
    s = np.exp(np.frombuffer(raw[o:o + 3 * n], np.uint8).reshape(n, 3) / 16. - 10.)
    return xyz, rgb, a, s


def main(spz):
    xyz, rgb, a, s = read_spz(spz)
    print(len(xyz), 'splats')
    # scan frame: y up, person faces -z, person's right = +x (checked on renders)
    floor_sel = (np.abs(xyz[:, 0] + 0.4) < 1.2) & (np.abs(xyz[:, 2] + 1.05) < 1.2) & (xyz[:, 1] < -1.2)
    floor_y = np.percentile(xyz[floor_sel, 1], 60)   # dense floor layer
    box = (xyz[:, 0] > -0.82) & (xyz[:, 0] < -0.06) & (xyz[:, 2] > -1.36) & (xyz[:, 2] < -0.76) \
        & (xyz[:, 1] > floor_y + 0.012) & (xyz[:, 1] < 0.45)
    keep = box & (a > 0.5) & (s.max(1) < 0.04)       # opaque, small splats = surface
    P, C = xyz[keep], rgb[keep]
    print('floor y %.4f, %d body candidates' % (floor_y, len(P)))

    pc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(P))
    pc.colors = o3d.utility.Vector3dVector(C)
    pc, _ = pc.remove_statistical_outlier(20, 2.0)
    lab = np.array(pc.cluster_dbscan(eps=0.02, min_points=8))
    big = np.argmax(np.bincount(lab[lab >= 0]))
    pc = pc.select_by_index(np.where(lab == big)[0])
    P = np.asarray(pc.points); C = np.asarray(pc.colors)
    print('%d points after outlier + cluster' % len(P))

    # to world: X forward (-z scan), Y up, Z right (+x scan), metres for now
    W = np.c_[-P[:, 2], P[:, 1] - floor_y, P[:, 0]]
    # yaw: chest slice (1.15..1.35 m) principal axis = left-right
    h = W[:, 1]
    ch = W[(h > 1.15) & (h < 1.35)][:, [0, 2]]
    ch0 = ch.mean(0)
    ev, evec = np.linalg.eigh(np.cov((ch - ch0).T))
    lr = evec[:, np.argmax(ev)]                       # (x, z) of shoulder line
    if lr[1] < 0: lr = -lr                            # point it to the right (+Z)
    yaw = np.arctan2(lr[0], lr[1])                    # rotate so lr -> +Z
    cy, sy = np.cos(yaw), np.sin(yaw)
    R = np.array([[cy, 0, -sy], [0, 1, 0], [sy, 0, cy]])
    W = W @ R.T
    # origin: floor under chest-slice centre
    ctr = np.r_[(W[(h > 1.15) & (h < 1.35)][:, [0, 2]]).mean(0)]
    W[:, 0] -= ctr[0]; W[:, 2] -= ctr[1]
    W *= 1000.
    print('yaw correction %.1f deg' % np.degrees(yaw))
    print('extent mm  X %.0f..%.0f  Y %.0f..%.0f  Z %.0f..%.0f' % (
        W[:, 0].min(), W[:, 0].max(), W[:, 1].min(), W[:, 1].max(), W[:, 2].min(), W[:, 2].max()))

    out = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(W))
    out.colors = o3d.utility.Vector3dVector(C)
    o3d.io.write_point_cloud(str(OUT / 'body_pts.ply'), out)
    json.dump({'floor_y_scan': float(floor_y), 'yaw_rad': float(yaw), 'centre_after_yaw_m': ctr.tolist(),
               'map': 'world=[-z, y-floor, x] (m), rotate yaw about Y, subtract centre, *1000 -> mm'},
              open(OUT / 'body_frame.json', 'w'), indent=1)

    fig, ax = plt.subplots(1, 3, figsize=(15, 9))
    for k, (u, v, t) in enumerate([(2, 1, 'front (from +X): Z right'), (0, 1, 'side (from +Z): X fwd'),
                                   (2, 0, 'top: Z right, X fwd')]):
        o = np.argsort(W[:, [0, 2, 1][k]] * (1 if k < 2 else 1))
        ax[k].scatter(W[o, u], W[o, v], c=C[o], s=1)
        ax[k].set_aspect('equal'); ax[k].set_title(t); ax[k].grid(alpha=.3)
    plt.tight_layout(); plt.savefig(OUT / 'body_pts.png', dpi=80)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\PC\Downloads\exoarm2.spz')
