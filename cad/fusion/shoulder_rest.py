"""Right shoulder rest (real parts): a chain of hinged blades from the shoulder tower over the top of the shoulder.

Layout from shoulder_rest_layout.py (shoulder_rest_layout.json): all hinge axes parallel, tilted 25 deg down toward
the arm (the shoulder top's sideways slope). Pieces, back to front:
  BRACKET (bolted to the tower's front plate) -> ROOT ARM (bridges to the back of the shoulder) -> BLADE 1 -> 2 -> 3
  (each wider than the last, 58 -> 106 mm) -> strap tab + buckle at the front end.
Each joint is one continuous hinge: two end knuckles on the rear piece, one long middle knuckle on the front piece,
one M6 x 70 steel clevis pin (head + R-clip) through all three. The chain drapes to the wearer's shoulder
and the front strap's tension holds it. Under each blade: hook-and-loop + a 1/2" foam pad,
smaller than the blade (removable, washable). Back pads (same build) on the body side of the three frame nodes.
Scan frame: mm, X forward, Y up, Z right.
"""
import json
import math
import os

import adsk.core
import adsk.fusion

import fxlib as fx
from fxlib import Part, JOIN, CUT, add, sub, mul, unit, cross, norm
import shoulder as sh

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = 'Shoulder rest (right)'
PRINT, HWC, FOAM, VELCRO, BUCKLE = '#647684', '#c9d2d9', '#3f6f8f', '#1e2226', '#2a2d31'
P = dict(t=8.0, k=12.0, g=0.5, r_k=6.5, end_gap=8.0, hole=6.3, velcro=1.5, pad=12.7, inset=5.0,
         pin=dict(d=6.0, head=(10.0, 2.0), clip=3.0),    # M6 x 70 clevis pin + R-clip (6-pack): one per joint, full width
         hinge_w=64.0,                                   # every hinge 64 wide: all pins M6 x 70
         gusset=8.0,                                      # knuckle gusset runs this far past the plate's end
         t_root=9.0,                                     # root arm spans air: a 9 mm plate
         hexcell=dict(af=9.0, wall=1.8, depth=3.0, depth_root=4.0, edge=3.0),   # honeycomb pockets on top
         tab=(34.0, 24.0), slot=(26.0, 5.0), buckle=(34.0, 44.0, 12.0),
         x_face=-190.34,                                  # shoulder tower front plate (front fork cheek)
         bracket=dict(s=6.0, t=(-14.0, 10.0), lobe=(8.0, 36.0), plate=6.0,   # band for the arms + a lobe for the slot     # turns on a Ø16 boss on the tower (centred under the hinge);
                      boss=(16.0, 5.5, 0.4), slot=dict(r=30.0, sweep=15.0, w=6.6, phi=50.0),   # 1 arc slot + an M6 thumb screw lock it
                      backing=3.0),  # top clears the gas spring; bolts inside the tower's slanted edge
         nut_trap=(8.1, 4.2),                             # M5 nut (8 AF): hex pocket in the tower plate's inside face
         m6_nut=(10.0, 5.0), thumb=dict(len=16.0, head=(16.0, 6.0)),   # M6 x 16 knurled thumb screw + M6 nut
         back_pad=dict(dz=45.0, w=60.0, edge=3.0))
# Print: blades, root arm and bracket print flat side down (pad side / tower side). The plate's underside is flush
# with the knuckles' underside (hinge axis r_k above it); each knuckle sits on a gusset: no supports, no overhangs.
LAY = json.load(open(os.path.join(HERE, 'shoulder_rest_layout.json')))
O, N, A = LAY['origin'], LAY['N'], LAY['A']
X = [1.0, 0.0, 0.0]


def xyz(u, v, w=0.0):
    return add(add([u, O[1], O[2]], mul(N, v)), mul(A, w))


def poly(pts):
    def draw(sk, to):
        ln = sk.sketchCurves.sketchLines
        q = [to(*c) for c in pts]
        for i in range(len(q)):
            ln.addByTwoPoints(q[i], q[(i + 1) % len(q)])
    return draw


def zones(rng, outer):
    """Knuckle zones (w) of a joint whose width is rng: the rear piece has the two end knuckles, the front piece one
    long middle knuckle. One M6 clevis pin runs through all three: a continuous hinge line, free to turn."""
    a, b = hinge(rng)
    k, g = P['k'], P['g']
    return [(a, a + k), (b - k, b)] if outer else [(a + k + g, b - k - g)]


