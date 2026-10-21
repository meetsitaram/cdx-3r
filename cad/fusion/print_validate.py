"""Printability checks on exported STLs (offline, numpy). Run by orient_stls.py after every export, and by the
pre-commit hook through it. Usage: python cad/fusion/print_validate.py prints/<set> [file.stl ...]

Checks per part:
  - one solid (a second shell is a loose sliver or a failed cut);
  - wall thickness: rays from sampled surface points straight inward; the distance to the opposite wall is the local
    thickness. Spots thinner than MIN_WALL (3 lines of a 0.4 mm nozzle) are flagged with their position, grouped.
Exit code 1 if any part fails, so the hook stops the commit.
"""
import os
import sys

import numpy as np

MIN_WALL = 1.2          # mm, measured sideways (3 lines of a 0.4 mm nozzle). 0.8 let a 0.8 mm skin over a slot end
MIN_FLOOR = 0.8         # mm, measured vertically in the print orientation (4 layers of 0.2 mm)    through (collar, 21 Oct)
SKIN_DEG = 20.0         # opposite faces within this angle of parallel: a skin (fails when thin); wider: an edge (ok)
THIN_STRIP = 2.0        # mm: parallel-faced thin points strung out longer than this are a thin wall (0.3 mm between
                        # two holes in the gripper base, 21 Oct), not a knife edge
FILM_SPREAD = 0.6       # mm: thin points spread this wide in two directions are a skin/plate, not a knife edge
SAMPLES = 30000          # dense enough that a 3 x 4 mm skin gets several hits


def load(p):
    import struct
    d = open(p, 'rb').read()
    n = struct.unpack('<I', d[80:84])[0]
    a = np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
    return a['v'].reshape(-1, 3, 3).astype(float)


def shells(t):
    """Number of connected shells (triangles sharing vertices)."""
    v = np.round(t.reshape(-1, 3), 3)
    _, inv = np.unique(v, axis=0, return_inverse=True)
    inv = inv.reshape(-1, 3)
    parent = np.arange(inv.max() + 1)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b, c in inv:
        ra, rb, rc = find(a), find(b), find(c)
        parent[rb] = ra
        parent[rc] = ra
    return len({find(x) for x in np.unique(inv)})


def first_hit(orig, dirs, tris, want_index=False):
    """Distance along each ray (origin, direction) to the nearest triangle, inf if none (Moller-Trumbore); with
    want_index also the index of the triangle hit (-1 if none)."""
    e1, e2, v0 = tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0], tris[:, 0]
    out = np.full(len(orig), np.inf)
    idx = np.full(len(orig), -1)
    for i0 in range(0, len(orig), 48):
        o, d = orig[i0:i0 + 48][:, None, :], dirs[i0:i0 + 48][:, None, :]
        p = np.cross(d, e2[None])
        det = np.einsum('ij,mij->mi', e1, p)
        ok = np.abs(det) > 1e-12
        det = np.where(ok, det, 1.0)
        s = o - v0[None]
        u = np.einsum('mij,mij->mi', s, p) / det
        q = np.cross(s, e1[None])
        w = np.einsum('mij,mij->mi', d, q) / det
        t = np.einsum('ij,mij->mi', e2, q) / det
        hit = ok & (u >= 0) & (w >= 0) & (u + w <= 1) & (t > 1e-3)
        tt = np.where(hit, t, np.inf)
        out[i0:i0 + 48] = tt.min(1)
        idx[i0:i0 + 48] = np.where(np.isfinite(tt.min(1)), tt.argmin(1), -1)
    return (out, idx) if want_index else out


