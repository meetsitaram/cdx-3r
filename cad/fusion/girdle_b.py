"""Shoulder girdle v3b (real parts), right side: shoulder tower saddled on the top node, tilted lift parallelogram,
belt-kept SCARA, abduction housing.

Layout from girdle_layout.py (belt keeper). Scan frame: mm, X forward, Y up, Z right.

  frame top node + right backbone (runs on up into the tower) -> TOWER (saddle over the node's right end, 2 x M5)
  TOWER --(2 lift links, 100 mm, tilted 15 deg down at rest, gas spring)--> CARRIAGE            shrug up / down
  CARRIAGE --S0 (bolt clamped, pulley P0 fixed)--> LINK 1 (hollow box, belt 1 inside, upper level)
  LINK 1 --C (bolt free, pulleys PA + PB keyed to it)--> LINK 2 (hollow box, belt 2 inside, lower level)
  LINK 2 --E (bolt clamped, pulley P2 fixed)--> END PLATE + ABDUCTION HOUSING           forward/back + in/out
  P0 and P2 fixed, belts 1:1: the housing never turns (it only translates), like a robot SCARA's J4.

Pivots: 608-2RS in the top and bottom plates of the link boxes; M8 bolts. S0 is held from above (carriage), E from
below (end plate), C is free: nothing outside the link boxes at C. Hardware, pulleys and belts live in the component
they move with, so every pose shows them.
"""
import math

import adsk.core
import adsk.fusion

import fxlib as fx
from fxlib import Part, JOIN, CUT, add, sub, mul, unit, dot, norm
import shoulder as sh
import girdle as g1
from girdle import P3, stadium, poly, plan_prism, side_prism, cheek_ranges, fork_fits, tongue_fits, _join

NAME = 'Shoulder girdle v3b (right)'
PRINT, HWC, BRG, PVC, BELT = '#647684', '#c9d2d9', '#d4a017', '#e9eef2', '#2b2f33'
XL = sh.D['xf']
GH = sh.GH
G = dict(
    lift_L=100.0, tilt=15.0, lift_z0=95.0, carr_y=(1545.0, 1500.0), mast=(XL, 30.0), mast_top=sh.S['mast_top'],
    S0=(-240.0, 200.0), E=(-180.5, 153.0), L=65.0, branch=1,
    yU=1440.0, yL=1409.0, box_h=15.0, plate=8.5, r_box=22.0, r_cav=14.8, pulley_r=11.14, pulley_h=8.0,
    lip_d=19.0, lid_screws=((0.45, 0.8), (0.2, 0.55)), brg=(8.0, 22.0, 7.0), land=11.0,   # link boxes: tray + lid, 608 lips
    root_loft=24.0,                                                      # carriage: round foot -> square hanger
    hexhead=(13.0, 5.3),                                                   # M8 hex head (DIN 933)
    # strut ends are flat eyelets (Motoforti 180 mm): each sits in a fork in its ear, on an M6 x 16 socket head (the
    # rest-lock part: no new part) into a hidden
    # M6 nut. eye: OD, hole, thickness (assumed; the listing gives none: the slot clears up to 19 OD x 4.5)
    spring_end=dict(eye=(14.0, 6.2, 3.0), gap=4.5, cheek=3.5, wall=3.0, r_ear=14.0, clear=9.5, open=70.0,
                    neck=20.0, bolt=16.0, nut=(10.0, 5.0)),   # 3.5 + 4.5 + 3 + 5 = 16: full nut
    spring_len=(120.0, 180.0),               # pin to pin 120 (drop 20) .. 177 (shrug 60): a 180 / 120 mm, 100 N strut
    root_t=12.0, end_t=12.0, r_plate=22.0,
    housing=(-215.0, -146.0), housing_r=28.0,
    spring_x=XL + 40.0, spring_lo=(1475.4, 63.5), spring_hi=(1555.0, 175.0),
)
H0 = [(G['housing'][0] + G['housing'][1]) / 2, GH[1], GH[2]]
PHI0 = -math.radians(G['tilt'])
ZC = G['lift_z0'] + G['lift_L'] * math.cos(PHI0)
BASE_Y = tuple(y - G['lift_L'] * math.sin(PHI0) for y in G['carr_y'])     # tower pivots (higher than the carriage)
STATE = {}


# ------------------------------------------------------------------ kinematics
def ik(S, E, branch):
    L = G['L']
    dx, dz = E[0] - S[0], E[1] - S[1]
    d = math.hypot(dx, dz)
    if d > 2 * L - 0.5 or d < 1:
        raise RuntimeError('SCARA out of reach (%.0f mm)' % d)
    a = math.atan2(dz, dx) + branch * math.acos(d / (2 * L))
    return (S[0] + L * math.cos(a), S[1] + L * math.sin(a))


def rest():
    if 'rest' not in STATE:
        STATE['rest'] = dict(S0=G['S0'], E=G['E'], C=ik(G['S0'], G['E'], G['branch']))
    return STATE['rest']