def hinge(rng):
    """Every hinge is the same width (one clevis pin length to buy), centred on the joint; the blades are wider."""
    c = (rng[0] + rng[1]) / 2
    return c - P['hinge_w'] / 2, c + P['hinge_w'] / 2


def frame(pc):
    """Plate frame of a piece: origin on its rear hinge line (w = 0), ex along the chain, ey = hinge axis, ez up."""
    R, F = xyz(*pc['R']), xyz(*pc['F'])
    t = unit(sub(F, R))
    return R, (t, A, cross(A, t)), norm(sub(F, R))


def _knuckles(p, c, zs, name):
    out = []
    for w0, w1 in zs:
        out.append(p.prism(c, sh.frame_of(A), w0, w1, sh.circle(P['r_k']), name=name).bodies.item(0))
    return out


def _gussets(p, c, fr, zs, s0, sgn, name):
    """D-profile under and behind each knuckle: flat underneath (flush with the plate's underside), up to the top of
    the knuckle at the hinge, sloping down onto the plate's top past its end. sgn +1: the plate is on the + side."""
    rk, t, e, gl = P['r_k'], P['t'], P['end_gap'], P['gusset']
    side = (fr[0], fr[2], A)                              # sketch in (s, m), extrude along the hinge axis
    prof = poly([(s0, -rk), (s0 + sgn * (e + gl), -rk), (s0 + sgn * (e + gl), -rk + t), (s0, rk)])
    out = []
    for w0, w1 in zs:
        out += p.prism(c, side, w0, w1, prof, name=name).bodies
    return out


def _hex_pockets(p, body, c, fr, outline, z_top, depth):
    """Honeycomb on a plate's top: hexagonal pockets that fit inside the outline less an edge; the walls left between
    them are the ribs. Open at the top: prints without supports, flat underside kept."""
    hc = P['hexcell']
    af, wall, edge = hc['af'], hc['wall'], hc['edge']
    rv = af / math.sqrt(3)                                # hexagon corner radius
    pitch = af + wall
    n = len(outline)
    cx = sum(q[0] for q in outline) / n
    cy = sum(q[1] for q in outline) / n

    def inside(u, v):
        for i in range(n):
            (x0, y0), (x1, y1) = outline[i], outline[(i + 1) % n]
            ex, ey = x1 - x0, y1 - y0
            L = math.hypot(ex, ey)
            nx, ny = ey / L, -ex / L
            if (cx - x0) * nx + (cy - y0) * ny < 0:
                nx, ny = -nx, -ny
            if (u - x0) * nx + (v - y0) * ny < edge:
                return False
        return True
    us = [q[0] for q in outline]
    vs = [q[1] for q in outline]
    cells, row, v = [], 0, min(vs)
    while v <= max(vs):
        u = min(us) + (pitch / 2 if row % 2 else 0)
        while u <= max(us):
            corners = [(u + rv * math.cos(math.radians(60 * k + 30)), v + rv * math.sin(math.radians(60 * k + 30)))
                       for k in range(6)]
            if all(inside(*q) for q in corners):
                cells.append(corners)
            u += pitch
        v += pitch * math.sqrt(3) / 2
        row += 1
    if not cells:
        return 0

    def draw(sk, to):
        ln = sk.sketchCurves.sketchLines
        for corners in cells:
            q = [to(*xy) for xy in corners]
            for k in range(6):
                ln.addByTwoPoints(q[k], q[(k + 1) % 6])
    p.prism(c, fr, z_top - depth, z_top + 1, draw, name='honeycomb', op=CUT, targets=[body])
    return len(cells)


def _holes(p, body, c, zs):
    for w0, w1 in zs:
        p.prism(c, sh.frame_of(A), w0 - 1, w1 + 1, sh.circle(P['hole'] / 2), name='hinge pin hole', op=CUT,
                targets=[body])


