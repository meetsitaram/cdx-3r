"""Compare the girdle placed ON TOP (v3b: tower above the top node, SCARA hanging above the housing) with UNDER
(lift on the backbone between the mid and top nodes, SCARA under the housing, housing resting on the SCARA end).

Same plan model as girdle_layout.py (belt-kept SCARA, single bars, pulley discs), plus a clearance check against the
scanned torso and arm surfaces at each part's own height band, for every pose. Run: python girdle_layout_under.py
"""
import itertools
import math

import numpy as np
import trimesh
from scipy.spatial import cKDTree

import girdle_layout as gl

SCAN = r'C:\Users\PC\projects\exoarm2-scan\out\layout'
TORSO = trimesh.load(SCAN + r'\body_torso_trim.stl').vertices
ARM = trimesh.load(SCAN + r'\body_arm_trim.stl').vertices
BODY = np.vstack([TORSO, ARM])
XL = gl.XL
EA0 = gl.EA0
R_T, R_P = 17.0, 24.0
POSES = gl.POSES

# height bands (scan y of the part's bottom..top at rest), per variant
TOP = dict(upper=(1420.0, 1470.0), lower=(1386.0, 1428.0))          # v3b: link 1 (+root plate) upper, link 2 lower
UNDER = dict(upper=(1276.0, 1320.0), lower=(1232.0, 1277.0))        # under: link 2 (+end plate) upper, link 1 lower


def body_clear(segs, band, dy, dx):
    """Smallest plan clearance from capsules (a, b, r) to body points inside the height band (moved by dy).
    The torso's back moves forward with a reach, so body points shift by max(dx, 0) * 0.8 in x."""
    lo, hi = band[0] + dy, band[1] + dy
    m = (BODY[:, 1] > lo) & (BODY[:, 1] < hi)
    if not m.any():
        return 1e9
    P = BODY[m][:, [0, 2]].copy()
    P[:, 0] += max(dx, 0) * 0.8
    tree = cKDTree(P)
    best = 1e9
    for a, b, r in segs:
        n = max(2, int(np.hypot(*(b - a)) / 5))
        for k in range(n + 1):
            q = a + (b - a) * k / n
            dd, _ = tree.query(q)
            best = min(best, dd - r)
    return best


def evaluate(variant, S0a, L, br):
    S0a = np.array(S0a)
    bands = TOP if variant == 'top' else UNDER
    rest_C, _ = gl.ik(S0a, EA0, L, br)
    if rest_C is None:
        return None
    worst, why, bodymin, folds = 1e9, '', 1e9, []
    for dx, dy, dz in POSES:
        cz, _ = gl.lift(dy)
        S = S0a + np.array([0.0, cz])
        Et = EA0 + np.array([dx, dz])
        C, dd = gl.ik(S, Et, L, br)
        if C is None:
            return None
        folds.append(dd)
        link1 = [('root', S, S, R_P), ('l1', S, C, R_T), ('elbow1', C, C, R_P)]
        link2 = [('elbow2', C, C, R_P), ('l2', C, Et, R_T), ('end', Et, Et, R_P)]
        up, lo = (link1, link2) if variant == 'top' else (link2, link1)
        # body (torso + arm) at each band's own height
        for grp, band in ((up, bands['upper']), (lo, bands['lower'])):
            c = body_clear([(a, b, r) for _, a, b, r in grp], band, dy, dx)
            bodymin = min(bodymin, c)
            if c < worst:
                worst, why = c, 'body vs %s band @%s' % ('upper' if grp is up else 'lower', (dx, dy, dz))
        # fixed frame parts
        # fixed frame parts with the heights they occupy: (plan rect, y0, y1, name)
        if variant == 'top':
            obst = [((XL - 20.5, XL + 20.5, 14.0, 95.0), 1440.0, 1600.0, 'tower web'),
                    ((XL - 20.5, XL + 20.5, 78.0, 112.0), 1509.0, 1588.0, 'tower lift cheeks'),
                    ((XL - 46.0, XL - 13.0, 18.0, 75.0), 1425.0, 1480.0, 'tower strut block'),
                    ((XL - 52.0, XL - 30.0, -110.0, 62.0), 1250.0, 1440.0, 'strut'),
                    ((XL - 18.0, XL + 18.0, -130.0, 50.0), 1385.0, 1425.0, 'top node')]
        else:
            obst = [((XL - 20.5, XL + 20.5, 14.0, 87.0), 1199.0, 1268.0, 'lift base on backbone'),
                    ((XL - 18.0, XL + 18.0, -130.0, 50.0), 1182.0, 1218.0, 'mid node'),
                    ((XL - 18.0, XL + 18.0, -130.0, 50.0), 1385.0, 1425.0, 'top node'),
                    ((XL - 11.0, XL + 11.0, 19.0, 41.0), 0.0, 9999.0, 'backbone pipe')]
        for rect, y0, y1, nm in obst:
            for grp, band in ((up, bands['upper']), (lo, bands['lower'])):
                if band[1] + dy < y0 or band[0] + dy > y1:
                    continue
                for n, a, b, r in grp:
                    c = gl.rect_seg(a, b, rect) - r - 3
                    if c < worst:
                        worst, why = c, '%s vs %s @%s' % (nm, n, (dx, dy, dz))
        # lift links move relative to the carriage near their fixed end
        strip = (XL - 16, XL + 16, 0.0, 130.0)
        risky = (variant == 'top' and dy > 0) or (variant == 'under' and dy < 0)
        if risky:
            near = up if variant == 'top' else lo
            for n, a, b, r in near:
                c = gl.rect_seg(a, b, strip) - r
                if c < worst:
                    worst, why = c, 'lift link vs %s @%s' % (n, (dx, dy, dz))
        for n1, a1, b1, r1 in up:                           # link 1 / link 2 cross only on different levels
            pass
        for n, a, b, r in up + lo:                          # size limits as before
            if max(a[1], b[1]) + r > 250 + max(dz, 0) or min(a[0], b[0]) - r < XL - 70:
                return None
    margin = min(min(folds) - 42, 2 * L - 8 - max(folds))
    return min(worst, margin / 2), worst, margin, bodymin, why


def search(variant):
    rows = []
    for x in range(-290, -120, 10):
        for z in range(90, 230, 10):
            for L in (65.0, 75.0, 85.0):
                for br in (1, -1):
                    r = evaluate(variant, (x, z), L, br)
                    if r:
                        rows.append((round(r[0], 1), round(r[1], 1), round(r[2], 1), round(r[3], 1), (x, z), L, br, r[4]))
    rows.sort(key=lambda t: -t[0])
    return rows[:5]


if __name__ == '__main__':
    print('v3b layout re-scored:', evaluate('top', (-240, 200), 65.0, 1))
    for v in ('top', 'under'):
        print('---', v, '(score, clearance, fold margin, body/arm clearance, S0, L, branch, limiting)')
        for row in search(v):
            print(row)