def _ang(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def kin(d):
    g = rest()
    L = G['lift_L']
    s = max(-0.99, min(0.99, math.sin(PHI0) + d[1] / L))
    phi = math.asin(s)
    Tc = [0.0, d[1], L * (math.cos(phi) - math.cos(PHI0))]
    S = (g['S0'][0], g['S0'][1] + Tc[2])
    E = (g['E'][0] + d[0], g['E'][1] + d[2])
    C = ik(S, E, G['branch'])
    da1 = _ang(S, C) - _ang(g['S0'], g['C'])
    da2 = _ang(C, E) - _ang(g['C'], g['E'])
    return dict(dphi=phi - PHI0, Tc=Tc, Te=[C[0] - g['C'][0], d[1], C[1] - g['C'][1]], TE=[d[0], d[1], d[2]],
                da1=da1, da2=da2, C=C)


# ------------------------------------------------------------------ parts
def _box_link(grp, name, a, b, level, pulleys, lid_up=True):
    """Hollow link box between pivots a, b (plan) at a level, printed as two pieces so the belt and pulleys go in: a
    TRAY (one plate + the walls) and a LID (the other plate), 4 x M3 x 12 through the lid into ruthex inserts in the
    wall ends. Link 1's lid is on top, link 2's underneath: screw heads face away from the other link. Each plate
    has a 608 pocket from its outer face with a Ø19 lip on the cavity side, so a bearing carries the link both ways
    (the inner rings are clamped by the bolt stack). Built as one rounded box and split at the lid line, so the seam
    stays sharp. Both pieces print outer face down: no supports (the lip overhangs 1.5 mm)."""
    p = Part(grp, name, color=PRINT)
    h, t = G['box_h'], G['plate']
    body = plan_prism(p, stadium(a, b, G['r_box']), level - h, level + h, 'box')
    sh.round_edges(p, body, r=2.0)
    ys = level + h - t if lid_up else level - h + t
    sf = p.comp.features.splitBodyFeatures
    sf.add(sf.createInput(p.comp.bRepBodies.item(0), p.plane([0, ys, 0], [0, 1, 0], [1, 0, 0]), True))
    bs = list(p.comp.bRepBodies)
    lid = (max if lid_up else min)(bs, key=lambda q: q.boundingBox.minPoint.y + q.boundingBox.maxPoint.y)
    tray = next(q for q in bs if q != lid)
    lid.name, tray.name = name + ' lid', name + ' tray'
    plan_prism(p, stadium(a, b, G['r_cav']), level - h + t, level + h - t, 'belt cavity', op=CUT, targets=[tray])
    top, bot = (lid, tray) if lid_up else (tray, lid)
    bi, bo, bw = G['brg']
    for c in (a, b):
        for z0, z1, tgt in ((h - bw, h + 1, top), (-h - 1, -h + bw, bot)):
            p.prism(P3(c, level), fx.AX['y'], z0, z1, sh.circle(bo / 2 + 0.05), name='608 pocket', op=CUT, targets=[tgt])
        for z0, z1, tgt in ((h - t - 1, h, top), (-h, -h + t + 1, bot)):
            p.prism(P3(c, level), fx.AX['y'], z0, z1, sh.circle(G['lip_d'] / 2), name='bearing lip hole', op=CUT,
                    targets=[tgt])
    hw = Part(grp, name + ' HW (buy)', color=HWC)
    dd = unit([b[0] - a[0], b[1] - a[1], 0])
    n = (-dd[1], dd[0])
    off = (G['r_box'] + G['r_cav']) / 2                   # mid-wall
    ins_d, ins_l = sh.S['m3']['insert']
    sgn = 1 if lid_up else -1                             # lid side
    yo = level + sgn * h                                  # lid outer face
    for f in G['lid_screws'][0 if lid_up else 1]:
        base = (a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1]))
        for s in (1, -1):
            q = (base[0] + s * off * n[0], base[1] + s * off * n[1])
            y0, y1 = sorted((ys + sgn * 0.1, ys - sgn * ins_l))
            plan_prism(p, stadium(q, q, ins_d / 2), y0, y1, 'insert hole', op=CUT, targets=[tray])
            y0, y1 = sorted((ys, yo))
            plan_prism(p, stadium(q, q, sh.S['m3']['clear'] / 2), y0 - 0.1, y1 + 0.1, 'M3 clearance', op=CUT,
                       targets=[lid])
            ins = hw.ann(fx.AX['y'], [q[0], ys - sgn * ins_l / 2, q[1]], ins_d / 2 - 0.2, 1.5, sh.S['m3']['insert_len'],
                         name='insert')[0]
            ins.name = 'M3 heat-set insert ruthex 5.7 (buy)'
            sh.hw_bolt(hw, [q[0], yo, q[1]], sh.frame_of([0, -sgn, 0]), 12.0, sh.S['m3']['head'],
                       'M3 x 12 socket head (buy)', dia=3.0)
    for c in (a, b):
        for s in (1, -1):
            sh.hw_bearing(hw, add(P3(c, level), [0, s * (h - bw / 2), 0]), fx.AX['y'], '608-2RS (buy)', (bi, bo, bw))
    loop_o = plan_prism(hw, stadium(a, b, G['pulley_r'] + 1.4), level - 3, level + 3, 'belt')
    plan_prism(hw, stadium(a, b, G['pulley_r']), level - 4, level + 4, 'belt inside', op=CUT, targets=[loop_o])
    loop_o.name = 'GT2 6 mm belt, closed loop 200 mm (buy)'
    return p, hw


def _pulley(p, c, level, name):
    """Printed GT2 35-tooth pulley (pitch Ø22.28): with a stock 200 mm closed loop (2C + pi PD) it fits 65 mm centres
    exactly."""
    b = plan_prism(p, stadium(c, c, G['pulley_r']), level - G['pulley_h'] / 2, level + G['pulley_h'] / 2, name)
    p.prism(P3(c, level), fx.AX['y'], -G['pulley_h'], G['pulley_h'], sh.circle(4.25), name='bore', op=CUT, targets=[b])
    b.name = name
    return b


def _spacer(hw, c, y0, y1, name='inner-ring spacer (printed)'):
    """Ø11 / 8.4 sleeve: carries the bolt clamp to a 608's inner ring without touching the outer ring or a plate."""
    s = hw.ann(fx.AX['y'], [c[0], (y0 + y1) / 2, c[1]], G['land'] / 2, 4.2, y1 - y0, name='spacer')[0]
    s.name = name
    return s


def _stack(hw, c, level):
    """Spacers between the pulley and the two bearings' inner rings inside a link box (4 mm each side)."""
    h, bw, ph = G['box_h'], G['brg'][2], G['pulley_h']
    _spacer(hw, c, level + ph / 2, level + h - bw)
    _spacer(hw, c, level - h + bw, level - ph / 2)


def _bolt(hw, c, y_head, y_end, name, hexhead=False):
    """M8 with its head on top at y_head (socket head, or hex head for a hex pocket), shank to y_end, nyloc below."""
    down = sh.frame_of([0, -1, 0])
    L = 5 * math.ceil((y_head - y_end + sh.S['m8']['nut_h'] + 1.5) / 5)   # through the nyloc + 1.5 mm
    if hexhead:
        b = hw.prism([c[0], y_head, c[1]], down, -G['hexhead'][1], 0, sh.hexagon(G['hexhead'][0]),
                     name='hex head').bodies.item(0)
        hw.prism([c[0], y_head, c[1]], down, -0.5, L, sh.circle(4.0), name='shank', op=JOIN, targets=[b])
        b.name = 'M8 x %d hex head (buy)' % L
    else:
        sh.hw_bolt(hw, [c[0], y_head, c[1]], down, L, sh.S['m8']['shcs_head'], 'M8 x %d socket head (buy)' % L)
    sh.hw_nut(hw, [c[0], y_end, c[1]], down)
    return L


