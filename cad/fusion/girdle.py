"""Shoulder girdle v3 (real parts), right side.

Lift parallelogram on a mast (shrug up/down) -> double-parallelogram SCARA under its carriage (shoulder forward/back
and in/out, housing never turns) -> abduction housing (2 x 6806 at the old mount block's bearing positions, so the
existing sleeve, yoke, M8 x 100 and washer fit unchanged). Scan frame: mm, X forward, Y up, Z right.

Every pivot is the same: a tongue (26 thick) with a 608-2RS pressed into each face, in a fork (two 7 mm cheeks,
0.5 mm gap), Ø11 inner-ring bosses on the cheeks (washer rule: bore 8 < 11 <= 608 ring land ~12), M8 x 55 socket
head + nyloc. Levels: SCARA link 1 (carriage side) on the UPPER level, link 2 (end-plate side) on the LOWER level,
so the end plate sits straight on the housing and nothing has to pass through the other level.
"""
import math

import adsk.core
import adsk.fusion

import fxlib as fx
from fxlib import Part, JOIN, CUT, add, sub, mul, unit, dot, norm
import shoulder as sh

NAME = 'Shoulder girdle v3 (right)'
PRINT, HWC, BRG, PVC = '#647684', '#c9d2d9', '#d4a017', '#e9eef2'
XL = sh.D['xf']                          # lift plane = backbone pipe axis plane
G = dict(
    pocket=22.1, brg=(8.0, 22.0, 7.0), half=13.0, cheek=7.0, gap=0.5, land=11.0, clear=8.5, web=14.0,
    r_t=17.0, r_f=28.0, post_r=6.0, post_off=24.0, bolt=55.0,
    lift_z0=68.0, lift_L=110.0, lift_y=(1545.0, 1500.0), mast_z=30.0, mast_y=(1424.0, 1565.0),
    yU=1435.0, yL=1390.0,                # SCARA levels (tongue centres): link 1 upper, link 2 lower
    L=65.0, e=42.0, S0a=(-183.0, 95.0), u1=61.0, u2=114.0,   # u1: square to link 1 and away from the mast
    housing=(-215.0, -146.0), housing_r=28.0, Ea_off=(0.0, -12.0),
    spring_x=-243.0, spring_lo=(1460.0, 50.0), spring_hi=(1535.0, 170.0),
)
GH = sh.GH
H0 = [(G['housing'][0] + G['housing'][1]) / 2, GH[1], GH[2]]
STATE = {}


# ------------------------------------------------------------------ geometry
def P3(pl, y):
    return [pl[0], y, pl[1]]


def pl_add(a, b, s=1.0):
    return (a[0] + s * b[0], a[1] + s * b[1])


def dirv(deg):
    return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))


def ang(v):
    return math.atan2(v[1], v[0])


def ik(S, E, branch=None):
    L = G['L']
    dx, dz = E[0] - S[0], E[1] - S[1]
    d = math.hypot(dx, dz)
    if d > 2 * L - 0.5 or d < 1:
        raise RuntimeError('SCARA out of reach (%.0f mm, max %.0f)' % (d, 2 * L))
    a0, c = math.atan2(dz, dx), math.acos(d / (2 * L))
    cands = {s: (S[0] + L * math.cos(a0 + s * c), S[1] + L * math.sin(a0 + s * c)) for s in (1, -1)}
    if branch is None:
        branch = min(cands, key=lambda s: cands[s][0])     # rest: elbow behind (smaller x), away from the back
    return cands[branch], branch


def rest():
    if 'rest' in STATE:
        return STATE['rest']
    u1, u2 = dirv(G['u1']), dirv(G['u2'])
    S0a = G['S0a']
    S0b = pl_add(S0a, u1, G['e'])
    Ea = (H0[0] + G['Ea_off'][0], H0[2] + G['Ea_off'][1])
    Eb = pl_add(Ea, u2, G['e'])
    Ca, br = ik(S0a, Ea)
    g = dict(S0a=S0a, S0b=S0b, Ea=Ea, Eb=Eb, Ca=Ca, Cb=pl_add(Ca, u1, G['e']), Cb2=pl_add(Ca, u2, G['e']),
             branch=br, u1=u1, u2=u2)
    STATE['rest'] = g
    return g


