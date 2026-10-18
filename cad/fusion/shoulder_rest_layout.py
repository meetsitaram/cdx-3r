"""Layout of the right shoulder rest: a chain of hinged blades draped over the shoulder top (offline, numpy).

The blades hinge about parallel axes tilted ROLL deg down toward the arm (the shoulder top's sideways slope), so the
chain bends in one tilted plane. Coordinates in that plane: u = x (forward), v = up in the plane, w = along the hinge
axes (outward and down). The front blade's front hinge sits on the front of the shoulder; the other hinges sit
backward along the pad-offset outline of the scan, one blade length apart (pads compress COMPRESS mm). The root arm
then joins the last hinge to a bracket on the shoulder tower's front plate.
Run: python shoulder_rest_layout.py  (prints the layout, writes shoulder_rest_layout.json + a plot)
"""
import json
import math
import os

import numpy as np
import trimesh

SCAN = r'C:\Users\PC\projects\exoarm2-scan\out\layout'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shoulder_rest_layout.json')
ROLL = math.radians(25.0)
O = np.array([0.0, 1420.0, 110.0])                       # plane origin over the shoulder top
X = np.array([1.0, 0.0, 0.0])
N = np.array([0.0, math.cos(ROLL), math.sin(ROLL)])      # up in the chain plane (tilted toward the arm)
A = np.array([0.0, -math.sin(ROLL), math.cos(ROLL)])     # hinge axis: outward and down
R = dict(
    hinge_drop=6.5, velcro=1.5, pad_t=12.7, compress=2.0,  # hinge axis to the blade's flat underside; 1/2" pads
    knuckle=12.0, end_gap=8.0, pad_inset=5.0,             # plate stops end_gap short of each hinge; pads inset
    front_u=40.0,                                        # front hinge (buckle end) over the front of the shoulder
    blades=[48.0, 54.0, 60.0],                          # back -> front after the root arm: hinge-to-hinge
    joints=[(64.0, 90.0), (74.0, 98.0), (90.0, 105.0)],  # hinge width, centre z: root arm/1, 1/2, 2/3 (>= 64: two M5 x 30 from the ends must not meet)
    front_end=(106.0, 110.0),                            # front edge of blade 3 (buckle tab)
    # root hinge in front of the tower plate; >= 64 wide (see joints). x -166: the bracket pivot bolt (head + washer,
    # 9 mm proud of the bracket) sits on this hinge's axis line and needs the knuckle 16 mm out (docs/bugs/pivot-bolt-hits-rest-hinge.md)
    root=dict(H0=(-166.0, 1442.0, 66.0), width=64.0),
)


def uvw(P):
    D = np.atleast_2d(P) - O
    return np.c_[np.atleast_2d(P)[:, 0], D @ N, D @ A]


def xyz(u, v, w):
    return O + (u - O[0]) * X + v * N + w * A


def body():
    V = np.vstack([trimesh.load(SCAN + r'\body_torso_trim.stl').vertices,
                   trimesh.load(SCAN + r'\body_arm_trim.stl').vertices])
    V = V[(V[:, 1] > 1200) & (V[:, 2] > 20) & (V[:, 0] > -220) & (V[:, 0] < 140)]
    return uvw(V)


def w_of_z(zc):
    return (zc - O[2]) / math.cos(ROLL)                  # on the shoulder top (v ~ 0)


def offset_curve(Q, d, u0=-200.0, u1=90.0):
    """Upper envelope of the points Q (u, v) dilated by d: where a hinge line sits when its pad rests on them."""
    us = np.arange(u0, u1 + 0.5, 1.0)
    vs = np.full(us.shape, -1e9)
    for qu, qv in Q:
        k0, k1 = np.searchsorted(us, qu - d), np.searchsorted(us, qu + d)
        du = us[k0:k1] - qu
        vs[k0:k1] = np.maximum(vs[k0:k1], qv + np.sqrt(np.maximum(d * d - du * du, 0.0)))
    return us, vs


