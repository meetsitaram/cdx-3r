"""Rotate every STL in a print folder into its best print orientation (offline, numpy only). Standard last step of
every print export (docs/PIPELINE-PLAYBOOK.md 5.4): run it on the freshly exported folder, check the table, ship.

Candidates: every large flat face that can sit on the bed (all of the part is on one side of its plane). For each,
score = support area that would land ON the part (a ray straight down from an overhanging face hits the part: those
supports end up inside holes and pockets) x 5 + total overhang area (faces more than 60 deg past vertical) - base area.
The winner is rotated so that face is down, moved to z = 0 and centred, and written back (binary STL).
Run: python cad/fusion/orient_stls.py prints/shoulder-back-v3   (prints a table; --dry to only report)
Slicer: import, do NOT auto-orient; tree supports, on build plate only.
"""
import json
import os
import struct
import sys

import numpy as np


def load(p):
    d = open(p, 'rb').read()
    n = struct.unpack('<I', d[80:84])[0]
    a = np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
    return a['v'].reshape(-1, 3, 3).astype(float)


def save(p, t):
    nr = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    nr /= np.linalg.norm(nr, axis=1)[:, None] + 1e-12
    rec = np.zeros(len(t), dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
    rec['n'] = nr
    rec['v'] = t.reshape(-1, 9)
    with open(p, 'wb') as f:
        f.write(b'oriented for printing (cad/fusion/orient_stls.py)'.ljust(80, b' '))
        f.write(struct.pack('<I', len(t)))
        f.write(rec.tobytes())


def rot_to_z(u):
    """Rotation matrix taking unit vector u to +z."""
    z = np.array([0.0, 0.0, 1.0])
    v = np.cross(u, z)
    s, c = np.linalg.norm(v), float(u @ z)
    if s < 1e-9:
        return np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    k = v / s
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + s * K + (1 - c) * K @ K


def ray_hits(orig, tris):
    """For each origin, does a ray along -z hit any triangle? (Moller-Trumbore, chunked)."""
    d = np.array([0.0, 0.0, -1.0])
    e1, e2 = tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]
    p = np.cross(d, e2)
    det = np.einsum('ij,ij->i', e1, p)
    ok = np.abs(det) > 1e-9
    e1, e2, p, det, v0 = e1[ok], e2[ok], p[ok], det[ok], tris[ok, 0]
    out = np.zeros(len(orig), bool)
    for i0 in range(0, len(orig), 64):
        o = orig[i0:i0 + 64][:, None, :]
        s = o - v0[None]
        u = np.einsum('mij,ij->mi', s, p) / det
        q = np.cross(s, e1[None])
        v = np.einsum('k,mik->mi', d, q) / det
        t = np.einsum('ij,mij->mi', e2, q) / det
        out[i0:i0 + 64] = ((u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0.3)).any(1)
    return out


def evaluate(t, up, rng):
    c = t.mean(1)
    nr = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    ar = np.linalg.norm(nr, axis=1) / 2
    nr /= (2 * ar[:, None] + 1e-12)
    h = c @ up
    h0 = (t.reshape(-1, 3) @ up).min()
    base = ar[(h < h0 + 0.3) & (nr @ up < -0.99)].sum()
    om = (nr @ up < -0.866) & (h > h0 + 0.3)
    over = ar[om].sum()
    idx = np.nonzero(om)[0]
    if len(idx) > 400:
        idx = rng.choice(idx, 400, replace=False, p=ar[idx] / ar[idx].sum())
        w = over / len(idx)
        wts = np.full(len(idx), w)
    else:
        wts = ar[idx]
    on = 0.0
    if len(idx):
        R = rot_to_z(up)
        tr = t @ R.T
        hits = ray_hits(c[idx] @ R.T - np.array([0, 0, 0.5]), tr)
        on = float(wts[hits].sum())
    return base, over, on


def candidates(t):
    nr = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    ar = np.linalg.norm(nr, axis=1) / 2
    nr /= (2 * ar[:, None] + 1e-12)
    pts = t.reshape(-1, 3)
    groups = {}
    for n, nf, a, tri in zip(np.round(nr, 2), nr, ar, t):
        groups.setdefault(tuple(n), [0.0, [], np.zeros(3)])
        groups[tuple(n)][0] += a
        groups[tuple(n)][1].append(tri[0] @ n)
        groups[tuple(n)][2] += a * nf
    out = []
    for n, (a, offs, ns) in groups.items():
        n = ns / np.linalg.norm(ns)               # the true face normal: the rounded key tilts it up to ~0.3 deg
        if a < 150:
            continue
        top = (pts @ n).max()                     # the plane must be extremal: nothing sticks out past it
        if max(offs) > top - 0.3:
            out.append(-n)                        # this face down -> up = -n
    for ax in np.eye(3):
        out += [ax, -ax]
    uniq = []
    for u in out:
        if all(np.dot(u, v) < 0.999 for v in uniq):
            uniq.append(u)
    return uniq