def kin(d):
    """Pose for a girdle offset d (mm): returns placements of every moving part."""
    g = rest()
    L = G['lift_L']
    th = math.asin(max(-0.95, min(0.95, d[1] / L)))
    Tc = [0.0, L * math.sin(th), L * (math.cos(th) - 1)]
    S0a = (g['S0a'][0], g['S0a'][1] + Tc[2])
    Ea = (g['Ea'][0] + d[0], g['Ea'][1] + d[2])
    Ca, _ = ik(S0a, Ea, g['branch'])
    da1 = ang((Ca[0] - S0a[0], Ca[1] - S0a[1])) - ang((g['Ca'][0] - g['S0a'][0], g['Ca'][1] - g['S0a'][1]))
    da2 = ang((Ea[0] - Ca[0], Ea[1] - Ca[1])) - ang((g['Ea'][0] - g['Ca'][0], g['Ea'][1] - g['Ca'][1]))
    Te = [Ca[0] - g['Ca'][0], Tc[1], Ca[1] - g['Ca'][1]]
    TE = [d[0], Tc[1], d[2]]
    return dict(th=th, Tc=Tc, da1=da1, da2=da2, Te=Te, TE=TE, Ca=Ca, S0a=S0a, Ea=Ea)


def _rx(t):
    c, s = math.cos(t), math.sin(t)
    return [[1, 0, 0], [0, c, s], [0, -s, c]]


def _ry_plan(a):
    """Rotate in plan by a (from +X toward +Z) about a vertical axis."""
    c, s = math.cos(a), math.sin(a)
    return [[c, 0, -s], [0, 1, 0], [s, 0, c]]


def _about(R, c, t=(0, 0, 0)):
    return fx.matrix(R, add(sub(c, fx.mat_vec(R, c)), t))


# ------------------------------------------------------------------ sketch helpers
def stadium(a, b, r):
    """Outline of two circles (a, b in sketch-plane coords, mm) joined by tangent lines; a == b -> circle."""
    def draw(sk, to):
        if math.hypot(b[0] - a[0], b[1] - a[1]) < 0.01:
            sk.sketchCurves.sketchCircles.addByCenterRadius(to(*a), r / 10.0)
            return
        dd = unit([b[0] - a[0], b[1] - a[1], 0])
        n = (-dd[1], dd[0])
        pa1, pb1 = (a[0] + r * n[0], a[1] + r * n[1]), (b[0] + r * n[0], b[1] + r * n[1])
        pb2, pa2 = (b[0] - r * n[0], b[1] - r * n[1]), (a[0] - r * n[0], a[1] - r * n[1])
        ln, ar = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
        l1 = ln.addByTwoPoints(to(*pa1), to(*pb1))
        l2 = ln.addByTwoPoints(to(*pb2), to(*pa2))
        ar.addByThreePoints(l1.endSketchPoint, to(b[0] + r * dd[0], b[1] + r * dd[1]), l2.startSketchPoint)
        ar.addByThreePoints(l2.endSketchPoint, to(a[0] - r * dd[0], a[1] - r * dd[1]), l1.startSketchPoint)
    return draw


def poly(pts):
    def draw(sk, to):
        q = [to(*p) for p in pts]
        ln = sk.sketchCurves.sketchLines
        for i in range(len(q)):
            ln.addByTwoPoints(q[i], q[(i + 1) % len(q)])
    return draw


PLAN = fx.AX['y']                         # sketch (u, v) = (x, z), normal +Y
SIDE = fx.AX['x']                         # sketch (u, v) = (y, z), normal +X


def plan_prism(p, outline, y0, y1, name, op=fx.NEW, targets=None):
    f = p.prism([0, 0, 0], PLAN, y0, y1, outline, name=name, op=op, targets=targets)
    return f.bodies.item(0) if op == fx.NEW else None


def side_prism(p, outline, x0, x1, name, op=fx.NEW, targets=None):
    f = p.prism([0, 0, 0], SIDE, x0, x1, outline, name=name, op=op, targets=targets)
    return f.bodies.item(0) if op == fx.NEW else None


def _join(p, bodies):
    return p.join(bodies)[0] if len(bodies) > 1 else bodies[0]