def _x_pivot_bolt(hw, c, length=55.0, head_back=False):
    """Lift pivot: M8 x 55 through both cheeks + nyloc. Head on the front (+x) face, or on the back face
    (head_back: the carriage, whose back cheek is buried in the hanger: the head sits in a round tunnel a hex key
    reaches through, the nyloc goes on the open front face)."""
    top = g1.G['half'] + g1.G['gap'] + g1.G['cheek']
    s = -1 if head_back else 1
    d = sh.frame_of([-s, 0, 0])
    sh.hw_bolt(hw, add(c, [s * top, 0, 0]), d, length, sh.S['m8']['shcs_head'], 'M8 x %d socket head (buy)' % length)
    sh.hw_nut(hw, add(c, [-s * top, 0, 0]), d)


def _plan_profile(p, y, draw, name):
    """A closed plan outline (x, z) in a hidden sketch at height y: one section of a loft."""
    sk = p.comp.sketches.add(p.plane([0, y, 0], [0, 1, 0], [1, 0, 0]))
    sk.name, sk.isVisible = name, False
    o = [0, y, 0]
    draw(sk, lambda u, v: sk.modelToSketchSpace(fx.P(add(o, [u, 0, v]))))
    return sk.profiles.item(0)


def _loft(p, profiles, name):
    lf = p.comp.features.loftFeatures
    li = lf.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    for pr in profiles:
        li.loftSections.add(pr)
    li.isSolid = True
    f = lf.add(li)
    f.name = name
    return f.bodies.item(0)


def _ear_face():
    """Inner cheek face of the strut fork (the eyelet's mid-plane is at spring_x)."""
    return G['spring_x'] - G['spring_end']['gap'] / 2


def _ear_out():
    """Outer face of the fork's outer cheek (the bolt head sits here)."""
    se = G['spring_end']
    return G['spring_x'] + se['gap'] / 2 + se['cheek']


def _strut_dir(end):
    """Unit (y, z) direction from this end of the strut toward the other (rest pose)."""
    a, b = _spring_pts()
    d = [b[1] - a[1], b[2] - a[2]] if end == 'lo' else [a[1] - b[1], a[2] - b[2]]
    n = math.hypot(*d)
    return d[0] / n, d[1] / n


def _spring_ear(p, body, c, fu0, end):
    """Strut fork: the ear runs out past the strut plane; a 4.5 mm slot takes the eyelet (round, r 9.5, so the eye
    turns freely) and a wide-open sector toward the strut lets the eyelet's neck swing through the outer cheek. The
    outer cheek hangs on the ring behind the bolt. An M6 x 16 socket head goes in from the outside through both cheeks and the
    eyelet into an M6 nut locked in a hex pocket that opens on the plate's inside face (drop it in first). The bolt
    clamps the fork, not the eyelet."""
    se = G['spring_end']
    X = fx.AX['x']
    p.prism(c, X, fu0 - 1 - c[0], _ear_out() + 1 - c[0], sh.circle(3.2), name='strut bolt hole', op=CUT, targets=[body])
    p.prism(c, X, fu0 - 0.1 - c[0], _ear_face() - se['wall'] - c[0], sh.hexagon(se['nut'][0] + 0.3),
            name='strut nut (hex, locked)', op=CUT, targets=[body])
    p.prism(c, X, _ear_face(), _ear_face() + se['gap'], sh.circle(se['clear']), name='eyelet slot', op=CUT, targets=[body])
    dy, dz = _strut_dir(end)
    th = math.atan2(dz, dy)
    angs = [th + math.radians(a) for a in range(-int(se['open']), int(se['open']) + 1, 10)]
    pts = [(c[1] + se['clear'] * math.cos(a), c[2] + se['clear'] * math.sin(a)) for a in angs]
    pts += [(c[1] + 40 * math.cos(a), c[2] + 40 * math.sin(a)) for a in reversed(angs)]
    side_prism(p, poly(pts), _ear_face() - 1.5, _ear_out() + 1, 'eyelet neck opening', op=CUT, targets=[body])


def _teardrop(p, body, c, z0, z1, r):
    """45-degree point on top of a horizontal round hole along -x (the carriage prints standing on its root disc,
    design +y up): the hole's roof needs no support. The bottom stays round."""
    k = r / math.sqrt(2)
    p.prism(c, sh.frame_of([-1, 0, 0]), z0, z1, poly([(-k, k - 0.5), (k, k - 0.5), (0, r * math.sqrt(2))]),
            name='hole teardrop point', op=CUT, targets=[body])


def pivot_nut_flat(p, body, fu1, yt):
    """Flat cut through the strut ear on the upper pivot's side: everything forward of the front cheek's outer face
    (x > fu1; the cheek itself is the nut's seat and stays whole) and
    beyond a chord 10.5 mm from the pivot axis, toward the pivot, is removed."""
    ey, ez = G['spring_hi']
    u = unit([yt - ey, ZC - ez, 0])[:2]
    n = (-u[1], u[0])
    se = G['spring_end']
    d = math.hypot(yt - ey, ZC - ez) - (se['clear'] + 1.2)    # 1.2 mm of wall left round the eyelet slot
    cy, cz = yt - u[0] * d, ZC - u[1] * d
    pts = [(cy - n[0] * 40, cz - n[1] * 40), (cy + n[0] * 40, cz + n[1] * 40),
           (cy + n[0] * 40 + u[0] * 40, cz + n[1] * 40 + u[1] * 40), (cy - n[0] * 40 + u[0] * 40, cz - n[1] * 40 + u[1] * 40)]
    side_prism(p, poly(pts), fu1, _ear_out() + 1, 'pivot nut flat', op=CUT, targets=[body])   # exactly at the cheek face: an offset left a 0.05 mm film