def build_piece(grp, i):
    """Root arm (i = 0) or blade i: a flat plate (tapers from the rear width to the front width) whose underside is
    flush with the knuckles' underside; knuckles inside at the rear hinge and outside at the front hinge, each on a
    gusset; the last blade ends in the strap tab; the root arm (it spans air) is a thicker plate."""
    pcs = LAY['pieces']
    pc = pcs[i]
    last = i == len(pcs) - 1
    p = Part(grp, pc['name'], color=PRINT)
    c, fr, Lp = frame(pc)
    eg, t, rk = P['end_gap'], P['t'], P['r_k']
    (r0, r1), (f0, f1) = pc['rear'], pc['front']
    s1 = Lp if last else Lp - eg
    z0, z1 = -rk, -rk + (P['t_root'] if i == 0 else t)
    bodies = list(p.prism(c, fr, z0, z1, poly([(eg, r0), (s1, f0), (s1, f1), (eg, r1)]), name='plate').bodies)
    bodies += _gussets(p, c, fr, zones(pc['rear'], False), 0.0, 1, 'knuckle gusset (rear)')
    bodies += _knuckles(p, c, zones(pc['rear'], False), 'knuckle (rear, inner)')
    cf = xyz(*pc['F'])
    if not last:
        bodies += _gussets(p, c, fr, zones(pc['front'], True), Lp, -1, 'knuckle gusset (front)')
        bodies += _knuckles(p, cf, zones(pc['front'], True), 'knuckle (front, outer)')
    else:
        tw, tl = P['tab']
        wc = (f0 + f1) / 2
        bodies += p.prism(c, fr, z0, z1, poly([(Lp - 2, wc - tw / 2), (Lp + tl, wc - tw / 2), (Lp + tl, wc + tw / 2),
                                                (Lp - 2, wc + tw / 2)]), name='strap tab').bodies
    body = p.join(bodies)[0]
    sh.round_edges(p, body, r=1.5)
    body = p.comp.bRepBodies.item(0)
    hc = P['hexcell']
    s_end = s1 if not last else Lp - 2
    _hex_pockets(p, body, c, fr, [(eg, r0), (s_end, f0), (s_end, f1), (eg, r1)], z1,
                 hc['depth_root'] if i == 0 else hc['depth'])
    _holes(p, body, c, zones(pc['rear'], False))
    if not last:
        _holes(p, body, cf, zones(pc['front'], True))
    else:
        sl, sw = P['slot']
        sc = Lp + P['tab'][1] - 4 - sw / 2
        p.prism(c, fr, z0 - 1, z1 + 1, poly([(sc - sw / 2, wc - sl / 2), (sc + sw / 2, wc - sl / 2),
                                             (sc + sw / 2, wc + sl / 2), (sc - sw / 2, wc + sl / 2)]),
                name='strap slot', op=CUT, targets=[body])
    body.name = pc['name']
    return p


def _arc_slot(R, phi, sweep, w):
    """Sketch draw: an arc slot of width w on radius R about the origin, centred at angle phi, +- sweep (degrees).
    One closed outline (2 arcs + 2 half-round ends): separate end circles split it into profiles that left the
    middle of the slot uncut."""
    def draw(sk, to):
        arcs = sk.sketchCurves.sketchArcs
        a0, a1 = math.radians(phi - sweep), math.radians(phi + sweep)
        pt = lambda r, a: to(r * math.cos(a), r * math.sin(a))
        ro, ri = R + w / 2, R - w / 2
        arcs.addByThreePoints(pt(ro, a0), pt(ro, (a0 + a1) / 2), pt(ro, a1))
        arcs.addByThreePoints(pt(ri, a0), pt(ri, (a0 + a1) / 2), pt(ri, a1))
        for a, sg in ((a0, -1), (a1, 1)):
            cx, cy = R * math.cos(a), R * math.sin(a)
            tx, ty = -math.sin(a), math.cos(a)
            arcs.addByThreePoints(pt(ro, a), to(cx + sg * tx * w / 2, cy + sg * ty * w / 2), pt(ri, a))
    return draw