# ------------------------------------------------------------------ pivot features
def tongue_fits(p, body, c, axis):
    """Bearing pockets in both faces + web hole, at pivot c, axis 'x' or 'y'."""
    fr, h = fx.AX[axis], G['half']
    bw = G['brg'][2]
    for z0, z1 in ((h - bw, h + 1), (-h - 1, -h + bw)):
        p.prism(c, fr, z0, z1, sh.circle(G['pocket'] / 2), name='608 pocket', op=CUT, targets=[body])
    p.prism(c, fr, -h - 1, h + 1, sh.circle(G['web'] / 2), name='web hole', op=CUT, targets=[body])


def fork_fits(p, body, c, axis):
    """Inner-ring bosses on both cheeks + the M8 clearance hole."""
    fr, h, g = fx.AX[axis], G['half'], G['gap']
    for z0, z1 in ((h, h + g + 0.2), (-h - g - 0.2, -h)):
        p.prism(c, fr, z0, z1, sh.circle(G['land'] / 2), name='inner-ring boss', op=JOIN, targets=[body])
    p.prism(c, fr, -h - g - G['cheek'] - 1, h + g + G['cheek'] + 1, sh.circle(G['clear'] / 2), name='M8 hole',
            op=CUT, targets=[body])


def cheek_ranges(level):
    h, g, t = G['half'], G['gap'], G['cheek']
    return (level + h + g, level + h + g + t), (level - h - g - t, level - h - g)


def pivot_hw(hw, c, axis):
    """Two 608s, an M8 x 55 (head on the + side) and a nyloc, for a pivot at c."""
    a = [1.0, 0, 0] if axis == 'x' else [0, 1.0, 0]
    fr = fx.AX[axis]
    bi, bo, bw = G['brg']
    for s in (1, -1):
        sh.hw_bearing(hw, add(c, mul(a, s * (G['half'] - bw / 2))), fr, '608-2RS (buy)', (bi, bo, bw))
    top = G['half'] + G['gap'] + G['cheek']
    down = sh.frame_of(mul(a, -1))
    sh.hw_bolt(hw, add(c, mul(a, top)), down, G['bolt'], sh.S['m8']['shcs_head'], 'M8 x 55 socket head (buy)')
    sh.hw_nut(hw, add(c, mul(a, -top)), down)


# ------------------------------------------------------------------ parts
def _bar_plan(grp, name, a, b, level):
    p = Part(grp, name, color=PRINT)
    h = G['half']
    body = plan_prism(p, stadium(a, b, G['r_t']), level - h, level + h, 'bar')
    sh.round_edges(p, body, r=2.0)
    for c in (a, b):
        tongue_fits(p, p.comp.bRepBodies.item(0), P3(c, level), 'y')
    return p


def _fork_layers_plan(p, pts_pairs, level, name, posts=()):
    """Cheek layers (stadium per pair of plan points, r_f) above and below a tongue level, + posts between them."""
    bodies = []
    (u0, u1), (l0, l1) = cheek_ranges(level)
    for a, b in pts_pairs:
        bodies.append(plan_prism(p, stadium(a, b, G['r_f']), u0, u1, name + ' upper cheek'))
        bodies.append(plan_prism(p, stadium(a, b, G['r_f']), l0, l1, name + ' lower cheek'))
    for q in posts:
        bodies.append(plan_prism(p, stadium(q, q, G['post_r']), l0, u1, name + ' post'))
    return bodies