def wall_check(t, rng):
    nr = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    ar = np.linalg.norm(nr, axis=1) / 2
    keep = ar > 1e-6
    t, nr, ar = t[keep], nr[keep] / (2 * ar[keep, None]), ar[keep]
    idx = rng.choice(len(t), min(SAMPLES, len(t)), replace=False, p=ar / ar.sum())
    # random point inside each sampled triangle, nudged just inside the surface
    r1, r2 = rng.random(len(idx)), rng.random(len(idx))
    flip = r1 + r2 > 1
    r1[flip], r2[flip] = 1 - r1[flip], 1 - r2[flip]
    tri = t[idx]
    pts = tri[:, 0] + r1[:, None] * (tri[:, 1] - tri[:, 0]) + r2[:, None] * (tri[:, 2] - tri[:, 0])
    d = -nr[idx]
    th, hit = first_hit(pts + d * 0.01, d, t, want_index=True)
    th = th + 0.01
    # the opposite wall's slope tells a skin from an edge: a skin's two faces are (nearly) parallel; near an edge or a
    # bevel the faces meet at an angle and the thin band is just the last bit of a wedge, which prints fine
    nh = np.where(hit[:, None] >= 0, nr[np.maximum(hit, 0)], 0.0)
    parallel = np.abs(np.einsum('ij,ij->i', nh, d)) > np.cos(np.radians(SKIN_DEG))
    vertical = np.abs(d[:, 2]) > 0.7                       # STLs are in print orientation: z is up
    thin = (th < np.where(vertical, MIN_FLOOR, MIN_WALL)) & parallel
    groups = []
    for pnt, val in sorted(zip(pts[thin], th[thin]), key=lambda x: x[1]):
        for g in groups:
            if np.linalg.norm(g['at'] - pnt) < 5:
                g['n'] += 1
                g['pts'].append(pnt)
                break
        else:
            groups.append(dict(at=pnt, min=val, n=1, pts=[pnt]))
    # a FILM is thin over an area (thin points spread in two directions): it prints as nothing or as a loose skin.
    # Thin points along a line are a knife edge or an acute corner tip: the slicer just drops the last fraction of a
    # millimetre there, harmless.
    for g in groups:
        q = np.array(g['pts'])
        ev = np.sort(np.linalg.eigvalsh(np.cov((q - q.mean(0)).T))) if len(q) >= 3 else np.zeros(3)
        g['spread'] = float(np.sqrt(max(ev[1], 0.0)))
        g['length'] = float(np.sqrt(max(ev[2], 0.0))) * 2
        g['film'] = g['spread'] > FILM_SPREAD or g['length'] > THIN_STRIP   # a skin, or a thin wall along a line
    return groups, float(np.percentile(th[np.isfinite(th)], 5)), pts[thin], th[thin]


THIN = {}


def validate(paths):
    import orient_stls
    bad = 0
    for p in paths:
        rng = np.random.default_rng(sum(map(ord, os.path.basename(p))))      # repeatable per file
        t = load(p)
        sh = shells(t)
        groups, p5, tp, tv = wall_check(t, rng)
        THIN[os.path.basename(p)] = (tp, tv)
        groups = [g for g in groups if g['n'] >= 3]             # 1-2 rays grazing an edge are noise
        films = [g for g in groups if g['film']]
        _, tilt = orient_stls.level(t)                         # the bed face must lie dead flat, or the slicer
        ok = sh == 1 and not films and tilt < 0.01              # sees an edge on the bed (rest blades, 18 Oct)
        bad += not ok
        msg = '%-32s %s  shells %d  5th-pct wall %.1f mm' % (os.path.basename(p), 'OK  ' if ok else 'FAIL', sh, p5)
        if films:
            msg += '  FILM: ' + '; '.join('%.2f mm at (%.0f, %.0f, %.0f) over %.1f mm' % (g['min'], *g['at'], g['spread']) for g in films[:4])
        if tilt >= 0.01:
            msg += '  BED FACE TILTED %.3f deg (run orient_stls.py on the folder)' % tilt
        edges = [g for g in groups if not g['film']]
        if edges:
            msg += '  (edges/tips, ok: %d)' % len(edges)
        print(msg)
    return bad


if __name__ == '__main__':
    folder = sys.argv[1]
    files = sys.argv[2:] or sorted(f for f in os.listdir(folder) if f.endswith('.stl'))
    sys.exit(1 if validate([os.path.join(folder, f) for f in files]) else 0)