def build_bracket(grp):
    """Bracket on the tower's front plate. It turns on a Ø16 boss on the tower, centred under the root hinge, and is
    locked by 2 x M3 x 8 through arc slots (+- 20 deg) into inserts in the tower: loosen, turn the whole chain to
    the wearer's shoulder slope, tighten. (Locked by one M6 thumb screw in an arc slot, r 30, +- 20 deg.) Two arms carry the root hinge's end knuckles."""
    p = Part(grp, 'Rest bracket (on the tower)', color=PRINT)
    pc = LAY['pieces'][0]
    H = xyz(*pc['R'])
    b = P['bracket']
    wc = sum(pc['rear']) / 2
    c = bracket_pivot()                                   # on the tower face, under the hinge's middle
    fr = (A, N, X)
    bodies = list(p.prism(c, fr, 0, b['plate'], poly(bracket_outline()), name='plate').bodies)
    rk = P['r_k']
    for w0, w1 in zones(pc['rear'], True):
        bodies += p.prism(c, fr, b['plate'] - 0.5, H[0] - P['x_face'],
                          poly([(w0 - wc, -rk), (w1 - wc, -rk), (w1 - wc, rk), (w0 - wc, rk)]), name='arm').bodies
    bodies += _knuckles(p, H, zones(pc['rear'], True), 'knuckle (outer)')
    body = p.join(bodies)[0]
    sh.round_edges(p, body, r=1.5)
    body = p.comp.bRepBodies.item(0)
    _holes(p, body, H, zones(pc['rear'], True))
    bd, bh, fit = b['boss']
    p.prism(c, fr, -1, b['plate'] + 1, sh.circle(bd / 2 + fit / 2), name='pivot hole', op=CUT, targets=[body])
    sl = b['slot']
    p.prism(c, fr, -1, b['plate'] + 1, _arc_slot(sl['r'], sl['phi'], sl['sweep'], sl['w']), name='lock slot', op=CUT,
            targets=[body])
    body.name = 'Rest bracket (on the tower)'
    return p


def bracket_outline(m=0.0):
    """Bracket plate outline (s, t) about the pivot, grown by m: a band carrying the two arms and a lobe on the
    outer side for the lock slot; it keeps clear of the gas strut's ear (above, inboard) over the whole swing."""
    b = P['bracket']
    wc = sum(LAY['pieces'][0]['rear']) / 2
    r0, r1 = [w - wc for w in hinge(LAY['pieces'][0]['rear'])]
    s0, s1 = r0 - b['s'] - m, r1 + b['s'] + m
    t0, t1 = b['t'][0] - m, b['t'][1] + m
    l0, l1 = b['lobe'][0] - m, b['lobe'][1] + m
    return [(s0, t0), (s1, t0), (s1, l1), (l0, l1), (l0, t1), (s0, t1)]


def bracket_pivot():
    pc = LAY['pieces'][0]
    H = xyz(*pc['R'])
    return add([P['x_face'], H[1], H[2]], mul(A, sum(pc['rear']) / 2))


def bracket_bolts():
    """The lock screw's centre on the tower face (slot at its middle position)."""
    c = bracket_pivot()
    sl = P['bracket']['slot']
    a = math.radians(sl['phi'])                       # same angle the slot is cut at (sketch u = A, v = N)
    return [add(c, add(mul(A, sl['r'] * math.cos(a)), mul(N, sl['r'] * math.sin(a))))]


def cut_tower_holes():
    """Re-cut the shoulder rest's holes and boss on the existing tower (girdle_b.build_tower does this on a rebuild)."""
    fx.init()
    occ = next(o for o in fx.design.rootComponent.allOccurrences if o.component.name == 'Shoulder tower')
    for f in list(occ.component.features.extrudeFeatures):
        if f.name.startswith(('shoulder rest bolt hole', 'shoulder rest nut trap', 'shoulder rest insert hole',
                              'shoulder rest pivot boss')):
            f.deleteMe()
    p = Part.__new__(Part)
    p.occ, p.comp, p.color = occ, occ.component, None
    p._planes, p._refs, p._paths = {}, None, {}
    tower_holes(p, p.comp.bRepBodies.item(0))
    return [[round(v, 1) for v in c] for c in bracket_bolts()]


def tower_holes(p, body):
    """On the tower's front plate: the Ø16 pivot boss for the bracket, and for the M6 thumb screw a clearance hole
    + an M6 nut trapped in a hex pocket in the plate's inside face (drop the nut in before the lift links)."""
    bd, bh, fit = P['bracket']['boss']
    p.prism(bracket_pivot(), sh.frame_of(X), -0.5, bh, sh.circle(bd / 2), name='shoulder rest pivot boss', op=JOIN,
            targets=[body])
    af, nt = P['m6_nut']
    for c in bracket_bolts():
        p.prism(c, sh.frame_of(X), -8.5, 0.1, sh.circle(3.3), name='shoulder rest bolt hole', op=CUT, targets=[body])
        p.prism(c, sh.frame_of(X), -7.5, -7.0 + nt + 0.3, sh.hexagon(af + 0.3), name='shoulder rest nut trap', op=CUT,
                targets=[body])
    return [[round(v, 1) for v in c] for c in bracket_bolts()]