def build_base(grp):
    p = Part(grp, 'Lift base (on the mast)', color=PRINT)
    yb, yt = G['lift_y'][1], G['lift_y'][0]
    z0, zm = G['lift_z0'], G['mast_z']
    bodies = [plan_prism(p, stadium((XL, zm), (XL, zm), 16.0), 1427, G['mast_y'][1] + 3, 'mast socket boss')]
    (fu0, fu1), (fl0, fl1) = cheek_ranges(XL)             # cheeks along X (front = +)
    for x0, x1 in ((fu0, fu1), (fl0, fl1)):
        bodies.append(side_prism(p, stadium((yb, z0), (yt, z0), G['r_t']), x0, x1, 'lift cheek'))
        bodies.append(side_prism(p, poly([(1440, zm), (yt + 17, zm), (yt + 17, z0), (1440, z0)]), x0, x1,
                                 'lift cheek web'))
    sx = G['spring_x']; sy, sz = G['spring_lo']
    bodies.append(side_prism(p, stadium((sy, sz), (sy, sz), 11.0), sx - 9, fl1, 'spring ear'))
    body = _join(p, bodies)
    sh.round_edges(p, body, r=2.0)
    body = p.comp.bRepBodies.item(0)
    p.prism([XL, 0, zm], fx.AX['y'], 1420, G['mast_y'][1] + 1, sh.circle(sh.S['pipe_bore'] / 2), name='mast socket',
            op=CUT, targets=[body])
    for y in (1440.0, 1458.0):                              # two #4 pipe screws from behind
        p.prism([XL - 5, y, zm], fx.AX['x'], -20, 0, sh.circle(sh.S['pipe_screw']['hole'] / 2), name='pipe screw hole',
                op=CUT, targets=[body])
    for y in (yt, yb):
        fork_fits(p, body, [XL, y, z0], 'x')
    p.prism([0, sy, sz], fx.AX['x'], sx - 10, fl1 + 1, sh.circle(4.25), name='spring pin hole', op=CUT, targets=[body])
    return p


def build_lift_link(grp, y, name):
    p = Part(grp, name, color=PRINT)
    h = G['half']
    body = side_prism(p, stadium((y, G['lift_z0']), (y, G['lift_z0'] + G['lift_L']), G['r_t']), XL - h, XL + h, 'link')
    sh.round_edges(p, body, r=2.0)
    for z in (G['lift_z0'], G['lift_z0'] + G['lift_L']):
        tongue_fits(p, p.comp.bRepBodies.item(0), [XL, y, z], 'x')
    return p


def build_carriage(grp, g):
    p = Part(grp, 'Lift carriage + SCARA root', color=PRINT)
    yb, yt = G['lift_y'][1], G['lift_y'][0]
    zc = G['lift_z0'] + G['lift_L']
    (fu0, fu1), (fl0, fl1) = cheek_ranges(XL)
    bodies = []
    for x0, x1 in ((fu0, fu1), (fl0, fl1)):
        bodies.append(side_prism(p, stadium((yb, zc), (yt, zc), G['r_t']), x0, x1, 'lift cheek'))
        bodies.append(side_prism(p, poly([(yb - 17, zc), (yt + 17, zc), (yt + 17, zc + 30), (yb - 17, zc + 30)]), x0, x1,
                                 'cheek extension'))
    # bridge joining the two cheeks beyond the links' rounded ends (they reach zc + 17): the back cheek had nothing
    # else holding it
    bodies.append(p.box(fl1 - 0.5, fu0 + 0.5, yb - 17, yt + 17, zc + G['r_t'] + 2, zc + 30)[0])
    (uu0, uu1), (ul0, ul1) = cheek_ranges(G['yU'])
    # front plate: from the lift cheeks forward of the lift links, down to the SCARA root's upper cheek
    front = poly([(yt + 17, 82), (yt + 17, zc + 17), (yb - 17, zc + 17), (yb - 17, 118), (uu0, 118), (uu0, 82)])
    bodies.append(side_prism(p, front, fu1 - 0.5, fu1 + 14, 'front plate'))
    w = unit([g['S0a'][0] - g['Ca'][0], 0, g['S0a'][1] - g['Ca'][1]])        # away from link 1
    posts = [pl_add(q, (w[0], w[2]), G['post_off']) for q in (g['S0a'], g['S0b'])]
    bodies += _fork_layers_plan(p, [(g['S0a'], g['S0b'])], G['yU'], 'SCARA root', posts)
    sx = G['spring_x']; sy, sz = G['spring_hi']
    bodies.append(side_prism(p, stadium((sy, sz), (sy, sz), 11.0), sx - 9, fl1, 'spring ear'))
    bodies.append(side_prism(p, poly([(sy - 11, sz), (sy + 11, sz), (yt, zc), (yb, zc)]), sx - 9, fl1, 'ear web'))
    body = _join(p, bodies)
    sh.round_edges(p, body, r=2.0)
    body = p.comp.bRepBodies.item(0)
    for y in (yt, yb):
        fork_fits(p, body, [XL, y, zc], 'x')
    for q in (g['S0a'], g['S0b']):
        fork_fits(p, body, P3(q, G['yU']), 'y')
    p.prism([0, sy, sz], fx.AX['x'], sx - 10, fl1 + 1, sh.circle(4.25), name='spring pin hole', op=CUT, targets=[body])
    return p


