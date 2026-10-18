"""Top vs under girdle with the shoulder blade following the shoulder (offline, numpy).

The scan torso is static, so girdle_layout_under.py only moved the back forward on a reach. Here every torso point
near the shoulder moves with the shoulder by a weight that fades out toward the spine (z 40 -> 150 mm) and down the
back (y 1150 -> 1260 mm); arm points move fully. A shrug lifts the blade, a squeeze pulls it back and in.
Run: python girdle_follow.py  (prints the best layouts per placement; --anim seq.json out.json writes page data)
"""
import json
import sys

import numpy as np
from scipy.spatial import cKDTree

import girdle_layout as gl
import girdle_layout_under as gu

TORSO, ARM = gu.TORSO, gu.ARM
R_T, R_P = gu.R_T, gu.R_P


def _ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


W_T = _ss(TORSO[:, 2], 40.0, 150.0) * _ss(TORSO[:, 1], 1150.0, 1260.0)


def body_at(d):
    d = np.asarray(d, float)
    return np.vstack([TORSO + W_T[:, None] * d, ARM + d])


def parts(variant, S0a, L, br, d):
    dx, dy, dz = d
    cz, _ = gl.lift(dy)
    S = np.array(S0a, float) + np.array([0.0, cz])
    Et = gl.EA0 + np.array([dx, dz])
    C, dd = gl.ik(S, Et, L, br)
    if C is None:
        return None
    link1 = [('root', S, S, R_P), ('link 1', S, C, R_T), ('elbow', C, C, R_P)]
    link2 = [('elbow', C, C, R_P), ('link 2', C, Et, R_T), ('end plate', Et, Et, R_P)]
    up, lo = (link1, link2) if variant == 'top' else (link2, link1)
    return dict(S=S, C=C, E=Et, dd=dd, up=up, lo=lo)


def obstacles(variant):
    XL = gl.XL
    if variant == 'top':
        return [((XL - 20.5, XL + 20.5, 14.0, 95.0), 1440.0, 1600.0, 'tower web'),
                ((XL - 20.5, XL + 20.5, 78.0, 112.0), 1509.0, 1588.0, 'lift cheeks'),
                ((XL - 46.0, XL - 13.0, 18.0, 75.0), 1425.0, 1480.0, 'strut block'),
                ((XL - 52.0, XL - 30.0, -110.0, 62.0), 1250.0, 1440.0, 'strut'),
                ((XL - 18.0, XL + 18.0, -130.0, 50.0), 1385.0, 1425.0, 'top node')]
    return [((XL - 20.5, XL + 20.5, 14.0, 87.0), 1199.0, 1268.0, 'lift base'),
            ((XL - 18.0, XL + 18.0, -130.0, 50.0), 1182.0, 1218.0, 'mid node'),
            ((XL - 18.0, XL + 18.0, -130.0, 50.0), 1385.0, 1425.0, 'top node'),
            ((XL - 11.0, XL + 11.0, 19.0, 41.0), 0.0, 9999.0, 'backbone')]


def gaps(variant, S0a, L, br, d, body=None):
    """(body gap, why, parts gap, why, parts) for one pose; None if the SCARA cannot reach."""
    p = parts(variant, S0a, L, br, d)
    if p is None:
        return None
    dx, dy, dz = d
    bands = gu.TOP if variant == 'top' else gu.UNDER
    B = body_at(d) if body is None else body
    bgap, bwhy = 1e9, ''
    for grp, band in ((p['up'], bands['upper']), (p['lo'], bands['lower'])):
        lo, hi = band[0] + dy, band[1] + dy
        m = (B[:, 1] > lo) & (B[:, 1] < hi)
        if not m.any():
            continue
        tree = cKDTree(B[m][:, [0, 2]])
        for n, a, b, r in grp:
            k = max(2, int(np.hypot(*(b - a)) / 5))
            for t in range(k + 1):
                q = a + (b - a) * t / k
                g = tree.query(q)[0] - r
                if g < bgap:
                    bgap, bwhy = g, 'body vs %s' % n
    pgap, pwhy = 1e9, ''
    for rect, y0, y1, nm in obstacles(variant):
        for grp, band in ((p['up'], bands['upper']), (p['lo'], bands['lower'])):
            if band[1] + dy < y0 or band[0] + dy > y1:
                continue
            for n, a, b, r in grp:
                g = gl.rect_seg(a, b, rect) - r - 3
                if g < pgap:
                    pgap, pwhy = g, '%s vs %s' % (nm, n)
    risky = (variant == 'top' and dy > 0) or (variant == 'under' and dy < 0)
    if risky:
        for n, a, b, r in (p['up'] if variant == 'top' else p['lo']):
            g = gl.rect_seg(a, b, (gl.XL - 16, gl.XL + 16, 0.0, 130.0)) - r
            if g < pgap:
                pgap, pwhy = g, 'lift links vs %s' % n
    return bgap, bwhy, pgap, pwhy, p


