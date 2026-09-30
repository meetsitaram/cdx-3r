"""Harness illustration: webbing + buckles routed over the scanned torso from the frame's actual tabs.
Output: out/layout/harness_webbing.stl, harness_buckles.stl (scan frame, mm).  Illustration only."""
import json
import numpy as np
import trimesh

__file__ = __file__.replace('harness.py', 'layout.py')
exec(open(__file__).read().split('# ---------------- abduction-side parts')[0])   # fields, onsurf, strap, buckle

D_ = json.load(open(OUT / 'layout' / 'layout.json'))['derived']
xf, y_top, y_bot = D_['xf'], D_['y_top'], D_['y_bot']
HT, HB, TAB, SLOT = 40., 64., 30., 4. + 2.5              # top/bottom node heights, tab length, slot offset
G_ = 9.0                                                 # webbing sits this far off the skin


def tab_top(s):      # shoulder-strap top tab slot (upright on the top node), side s = +1 right / -1 left
    return np.array([xf, y_top + HT / 2 + TAB - SLOT, MID_Z + s * 30.])


def tab_bot(s):      # shoulder-strap bottom tab slot (upright on the bottom node)
    return np.array([xf, y_bot + HB / 2 + TAB - SLOT, MID_Z + s * 115.])


def tab_waist(s):    # waist tab slot (pointing sideways off the bottom node's ends)
    return np.array([xf, y_bot, MID_Z + s * (158. + TAB - SLOT)])


def surf(pts):
    return [onsurf(p, G_)[0] for p in pts]


webs, bucks = [], []
for s in (1, -1):
    z = lambda dz: MID_Z + s * dz
    # shoulder strap: top tab -> over the trapezius (inside the arm mechanism) -> chest -> under the arm -> bottom tab
    over = surf([[-120, 1452, z(55)], [-40, 1468, z(80)], [40, 1425, z(95)], [95, 1300, z(105)],
                 [85, 1200, z(135)], [20, 1130, z(170)], [-90, 1085, z(165)]])
    m, P = strap([tab_top(s)] + over + [tab_bot(s)], 25., G_)
    webs.append(m)
    i = int(len(P) * 0.78)                                     # ladder-lock on the lower, adjustable run
    bucks.append(buckle(P[i], P[i + 1] - P[i], (40, 32, 8)))
    if s == 1:
        PR = P
    else:
        PL = P
    # waist strap: side tab -> round the hip -> to the front, where the side-release buckle closes it
    wz = surf([[-170, y_bot, z(190)], [-60, y_bot, z(205)], [60, y_bot, z(160)], [115, y_bot, z(60)]])
    m, _ = strap([tab_waist(s)] + wz, 38., G_)
    webs.append(m)

# waist buckle at the front centre, sternum strap + buckle between the shoulder straps
front = onsurf([140, y_bot, MID_Z], G_)[0]
bucks.append(buckle(front, np.array([0, 0, 1.]), (90, 50, 14)))
yst = 1280.
fp = lambda P_: P_[np.argmin(np.abs(P_[:, 1] - yst) + 1000 * (P_[:, 0] < 0))]
mid_st = onsurf([125, yst, MID_Z], G_ + 2)[0]
m, _ = strap([fp(PR), mid_st, fp(PL)], 20., G_ + 2)
webs.append(m)
bucks.append(buckle(mid_st, np.array([0, 0, 1.]), (55, 26, 10)))

W = trimesh.util.concatenate(webs); B = trimesh.util.concatenate(bucks)
W.export(OUT / 'layout' / 'harness_webbing.stl'); B.export(OUT / 'layout' / 'harness_buckles.stl')
g = sample(sd_body, W.sample(20000))
print('webbing %d faces, gap to body min %.1f / p5 %.1f mm' % (len(W.faces), g.min(), np.percentile(g, 5)))