def build_elbow(grp, g):
    p = Part(grp, 'SCARA elbow plate', color=PRINT)
    wU = unit([g['Ca'][0] - g['S0a'][0], 0, g['Ca'][1] - g['S0a'][1]])     # upper level: away from link 1's root
    wL = unit([g['Ca'][0] - g['Ea'][0], 0, g['Ca'][1] - g['Ea'][1]])       # lower level: away from the end plate
    bodies = _fork_layers_plan(p, [(g['Ca'], g['Cb'])], G['yU'], 'upper',
                               [pl_add(q, (wU[0], wU[2]), G['post_off']) for q in (g['Ca'], g['Cb'])])
    bodies += _fork_layers_plan(p, [(g['Ca'], g['Cb2'])], G['yL'], 'lower',
                                [pl_add(q, (wL[0], wL[2]), G['post_off']) for q in (g['Ca'], g['Cb2'])])
    (_, _), (ul0, _) = cheek_ranges(G['yU'])
    (_, lu1), (_, _) = cheek_ranges(G['yL'])
    bodies.append(plan_prism(p, stadium(g['Ca'], g['Ca'], G['r_f']), lu1 - 0.5, ul0 + 0.5, 'level filler'))
    body = _join(p, bodies)
    sh.round_edges(p, body, r=1.5)
    body = p.comp.bRepBodies.item(0)
    for q in (g['Ca'], g['Cb']):
        fork_fits(p, body, P3(q, G['yU']), 'y')
    for q in (g['Ca'], g['Cb2']):
        fork_fits(p, body, P3(q, G['yL']), 'y')
    return p


def build_end(grp, g):
    p = Part(grp, 'SCARA end plate + abduction housing', color=PRINT)
    wE = unit([g['Ea'][0] - g['Ca'][0], 0, g['Ea'][1] - g['Ca'][1]])       # away from link 2
    bodies = _fork_layers_plan(p, [(g['Ea'], g['Eb'])], G['yL'], 'end',
                               [pl_add(q, (wE[0], wE[2]), G['post_off']) for q in (g['Ea'], g['Eb'])])
    (_, _), (ll0, _) = cheek_ranges(G['yL'])
    x0, x1 = G['housing']
    bodies.append(plan_prism(p, stadium(g['Ea'], g['Eb'], 20.0), GH[1], ll0 + 0.5, 'drop to the housing'))
    bodies.append(p.prism([0, GH[1], GH[2]], fx.AX['x'], x0, x1, sh.circle(G['housing_r']), name='housing').bodies.item(0))
    body = _join(p, bodies)
    sh.round_edges(p, body, r=2.0)
    body = p.comp.bRepBodies.item(0)
    for q in (g['Ea'], g['Eb']):
        fork_fits(p, body, P3(q, G['yL']), 'y')
    bi, bo, bw = sh.S['bearing']
    ax = [0, GH[1], GH[2]]
    p.prism(ax, fx.AX['x'], x0 - 1, x1 + 1, sh.circle(bi / 2 + 2), name='axle bore', op=CUT, targets=[body])
    for a0, a1 in ((x1 - bw, x1 + 1), (x0 - 1, x0 + bw)):
        p.prism(ax, fx.AX['x'], a0, a1, sh.circle(bo / 2 + sh.S['bearing_clear']), name='6806 pocket', op=CUT,
                targets=[body])
    return p


def build_hw(grp, g):
    hw = Part(grp, 'HW girdle (buy)', color=HWC)
    zc = G['lift_z0'] + G['lift_L']
    for y in G['lift_y']:
        for z in (G['lift_z0'], zc):
            pivot_hw(hw, [XL, y, z], 'x')
    for q, lv in ((g['S0a'], 'yU'), (g['S0b'], 'yU'), (g['Ca'], 'yU'), (g['Cb'], 'yU'), (g['Ca'], 'yL'),
                  (g['Cb2'], 'yL'), (g['Ea'], 'yL'), (g['Eb'], 'yL')):
        pivot_hw(hw, P3(q, G[lv]), 'y')
    pv = Part(grp, 'PVC mast extension (buy)', color=PVC)
    pv.ann(fx.AX['y'], [XL, sum(G['mast_y']) / 2, G['mast_z']], sh.S['pipe_od'] / 2, 7.75, G['mast_y'][1] - G['mast_y'][0])
    return hw, pv