BODIES = {pose: body_at(pose) for pose in gl.POSES}


def evaluate(variant, S0a, L, br):
    if gl.ik(np.array(S0a, float), gl.EA0, L, br)[0] is None:
        return None
    worst = dict(body=(1e9, ''), parts=(1e9, ''))
    folds = []
    for d in gl.POSES:
        r = gaps(variant, S0a, L, br, d, BODIES[d])
        if r is None:
            return None
        bg, bw, pg, pw, p = r
        folds.append(p['dd'])
        if bg < worst['body'][0]:
            worst['body'] = (bg, '%s @%s' % (bw, d))
        if pg < worst['parts'][0]:
            worst['parts'] = (pg, '%s @%s' % (pw, d))
        for grp in (p['up'], p['lo']):
            for n, a, b, r_ in grp:
                if max(a[1], b[1]) + r_ > 250 + max(d[2], 0) or min(a[0], b[0]) - r_ < gl.XL - 70:
                    return None
    margin = min(min(folds) - 42, 2 * L - 8 - max(folds))
    score = min(worst['parts'][0], worst['body'][0] - 20, margin / 2)
    return score, worst, margin


def search(variant):
    rows = []
    for x in range(-290, -120, 10):
        for z in range(90, 240, 10):
            for L in (65.0, 75.0, 85.0):
                for br in (1, -1):
                    r = evaluate(variant, (x, z), L, br)
                    if r:
                        rows.append((r[0], (x, z), L, br, r[1], r[2]))
    rows.sort(key=lambda t: -t[0])
    return rows


def anim(best, seq, out):
    """Per-frame plan data for the page: SCARA points, body dots at the girdle's height, gaps."""
    data = {}
    for variant, (S0a, L, br) in best.items():
        bands = gu.TOP if variant == 'top' else gu.UNDER
        y_lo, y_hi = min(bands['lower'][0], bands['upper'][0]), max(bands['lower'][1], bands['upper'][1])
        frames = []
        for _, d, _abd in seq:
            d = tuple(d)
            B = body_at(d)
            bg, bw, pg, pw, p = gaps(variant, S0a, L, br, d, B)
            m = (B[:, 1] > y_lo + d[1]) & (B[:, 1] < y_hi + d[1])
            pts = np.unique(np.round(B[m][:, [0, 2]] / 6.0).astype(int), axis=0) * 6
            frames.append(dict(S=[round(float(v), 1) for v in p['S']], C=[round(float(v), 1) for v in p['C']],
                               E=[round(float(v), 1) for v in p['E']], body=pts.flatten().tolist(),
                               bg=round(float(bg), 1), bw=bw, pg=round(float(pg), 1), pw=pw))
        data[variant] = dict(S0=list(S0a), L=L, band=[y_lo, y_hi], frames=frames,
                             obst=[[list(r), y0, y1, n] for r, y0, y1, n in obstacles(variant)])
    json.dump(data, open(out, 'w'), separators=(',', ':'))


def fmt(r):
    return '%.1f %s L%d br%d body %.1f (%s) parts %.1f (%s) fold %.1f' % (
        r[0], r[1], r[2], r[3], r[4]['body'][0], r[4]['body'][1], r[4]['parts'][0], r[4]['parts'][1], r[5])


if __name__ == '__main__':
    best = {}
    for v in ('top', 'under'):
        rows = search(v)
        print('---', v, len(rows), 'feasible')
        for r in rows[:6]:
            print(fmt(r))
        best[v] = (rows[0][1], rows[0][2], rows[0][3])
    r = evaluate('top', (-240, 200), 65.0, 1)
    print('v3b as built:', fmt((r[0], (-240, 200), 65, 1, r[1], r[2])))
    if '--anim' in sys.argv:
        k = sys.argv.index('--anim')
        seq = json.load(open(sys.argv[k + 1]))
        best['top'] = ((-240, 200), 65.0, 1)                     # show the built layout
        anim(best, seq[:61], sys.argv[k + 2])
        print('anim written', best)