def carriage_teardrops(p, body, fu0, fu1):
    """The carriage prints standing on its root disc (design +y up): every horizontal round hole gets 45-degree
    points (up and down) so its roof needs no support: the M8 pivot holes through both cheeks, the wrench clearance
    by the upper pivot nut, the strut bolt hole and the eyelet slot."""
    se = G['spring_end']
    sy, sz = G['spring_hi']
    reach = g1.G['half'] + g1.G['gap'] + g1.G['cheek'] + 1
    for y in G['carr_y']:
        _teardrop(p, body, [XL, y, ZC], -reach, reach, g1.G['clear'] / 2)
    _teardrop(p, body, [0, sy, sz], -(_ear_out() + 1), -(fu0 - 1), 3.2)
    _teardrop(p, body, [0, sy, sz], -(_ear_face() + se['gap']), -_ear_face(), se['clear'])


def _strut_bolt(hw, c):
    """M6 x 16 socket head from outside the fork + the M6 nut in its pocket."""
    se = G['spring_end']
    sh.hw_bolt(hw, [_ear_out(), c[1], c[2]], sh.frame_of([-1, 0, 0]), se['bolt'], (10.0, 6.0),
               'M6 x 16 socket head (buy)', dia=6.0)
    xn = _ear_face() - se['wall'] - se['nut'][1]
    b = hw.prism([xn, c[1], c[2]], fx.AX['x'], 0, se['nut'][1], sh.hexagon(se['nut'][0]), name='M6 hex nut (buy)').bodies.item(0)
    hw.prism([xn, c[1], c[2]], fx.AX['x'], -1, se['nut'][1] + 1, sh.circle(3.0), name='thread', op=CUT, targets=[b])
    b.name = 'M6 hex nut (buy)'


def build_tower(grp):
    """Shoulder tower. It slides down over the right backbone pipe, which runs on up through the top node into the
    tower's bore, and over the top node's right end. That end is a tenon (shoulder.build_top_node): the saddle's
    cheeks, top plate and end wall replace the node's skin there, flush with its faces, so node + tower read as one
    block. 4 x M3 x 8 into ruthex inserts in the node's tenon, 2 pipe screws into the backbone above the node.
    The node and both backbones carry the arm: no mast stub, no strut."""
    p = Part(grp, 'Shoulder tower', color=PRINT)
    yb, yt = BASE_Y[1], BASE_Y[0]
    z0 = G['lift_z0']
    xm, zm = G['mast']
    sd = sh.S['saddle']
    ht = sh.S['node_h'][2]
    ny0, ny1 = sh.D['y_top'] - ht / 2, sh.D['y_top'] + ht / 2      # top node bottom / top
    nz1 = sh.MID_Z + 90                                             # top node right end
    xo = sh.S['node_depth'] / 2                                     # saddle outer faces = the node's faces
    xi = xo - sd['cheek']
    ze = nz1 + sd['fit'] + sd['end']                                # end wall outer face
    bodies = [plan_prism(p, stadium((xm, zm), (xm, zm), 16.0), ny1, yt + 17, 'mast boss')]   # sits on the node top
    (fu0, fu1), (fl0, fl1) = cheek_ranges(XL)
    for x0, x1 in ((fu0, fu1), (fl0, fl1)):
        bodies.append(side_prism(p, stadium((yb, z0), (yt, z0), 17.0), x0, x1, 'lift cheek'))
        # outer edge cut on a slant from the lower lift pivot down to the saddle's end: no square corner (it also
        # carries the round end of the lift cheek when printed upright)
        bodies.append(side_prism(p, poly([(ny1, zm - 16), (yt + 17, zm - 16), (yt + 17, z0), (yb, z0 + 17), (ny1, ze)]),
                                 x0, x1, 'cheek web'))
    import shoulder_rest as sr                                      # the front plate backs the whole rest bracket
    bodies.append(side_prism(p, poly(sr.bracket_backing(ny1 + 0.5)), fu0, fu1, 'rest bracket backing'))
    sx = G['spring_x']
    sy, sz = G['spring_lo']
    bodies.append(side_prism(p, stadium((sy, sz), (sy, sz), G['spring_end']['r_ear']), fu0, _ear_out(), 'spring ear'))
    body = _join(p, bodies)
    sh.round_edges(p, body, r=2.0)
    # saddle (flush with the node): cheeks on the cut-down faces, top plate on the cut-down top, end wall
    saddle = []
    for xa, xb in ((XL - xo, XL - xi), (XL + xi, XL + xo)):
        saddle += p.box(xa, xb, ny0, ny1, sd['z0'], ze, name='saddle cheek')
    saddle += p.box(XL - xo, XL + xo, ny1 - sd['top'], ny1, sd['top_z0'] + sd['fit'], ze, name='saddle top')
    saddle += p.box(XL - xo, XL + xo, ny0, ny1, nz1 + sd['fit'], ze, name='saddle end wall')
    body = _join(p, [p.comp.bRepBodies.item(0)] + saddle)
    # round the saddle like the node (r 2) but not where it meets the node: its left end (z0) and the top
    # plate's left end (top_z0) stay sharp, so the seam is a hairline
    sh.round_edges(p, body, r=2.0, seam_z=(sd['z0'], sd['top_z0'] + sd['fit']))
    body = p.comp.bRepBodies.item(0)
    # re-cut the cavity square: the rounding put concave fillets in its corners, which sit on the tenon's corners
    p.prism([0, 0, 0], fx.AX['z'], sd['z0'] - 1, nz1 + sd['fit'], sh.rect(XL - xi, XL + xi, ny0 - 1, ny1 - sd['top']),
            name='saddle cavity (square)', op=CUT, targets=[body])
    p.prism([0, 0, 0], fx.AX['z'], sd['z0'] - 1, sd['top_z0'] + sd['fit'], sh.rect(XL - xi, XL + xi, ny0 - 1, ny1),
            name='saddle cavity (square, under the tab)', op=CUT, targets=[body])
    p.prism([xm, 0, zm], fx.AX['y'], ny0 - 1,yt + 17 - 6, sh.circle(sh.S['pipe_bore'] / 2), name='backbone bore',
            op=CUT, targets=[body])                                 # blind at the top: 6 mm cap
    # 2 pipe screws into the backbone from the back; 9.75 mm of plastic to the pipe, so the helper counterbores
    sh.pipe_screws(p, body, [xm, ny1, zm], [0, 1, 0], (25.0, 45.0), [-1, 0, 0], -(fl0 - XL) - sh.S['pipe_od'] / 2)
    m3 = sh.S['m3']
    for z in sd['bolts_z']:                                  # 2 x M3 x 8 per face into inserts in the node tenon
        for xa, xb, cb in ((XL - xo - 1, XL - xi + 0.1, (XL - xo - 1, XL - xo + sd['cbore'])),
                           (XL + xi - 0.1, XL + xo + 1, (XL + xo - sd['cbore'], XL + xo + 1))):
            p.prism([0, sh.D['y_top'], z], fx.AX['x'], xa, xb, sh.circle(m3['clear'] / 2), name='saddle screw hole',
                    op=CUT, targets=[body])
            p.prism([0, sh.D['y_top'], z], fx.AX['x'], cb[0], cb[1], sh.circle(m3['cbore'] / 2),
                    name='saddle screw counterbore', op=CUT, targets=[body])
    for y in (yt, yb):
        fork_fits(p, body, [XL, y, z0], 'x')
    _spring_ear(p, body, [0, sy, sz], fu0, 'lo')
    sr.tower_holes(p, body)                                         # 4 M3 inserts for the rest bracket
    hw = Part(grp, 'Tower HW (buy)', color=HWC)
    for y in (yt, yb):
        _x_pivot_bolt(hw, [XL, y, z0])
    _strut_bolt(hw, [0, sy, sz])
    tower_pipe_screws(hw)
    for z in sd['bolts_z']:
        for x_head, d in ((XL - xo + sd['cbore'], 1), (XL + xo - sd['cbore'], -1)):
            sh.hw_bolt(hw, [x_head, sh.D['y_top'], z], sh.frame_of([d, 0, 0]), 8.0, sh.S['m3']['head'],
                       'M3 x 8 socket head (buy)', dia=3.0)
            ins = hw.ann(fx.AX['x'], [x_head + d * (sd['cheek'] - sd['cbore'] + sd['fit'] + 2.85), sh.D['y_top'], z], 2.0,
                         1.5, 5.7, name='insert')[0]
            ins.name = 'M3 heat-set insert ruthex 5.7 (buy)'
    return p, hw