def build_spring(grp):
    sp = Part(grp, 'Gas spring (buy)', color='#3a3f44')
    a = [G['spring_x'], G['spring_lo'][0], G['spring_lo'][1]]
    b = [G['spring_x'], G['spring_hi'][0], G['spring_hi'][1]]
    L = norm(sub(b, a))
    d = unit(sub(b, a))
    sp.cyl(sh.frame_of(d), add(a, mul(d, 0.30 * L)), 9.0, 0.5 * L, name='gas spring body')
    sp.cyl(sh.frame_of(d), add(a, mul(d, 0.75 * L)), 4.0, 0.45 * L, name='gas spring rod')
    for c in (a, b):
        sp.cyl('x', c, 7.0, 10.0, name='eye')
    return sp


# ------------------------------------------------------------------ assembly
def _top():
    return next(o for o in fx.design.rootComponent.occurrences if o.component.name == sh.TOP)


def _old_parts():
    """The old right mount block and the PVC beam + diagonal that ran to it (hidden while v3 is shown)."""
    root = fx.design.rootComponent
    for o in root.allOccurrences:
        if o.component.name == 'Abduction mount blocks':
            for b in o.component.bRepBodies:
                if b.name.endswith(' R'):
                    yield b
        if o.component.name.startswith('PVC pipes'):
            for b in o.component.bRepBodies:
                bb = b.createForAssemblyContext(o).boundingBox
                # the right beam and diagonal reach out to the old block (scan z ~150); the right backbone stays
                # within z 19..41. Test the outer end (scan z = -10 x Fusion y), not the centre: the diagonal's
                # centre sits at z 98 and slipped through a centre test.
                if bb.minPoint.y < -10 and (bb.minPoint.z + bb.maxPoint.z) / 2 > 115:
                    yield b


def build():
    fx.init()
    STATE.pop('rest', None)
    g = rest()
    top = _top().component
    grp = fx.group(top, NAME)
    parts = dict(base=build_base(grp))
    for i, y in enumerate(G['lift_y']):
        parts['lift%d' % i] = build_lift_link(grp, y, 'Lift link %s' % ('upper' if i == 0 else 'lower'))
    parts['carriage'] = build_carriage(grp, g)
    parts['l1a'] = _bar_plan(grp, 'SCARA link 1a', g['S0a'], g['Ca'], G['yU'])
    parts['l1b'] = _bar_plan(grp, 'SCARA link 1b', g['S0b'], g['Cb'], G['yU'])
    parts['elbow'] = build_elbow(grp, g)
    parts['l2a'] = _bar_plan(grp, 'SCARA link 2a', g['Ca'], g['Ea'], G['yL'])
    parts['l2b'] = _bar_plan(grp, 'SCARA link 2b', g['Cb2'], g['Eb'], G['yL'])
    parts['end'] = build_end(grp, g)
    parts['hw'], parts['pvc'] = build_hw(grp, g)
    parts['spring'] = build_spring(grp)
    for p in parts.values():
        p.finish()
    for b in parts['hw'].comp.bRepBodies:
        if '608' in b.name:
            b.appearance = fx.appearance(BRG)
    for b in _old_parts():
        b.isLightBulbOn = False
    STATE['parts'] = {k: p.occ.fullPathName for k, p in parts.items()}
    printed = {k: p.comp.bRepBodies.count for k, p in parts.items() if k not in ('hw', 'pvc', 'spring')}
    return dict(g={k: [round(c, 1) for c in v] if isinstance(v, tuple) else v for k, v in g.items()},
                bodies=printed)


# ------------------------------------------------------------------ step-wise build (one part per MCP call)
STEPS = ('start', 'base', 'lift0', 'lift1', 'carriage', 'l1a', 'l1b', 'elbow', 'l2a', 'l2b', 'end', 'hw', 'spring',
         'finish')


