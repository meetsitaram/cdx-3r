"""Offline layout search for the v3 girdle SCARA (plain Python + numpy, no Fusion).

Plan view (x fwd, z right) with the parts as circles/capsules and their height bands; every candidate layout is
posed through shrug, reach, squeeze and combinations, and scored by its smallest clearance to the fixed lift base on
the mast, to the lift links (which move relative to the carriage), between its own non-adjacent parts, and by how far
each SCARA stays from full stretch / full fold. Run: python girdle_layout.py
"""
import itertools
import math

import numpy as np

XL = -210.84
MAST = (XL, 30.0)
BASE_RECT = (XL - 20.5, XL + 20.5, 14.0, 112.0)          # shoulder tower (lift fork + mast clamp)
DIAG_RECT = (XL - 11.0, XL + 11.0, -10.0, 62.0)          # diagonal strut, LEFT mid node (z -110) -> tower (z ~50)            # lift fork cheeks in plan (x0, x1, z0, z1)
LIFT_X = (XL - 13.0, XL + 13.0)
EA0 = np.array([-180.5, 153.0])                           # end-plate pivot over the housing at rest
E = 42.0
R_T, R_F = 17.0, 28.0
KEEPER = 'belt'                                           # 'bars' (parallelogram) or 'belt' (no second bar)
POSES = [(0, 0, 0), (0, 60, 0), (0, -20, 0), (40, 0, 25), (-40, 0, -25), (40, 50, 25), (-40, 50, -25), (40, -20, 25),
         (-40, -20, -25), (20, 30, 12), (-20, 30, -12), (40, 0, 0), (-40, 0, 0), (0, 0, 25), (0, 0, -25)]
LIFT = dict(L=100.0, tilt=math.radians(15.0), zc=95.0 + 100.0 * math.cos(math.radians(15.0)))  # links slope down 15 deg at rest: shrug passes level


def lift(dy):
    """Carriage plan drift (z) and link angle for a vertical carriage move dy."""
    L, t0 = LIFT['L'], LIFT['tilt']
    th = math.asin(max(-0.99, min(0.99, math.sin(-t0) + dy / L)))
    dz = L * (math.cos(th) - math.cos(t0))
    return dz, th


def ik(S, Et, L, br):
    d = Et - S
    dd = float(np.hypot(*d))
    if dd > 2 * L - 8 or dd < 42:
        return None, dd
    a0, c = math.atan2(d[1], d[0]), math.acos(dd / (2 * L))
    a = a0 + br * c
    return S + L * np.array([math.cos(a), math.sin(a)]), dd


def seg_pt(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, float(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-9))))
    return float(np.hypot(*(p - (a + t * ab))))


def seg_seg(a, b, c, d):
    return min(seg_pt(a, c, d), seg_pt(b, c, d), seg_pt(c, a, b), seg_pt(d, a, b))


def rect_pt(p, r):
    dx = max(r[0] - p[0], 0, p[0] - r[1])
    dz = max(r[2] - p[1], 0, p[1] - r[3])
    return math.hypot(dx, dz)


def rect_seg(a, b, r, n=12):
    return min(rect_pt(a + (b - a) * k / n, r) for k in range(n + 1))