def tower_pipe_screws(hw):
    """The 2 #4 pipe screws from the tower's back into the right backbone (in their counterbores)."""
    xm, zm = G['mast']
    ny1 = sh.D['y_top'] + sh.S['node_h'][2] / 2
    (fu0, fu1), (fl0, fl1) = cheek_ranges(XL)
    return sh.hw_pipe_screws(hw, [xm, ny1, zm], [0, 1, 0], (25.0, 45.0), [-1, 0, 0], -(fl0 - XL) - sh.S['pipe_od'] / 2)


def build_lift_link(grp, i):
    yc = G['carr_y'][i]
    yb = BASE_Y[i]
    p = Part(grp, 'Lift link %s' % ('upper' if i == 0 else 'lower'), color=PRINT)
    h = G['half'] if 'half' in G else 13.0
    body = side_prism(p, stadium((yb, G['lift_z0']), (yc, ZC), 17.0), XL - h, XL + h, 'link')
    sh.round_edges(p, body, r=2.0)
    for y, z in ((yb, G['lift_z0']), (yc, ZC)):
        tongue_fits(p, p.comp.bRepBodies.item(0), [XL, y, z], 'x')
    hw = Part(grp, p.comp.name + ' HW (buy)', color=HWC)
    for y, z in ((yb, G['lift_z0']), (yc, ZC)):
        for s in (1, -1):
            sh.hw_bearing(hw, [XL + s * 9.5, y, z], fx.AX['x'], '608-2RS (buy)', (8.0, 22.0, 7.0))
    return p, hw