def _grp(create=False):
    top = _top().component
    for o in top.occurrences:
        if o.component.name == NAME:
            return o.component
    return fx.group(top, NAME) if create else None


def build_step(step):
    """Build one part (see STEPS). 'start' replaces the group; 'finish' hides the old block and reports bodies."""
    fx.init()
    if step == 'start':
        STATE.pop('rest', None)
        rest()
        fx.group(_top().component, NAME)                    # replaces an existing group
        return 'group ready'
    g = rest()
    grp = _grp()
    builders = dict(
        base=lambda: build_base(grp),
        lift0=lambda: build_lift_link(grp, G['lift_y'][0], 'Lift link upper'),
        lift1=lambda: build_lift_link(grp, G['lift_y'][1], 'Lift link lower'),
        carriage=lambda: build_carriage(grp, g),
        l1a=lambda: _bar_plan(grp, 'SCARA link 1a', g['S0a'], g['Ca'], G['yU']),
        l1b=lambda: _bar_plan(grp, 'SCARA link 1b', g['S0b'], g['Cb'], G['yU']),
        elbow=lambda: build_elbow(grp, g),
        l2a=lambda: _bar_plan(grp, 'SCARA link 2a', g['Ca'], g['Ea'], G['yL']),
        l2b=lambda: _bar_plan(grp, 'SCARA link 2b', g['Cb2'], g['Eb'], G['yL']),
        end=lambda: build_end(grp, g),
        spring=lambda: build_spring(grp),
    )
    if step == 'hw':
        hw, pv = build_hw(grp, g)
        hw.finish()
        pv.finish()
        for b in hw.comp.bRepBodies:
            if '608' in b.name:
                b.appearance = fx.appearance(BRG)
        return 'hw: %d bodies' % hw.comp.bRepBodies.count
    if step == 'finish':
        for b in _old_parts():
            b.isLightBulbOn = False
        return {o.component.name: o.component.bRepBodies.count for o in grp.occurrences}
    names = dict(base='Lift base (on the mast)', lift0='Lift link upper', lift1='Lift link lower',
                 carriage='Lift carriage + SCARA root', l1a='SCARA link 1a', l1b='SCARA link 1b',
                 elbow='SCARA elbow plate', l2a='SCARA link 2a', l2b='SCARA link 2b',
                 end='SCARA end plate + abduction housing', spring='Gas spring (buy)')
    for o in list(grp.occurrences):                         # rebuilding a part replaces it
        if o.component.name == names[step]:
            o.deleteMe()
    p = builders[step]()
    p.finish()
    return '%s: %d body(s)' % (p.comp.name, p.comp.bRepBodies.count)


# ------------------------------------------------------------------ posing
MOVERS = {'Lift link upper': 'lift', 'Lift link lower': 'lift', 'Lift carriage + SCARA root': 'carriage',
          'SCARA link 1a': 'l1a', 'SCARA link 1b': 'l1b', 'SCARA elbow plate': 'elbow', 'SCARA link 2a': 'l2a',
          'SCARA link 2b': 'l2b', 'SCARA end plate + abduction housing': 'end'}


def pose(d=(0.0, 0.0, 0.0), abd_deg=0.0):
    """Place every girdle part (and the shoulder module) for girdle offset d. Hardware and the spring are modelled
    at rest only, so they are hidden in any other pose."""
    fx.init()
    g, k = rest(), kin(d)
    topm = _top().transform2
    at_rest = max(abs(c) for c in d) < 1e-6
    # transform2 can only be set on occurrence proxies from the root (the group's own .occurrences are refused)
    occs = [o for o in fx.design.rootComponent.allOccurrences if NAME in o.fullPathName and o.component.name != NAME]
    for o in occs:
        name = o.component.name
        role = MOVERS.get(name)
        if role is None:
            if not name.startswith('Lift base') and not name.startswith('PVC'):
                o.isLightBulbOn = at_rest
            continue
        if role == 'lift':
            y = G['lift_y'][0] if 'upper' in name else G['lift_y'][1]
            m = _about(_rx(k['th']), [XL, y, G['lift_z0']])
        elif role == 'carriage':
            m = fx.matrix(None, k['Tc'])
        elif role in ('l1a', 'l1b'):
            m = _about(_ry_plan(k['da1']), P3(g['S0a'] if role == 'l1a' else g['S0b'], G['yU']), k['Tc'])
        elif role == 'elbow':
            m = fx.matrix(None, k['Te'])
        elif role in ('l2a', 'l2b'):
            m = _about(_ry_plan(k['da2']), P3(g['Ca'] if role == 'l2a' else g['Cb2'], G['yL']), k['Te'])
        else:
            m = fx.matrix(None, k['TE'])
        m.transformBy(topm)
        o.transform2 = m
    import concept_v4
    concept_v4.move_module(k['TE'], abd_deg)
    return dict(TE=[round(c, 1) for c in k['TE']], da1=round(math.degrees(k['da1']), 1),
                da2=round(math.degrees(k['da2']), 1), Tc=[round(c, 1) for c in k['Tc']])