def level(t):
    """Lay the bed face exactly flat: rotate the near-flat downward faces touching the bed (within 1 deg, 0.5 mm) so
    their true area-weighted normal is -z, then drop to z = 0. Returns (triangles, tilt fixed in deg)."""
    nr = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    ar = np.linalg.norm(nr, axis=1) / 2
    nr /= (2 * ar[:, None] + 1e-12)
    z0 = t[:, :, 2].min()
    sel = (nr[:, 2] < -0.9998) & (t[:, :, 2].max(1) < z0 + 0.5)
    if ar[sel].sum() < 1.0:
        return t, 0.0
    n = (nr[sel] * ar[sel][:, None]).sum(0)
    n /= np.linalg.norm(n)
    tilt = float(np.degrees(np.arccos(min(1.0, -n[2]))))
    if tilt < 1e-4:
        return t, 0.0
    tr = t @ rot_to_z(-n).T
    tr[:, :, 2] -= tr[:, :, 2].min()
    return tr, tilt


# the shoulder-rest pieces (27-30) are left to the search: it lays them flat (honeycomb holes vertical, pin holes
# horizontal). Stood on edge they have no flat face on the bed.
FIXED = {}
# Per-folder overrides: <folder>/orientation_up.json maps a file-name prefix (e.g. "07") to the up direction in the
# design frame (x forward, y up, z right). Parts not listed are searched. Review the printed table for every new
# part: a search pick that balances on a corner or is too tall is a reason to add an override.
UP = {}


def main(folder, dry=False):
    global UP
    rng = np.random.default_rng(1)
    up_file = os.path.join(folder, 'orientation_up.json')
    UP = json.load(open(up_file)) if os.path.exists(up_file) else {}
    rows = {}
    for f in sorted(os.listdir(folder)):
        if not f.endswith('.stl'):
            continue
        p = os.path.join(folder, f)
        if open(p, 'rb').read(80).startswith(b'oriented for printing'):
            t, tilt = level(load(p))                         # already oriented: only make the bed face dead flat
            if tilt and not dry:
                print('%-32s levelled: bed face was tilted %.3f deg' % (f, tilt))
                save(p, t)
            continue
        t = load(p)
        ev = []
        if f[:2] in UP:
            cands = [np.array(UP[f[:2]], float)]
        elif f[:2] in FIXED:
            cands = [np.array(FIXED[f[:2]]), -np.array(FIXED[f[:2]])]
        else:
            cands = candidates(t)
        for up in cands:
            b, o, on = evaluate(t, up, rng)
            ev.append((on * 5 + o - b, up, b, o, on))
        bmax = max(e[2] for e in ev)
        need = 0.0 if (f[:2] in FIXED or f[:2] in UP) else min(0.4 * bmax, 600.0)
        stable = [e for e in ev if e[2] >= need] or ev               # stand on a real flat face, never on a corner
        _, up, b, o, on = min(stable, key=lambda e: e[0])
        R = rot_to_z(up)
        tr = t @ R.T
        lo, hi = tr.reshape(-1, 3).min(0), tr.reshape(-1, 3).max(0)
        tr -= np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
        tr, _ = level(tr)
        rows[f] = dict(up=[round(x, 3) for x in up], base=round(b), overhang=round(o), on_part=round(on),
                       height=round(float(hi[2] - lo[2]), 1))
        print('%-32s base %6.0f  overhang %6.0f  on-part %5.0f  height %5.1f  up %s' % (f, b, o, on, hi[2] - lo[2], np.round(up, 2)))
        if not dry:
            save(p, tr)
    if not dry and rows:
        jf = os.path.join(folder, 'orientation.json')
        allrows = json.load(open(jf)) if os.path.exists(jf) else {}
        allrows = {k: v for k, v in allrows.items() if os.path.exists(os.path.join(folder, k))}
        allrows.update(rows)
        json.dump(dict(sorted(allrows.items())), open(jf, 'w'), indent=1)
    check_current(folder)
    import print_validate                                   # walls, one solid per part: the files just oriented
    return print_validate.validate([os.path.join(folder, f) for f in rows])


def check_current(folder):
    """Compare each STL's volume with model_volumes.json (written by export_prints.export): a mismatch means the
    model changed after that STL was exported."""
    vf = os.path.join(folder, 'model_volumes.json')
    if not os.path.exists(vf):
        print('no model_volumes.json: run export_prints.export() to record the model')
        return
    vols, stale = json.load(open(vf)), []
    for f, v in vols.items():
        p = os.path.join(folder, f + '.stl')
        if not os.path.exists(p):
            stale.append(f + ' (missing)')
            continue
        t = load(p)
        sv = abs(np.einsum('ij,ij->i', t[:, 0], np.cross(t[:, 1], t[:, 2])).sum() / 6)
        if abs(sv - v) > 0.01 * v:
            stale.append('%s (stl %.0f vs model %.0f mm3)' % (f, sv, v))
    print('STALE, re-export: ' + ', '.join(stale) if stale else 'all %d STLs match the model' % len(vols))


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(1 if main(sys.argv[1], '--dry' in sys.argv) else 0)