def score(S0a, L, u1s, u2s, br, E=E):
    S0a = np.array(S0a)
    rest_C, _ = ik(S0a, EA0, L, br)
    if rest_C is None:
        return None
    l1 = rest_C - S0a; l2 = EA0 - rest_C
    u1 = u1s * np.array([-l1[1], l1[0]]) / np.hypot(*l1)
    u2 = u2s * np.array([-l2[1], l2[0]]) / np.hypot(*l2)
    worst, why = 1e9, ''
    folds = []
    for dx, dy, dz in POSES:
        cz, th = lift(dy)
        S = S0a + np.array([0.0, cz]); Sb = S + E * u1
        Et = EA0 + np.array([dx, dz]); Eb = Et + E * u2
        C, dd = ik(S, Et, L, br)
        if C is None:
            return None
        folds.append(dd)
        Cb, Cb2 = C + E * u1, C + E * u2
        # parallelogram must not go flat: links stay > 25 deg from their offset direction
        for a, b, u in (((S, C, u1), (Et, C, u2)) if KEEPER == 'bars' else ()):
            v = (b - a) / np.hypot(*(b - a))
            if abs(float(np.dot(v, u))) > math.cos(math.radians(20)):
                return None
        upper = [('root', S, Sb, R_F), ('l1a', S, C, R_T), ('l1b', Sb, Cb, R_T), ('elbowU', C, Cb, R_F)]
        lower = [('elbowL', C, Cb2, R_F), ('l2a', C, Et, R_T), ('l2b', Cb2, Eb, R_T), ('end', Et, Eb, R_F)]
        if KEEPER == 'belt':                               # one bar per link; pulley discs at each pivot
            upper = [('root', S, S, 24.0), ('l1a', S, C, R_T), ('elbowU', C, C, 24.0)]
            lower = [('elbowL', C, C, 24.0), ('l2a', C, Et, R_T), ('end', Et, Et, 24.0)]
        # fixed base (mast clamp + lift cheeks): its bottom is ~1470; the SCARA's upper band reaches 1456 + dy
        reach_base = True                                    # the tower reaches down to ~1440 now
        for n, a, b, r in upper + (lower if dy > 55 else []):
            if reach_base:
                c1 = rect_seg(a, b, BASE_RECT) - r
                c2 = min(seg_pt(np.array(MAST), a, b) - r - 16.0, 1e9)
                if min(c1, c2) < worst:
                    worst, why = min(c1, c2), 'base vs %s @%s' % (n, (dx, dy, dz))
        for n, a, b, r in upper + lower:                     # diagonal strut (fixed) at every height
            c = rect_seg(a, b, DIAG_RECT) - r - 3
            if c < worst:
                worst, why = c, 'diagonal strut vs %s @%s' % (n, (dx, dy, dz))
        # lift links pass over the upper band near the base end when the carriage is up: keep the upper band's
        # plan footprint out of the lift links' x-strip for z below ~zc - 50
        if dy > 0:
            strip = (LIFT_X[0] - 3, LIFT_X[1] + 3, 0.0, LIFT['zc'] - 40)
            for n, a, b, r in upper:
                c = rect_seg(a, b, strip) - r
                if c < worst:
                    worst, why = c, 'lift link vs %s @%s' % (n, (dx, dy, dz))
        # own parts on the same band, not sharing a pivot
        for grp in (upper, lower):
            for (n1, a1, b1, r1), (n2, a2, b2, r2) in itertools.combinations(grp, 2):
                shared = any(np.allclose(p, q) for p in (a1, b1) for q in (a2, b2))
                if shared:
                    continue
                c = seg_seg(a1, b1, a2, b2) - r1 - r2
                if c < worst:
                    worst, why = c, '%s vs %s @%s' % (n1, n2, (dx, dy, dz))
        # size limits: not wider than the arm's outer line (z ~250, moving out with the shoulder), not more than
        # ~70 mm behind the frame plane
        for n, a, b, r in upper + lower:
            if max(a[1], b[1]) + r > 250 + max(dz, 0) or min(a[0], b[0]) - r < XL - 70:
                return None
        # stay behind the back: nothing forward of x = -112 (skin ~-75 at these heights)
        for n, a, b, r in upper + lower:
            c = -112 + max(dx, 0) - (max(a[0], b[0]) + r)       # the back moves forward with a reach
            if c < worst:
                worst, why = c, 'too far forward: %s @%s' % (n, (dx, dy, dz))
    margin = min(min(folds) - 42, 2 * L - 8 - max(folds))
    bulk = -min(S0a[0] - R_F, -260)                         # behind the frame plane costs a little
    return worst, margin, why, bulk


def search():
    best = []
    for x in range(-300, -120, 10):
        for z in range(90, 210, 10):
            for L, Ee in itertools.product((65.0, 75.0, 85.0), (60.0,) if KEEPER == 'belt' else (60.0, 70.0, 80.0)):
                for u1s, u2s, br in itertools.product((1, -1), (1, -1) if KEEPER == 'bars' else (1,), (1, -1)):
                    r = score((x, z), L, u1s, u2s, br, Ee)
                    if r is None:
                        continue
                    worst, margin, why, bulk = r
                    best.append((min(worst, margin / 2), worst, margin, (x, z), L, Ee, u1s, u2s, br, why))
    ok = [b for b in best if b[0] >= 5.0]
    ok.sort(key=lambda t: (-(t[3][0] - 17 - 28), -t[0]))   # most compact first (root nearest the frame plane)
    best.sort(key=lambda t: -t[0])
    return ok[:8] if ok else best[:8]


if __name__ == '__main__':
    import sys
    KEEPER = sys.argv[1] if len(sys.argv) > 1 else 'bars'
    for row in search():
        print(['%.1f' % row[0], 'clear %.1f' % row[1], 'fold margin %.1f' % row[2]] + list(row[3:]))