def build_carriage(grp):
    p = Part(grp, 'Lift carriage + SCARA root', color=PRINT)
    yb, yt = G['carr_y'][1], G['carr_y'][0]
    (fu0, fu1), (fl0, fl1) = cheek_ranges(XL)
    S0 = rest()['S0']
    yU, h = G['yU'], G['box_h']
    y_root = yU + h + 1.0                                  # root plate on a printed Ø11 x 1 spacer on link 1's inner ring
    bodies = []
    for x0, x1 in ((fu0, fu1), (fl0, fl1)):
        bodies.append(side_prism(p, stadium((yb, ZC), (yt, ZC), 17.0), x0, x1, 'lift cheek'))
        bodies.append(side_prism(p, poly([(yb - 17, ZC), (yt + 17, ZC), (yt + 17, ZC + 32), (yb - 17, ZC + 32)]), x0, x1,
                                 'cheek extension'))
    bodies.append(p.box(fl1 - 0.5, fu0 + 0.5, yb - 17, yt + 17, ZC + 19, ZC + 32)[0])          # bridge past the links
    # root: a loft from the round foot over S0 up into the square hanger (no ring where round meets square)
    hx0, hx1, hz0, hz1 = S0[0] - 20, fl1, ZC - 12, S0[1] + 18
    yl = y_root + G['root_loft']
    bodies.append(_loft(p, [_plan_profile(p, y_root, stadium(S0, S0, G['r_plate']), 'root circle'),
                            _plan_profile(p, yl, poly([(hx0, hz0), (hx1, hz0), (hx1, hz1), (hx0, hz1)]), 'hanger square')],
                        'root loft'))
    bodies.append(p.box(hx0, hx1, yl, yt + 17, hz0, hz1)[0])          # hanger behind: starts exactly on the loft top (an overlap left 0.5 mm steps)
    sx = G['spring_x']
    sy, sz = G['spring_hi']
    bodies.append(side_prism(p, stadium((sy, sz), (sy, sz), G['spring_end']['r_ear']), fu0, _ear_out(), 'spring ear'))
    # 45-degree web under the front cheek, down to the bed beside the hanger: the cheek's lower end no longer hangs in
    # the air when printing. Only on the cheek-extension side (z >= ZC): the lower lift link lives at z < ZC and above
    # yb - 17 (its round end), so the web never touches it at any lift.
    yw = yb - 17
    bodies.append(p.prism([0, 0, 0], fx.AX['z'], ZC, ZC + 32, poly([(hx1 - 0.5, yw), (fu1, yw), (fu1 - (yw - y_root), y_root),
                                                                    (hx1 - 0.5, y_root)]), name='front cheek web').bodies.item(0))
    body = _join(p, bodies)
    sh.round_edges(p, body, r=2.0)
    body = p.comp.bRepBodies.item(0)
    # no boss under the root plate (it would lift the disc off the bed): a printed Ø11 x 1 spacer clamps link 1's
    # top bearing inner ring instead, so the carriage prints flat on its root disc
    for y in (yt, yb):
        fork_fits(p, body, [XL, y, ZC], 'x')
        # the back cheek is buried in the hanger: the bolt goes in from the back down a round tunnel (head on the
        # back cheek, a hex key reaches it), the nyloc goes on the open front face
        p.prism([XL, y, ZC], sh.frame_of([-1, 0, 0]), g1.G['half'] + g1.G['gap'] + g1.G['cheek'] - 0.1, XL - hx0 + 1,
                sh.circle(sh.S['m8']['shcs_head'][0] / 2 + 0.75), name='pivot bolt tunnel', op=CUT, targets=[body])
        _teardrop(p, body, [XL, y, ZC], g1.G['half'] + g1.G['gap'] + g1.G['cheek'] - 0.1, XL - hx0 + 1,
                  sh.S['m8']['shcs_head'][0] / 2 + 0.75)
    yp = y_root + G['root_t'] - 6                           # hex pocket floor: the S0 nyloc sits here, locked
    nh = sh.S['m8']['nut_h'] + 0.4
    p.prism(P3(S0, yU + h), fx.AX['y'], -1, yp - yU - h + 0.1, sh.circle(4.25), name='S0 bolt hole', op=CUT, targets=[body])
    p.prism(P3(S0, yp + nh), sh.frame_of([0, 1, 0]), -nh, 0, sh.hexagon(sh.S['m8']['nut_af'] + 0.3), name='S0 nut (hex, locked)',
            op=CUT, targets=[body])
    # access bore from the hanger's top: the nut drops down it into the hex pocket; the bolt comes up from below
    p.prism(P3(S0, yp + nh - 0.1), fx.AX['y'], 0, yt + 17 - yp + 1, sh.circle(7.75), name='S0 access bore',
            op=CUT, targets=[body])                         # round at the bottom: it guides the nut into its pocket
    # above that, widened toward the pivot axis (z = ZC) into a slot: the two bolt-head tunnels cross it, and the
    # round bore beside them left walls of 0.03-0.2 mm where the round shapes grazed; through the slot they cross cleanly
    tr = sh.S['m8']['shcs_head'][0] / 2 + 0.75
    plan_prism(p, stadium((S0[0], S0[1]), (S0[0], ZC), 7.75), yb - tr - 4, yt + 18, 'S0 access slot', op=CUT,
               targets=[body])
    _spring_ear(p, body, [0, sy, sz], fu0, 'hi')
    # the upper pivot's nyloc sits 19 mm from the strut ear: cut the ear off flat on that side, tangent to a 10.5 mm
    # wrench circle round the pivot (a round well here left a crescent of wall thinning to nothing)
    pivot_nut_flat(p, body, fu1, yt)
    carriage_teardrops(p, body, fu0, fu1)
    # S0 hardware + fixed pulley P0 (inside link 1's cavity) move with the carriage
    hw = Part(grp, 'Carriage HW + pulley P0 (buy)', color=HWC)
    _pulley(hw, S0, yU, 'pulley P0 (fixed, printed)')
    _stack(hw, S0, yU)
    _spacer(hw, S0, yU - h - 1.0, yU - h, 'nut spacer Ø11 x 1 (printed)')
    _spacer(hw, S0, yU + h, yU + h + 1.0, 'root spacer Ø11 x 1 (printed)')   # carriage root on link 1's inner ring
    sh.hw_bolt(hw, [S0[0], yU - h - 1.0, S0[1]], sh.frame_of([0, 1, 0]), 55.0, sh.S['m8']['shcs_head'],
               'M8 x 55 socket head (buy)')                 # head under link 1, nyloc locked in the carriage
    sh.hw_nut(hw, [S0[0], yp, S0[1]], sh.frame_of([0, 1, 0]))
    for y in (yt, yb):
        _x_pivot_bolt(hw, [XL, y, ZC], head_back=True)
    _strut_bolt(hw, [0, sy, sz])
    return p, hw


def build_elbow_spool(grp):
    """Elbow: the M8 bolt turns freely in link 1's and link 2's bearings and carries pulleys PA (link 1) and PB
    (link 2), keyed to it; they only translate (belt 1 holds them square)."""
    C = rest()['C']
    hw = Part(grp, 'Elbow spool: bolt + pulleys PA/PB (buy)', color=HWC)
    h = G['box_h']
    _pulley(hw, C, G['yU'], 'pulley PA (printed)')
    _pulley(hw, C, G['yL'], 'pulley PB (printed)')
    _stack(hw, C, G['yU'])
    _stack(hw, C, G['yL'])
    _spacer(hw, C, G['yU'] + h, G['yU'] + h + 1.0, 'head spacer Ø11 x 1 (printed)')
    _spacer(hw, C, G['yL'] + h, G['yU'] - h, 'link spacer Ø11 x 1 (printed)')
    _spacer(hw, C, G['yL'] - h - 1.0, G['yL'] - h, 'nut spacer Ø11 x 1 (printed)')
    L = _bolt(hw, C, G['yU'] + h + 1.0, G['yL'] - h - 1.0, 'C')
    next(b for b in hw.comp.bRepBodies if b.name.startswith('M8 x %d' % L)).name = 'M8 x 100 socket head, cut to %d (buy)' % L
    return hw