def bracket_backing(y_min):
    """Where the bracket can sit over its +- 20 deg swing, + a margin, as (y, z), cut off at y_min (the top node's
    top): the tower's front plate is extended to it so the bracket always bears on the tower."""
    b = P['bracket']
    c = bracket_pivot()
    corners = bracket_outline(b['backing'])
    pts = []
    for ang in (-b['slot']['sweep'], 0.0, b['slot']['sweep']):
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        for s, t_ in corners:
            q = add(c, add(mul(A, s * ca - t_ * sa), mul(N, s * sa + t_ * ca)))
            pts.append((q[1], q[2]))
    return _clip_y(_hull(pts), y_min)


def _hull(pts):
    pts = sorted(set(pts))
    cross2 = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for q in pts:
        while len(lo) >= 2 and cross2(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(pts):
        while len(hi) >= 2 and cross2(hi[-2], hi[-1], q) <= 0:
            hi.pop()
        hi.append(q)
    return lo[:-1] + hi[:-1]


def _clip_y(poly_, y_min):
    out = []
    for i in range(len(poly_)):
        a, b = poly_[i], poly_[(i + 1) % len(poly_)]
        ina, inb = a[0] >= y_min, b[0] >= y_min
        if ina:
            out.append(a)
        if ina != inb:
            f = (y_min - a[0]) / (b[0] - a[0])
            out.append((y_min, a[1] + f * (b[1] - a[1])))
    return out


def build_soft(grp):
    """Hook-and-loop + 1/2" foam pad under each blade (inset from the plate)."""
    v = Part(grp, 'Rest hook-and-loop (buy)', color=VELCRO)
    f = Part(grp, 'Rest foam pads 1/2 in (buy)', color=FOAM)
    pcs = LAY['pieces']
    for i, pc in enumerate(pcs[1:], 1):
        c, fr, Lp = frame(pc)
        e, n = P['end_gap'] + P['inset'], P['inset']
        s1 = Lp - (n if i == len(pcs) - 1 else e)
        (r0, r1), (f0, f1) = pc['rear'], pc['front']
        out = poly([(e, r0 + n), (s1, f0 + n), (s1, f1 - n), (e, r1 - n)])
        z0 = -P['r_k']                                    # the plate's flat underside
        v.prism(c, fr, z0 - P['velcro'], z0, out, name='hook-and-loop').bodies.item(0).name = 'hook-and-loop %d' % i
        f.prism(c, fr, z0 - P['velcro'] - P['pad'], z0 - P['velcro'], out,
                name='foam pad').bodies.item(0).name = 'foam pad 1/2 in, blade %d' % i
    return v, f


def build_hw(grp):
    """Hinge pins (one Ø5 clevis pin + R-clip per joint, through all three knuckles: the chain drapes freely and
    the front strap's tension holds it on the shoulder). Bracket bolts: M5 x 16 into nuts held in the tower's nut
    traps. Buckle."""
    hw = Part(grp, 'Rest HW (buy)', color=HWC)
    pcs = LAY['pieces']
    hd, hh = 8.5, 5.0
    pin = P['pin']
    fr = sh.frame_of(A)
    for pc in pcs:
        H = xyz(*pc['R'])
        a, b = hinge(pc['rear'])
        L = 2 * math.ceil((b - a + pin['clip'] + 2) / 2)    # head side flush at a, R-clip hole past b
        c = add(H, mul(A, a))
        q = hw.prism(c, fr, -pin['head'][1], 0, sh.circle(pin['head'][0] / 2), name='pin head').bodies.item(0)
        hw.prism(c, fr, -0.1, L, sh.circle(pin['d'] / 2), name='pin', op=JOIN, targets=[q])
        q.name = 'Clevis pin M6 x 70 + R-clip (buy), %d needed' % L
        r = hw.prism(add(H, mul(A, b + 0.5 + pin['clip'] / 2)), sh.frame_of(N), -6, 6, sh.circle(0.6),
                     name='R-clip').bodies.item(0)
        r.name = 'R-clip / split pin 1.2 mm (buy)'
    th = P['thumb']
    for c in bracket_bolts():
        ch = add(c, [P['bracket']['plate'], 0, 0])
        sh.hw_bolt(hw, ch, sh.frame_of([-1, 0, 0]), th['len'], th['head'], 'M6 x 16 knurled thumb screw (buy)', dia=6.0)
        nc = add(c, [-7.0 + P['m6_nut'][1], 0, 0])
        n = hw.prism(nc, sh.frame_of([-1, 0, 0]), 0, P['m6_nut'][1], sh.hexagon(P['m6_nut'][0]), name='M6 nut').bodies.item(0)
        hw.prism(nc, sh.frame_of([-1, 0, 0]), -1, P['m6_nut'][1] + 1, sh.circle(3.0), name='thread', op=CUT, targets=[n])
        n.name = 'M6 hex nut, in the tower nut trap (buy)'
    bk = Part(grp, 'Rest buckle 25 mm (buy)', color=BUCKLE)
    pc = pcs[-1]
    c, fr, Lp = frame(pc)
    bw, bl, bt = P['buckle']
    wc = sum(pc['front']) / 2
    s0 = Lp + P['tab'][1] + 2
    bk.prism(c, fr, -bt / 2, bt / 2, poly([(s0, wc - bw / 2), (s0 + bl, wc - bw / 2), (s0 + bl, wc + bw / 2),
                                           (s0, wc + bw / 2)]), name='buckle').bodies.item(0).name = \
        'Side-release buckle 25 mm, female half (buy)'
    return hw, bk


def build_back_pads(frame_comp):
    """Hook-and-loop + 1/2" foam pads on the body side of the three frame nodes, either side of the spine."""
    p = Part(frame_comp, 'Back pads 1/2 in + hook-and-loop (buy)', color=FOAM)
    v = Part(frame_comp, 'Back pad hook-and-loop (buy)', color=VELCRO)
    xf = sh.D['xf'] + sh.S['node_depth'] / 2
    bp = P['back_pad']
    for name, y, h in (('bottom', sh.D['y_bot'], sh.S['node_h'][0]), ('mid', sh.D['y_mid'], sh.S['node_h'][1]),
                       ('top', sh.D['y_top'], sh.S['node_h'][2])):
        for side, s in (('L', -1), ('R', 1)):
            z = sh.MID_Z + s * bp['dz']
            y0, y1, z0, z1 = y - h / 2 + bp['edge'], y + h / 2 - bp['edge'], z - bp['w'] / 2, z + bp['w'] / 2
            v.box(xf, xf + P['velcro'], y0, y1, z0, z1, name='hook-and-loop')[0].name = 'hook-and-loop, %s %s' % (name, side)
            p.box(xf + P['velcro'], xf + P['velcro'] + P['pad'], y0, y1, z0, z1,
                  name='foam pad')[0].name = 'foam pad 1/2 in, %s node %s' % (name, side)
    return p, v


# ------------------------------------------------------------------ step-wise build (one part per MCP call)
def _top():
    return next(o for o in fx.design.rootComponent.occurrences if o.component.name == sh.TOP).component


def _grp():
    return next((o.component for o in _top().occurrences if o.component.name == NAME), None)


STEPS = ('start', 'bracket', 'root', 'blade1', 'blade2', 'blade3', 'soft', 'hw', 'back')


def build_step(step):
    fx.init()
    if step == 'start':
        fx.group(_top(), NAME)
        return 'group ready'
    if step == 'back':
        fr = next(o.component for o in _top().occurrences if o.component.name == 'Frame')
        for o in list(fr.occurrences):
            if o.component.name.startswith(('Back pads', 'Back pad hook')):
                o.deleteMe()
        out = build_back_pads(fr)
    else:
        grp = _grp()
        names = dict(bracket=['Rest bracket'], root=['Rest root arm'], blade1=['Rest blade 1'], blade2=['Rest blade 2'],
                     blade3=['Rest blade 3'], soft=['Rest hook-and-loop', 'Rest foam pads'],
                     hw=['Rest HW', 'Rest buckle'])[step]
        for o in list(grp.occurrences):
            if o.component.name.startswith(tuple(names)):
                fx.retire(o)
        out = dict(bracket=lambda: build_bracket(grp), root=lambda: build_piece(grp, 0),
                   blade1=lambda: build_piece(grp, 1), blade2=lambda: build_piece(grp, 2),
                   blade3=lambda: build_piece(grp, 3), soft=lambda: build_soft(grp), hw=lambda: build_hw(grp))[step]()
    res = []
    for q in (out if isinstance(out, tuple) else (out,)):
        names = [b.name for b in q.comp.bRepBodies]
        q.finish()
        for b, n in zip(q.comp.bRepBodies, names):
            b.name = n
        res.append('%s: %d' % (q.comp.name, q.comp.bRepBodies.count))
    return ', '.join(res)