def restore_pose():
    pose((0.0, 0.0, 0.0), 0.0)
    import concept_v4
    m = concept_v4.STATE.pop('abd_rest', None)
    if m:
        mm = adsk.core.Matrix3D.create()
        mm.setWithArray(m)
        concept_v4._abd().transform2 = mm
    return 'at rest'


# ------------------------------------------------------------------ checks
def _pivots_posed(d):
    """(centre, axis, part-name prefixes) of every pivot in the posed state."""
    g, k = rest(), kin(d)
    zc = G['lift_z0'] + G['lift_L']
    out = []
    for y in G['lift_y']:
        out.append(([XL, y, G['lift_z0']], [1, 0, 0], ('Lift base', 'Lift link')))
        out.append((add([XL, y, zc], k['Tc']), [1, 0, 0], ('Lift carriage', 'Lift link')))
    for q in ('S0a', 'S0b'):
        out.append((add(P3(g[q], G['yU']), k['Tc']), [0, 1, 0], ('Lift carriage', 'SCARA link 1')))
    for q, lv, pr in (('Ca', 'yU', 'SCARA link 1'), ('Cb', 'yU', 'SCARA link 1'), ('Ca', 'yL', 'SCARA link 2'),
                      ('Cb2', 'yL', 'SCARA link 2')):
        out.append((add(P3(g[q], G[lv]), k['Te']), [0, 1, 0], ('SCARA elbow', pr)))
    for q in ('Ea', 'Eb'):
        out.append((add(P3(g[q], G['yL']), k['TE']), [0, 1, 0], ('SCARA end', 'SCARA link 2')))
    return out


def _near_pivot(p, pivots, na, nb):
    for c, a, prs in pivots:
        if any(na.startswith(x) for x in prs) and any(nb.startswith(x) for x in prs):
            v = sub(p, c)
            al = dot(v, a)
            if abs(al) < 26 and norm(sub(v, mul(a, al))) < 30:
                return True
    return False


def check(d=(0.0, 0.0, 0.0), abds=(-60, 0, 20)):
    """Posed clearances: part to part (pivot neighbourhoods excluded), parts to the torso (signed), and the arm
    module (yoke, link) against the girdle while the arm is raised (abd < 0) or lowered."""
    import diag
    fx.init()
    pts = {}
    for o in _grp().occurrences:
        n = o.component.name
        if n in MOVERS or n.startswith('Lift base'):
            for k_, v in diag.body_points(n).items():
                pts[n] = pts.get(n, []) + v[::2]
    pv = _pivots_posed(d)
    names = sorted(pts)
    grids = {n: diag.grid(pts[n]) for n in names}
    pair = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            best = 1e9
            for p in pts[a]:
                if _near_pivot(p, pv, a, b):
                    continue
                dd, t = diag.nearest(grids[b], p, rmax=1)
                if t is not None and dd < best:
                    best = dd
            if best < 5:
                pair.append((a[:24], b[:24], round(best, 1)))
    g_t = diag.grid(diag.torso_points())
    worst = (1e9, None)
    for n, ps in pts.items():
        for p in ps:
            dd, t = diag.nearest(g_t, p)
            if t is None:
                continue
            # the torso reference is cut open at the neck (y ~1458): above/near the cut the nearest vertex's normal
            # points sideways and the inside/outside sign flips, so the sign is only trusted close to the skin
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