def build_end(grp):
    p = Part(grp, 'SCARA end plate + abduction housing', color=PRINT)
    E = rest()['E']
    yL, h = G['yL'], G['box_h']
    y_top = yL - h - 0.5                                    # end plate under link 2
    x0, x1 = G['housing']
    bodies = [plan_prism(p, stadium(E, E, G['r_plate']), y_top - G['end_t'], y_top, 'end plate'),
              plan_prism(p, stadium(E, E, 18.0), GH[1], y_top - G['end_t'] + 0.5, 'drop to the housing'),
              p.prism([0, GH[1], GH[2]], fx.AX['x'], x0, x1, sh.circle(G['housing_r']), name='housing').bodies.item(0)]
    body = _join(p, bodies)
    sh.round_edges(p, body, r=2.0)
    body = p.comp.bRepBodies.item(0)
    bi, bo, bw = sh.S['bearing']
    ax = [0, GH[1], GH[2]]
    p.prism(ax, fx.AX['x'], x0 - 1, x1 + 1, sh.circle(bi / 2 + 2), name='axle bore', op=CUT, targets=[body])
    for a0, a1 in ((x1 - bw, x1 + 1), (x0 - 1, x0 + bw)):
        p.prism(ax, fx.AX['x'], a0, a1, sh.circle(bo / 2 + sh.S['bearing_clear']), name='6806 pocket', op=CUT,
                targets=[body])
    # E: the nyloc sits in a hex pocket in the end plate's top (it can't turn, so P2 stays fixed); link 2 slides on
    # over it and the M8 x 55 goes in from the top of link 2. A Ø11 spacer on the nut carries the clamp to the
    # bearing's inner ring.
    nh = sh.S['m8']['nut_h']
    y_nut = y_top - 0.4                                      # nut top, 0.4 under the plate's top face
    p.prism(P3(E, y_top + 0.1), sh.frame_of([0, -1, 0]), 0, nh + 0.4 + 0.3, sh.hexagon(sh.S['m8']['nut_af'] + 0.3),
            name='E nut (hex, locked)', op=CUT, targets=[body])
    L = 55.0
    y_head = yL + h + 1.0
    p.prism(P3(E, y_nut - nh), fx.AX['y'], -(L - (y_head - y_nut + nh)) - 2, 0.5, sh.circle(4.25), name='E bolt hole',
            op=CUT, targets=[body])                         # room for the bolt's end below the nut
    hw = Part(grp, 'End plate HW + pulley P2 (buy)', color=HWC)
    _pulley(hw, E, yL, 'pulley P2 (fixed, printed)')
    _stack(hw, E, yL)
    _spacer(hw, E, y_nut, yL - h, 'nut spacer Ø11 (printed)')
    _spacer(hw, E, yL + h, y_head, 'head spacer Ø11 x 1 (printed)')
    sh.hw_bolt(hw, [E[0], y_head, E[1]], sh.frame_of([0, -1, 0]), L, sh.S['m8']['shcs_head'], 'M8 x 55 socket head (buy)')
    sh.hw_nut(hw, [E[0], y_nut, E[1]], sh.frame_of([0, -1, 0]))
    return p, hw


def _spring_pts():
    return ([G['spring_x'], G['spring_lo'][0], G['spring_lo'][1]], [G['spring_x'], G['spring_hi'][0], G['spring_hi'][1]])


def build_spring(grp):
    """Gas strut (Motoforti 180 / 120 mm, 22 N, ball-socket ends) in two pieces so it can re-aim and change length
    in a pose: cylinder (+ lower socket) turns about the tower ball; rod (+ upper socket) follows the carriage ball."""
    sp = Part(grp, 'Gas spring cylinder (buy)', color='#3a3f44')
    rp = Part(grp, 'Gas spring rod (buy)', color='#3a3f44')
    a, b = _spring_pts()
    L, d = norm(sub(b, a)), unit(sub(b, a))
    neck = G['spring_end']['neck']                           # eye centre to the body / rod end
    # each end is a flat eyelet in the strut plane (y-z) on the M6 fork bolt; a neck runs to the body / rod
    eo, eh, et = G['spring_end']['eye']
    for part, c, sg in ((sp, a, 1), (rp, b, -1)):
        part.ann(sh.frame_of([1, 0, 0]), c, eo / 2, eh / 2, et, name='eyelet')
        r0 = G['spring_end']['clear'] + 0.5                 # flat tab inside the fork, round neck outside it
        part.cyl(sh.frame_of(d), add(c, mul(d, sg * (r0 + neck) / 2)), 3.0, neck - r0 + 0.5, name='eyelet neck')
    body_l = 0.55 * (L - 2 * neck)
    sp.cyl(sh.frame_of(d), add(a, mul(d, neck + body_l / 2)), 9.0, body_l, name='gas spring body')
    rod_l = G['spring_len'][1] - 2 * neck - body_l + 2       # long enough to stay in the cylinder at full stroke
    rp.cyl(sh.frame_of(d), add(b, mul(d, -(neck + rod_l / 2 - 1))), 4.0, rod_l, name='gas spring rod')
    return sp, rp


# ------------------------------------------------------------------ step-wise build
def _top():
    return next(o for o in fx.design.rootComponent.occurrences if o.component.name == sh.TOP)


def _grp(create=False):
    for o in _top().component.occurrences:
        if o.component.name == NAME:
            return o.component
    return fx.group(_top().component, NAME) if create else None


STEPS = ('start', 'tower', 'lift0', 'lift1', 'carriage', 'link1', 'link2', 'spool', 'end', 'spring', 'finish')
NAMES = dict(tower=['Shoulder tower', 'Tower HW (buy)', 'Strut foot (left backbone)', 'PVC strut + mast (buy)'],
             lift0=['Lift link upper', 'Lift link upper HW (buy)'], lift1=['Lift link lower', 'Lift link lower HW (buy)'],
             carriage=['Lift carriage + SCARA root', 'Carriage HW + pulley P0 (buy)'],
             link1=['SCARA link 1', 'SCARA link 1 HW (buy)'], link2=['SCARA link 2', 'SCARA link 2 HW (buy)'],
             spool=['Elbow spool: bolt + pulleys PA/PB (buy)'],
             end=['SCARA end plate + abduction housing', 'End plate HW + pulley P2 (buy)'], spring=['Gas spring (buy)', 'Gas spring cylinder (buy)', 'Gas spring rod (buy)'])