def layout():
    """Hinges on the pad-offset outline of the shoulder (the union of the blades' widths), from the front hinge
    backward at each blade's length: the chain settles on the shoulder; blades are chords, pads squeeze a little
    more mid-blade where the shoulder bulges."""
    Q3 = body()
    d = R['hinge_drop'] + R['velcro'] + R['pad_t'] - R['compress']
    H0 = uvw(np.array(R['root']['H0']))[0]
    ranges = [(H0[2] - R['root']['width'] / 2, H0[2] + R['root']['width'] / 2)]
    ranges += [(w_of_z(zc) - W / 2, w_of_z(zc) + W / 2) for W, zc in R['joints'] + [R['front_end']]]
    blades = [dict(L=L, rear=ranges[i + 1], front=ranges[i + 2]) for i, L in enumerate(R['blades'])]
    lo = min(r[0] for r in ranges[1:]) + R['pad_inset']
    hi = max(r[1] for r in ranges[1:]) - R['pad_inset']
    us, vs = offset_curve(Q3[(Q3[:, 2] > lo) & (Q3[:, 2] < hi)][:, :2], d)
    curve = np.c_[us, vs][vs > -1e8]
    k = int(np.argmin(np.abs(curve[:, 0] - R['front_u'])))
    F = curve[k]
    for b in reversed(blades):
        dist = np.hypot(*(curve[:k] - F).T)
        j = int(np.nonzero(dist >= b['L'])[0].max())    # first point back along the curve that is L away
        b['F'], b['R'] = F, curve[j]
        b['phi'] = math.atan2(*(b['R'] - F)[::-1])
        F, k = curve[j], j
    root = dict(L=float(np.hypot(*(blades[0]['R'] - H0[:2]))), rear=ranges[0], front=ranges[1], R=H0[:2],
                F=blades[0]['R'])
    return blades, root, d, curve


def main():
    blades, root, d, curve = layout()
    piece = lambda p, name: dict(name=name, L=float(p.get('L', 0.0)), R=list(map(float, p['R'])),
                                 F=list(map(float, p['F'])), rear=list(map(float, p['rear'])),
                                 front=list(map(float, p['front'])))
    out = dict(roll_deg=math.degrees(ROLL), origin=O.tolist(), N=N.tolist(), A=A.tolist(), params=R, offset=d,
               pieces=[piece(root, 'Rest root arm')] + [piece(b, 'Rest blade %d' % i) for i, b in enumerate(blades, 1)])
    json.dump(out, open(OUT, 'w'), indent=1)
    print('root arm: %.0f mm long, %.0f deg' % (root['L'], math.degrees(math.atan2(*(root['F'] - root['R'])[::-1]))))
    for i, b in enumerate(blades, 1):
        wc = (b['front'][0] + b['front'][1]) / 2
        Rr, F = xyz(b['R'][0], b['R'][1], wc), xyz(b['F'][0], b['F'][1], wc)
        print('blade %d: %2.0f long, %3.0f -> %3.0f wide, rear hinge x %4.0f y %4.0f -> front x %4.0f y %4.0f'
              % (i, b['L'], b['rear'][1] - b['rear'][0], b['front'][1] - b['front'][0], Rr[0], Rr[1], F[0], F[1]))
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        Q3 = body()
        fig, ax = plt.subplots(1, 2, figsize=(14, 6))
        sel = (Q3[:, 2] > w_of_z(60)) & (Q3[:, 2] < w_of_z(160))
        ax[0].scatter(Q3[sel, 0], Q3[sel, 1], s=1, c='#d9b38c')
        ax[0].plot(curve[:, 0], curve[:, 1], c='#bbbbbb', lw=1)
        pts = [root['R']] + [b['R'] for b in blades] + [blades[-1]['F']]
        ax[0].plot([p[0] for p in pts], [p[1] for p in pts], 'o-', c='#33414b', lw=3)
        for b in blades:
            t = (b['R'] - b['F']) / np.hypot(*(b['R'] - b['F']))
            m = np.array([-t[1], t[0]])
            a, c = b['F'] + t * (R['end_gap'] + R['pad_inset']), b['R'] - t * (R['end_gap'] + R['pad_inset'])
            ax[0].plot([a[0] + m[0] * d, c[0] + m[0] * d], [a[1] + m[1] * d, c[1] + m[1] * d], c='#4a90c2', lw=2)
        ax[0].set_aspect('equal'); ax[0].grid(alpha=.3); ax[0].set_xlabel('u = x fwd'); ax[0].set_ylabel('v (tilted up)')
        ax[0].set_title('side, in the chain plane: chain (dark), pad bottoms (blue)')
        V3 = np.array([xyz(*q) for q in Q3[::3]])
        ax[1].scatter(V3[:, 2], V3[:, 0], s=1, c=V3[:, 1], cmap='copper')
        for b in [root] + blades:
            c0 = [xyz(b['R'][0], b['R'][1], w) for w in b['rear']]
            c1 = [xyz(b['F'][0], b['F'][1], w) for w in b['front']]
            for p0, p1 in (c0, c1):
                ax[1].plot([p0[2], p1[2]], [p0[0], p1[0]], c='#33414b')
            for p, q_ in zip(c0, c1):
                ax[1].plot([p[2], q_[2]], [p[0], q_[0]], c='#33414b')
        ax[1].set_aspect('equal'); ax[1].grid(alpha=.3); ax[1].set_xlabel('z right'); ax[1].set_ylabel('x fwd')
        ax[1].set_title('plan')
        plt.tight_layout()
        plt.savefig(os.path.join(os.environ.get('SR_PLOT_DIR', os.path.dirname(OUT)), 'shoulder_rest_layout.png'), dpi=75)
    except ImportError:
        pass


if __name__ == '__main__':
    main()