def build_step(step):
    fx.init()
    if step == 'start':
        STATE.clear()
        fx.group(_top().component, NAME)
        g1.STATE.pop('rest', None)
        for o in _top().component.occurrences:              # hide the v3 (parallelogram) group if present
            if o.component.name == g1.NAME:
                o.isLightBulbOn = False
        return 'group ready'
    grp = _grp()
    g = rest()
    if step == 'finish':
        for b in g1._old_parts():
            b.isLightBulbOn = False
        return {o.component.name: o.component.bRepBodies.count for o in grp.occurrences}
    for o in list(grp.occurrences):
        if o.component.name in NAMES[step]:
            fx.retire(o)
    out = dict(tower=lambda: build_tower(grp),
               lift0=lambda: build_lift_link(grp, 0), lift1=lambda: build_lift_link(grp, 1),
               carriage=lambda: build_carriage(grp),
               link1=lambda: _box_link(grp, 'SCARA link 1', g['S0'], g['C'], G['yU'], None),
               link2=lambda: _box_link(grp, 'SCARA link 2', g['C'], g['E'], G['yL'], None, lid_up=False),
               spool=lambda: (build_elbow_spool(grp),), end=lambda: build_end(grp),
               spring=lambda: build_spring(grp))[step]()
    res = []
    for p in out:
        p.finish()
        for b in p.comp.bRepBodies:
            if '608' in b.name:
                b.appearance = fx.appearance(BRG)
            if 'belt' in b.name:
                b.appearance = fx.appearance(BELT)
        res.append('%s: %d' % (p.comp.name, p.comp.bRepBodies.count))
    return ', '.join(res)


# ------------------------------------------------------------------ posing
def _role(name):
    if name.startswith('Lift link'):
        return 'lift'
    if name.startswith('Gas spring cylinder'):
        return 'spring_cyl'
    if name.startswith('Gas spring rod'):
        return 'spring_rod'
    if name.startswith(('Lift carriage', 'Carriage HW')):
        return 'carriage'
    if name.startswith('SCARA link 1'):
        return 'l1'
    if name.startswith('SCARA link 2'):
        return 'l2'
    if name.startswith('Elbow spool'):
        return 'spool'
    if name.startswith(('SCARA end plate', 'End plate HW')):
        return 'end'
    return None


def pose(d=(0.0, 0.0, 0.0), abd_deg=0.0):
    fx.init()
    g, k = rest(), kin(d)
    topm = _top().transform2
    occs = [o for o in fx.design.rootComponent.allOccurrences if NAME in o.fullPathName and o.component.name != NAME]
    for o in occs:
        role = _role(o.component.name)
        if role is None:
            continue
        if role == 'lift':
            i = 0 if 'upper' in o.component.name else 1
            m = g1._about(g1._rx(k['dphi']), [XL, BASE_Y[i], G['lift_z0']])
        elif role == 'carriage':
            m = fx.matrix(None, k['Tc'])
        elif role == 'l1':
            m = g1._about(g1._ry_plan(k['da1']), P3(g['S0'], G['yU']), k['Tc'])
        elif role == 'l2':
            m = g1._about(g1._ry_plan(k['da2']), P3(g['C'], G['yL']), k['Te'])
        elif role == 'spool':
            m = fx.matrix(None, k['Te'])
        elif role in ('spring_cyl', 'spring_rod'):
            a, b = _spring_pts()
            b2 = add(b, k['Tc'])
            th = math.atan2(b2[2] - a[2], b2[1] - a[1]) - math.atan2(b[2] - a[2], b[1] - a[1])
            R = fx.rot('x', math.degrees(th))
            m = g1._about(R, a, (0, 0, 0) if role == 'spring_cyl' else sub(b2, add(a, fx.mat_vec(R, sub(b, a)))))
        else:
            m = fx.matrix(None, k['TE'])
        m.transformBy(topm)
        o.transform2 = m
    import concept_v4
    concept_v4.move_module(k['TE'], abd_deg)
    return dict(da1=round(math.degrees(k['da1']), 1), da2=round(math.degrees(k['da2']), 1),
                Tc=[round(c, 1) for c in k['Tc']])


# ------------------------------------------------------------------ checks
def check(d=(0.0, 0.0, 0.0), abds=(-60, 0, 20)):
    """Posed clearances between printed parts that are not joined at a pivot, to the torso, and of the arm module."""
    import diag
    fx.init()
    pts = {}
    for o in _grp().occurrences:
        n = o.component.name
        if '(buy)' in n:
            continue
        for v in diag.body_points(n).values():
            pts[n] = pts.get(n, []) + v[::2]
    joined = {frozenset(p) for p in (('Shoulder tower', 'Lift link upper'), ('Shoulder tower', 'Lift link lower'),
                                     ('Lift carriage + SCARA root', 'Lift link upper'),
                                     ('Lift carriage + SCARA root', 'Lift link lower'),
                                     ('Lift carriage + SCARA root', 'SCARA link 1'), ('SCARA link 1', 'SCARA link 2'),
                                     ('SCARA link 2', 'SCARA end plate + abduction housing'))}
    names = sorted(pts)
    grids = {n: diag.grid(pts[n]) for n in names}
    pair = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            lim = 0.6 if frozenset((a, b)) in joined else 5.0          # joined pairs: only report real overlaps
            best = 1e9
            for p in pts[a]:
                dd, t = diag.nearest(grids[b], p, rmax=1)
                if t is not None and dd < best:
                    best = dd
            if best < lim:
                pair.append((a[:24], b[:24], round(best, 1)))
    g_t = diag.grid(diag.torso_points())
    worst = (1e9, None)
    for n, ps in pts.items():
        for p in ps:
            dd, t = diag.nearest(g_t, p)
            if t is None:
                continue
            sd = dd if (dd > 30 or sum((p[i] - t[i]) * t[3 + i] for i in range(3)) >= 0) else -dd
            if sd < worst[0]:
                worst = (round(sd, 1), n[:30])
    H = add(H0, kin(d)['TE'])
    gpts = [p for ps in pts.values() for p in ps
            if not (H[0] - 40 < p[0] < H[0] + 40 and math.hypot(p[1] - H[1], p[2] - H[2]) < 34)]
    g_g = diag.grid(gpts)
    arm = {}
    for pat in ('Yoke', 'Upper-arm link'):
        arm.update(diag.body_points(pat))
    gh = add(GH, kin(d)['TE'])
    armc = {}
    for da in abds:
        best = 1e9
        for ps in arm.values():
            for p in ps[::3]:
                q = diag.rot_x(p, da, gh) if da else p
                dd, t = diag.nearest(g_g, q, rmax=3)
                if t is not None and dd < best:
                    best = dd
        armc['arm %+d' % (-da)] = round(best, 1) if best < 1e8 else '>60'
    return dict(collisions=pair, body=worst, arm=armc)
