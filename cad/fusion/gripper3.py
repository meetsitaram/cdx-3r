"""CDX-3R gripper, prototype 3: a fold-up, three-claw (octopus) gripper with a pistol grip. No slide.

Layout (user brief, 20 Oct 2026):
  * BASE (printed) clamped on the forearm's middle PVC pipe well behind the wrist (two snap clips, each with a
    screw pressing on the pipe): loosen them and the whole gripper slides along the pipe to set its distance
    from the wrist (anywhere in a 50 mm range forward of the shortest setting). Its front rides over the wrist ring to the HINGE CHEEKS.
  * CARRIER (printed), everything in front of the hinge: the grip, the trigger and the claw head. In use it is latched
    straight out (index plunger); to stow it, pull the plunger and flip the carrier up and back over the forearm,
    clear of the elbow. The GRIP folds flat forward under the carrier first (its own pin and latch), so the folded
    package stays low.
  * HEAD: right in front of the trigger, low, with a clear pocket between them for the fingers. Three curved TPU
    CLAWS, 120 deg apart round the claw axis (one on top opening upward, two below opening down and outward), pinned
    in forks on the HUB; closed they close like drill-chuck jaws (wedge ridges meeting on the axis, saw teeth). A
    COLLAR sliding on the hub holds the three claw tails: pull it back and all three open together.
  * DRIVE: the TRIGGER (spray-bottle style at the top of the grip) pulls a printed Y LINK: one stem from the
    trigger forward over the fingers, splitting into two angled arms that pass either side of the hub and pin onto the
    collar's two sides. Pulling both sides evenly, ~10 mm above the claw axis, the collar can't cock and jam. A
    RETURN SPRING (extension) from a lug on the Y link to a lug on the back of the hub is stretched by a squeeze; let
    go and it pulls the link, the collar and the trigger forward: that is what closes the claws.
  * CARRIER: a bridge from the fold knuckle over the grip and the trigger to the top of the hub; nothing below it in
    front of the trigger but the fingers.

Frame: the RAIL frame of gripper.py (X along the middle pipe toward the fingers, origin where the pipe ends at the
wrist ring; Y out from the pipe, "up"; Z across). Hand size is a guess (the scan has no hand): tune P after a fitting.

    import split; split.new('gripper3'); [split.build('gripper3', s) for s in gripper3.STEPS]; split.save('gripper3')
"""
import math

import adsk.core
import adsk.fusion

import fxlib as fx
import gripper as g2
import shoulder as sh
from fxlib import Part, add, mul, sub, unit, cross, dot

CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
PRINT, TPU, HWC, GRN = '#d9822b', '#2b2b2b', '#c9d2d9', '#2b9d8f'
NAME = 'Gripper 3 (fold-up, 3 claws)'
STEPS = ('frame', 'base', 'carrier', 'claws', 'collar', 'link', 'grip', 'trigger', 'hw')
ZF, XF, YF, _poly, _xz, _round_rect = g2.ZF, g2.XF, g2.YF, g2._poly, g2._xz, g2._round_rect

P = dict(
    base=dict(x0=-150.0, x1=34.0, y=(15.0, 20.0), z=12.0, web=(6.0, 12.0), front_lift=-85.0, slide=(0.0, 50.0), rib=(20.0, 38.0, 8.0)),   # stiff top rib: the front beam carries the gripper
    clips=(-140.0, -100.0),                      # clamps well back: the whole gripper slides along the pipe
    hinge=dict(x=45.0, y=60.0, pin_d=8.0, knuckle_r=15.0, knuckle_z=13.0, cheek_t=9.0, latch_r=11.0, stow_deg=200.0),
    carrier=dict(x1=175.0, y=(6.0, 32.0), z=13.0, bridge_y0=10.0, bend_r=(18.0, 12.0)),   # bridge: outer/inner bend
    hub=dict(x=(163.0, 200.0), y=-27.0, r=26.0, nose_r=27.5, nose_x=219.0),   # nose: rounded, slotted claw seat   # in front of the trigger
    claw=dict(xp=209.0, rp=22.0, L=95.0, root_in=15.0, pad=0.82, cup=14.0, pad_rise=1.2, apex=0.3, wedge_gap=0.1, tooth=(1.0, 4.0), teeth_from=30.0, cells=(9.0, 84.0, 9.0, 2.0, 2.0, 2.2, 3.0), t=14.0,
              root_depth=14.0, tip_depth=9.0, outer_bulge=12.0,
              alphas=(0.0, 120.0, 240.0), tail=(-7.0, 10.0), open_deg=32.0),
    collar=dict(x=(182.0, 194.0), skirt=(207.5, 29.0), r=(27.8, 36.0), lug_z=(30.0, 37.3), lobe_r=5.5,
                pad=(26.3, 10.0),    # bore clears the nose (27.5); 3 pads (inner r, width) ride the hub, pass the claw slots
                skirt_r=40.0),       # the tail cheeks reach out to this radius (36 broke, 27 Oct)
    link=dict(h=10.0, w=6.0, split=124.0, kink=152.0, diag_w=12.0, arm_z=(37.6, 43.6)),   # Y: stem, 2 angled arms
    spring=dict(rise=11.8, od=10.0, link_hook=115.0, link_holes=(115.0, 120.0, 125.0), hub_hook=160.0, free=36.0,
                max_ext=15.0, rate=2.0, init=4.0),   # Keadic kit 1.2 x 10 x 45 (loops ~36 apart): measure, pick a hole   # return spring:
    # an extension spring above the Y link, from a lug on the link (at its split) to a lug on the hub's back face
    grip=dict(x=65.0, z=0.0, r=16.0, y=(-105.0, 6.0), fold_pivot=(65.0, 6.0)),
    trigger=dict(pivot=(100.0, -4.0), len=55.0, rest_deg=16.0, travel_deg=15.0, t=8.0, z=(-10.0, 10.0),
                 horn_w=10.0, pull_r=17.0),               # pull pin 13 mm under the pivot, swings +-10 deg
    velcro=dict(t=2.0, d=22.0, x=130.0, pad=(105.0, 155.0)),   # stowed: bridge top dot meets a dot on a base pad
    ball_r=20.0,
)


# ------------------------------------------------------------------ claw geometry (pure python, testable offline)
def claw_curves(n=40):
    """Claw in its radial plane, closed: (a, r_inner, r_outer) lists. a: along the axis from the pivot plane; r: from
    the claw axis. The inner edge sweeps in from the root (a rounded, convex cup) to a fingertip PAD over the front
    part whose ridge reaches the axis (drill-chuck wedge, see _claws); the pad opens pad_rise mm towards its back so
    the tips touch first and pinch small things."""
    c = P['claw']
    rm, ap = c['apex'], c['pad'] * c['L']
    pts = []
    for k in range(n + 1):
        a = c['L'] * k / n
        if a >= ap:
            ri = rm + c['pad_rise'] * (c['L'] - a) / (c['L'] - ap)
        else:                                                       # C-cup: bows out, then hooks back in
            u = a / ap
            ri = (rm + c['pad_rise'] + (c['root_in'] - rm - c['pad_rise']) * (1 - u)
                  + c['cup'] * math.sin(math.pi * u) * (1 - u))
        pts.append((a, ri))
    ro0, roL = pts[0][1] + c['root_depth'], pts[-1][1] + c['tip_depth']    # outer edge: a convex curve, root to tip
    bulge = lambda u: c['outer_bulge'] * 6.75 * u * (1 - u) ** 2     # fullest a third of the way out, thin at both ends
    return [(a, ri, max(ro0 + (roL - ro0) * a / c['L'] + bulge(a / c['L']),
                        ri + c['root_depth'] + (c['tip_depth'] - c['root_depth']) * a / c['L']))
            for a, ri in pts]


def claw_teeth():
    """Saw teeth on the pad's gripping edge: [(a0, a1)], crest at both ends; the edge ramps away from the axis from a0
    to a valley just short of a1, then steps straight back: the steep face looks at the root, so a held thing can't
    slide out forward."""
    c = P['claw']
    if 'tooth' not in c:
        return []
    depth, pitch = c['tooth']
    a, out = c['teeth_from'], []
    while a + pitch <= c['L'] - 8.0:
        out.append((a, a + pitch))
        a += pitch
    return out


def claw_cells():
    """Fin-ray cells (closed claw, claw plane): quads (a, r) between the gripping wall and the outer wall, the ribs
    between them leaning back toward the root. Empty until the claw is made fin-ray."""
    c = P['claw']
    if 'cells' not in c:
        return []
    a0, a1, pitch, rib, w_in, w_out, lean = c['cells']
    cv = claw_curves(400)
    at = lambda x: min(cv, key=lambda q: abs(q[0] - x))
    inner = lambda x: max(at(x)[1] + 1.0, r_meet()) + w_in          # past the teeth and the wedge
    outer = lambda x: at(x)[2] - w_out
    out, a = [], a0
    while a + pitch <= a1 + 1e-6:
        s0, s1 = a + rib / 2, a + pitch - rib / 2
        q = [(s0, inner(s0)), (s1, inner(s1)), (s1 - lean, outer(s1 - lean)), (s0 - lean, outer(s0 - lean))]
        if min(q[3][1] - q[0][1], q[2][1] - q[1][1]) >= 2.0:
            out.append(q)
        a += pitch
    return out


def claw_outline():
    """Closed outline of one claw (a, r): inner face out to the tip, outer face back, root disc round the pivot."""
    c = P['claw']
    cv = claw_curves()
    inner = [(a, ri) for a, ri, _ in cv]
    depth = c['tooth'][0] if 'tooth' in c else 0.0
    ri_at = lambda x: next(r for a, r, _ in cv if a >= x - 1e-9)
    for a0, a1 in claw_teeth():                                     # crest on the curve, valley behind it
        inner = [q for q in inner if not a0 <= q[0] <= a1]
        inner += [(a0, ri_at(a0)), (a1 - 0.4, ri_at(a1) + depth), (a1, ri_at(a1))]
    inner.sort()
    outer = [(a, ro) for a, _, ro in cv][::-1]
    ri_, ro_ = cv[-1][1], cv[-1][2]                                  # round tip: a half circle, nothing to poke
    rc, rad = (ri_ + ro_) / 2, (ro_ - ri_) / 2
    tip = [(c['L'] + rad * math.cos(math.radians(f)), rc + rad * math.sin(math.radians(f)))
           for f in (-67.5, -45.0, -22.5, 0.0, 22.5, 45.0, 67.5)]
    return inner + tip + outer


def claw_point(a, r, deg):
    """Point (a, r) of a claw after it opens by deg about its pivot (0, rp): (a', r')."""
    c = P['claw']
    t = math.radians(deg)
    return (a * math.cos(t) - (r - c['rp']) * math.sin(t), c['rp'] + a * math.sin(t) + (r - c['rp']) * math.cos(t))


def ball_contact_deg(xb):
    """Opening angle at which the inner faces first touch a ball (ball_r) centred on the axis at a = xb."""
    cv = claw_curves(120)
    for k in range(400):
        deg = 30.0 - k * 0.1
        if min(math.hypot(claw_point(a, ri, deg)[0] - xb, claw_point(a, ri, deg)[1]) for a, ri, _ in cv) <= P['ball_r']:
            return deg
    return None


def to_xyz(a, r, alpha, t=0.0):
    """Claw-plane coordinates -> rail frame: a along X from the pivot plane, r radial at angle alpha (0 = +Y, toward
    +Z at 90), t tangential."""
    h, c = P['hub'], P['claw']
    al = math.radians(alpha)
    er, et = (0.0, math.cos(al), math.sin(al)), (0.0, -math.sin(al), math.cos(al))
    return [c['xp'] + a, h['y'] + r * er[1] + t * et[1], r * er[2] + t * et[2]]


def claw_frame(alpha):
    """Sketch frame for a claw: ex = X, ey = radial, ez = tangential."""
    al = math.radians(alpha)
    return ([1, 0, 0], [0, math.cos(al), math.sin(al)], [0, -math.sin(al), math.cos(al)])


# ------------------------------------------------------------------ build
def _path(items):
    """Closed outline from points (u, v), arcs ('arc', (um, vm), (ue, ve)) through a mid point and smooth runs
    ('spline', [(u, v), ...]) through their points, for prism()."""
    def draw(sk, to):
        ln, ar = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
        pts = []
        for it in items:
            pts.append(it)
        start = pts[0]
        cur = start
        for it in pts[1:] + [start]:
            if it[0] == 'spline':
                sk.sketchCurves.sketchFittedSplines.add(fx.coll([to(*cur)] + [to(*q) for q in it[1]]))
                cur = it[1][-1]
            elif isinstance(it[0], str):
                ar.addByThreePoints(to(*cur), to(*it[1]), to(*it[2]))
                cur = it[2]
            else:
                ln.addByTwoPoints(to(*cur), to(*it))
                cur = it
    return draw


def _revolve_x(p, cy, prof, name):
    """Solid of revolution about the line y = cy, z = 0 (parallel to X): prof is [(x, r)], closed along r = 0."""
    pl = p.plane([0, 0, 0], [0, 0, 1], [1, 0, 0])
    sk = p._hidden_sketch(pl, name)
    to = lambda x, r: sk.modelToSketchSpace(fx.P([x, cy + r, 0]))
    ln = sk.sketchCurves.sketchLines
    q = list(prof)
    axis = None
    for i in range(len(q)):
        a, b = q[i], q[(i + 1) % len(q)]
        l_ = ln.addByTwoPoints(to(*a), to(*b))
        if abs(a[1]) < 1e-9 and abs(b[1]) < 1e-9:
            axis = l_
    prof_ = sk.profiles.item(0)
    ri = p.comp.features.revolveFeatures.createInput(prof_, axis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ri.setAngleExtent(False, adsk.core.ValueInput.createByString('360 deg'))
    f = p.comp.features.revolveFeatures.add(ri)
    f.name = name
    return f.bodies.item(0)


def _is_sharp(e, deg=30.0):
    if e.faces.count != 2:
        return False
    pt = e.pointOnEdge
    ok1, n1 = e.faces.item(0).evaluator.getNormalAtPoint(pt)
    ok2, n2 = e.faces.item(1).evaluator.getNormalAtPoint(pt)
    return ok1 and ok2 and math.degrees(n1.angleTo(n2)) > deg


def _mm(e):
    q = e.pointOnEdge
    return q.x * 10, q.y * 10, q.z * 10


HOLE_R = (1.6, 1.7, 2.0, 3.4, 4.2)        # mm: screw, insert, plunger and pin holes: their edges stay sharp (fits)


def _hole_edge(e):
    """An edge of a drilled hole or the pipe bore (a concave cylinder of a hole radius): left sharp, it sets a fit."""
    for i in range(e.faces.count):
        g = e.faces.item(i).geometry
        if isinstance(g, adsk.core.Cylinder):
            r = g.radius * 10
            if any(abs(r - h) < 0.05 for h in HOLE_R + (g2.P['bore_r'],)):
                return True
    return False


def _soften(p, body, r, test):
    """Cosmetic fillets on the body's edges that pass test(edge): all at once, else one by one at r then r/2; a fillet
    Fusion can't build is deleted again so it never breaks the features after it."""
    ff = p.comp.features.filletFeatures
    ok_state = adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState

    def attempt(edges, rr):
        try:
            fi = ff.createInput()
            try:
                fi.edgeSetInputs.addConstantRadiusEdgeSet(fx.coll(edges), adsk.core.ValueInput.createByReal(rr / 10.0), True)
            except AttributeError:
                fi.addConstantRadiusEdgeSet(fx.coll(edges), adsk.core.ValueInput.createByReal(rr / 10.0), True)
            f = ff.add(fi)
        except Exception:
            return False
        if f.healthState != ok_state:
            f.deleteMe()
            return False
        return True
    edges = [e for e in body.edges if test(e)]
    if not edges or attempt(edges, r):
        return
    for rr in (r, r / 2):
        for _ in range(60):
            left = [e for e in body.edges if test(e)]
            if not any(attempt([e], rr) for e in left):
                break


def _group(top):
    return next(o.component for o in top.occurrences if o.component.name == NAME)


def build(top, step):
    if step == 'frame':
        o, R = g2.rail_frame()
        fx.group(top, NAME, R, o)
        return dict(origin=o)
    return globals()['_' + step](_group(top))


def _base(g):
    """Base (printed): saddle on the middle pipe, two snap clips, front tab on the wrist ring, forward over the wrist
    to the two hinge cheeks. Print on its side."""
    b, hg = P['base'], P['hinge']
    p = Part(g, 'Gripper3 base (printed)', color=PRINT)
    spine = p.prism([b['x0'], 0, 0], XF, 0, b['x1'] - b['x0'],
                    _poly([(b['y'][0], -b['z']), (b['y'][1], -b['z']), (b['y'][1], b['z']), (b['y'][0], b['z']),
                           (b['y'][0], b['web'][1]), (b['web'][0], b['web'][1]), (b['web'][0], -b['web'][1]),
                           (b['y'][0], -b['web'][1])]), name='spine').bodies.item(0)
    parts = [spine]
    c = g2.P['clip']
    for xc in P['clips']:
        parts += p.ann('x', [xc, 0, 0], c['ro'], g2.P['bore_r'], c['w'], name='pipe clip')
    zk, ct = hg['knuckle_z'], hg['cheek_t']
    xr = b['x1'] - 32                                              # cheeks: broad neck, round head round the pin
    yr, rt, rz = g2.P['ring_top'], b['rib'][1], b['z']
    xs = b['front_lift'] - 7                                       # rib: as wide as the base, sloped rear end (clear
    parts.append(p.prism([0, 0, 0], ZF, -rz, rz, _poly([(xs, b['y'][1] - 0.5), (xs + rt - b['y'][1], rt),   # of the
                                                         (b['x1'], rt), (b['x1'], b['y'][1] - 0.5)]),          # clamp
                         name='stiffening rib').bodies.item(0))                                                 # screw)
    parts.append(p.box(xr, b['x1'], yr, rt, -(zk + 0.4), zk + 0.4, name='filler between the cheeks')[0])
    parts.append(p.box(xr, b['x1'], yr, b['y'][1], -(zk + 0.4 + ct), zk + 0.4 + ct, name='cheek bridge')[0])
    rr = hg['knuckle_r'] + 3.0
    k = math.sqrt(0.5)
    cheek = [(xr, yr), (b['x1'] + 4, yr), (hg['x'] + rr, hg['y']),
             ('arc', (hg['x'] + rr * k, hg['y'] + rr * k), (hg['x'], hg['y'] + rr)),
             ('arc', (hg['x'] - rr * k, hg['y'] + rr * k), (hg['x'] - rr, hg['y'])),
             (xr, b['rib'][1])]
    for s in (1, -1):
        z0, z1 = sorted((s * (zk + 0.4), s * (zk + 0.4 + ct)))
        parts.append(p.prism([0, 0, 0], ZF, z0, z1, _path(cheek), name='hinge cheek').bodies.item(0))
    vc, yt = P['velcro'], P['carrier']['y'][1]                     # stow pad: meets the folded bridge's top face
    (ax, ay), _ = stow_point(vc['pad'][0], yt, 2 * vc['t'])
    (bx, by), _ = stow_point(vc['pad'][1], yt, 2 * vc['t'])
    parts.append(p.prism([0, 0, 0], ZF, -rz, rz,                     # flush with the rib's sides
                         _poly([(ax, ay), (bx, by), (bx, b['rib'][1] - 0.5), (ax, b['rib'][1] - 0.5)]),
                         name='stow pad').bodies.item(0))
    parts.append(p.prism([0, 0, 0], ZF, -rz, rz,                     # the rib's sloped end runs straight up into the pad
                         _poly([(xs, b['y'][1] - 0.5), (bx, by), (bx, rt - 0.5), (xs + rt - b['y'][1], rt - 0.5)]),
                         name='ramp up to the stow pad (no step)').bodies.item(0))
    body = p.join(parts)[0]
    p.prism([b['x0'] - 1, 0, 0], XF, 0, b['x1'] - b['x0'] + 2, sh.circle(g2.P['bore_r']), name='pipe bore', op=CUT,
            targets=[body])
    for x0, x1 in ((b['front_lift'], b['x1'] + 8), (b['x0'] - 1, g2.P['near_ring_x'])):   # all of the front rides high
        p.prism([x0, 0, 0], XF, 0, x1 - x0, sh.rect(-30, g2.P['ring_top'], -40, 40), name='ring clearance', op=CUT,
                targets=[body])                                  # slides over the wrist ring's pipe sockets
    p.prism([0, 0, 0], ZF, -20, 20, sh.rect(-200, 20, -30, c['open_y']), name='clip openings', op=CUT, targets=[body])
    for xc in P['clips']:                                           # clamp screw: insert from the top, tip on the pipe
        p.prism([xc, b['y'][1], 0], YF, -12, 1, sh.circle(1.7), name='clamp screw hole', op=CUT, targets=[body])
        p.prism([xc, b['y'][1], 0], YF, -5.9, 1, sh.circle(2.0), name='clamp insert hole', op=CUT, targets=[body])
    p.prism([hg['x'], hg['y'], -zk - ct - 2], ZF, 0, 2 * (zk + ct) + 4, sh.circle(hg['pin_d'] / 2 + 0.2),
            name='hinge pin hole', op=CUT, targets=[body])
    p.prism([hg['x'] - hg['latch_r'], hg['y'], zk], ZF, 0, ct + 2, sh.circle(3.4), name='latch plunger hole (6.8: the M8 plunger cuts its own thread)', op=CUT,
            targets=[body])
    _soften(p, body, 2.0, lambda e: _mm(e)[1] > rt - 0.5 and _is_sharp(e))      # round the rib's top edges
    _soften(p, body, 1.5, lambda e: _is_sharp(e, 50.0) and not _hole_edge(e))   # and every other edge (user, 21 Oct)
    body.name = 'base (printed)'
    p.finish()
    return 'base: %d bodies' % p.comp.bRepBodies.count


KNUCKLE_TOP_DEG = -25.0     # where the bridge's top edge leaves the knuckle (deg from +X, round the hinge pin)


def carrier_outline():
    """Carrier side profile (rail X, Y): the bridge from the hinge knuckle over the grip and the trigger, bending down
    to the hub. Its top edge leaves the knuckle at KNUCKLE_TOP_DEG and its back edge is tangent to the knuckle, so the
    knuckle sits on a broad shoulder (it hung on a 3 mm sliver until 21 Oct)."""
    hg, cr, h, tv = P['hinge'], P['carrier'], P['hub'], P['trigger']
    cx, cy, R_ = hg['x'], hg['y'], hg['knuckle_r']
    xb = tv['pivot'][0] + 12                                            # bridge lifts clear of the link here
    ro, ri_ = cr['bend_r']
    x0, x1, yt, yb = h['x'][0], cr['x1'], cr['y'][1], cr['bridge_y0']
    k = math.sqrt(0.5)
    a = math.radians(KNUCKLE_TOP_DEG)
    top = (cx + (R_ - 0.5) * math.cos(a), cy + (R_ - 0.5) * math.sin(a))   # just inside the knuckle: overlaps it
    qx, qy = cx + 6, cr['y'][0]                                         # back edge: from the bridge underside,
    d = math.hypot(cx - qx, cy - qy)                                    # tangent to the knuckle's back
    ang = math.atan2(cy - qy, cx - qx) + math.asin((R_ - 0.5) / d)
    tl = math.sqrt(d ** 2 - (R_ - 0.5) ** 2)
    back = (qx + tl * math.cos(ang), qy + tl * math.sin(ang))
    return [top, (cx + 35, yt), (x1 - ro, yt),
            ('arc', (x1 - ro + ro * k, yt - ro + ro * k), (x1, yt - ro)),           # outer bend
            (x1, h['y'] + 5), (x0, h['y'] + 5), (x0, yb - ri_),
            ('arc', (x0 - ri_ + ri_ * k, yb - ri_ + ri_ * k), (x0 - ri_, yb)),     # inner bend (fillet)
            (xb, yb), (xb, cr['y'][0]), (qx, qy), back, (cx, cy)]


def knuckle_neck_mm():
    """Width of solid carrier where the knuckle meets the bridge: the longest run of a circle 2 mm outside the
    knuckle that lies inside the bridge outline, as a chord (mm)."""
    hg = P['hinge']
    cx, cy, r = hg['x'], hg['y'], hg['knuckle_r'] + 2.0
    poly = [q for q in carrier_outline() if not isinstance(q[0], str)]

    def inside(x, y):
        n, j = False, len(poly) - 1
        for i in range(len(poly)):
            (xi, yi), (xj, yj) = poly[i], poly[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                n = not n
            j = i
        return n
    N = 720
    hit = [inside(cx + r * math.cos(2 * math.pi * i / N), cy + r * math.sin(2 * math.pi * i / N)) for i in range(N)]
    best = run = 0
    for v in hit + hit:
        run = run + 1 if v else 0
        best = max(best, min(run, N))
    return 2 * r * math.sin(math.pi * best / N)


def _carrier(g):
    """Carrier (printed, one piece): hinge knuckle, a bridge forward over the grip and the trigger that bends down in a
    smooth curve to the hub, the hub, and its rounded nose with a slot for each claw (the slot walls carry the claw
    pivots)."""
    hg, cr, h, c = P['hinge'], P['carrier'], P['hub'], P['claw']
    p = Part(g, 'Gripper3 carrier (printed)', color=PRINT)
    zk = hg['knuckle_z']
    knuckle = p.cyl('z', [hg['x'], hg['y'], 0], hg['knuckle_r'], 2 * zk, name='knuckle')[0]
    x0 = h['x'][0]
    web = p.prism([0, 0, 0], ZF, -cr['z'], cr['z'], _path(carrier_outline()), name='bridge').bodies.item(0)
    hub = p.cyl('x', [(x0 + h['x'][1]) / 2, h['y'], 0], h['r'], h['x'][1] - x0, name='hub')[0]
    nr, nx = h['nose_r'], h['nose_x']
    prof = [(h['x'][1] - 1.0, 0.0), (h['x'][1] - 1.0, nr)]
    for i in range(1, 9):                                               # quarter-ellipse dome, nr -> 11 at the tip
        t = math.radians(90.0 * i / 8)
        prof.append((c['xp'] + 2.0 + (nx - c['xp'] - 2.0) * math.sin(t), 11.0 + (nr - 11.0) * math.cos(t)))
    prof.append((nx, 0.0))
    nose = _revolve_x(p, h['y'], prof, 'nose')
    sy, sp = spring_y(), P['spring']
    hook = p.box(sp['hub_hook'], x0 + 0.5, sy - 4.0, sy + 4.0, -3.0, 3.0, name='spring hook lug')[0]
    hook_end = p.cyl('z', [sp['hub_hook'], sy, 0], 4.0, 6.0, name='spring hook lug end')[0]
    body = p.join([knuckle, web, hub, nose, hook, hook_end])[0]
    p.prism([sp['hub_hook'], sy, -4.0], ZF, 0, 8.0, sh.circle(1.2), name='spring hook hole', op=CUT, targets=[body])
    p.prism([hg['x'], hg['y'], -zk - 1], ZF, 0, 2 * zk + 2, sh.circle(hg['pin_d'] / 2 + 0.2), name='hinge bore',
            op=CUT, targets=[body])
    ft = c['t'] / 2 + 0.4
    for al in c['alphas']:                                              # claw slots: root swings back, body out
        p.prism(to_xyz(0, 0, al), claw_frame(al), -ft, ft,
                _poly([(h['x'][1] - 9 - c['xp'], 15.0), (h['x'][1] - 9 - c['xp'], 45.0), (nx - c['xp'] + 5, 45.0),
                       (nx - c['xp'] + 5, -2.0), (h['x'][1] - c['xp'], -2.0), (h['x'][1] - c['xp'], 15.0)]),
                name='claw slot', op=CUT, targets=[body])
        tw = PIVOT_HEAD_T
        p.prism(to_xyz(0, c['rp'], al, -tw - 8), claw_frame(al), 0, 2 * tw + 16, sh.circle(1.7),
                name='claw pivot hole', op=CUT, targets=[body])
        p.prism(to_xyz(0, c['rp'], al, -tw - 2.5), claw_frame(al), 0, 2.5, sh.circle(3.3),
                name='pivot head seat', op=CUT, targets=[body])
        p.prism(to_xyz(0, c['rp'], al, -tw - 10), claw_frame(al), 0, 7.5, sh.circle(6.0),
                name='pivot screw entry (wide, for the driver; breaks cleanly through the dome)', op=CUT, targets=[body])
        p.prism(to_xyz(0, c['rp'], al, PIVOT_INSERT[0]), claw_frame(al), 0, 12.0, sh.circle(2.0),
                name='pivot insert hole (from outside)', op=CUT, targets=[body])
        p.prism(to_xyz(0, c['rp'], al, 13.0), claw_frame(al), 0, 10.0, sh.circle(3.0),
                name='insert mouth (no feather edge on the dome)', op=CUT, targets=[body])
    for ang in (180.0, 180.0 - hg['stow_deg']):                         # fold latch: in use, and stowed
        a_ = math.radians(ang)
        p.prism([hg['x'] + hg['latch_r'] * math.cos(a_), hg['y'] + hg['latch_r'] * math.sin(a_), zk + 1], ZF, -4.5, 0,
                sh.circle(2.8), name='latch hole', op=CUT, targets=[body])
    for xx in GRIP_SCREWS:                                              # grip screw inserts in the spine's underside
        for zz in (-7.0, 7.0):
            p.prism([xx, cr['y'][0], zz], YF, -1, 6.0, sh.circle(2.0), name='insert hole', op=CUT, targets=[body])
    body.name = 'carrier (printed)'
    p.finish()
    return 'carrier: %d bodies' % p.comp.bRepBodies.count


def _tip_as_arc(out):
    """The claw outline with its 7-point round tip drawn as one true arc and the outer edge as one smooth spline
    (one face, so its long edges round cleanly)."""
    c = P['claw']
    i = next(k for k, q in enumerate(out) if q[0] > c['L'] + 1e-6)
    tip = out[i:i + 7]
    return out[:i] + [('arc', tip[3], out[i + 7]), ('spline', out[i + 8:])]


def _cap(p, al, a0, rc0, a1, rc1, R, n=16):
    """Half-spheroid cap (claw frame) on the axis from (a0, rc0) to its tip (a1, rc1): round, radius R, at the start,
    closing at the tip. The axis follows the claw's centre line, which drops toward the claw axis near the tip."""
    o = to_xyz(0, 0, al)
    ex, ey, ez = claw_frame(al)
    pl = p.plane(o, ez, ex)
    sk = p._hidden_sketch(pl, 'tip cap')
    to = lambda a, r: sk.modelToSketchSpace(fx.P(to_xyz(a, r, al)))
    L_ = math.hypot(a1 - a0, rc1 - rc0)
    u = ((a1 - a0) / L_, (rc1 - rc0) / L_)
    nrm = (-u[1], u[0])
    pts = []
    for k in range(n + 1):
        t = math.radians(90.0 * k / n)
        pts.append((a0 + u[0] * L_ * math.sin(t) + nrm[0] * R * math.cos(t),
                    rc0 + u[1] * L_ * math.sin(t) + nrm[1] * R * math.cos(t)))
    ln = sk.sketchCurves.sketchLines
    sk.sketchCurves.sketchFittedSplines.add(fx.coll([to(*q) for q in pts]))
    axis = ln.addByTwoPoints(to(a1, rc1), to(a0, rc0))
    ln.addByTwoPoints(to(a0, rc0), to(*pts[0]))
    prof = sk.profiles.item(0)
    ri = p.comp.features.revolveFeatures.createInput(prof, axis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ri.setAngleExtent(False, adsk.core.ValueInput.createByString('360 deg'))
    return p.comp.features.revolveFeatures.add(ri).bodies.item(0)


def _claws(g):
    """Three claws (TPU 95A, flat prints): curved fin-ray, cupped inner face, root disc on the pivot, tail out-and-back
    for the collar's pin."""
    c = P['claw']
    out = claw_outline()
    names = []
    for k, al in enumerate(c['alphas']):
        p = Part(g, 'Gripper3 claw %d (TPU)' % (k + 1), color=TPU)
        fr = claw_frame(al)
        o = to_xyz(0, 0, al)
        body = p.prism(o, fr, -c['t'] / 2, c['t'] / 2, _path(_tip_as_arc(out)), name='claw').bodies.item(0)
        disc = p.prism(o, fr, -c['t'] / 2, c['t'] / 2,
                       lambda sk, to: sk.sketchCurves.sketchCircles.addByCenterRadius(to(0, c['rp']), CLAW_DISC_R / 10.0),
                       name='root disc').bodies.item(0)
        ta, tr = c['tail']
        tail = p.prism(o, fr, -3.0, 3.0, _poly([(-2, c['rp'] - 3), (ta - 3, c['rp'] + tr - 3), (ta - 3, c['rp'] + tr + 3),
                                                (2, c['rp'] + 4)]), name='tail').bodies.item(0)
        body = p.join([body, disc, tail])[0]
        er, et = fr[1], fr[2]                                       # drill-chuck wedge: trim to the 120 deg sector
        t60, off = math.tan(math.radians(60)), 2 * c['wedge_gap']
        for sgn in (1, -1):
            side = (er, [sgn * v for v in et], [sgn * v for v in fr[0]])
            p.prism(to_xyz(-30 if sgn > 0 else c['L'] + 10, 0, al), side, 0, c['L'] + 40,
                    _poly([(-10, -10 * t60 - off), (25, 25 * t60 - off), (-10, 25 * t60)]),
                    name='sector trim', op=CUT, targets=[body])
        for q in claw_cells():                                      # fin-ray: open cells through the claw
            p.prism(o, fr, -c['t'], c['t'], _poly(q), name='fin-ray cell', op=CUT, targets=[body])
        p.prism(o, fr, -c['t'], c['t'], lambda sk, to: sk.sketchCurves.sketchCircles.addByCenterRadius(to(0, c['rp']), 0.17),
                name='pivot bore', op=CUT, targets=[body])
        p.prism(o, fr, -4, 4, lambda sk, to: sk.sketchCurves.sketchCircles.addByCenterRadius(to(ta, c['rp'] + tr), 0.17),
                name='tail pin bore', op=CUT, targets=[body])
        _soften(p, body, 1.5, lambda e: isinstance(e.geometry, adsk.core.NurbsCurve3D) and e.length * 10 > 30)   # back
        cv_ = claw_curves(400)                                      # egg cap: starts round the whole section, no steps
        ri_t, ro_t = cv_[-1][1], cv_[-1][2]
        ra_ = 26.0
        a_s = c['L'] + (ro_t - ri_t) / 2 - ra_
        q_ = min(cv_, key=lambda q: abs(q[0] - a_s))
        rc_ = (q_[1] + q_[2]) / 2
        R_ = math.hypot((q_[2] - q_[1]) / 2, c['t'] / 2) + 0.3      # round cap, wider than the section's corners
        a1_, rc1_ = c['L'] + (ro_t - ri_t) / 2, (ro_t + ri_t) / 2
        keep = _cap(p, al, a_s, rc_, a1_, rc1_, R_)
        L_ = math.hypot(a1_ - a_s, rc1_ - rc_)
        u_ = ((a1_ - a_s) / L_, (rc1_ - rc_) / L_)
        n_ = (-u_[1], u_[0])
        corner = lambda s_, w_: (a_s + u_[0] * s_ + n_[0] * w_, rc_ + u_[1] * s_ + n_[1] * w_)
        zone = p.prism(o, fr, -c['t'] / 2 - 3, c['t'] / 2 + 3,             # starts square to the cap's axis
                       _poly([corner(0, -16), corner(L_ + 20, -16), corner(L_ + 20, 16), corner(0, 16)]),
                       name='tip zone').bodies.item(0)
        tool = p.cut([zone], [keep])[0]
        body = p.cut([body], [tool])[0]
        _soften(p, body, 1.5, lambda e: _mm(e)[0] > c['xp'] + a_s and _is_sharp(e, 50.0))   # where the cap meets the top
        body.name = 'claw %d (TPU)' % (k + 1)
        p.finish()
        names.append(body.name)
    return names


def _slot_r(a, r0, r1, w):
    """A slot along r at a (claw-plane sketch)."""
    def draw(sk, to):
        ln, ar = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
        h = w / 2
        ln.addByTwoPoints(to(a - h, r0), to(a - h, r1))
        ln.addByTwoPoints(to(a + h, r0), to(a + h, r1))
        ar.addByThreePoints(to(a - h, r1), to(a, r1 + h), to(a + h, r1))
        ar.addByThreePoints(to(a + h, r0), to(a, r0 - h), to(a - h, r0))
    return draw


def _cheek_pad(p, co, al):
    """Thickens the skirt round one claw tail's pair of cheeks, out to skirt_r, with a 45 deg underside so it prints
    on the ring (the collar prints ring down). Only there: the Y link's arms pass the collar's sides at r ~38."""
    x1, r0, r1, xp, sx = co['x'][1], co['r'][1], co['skirt_r'], P['claw']['xp'], co['skirt'][0]
    w = TAIL_CHEEK[1] + 0.5
    return p.prism(to_xyz(0, 0, al), claw_frame(al), -w, w,
                   _poly([(x1 - (r1 - r0) - xp, r0 - 0.5), (x1 - (r1 - r0) - xp, r0), (x1 - xp, r1), (sx - xp, r1),
                          (sx - xp, r0 - 0.5)]), name='cheek pad').bodies.item(0)


def _collar(g):
    """Collar (printed, one piece): a ring sliding on the hub with a skirt over the nose, slotted for the three claw
    tails (each tail's pin crosses its slot), and two round side lobes for the Y link's pins. Pulled back, it drags
    the three tails back: all claws open together; pushed forward, it closes them."""
    h, c, co = P['hub'], P['claw'], P['collar']
    p = Part(g, 'Gripper3 collar (printed)', color=GRN)
    ring = p.ann('x', [sum(co['x']) / 2, h['y'], 0], co['r'][1], co['r'][0], co['x'][1] - co['x'][0], name='ring')[0]
    sx, sr = co['skirt']
    skirt = p.ann('x', [(co['x'][1] - 0.5 + sx) / 2, h['y'], 0], co['r'][1], sr, sx - co['x'][1] + 0.5, name='skirt')[0]
    hy, (z0, z1), lr = pull_point(0.0)[1], co['lug_z'], co['lobe_r']
    def lobe(zc):
        return lambda sk, to: sk.sketchCurves.sketchCircles.addByCenterRadius(to(hy, zc), lr / 10.0)
    lobes = [p.prism([co['x'][0], 0, 0], XF, 0, co['x'][1] - co['x'][0], lobe(sg * (z1 - lr)), name='side lobe')
             .bodies.item(0) for sg in (1, -1)]
    body = p.join([ring, skirt] + lobes)[0]
    p.prism([co['x'][0] - 1, h['y'], 0], XF, 0, co['x'][1] - co['x'][0] + 2, sh.circle(co['r'][0]), name='bore',
            op=CUT, targets=[body])                                  # nothing may reach into the bore (lobes did)
    pr, pw = co['pad']                                               # the bore clears the nose so the collar goes on
    for al in c['alphas']:                                           # over it; three pads centre it on the hub, and
        pad = p.prism(to_xyz(0, 0, al), claw_frame(al), -pw / 2, pw / 2,   # pass the nose through the claw slots
                      _poly([(co['x'][0] - c['xp'], pr), (co['x'][1] - c['xp'], pr), (co['x'][1] - c['xp'], co['r'][0] + 0.5),
                             (co['x'][0] - c['xp'], co['r'][0] + 0.5)]), name='centring pad').bodies.item(0)
        body = p.join([body, pad])[0]
    body = p.join([body] + [_cheek_pad(p, co, al) for al in c['alphas']])[0]   # cheeks out to skirt_r, 45 deg below
    ta, tr = c['tail']
    for al in c['alphas']:
        p.prism(to_xyz(0, 0, al), claw_frame(al), -TAIL_CHEEK[0], TAIL_CHEEK[0],
                _poly([(co['x'][1] - c['xp'] - 1, sr - 1), (sx - c['xp'] + 1, sr - 1), (sx - c['xp'] + 1, co['skirt_r'] + 3),
                       (co['x'][1] - c['xp'] - 1, co['skirt_r'] + 3)]), name='tail slot', op=CUT, targets=[body])
        p.prism(to_xyz(0, 0, al), claw_frame(al), -TAIL_CHEEK[1] - 1, TAIL_CHEEK[1] + 1, _slot_r(ta, c['rp'] + 4.0, c['rp'] + tr + 0.3, 3.4),
                name='tail pin slot', op=CUT, targets=[body])
        for sg in (1, -1):                                          # open beside the two cheeks: screw + nut reachable
            z_a, z_b = sorted((sg * TAIL_CHEEK[1], sg * 22.0))
            p.prism(to_xyz(0, 0, al), claw_frame(al), z_a, z_b,
                    _poly([(co['x'][1] - c['xp'] + 2.0, sr - 4), (sx - c['xp'] + 1, sr - 4),
                           (sx - c['xp'] + 1, co['skirt_r'] + 3), (co['x'][1] - c['xp'] + 2.0, co['skirt_r'] + 3)]),
                    name='open beside the tail cheeks', op=CUT, targets=[body])
        p.prism(to_xyz(0, 0, al), claw_frame(al), -TAIL_CHEEK[1] - 1, TAIL_CHEEK[1] + 1,   # round the claw's root disc
                lambda sk, to: sk.sketchCurves.sketchCircles.addByCenterRadius(to(0, c['rp']), (CLAW_DISC_R + 0.6) / 10.0),
                name='claw root clearance', op=CUT, targets=[body])
    for sg in (1, -1):
        p.prism([sum(co['x']) / 2, hy, sg * z1], ZF, *sorted((-sg * 6.0, 0.5 * sg)), sh.circle(2.0), name='insert hole',
                op=CUT, targets=[body])
    body.name = 'collar (printed)'
    p.finish()
    return 'collar ok'


def yoke_pin_x():
    return sum(P['collar']['x']) / 2


def _link(g):
    """Y link (printed flat, PETG): a stem from the trigger's fork forward over the fingers, splitting into two angled
    arms that run either side of the hub to the collar's side lugs; pinned at all three ends."""
    lk = P['link']
    hx, hy = pull_point(0.0)
    xs, xk, xc, r, (za, zb) = lk['split'], lk['kink'], yoke_pin_x(), lk['h'] / 2, lk['arm_z']
    zm = (za + zb) / 2
    p = Part(g, 'Gripper3 link (printed)', color=PRINT)
    parts = [p.box(hx, xs + 1.0, hy - r, hy + r, -lk['w'] / 2, lk['w'] / 2, name='stem')[0],
             p.cyl('z', [hx, hy, 0], r, lk['w'], name='end')[0]]
    for sg in (1, -1):
        L = math.hypot(xk - xs, zm)
        ux, uz = (xk - xs) / L, sg * zm / L                           # along the angled arm, and square to it
        nx, nz = -uz, ux
        w0, w1 = lk['diag_w'] / 2, lk['w'] / 2
        quad = [(xs - ux * 2 + nx * w0, -uz * 2 + nz * w0), (xs - ux * 2 - nx * w0, -uz * 2 - nz * w0),
                (xk + ux * 2 - nx * w1, sg * zm + uz * 2 - nz * w1), (xk + ux * 2 + nx * w1, sg * zm + uz * 2 + nz * w1)]
        parts.append(p.prism([0, hy - r, 0], YF, 0, 2 * r, _xz(quad), name='angled arm').bodies.item(0))
        z0, z1 = sorted((sg * za, sg * zb))
        parts.append(p.box(xk - 1.0, xc, hy - r, hy + r, z0, z1, name='arm')[0])
        parts.append(p.cyl('z', [xc, hy, (z0 + z1) / 2], r, zb - za, name='end')[0])
    sy, sp = spring_y(), P['spring']
    h0, h1 = min(sp['link_holes']), max(sp['link_holes'])           # tab with three hook holes: set the preload
    parts.append(p.box(h0, h1, hy + r - 0.5, sy + 3.5, -3.0, 3.0, name='spring hook lug')[0])
    parts.append(p.box(h0 - 3.5, h1 + 3.5, hy + r - 0.5, sy, -3.0, 3.0, name='spring hook lug base')[0])
    parts += [p.cyl('z', [x_, sy, 0], 3.5, 6.0, name='spring hook lug end')[0] for x_ in (h0, h1)]
    body = p.join(parts)[0]
    for x_ in sp['link_holes']:
        p.prism([x_, sy, -4.0], ZF, 0, 8.0, sh.circle(1.2), name='spring hook hole', op=CUT, targets=[body])
    p.prism([hx, hy, -lk['w']], ZF, 0, 2 * lk['w'], sh.circle(1.6), name='pin hole', op=CUT, targets=[body])
    p.prism([xc, hy, -zb - 1], ZF, 0, 2 * zb + 2, sh.circle(1.7), name='arm pin holes', op=CUT, targets=[body])
    body.name = 'link (printed)'
    p.finish()
    return 'link ok'


def stow_point(x, y, off=0.0):
    """Where the carrier point (x, y) is when folded to stow_deg, pushed off mm along the bridge top's outward normal."""
    hg = P['hinge']
    t = math.radians(hg['stow_deg'])
    dx, dy = x - hg['x'], y - hg['y']
    n = (-math.sin(t), math.cos(t))
    return (hg['x'] + dx * math.cos(t) - dy * math.sin(t) + n[0] * off,
            hg['y'] + dx * math.sin(t) + dy * math.cos(t) + n[1] * off), n


def spring_y():
    """Height of the return spring's axis: just above the Y link, under the bridge's bend."""
    return pull_point(0.0)[1] + P['spring']['rise']


def _oval_xz(cx, cz, rx, rz):
    """Smooth closed oval (X radius rx, Z radius rz) for a YF sketch: one closed fitted spline."""
    def draw(sk, to):
        pts = fx.coll([to(cz + rz * math.sin(math.radians(k * 30)), cx + rx * math.cos(math.radians(k * 30)))
                       for k in range(12)])
        sk.sketchCurves.sketchFittedSplines.add(pts).isClosed = True
    return draw


def _hull(pts):
    """Convex hull (monotone chain) of 2D points, counter-clockwise."""
    pts = sorted(set((round(x, 4), round(y, 4)) for x, y in pts))
    cross_ = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for q in pts:
        while len(lo) >= 2 and cross_(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(pts):
        while len(hi) >= 2 and cross_(hi[-2], hi[-1], q) <= 0:
            hi.pop()
        hi.append(q)
    return lo[:-1] + hi[:-1]


def _grip(g):
    """Grip (printed, on its side): the pistol grip with a top plate bolted under the carrier, and the two cheeks that
    carry the trigger pivot in front of it."""
    gr, tv, cr = P['grip'], P['trigger'], P['carrier']
    px_, py_ = tv['pivot']
    p = Part(g, 'Gripper3 grip (printed)', color=PRINT)
    cx_, hw_, (bx, bz) = GRIP_POST                                  # cross post: two blades between the 4 screws
    yb = gr['y'][1] - 12                                            # under the plate
    yf = gr['y'][0] + GRIP_FLOOR                                    # post foot: on the sleeve's floor
    blades = [p.box(cx_ - bx, cx_ + bx, yf, yb + 0.1, -hw_, hw_, name='post blade (front-back)')[0],
              p.box(cx_ - hw_, cx_ + hw_, yf, yb + 0.1, -bz, bz, name='post blade (side-side)')[0]]
    grip = p.join(blades)[0]
    zc = tv['z'][1] + 4.5                                           # plate: back half of the grip oval, a straight
    back = [(gr['x'] + gr['r'] * math.cos(math.radians(k)), gr['z'] + gr['r'] * 1.08 * math.sin(math.radians(k)))
            for k in range(90, 271, 10)]                                # taper to the cheeks, straight along them
    pts = back + [(px_ - 12, -zc), (px_ + 8, -zc), (px_ + 8, zc), (px_ - 12, zc)]
    plate = p.prism([0, gr['y'][1], 0], YF, -12, -0.1, _xz(pts), name='top plate').bodies.item(0)
    parts = [grip, plate]
    for z0, z1 in ((tv['z'][0] - 4.5, tv['z'][0] - 0.5), (tv['z'][1] + 0.5, tv['z'][1] + 4.5)):
        parts.append(p.box(px_ - 8, px_ + 8, py_ - 6, gr['y'][1] - 11.0, z0, z1, name='trigger cheek')[0])
    body = p.join(parts)[0]
    p.prism([0, 0, 0], ZF, tv['z'][0] - 0.5, tv['z'][1] + 0.5,
            sh.rect(px_ - 7, px_ + 9, gr['y'][1] - 13, gr['y'][1] + 1), name='trigger bay', op=CUT, targets=[body])
    p.prism([px_, py_, tv['z'][0] - 6], ZF, 0, tv['z'][1] - tv['z'][0] + 12, sh.circle(1.7), name='pivot hole',
            op=CUT, targets=[body])
    for xx in GRIP_SCREWS:
        for zz in (-7.0, 7.0):
            p.prism([xx, gr['y'][1], zz], YF, -13, 1, sh.circle(1.7), name='screw hole', op=CUT, targets=[body])
            p.prism([xx, gr['y'][1] - 13, zz], YF, 0, 5, sh.circle(3.25), name='head counterbore (open below)', op=CUT,
                    targets=[body])
    p.prism([cx_, yf - 1, 0], YF, 0, 9.0, sh.circle(2.0), name='insert hole (the sleeve screws on here)', op=CUT,
            targets=[body])
    body.name = 'grip (printed)'
    p.finish()
    q = Part(g, 'Gripper3 grip sleeve (printed)', color=PRINT)     # slides up over the post once the 4 screws are in
    sv = q.prism([0, yb - 0.2, 0], YF, gr['y'][0] - yb + 0.2, 0,
                 _oval_xz(gr['x'], gr['z'], gr['r'], gr['r'] * 1.08), name='grip sleeve').bodies.item(0)
    c_ = GRIP_FIT
    for x0, x1, z0, z1 in ((cx_ - bx - c_, cx_ + bx + c_, -hw_ - c_, hw_ + c_), (cx_ - hw_ - c_, cx_ + hw_ + c_, -bz - c_, bz + c_)):
        sv = q.cut([sv], [q.box(x0, x1, yf, yb + 1, z0, z1, name='bore (the post)')[0]])[0]
        sv = q.cut([sv], [q.box(x0 - 0.5, x1 + 0.5, yb - 0.8, yb + 1, z0 - 0.5, z1 + 0.5,   # mouth relief: it prints
                                name='bore mouth relief')[0]])[0]                       # mouth down (elephant foot)
    q.prism([cx_, gr['y'][0] - 1, 0], YF, 0, GRIP_FLOOR + 2, sh.circle(1.7), name='screw hole', op=CUT, targets=[sv])
    q.prism([cx_, gr['y'][0] - 1, 0], YF, 0, 4.0, sh.circle(3.0), name='head counterbore', op=CUT, targets=[sv])
    _soften(q, sv, 6.0, lambda e: _mm(e)[1] < gr['y'][0] + 1.0)        # round bottom rim
    sv.name = 'grip sleeve (printed)'
    q.finish()
    return 'grip ok'


CLAMP_SCREW = 12.0                             # mm: pipe clamp screw length (M3 x 10 thumb screws couldn't clamp)
GRIP_SCREWS = (58.0, 73.0)                     # rear pair far enough in that the counterbores stay inside the grip
GRIP_POST = (65.5, 3.5, (12.5, 13.0))          # grip for now (user, 27 Oct: the screw heads were sealed inside the
                                               # grip): a cross post between the 4 screws, x centre, blade half-width,
                                               # half-lengths (front-back, side-side); a sleeve slides over it
GRIP_FLOOR, GRIP_FIT = 4.0, 0.25               # sleeve: floor under the post's foot; bore clearance per side
CLAW_DISC_R = 7.4                              # claw root disc: covers the outline's root corners (15..29 at a=0)
TRIGGER_EYE_R = 6.0                            # trigger's pivot ring radius
FORK_TOP = 5.8                                 # link slot top above the pull pin, under the pivot ring
FORK_TOP_FRONT = 7.6                           # ... and further forward, where the tilting link needs room
CHEEK_NECK = 32.0                              # mm: narrowest width of a base hinge cheek (between bridge and knuckle)
TAIL_CHEEK = (3.4, 9.4)                       # collar cheeks either side of a claw tail: inner, outer |t| (4 mm broke)
CHEEK_MIN = 3.5                                # mm: least plastic round the tail pin's slot, every side (rule)
CHEEK_W = 5.5                                  # mm: least cheek width along the pin (4 broke)
PIVOT_HEAD_T = 15.0                            # claw pivot screw head sits this far out (tangential) in the nose
PIVOT_INSERT = (9.7, 5.7)                      # far-wall insert: starts this far out (tangential), length
WALL = 7.6                                     # claw slot wall carrying a pivot: from the slot to the head's spot face
KNOCK = 20.0                                   # N: side knock on an exposed link, mid-span, simply supported (M = F L / 4)
LINK_SECTION, LINK_MATERIAL = ('rect', 6.0, 10.0), 'PETG along layers'   # printed link, knocked across its 6 mm


def pull_point(squeeze=0.0):
    """(x, y) of the pull pin: pull_r down the trigger's centre line from the pivot (so the lever has a solid wall
    either side of its hole), swinging back by travel_deg as the trigger is squeezed (rises < 1 mm)."""
    tv = P['trigger']
    px_, py_ = tv['pivot']
    a = math.radians(tv['rest_deg'] - squeeze * tv['travel_deg'])   # on the lever's centre line: walls both sides
    return (px_ + tv['pull_r'] * math.sin(a), py_ - tv['pull_r'] * math.cos(a))


def trigger_pull(squeeze):
    """mm the link (disk, rods, collar) is pulled back at this squeeze."""
    return pull_point(0.0)[0] - pull_point(squeeze)[0]


def _trigger(g):
    """Spray-bottle trigger (printed, flat): lever hanging from the pivot at the grip's top front; a fork slot in its
    top holds the pull link on a pin."""
    tv = P['trigger']
    px_, py_ = tv['pivot']
    a = math.radians(tv['rest_deg'])
    d, n = (math.sin(a), -math.cos(a)), (math.cos(a), math.sin(a))
    T, L = tv['t'], tv['len']
    pts = []
    for k in range(9):
        s_ = L * k / 8
        bow = 2.5 * math.sin(math.pi * k / 8)
        pts.append((px_ + d[0] * s_ + n[0] * (T / 2 + bow), py_ + d[1] * s_ + n[1] * (T / 2 + bow)))
    pts += [(px_ + d[0] * L - n[0] * T / 2, py_ + d[1] * L - n[1] * T / 2), (px_ - n[0] * T / 2, py_ - n[1] * T / 2)]
    R_ = TRIGGER_EYE_R - 0.3                                        # neck: the lever's edges taper out into the ring
    pts[0] = (px_ + n[0] * R_, py_ + n[1] * R_)                     # (one outline, so nothing to join)
    pts[-1] = (px_ - n[0] * R_, py_ - n[1] * R_)
    p = Part(g, 'Gripper3 trigger (printed)', color=GRN)
    lever = p.prism([0, 0, 0], ZF, tv['z'][0], tv['z'][1], _poly(pts), name='lever').bodies.item(0)
    eye = p.cyl('z', [px_, py_, sum(tv['z']) / 2], TRIGGER_EYE_R, tv['z'][1] - tv['z'][0], name='eye')[0]   # flush faces
    body = p.join([lever, eye])[0]
    # one flat back face to print on (user, 21 Oct): fill the lever out to the line from its bottom back corner that
    # just clears the pivot ring (0.2 mm proud, so no face only grazes another)
    bx, by = px_ + d[0] * L - n[0] * T / 2, py_ + d[1] * L - n[1] * T / 2
    rr = TRIGGER_EYE_R + 0.2
    dist = math.hypot(px_ - bx, py_ - by)
    mx, my = px_ + d[0] * L / 2, py_ + d[1] * L / 2                    # a point on the lever's centre line
    best = None
    for sg in (1, -1):                                                  # of the two tangents from the back corner,
        ang = math.atan2(py_ - by, px_ - bx) + sg * math.asin(rr / dist)   # keep the one clear of the lever
        u_ = (math.cos(ang), math.sin(ang))
        off = (mx - bx) * u_[1] - (my - by) * u_[0]
        if best is None or abs(off) > abs(best[1]):
            best = (u_, off)
    u = best[0]
    tl = math.sqrt(dist ** 2 - rr ** 2)
    tx, ty = bx + u[0] * tl, by + u[1] * tl                             # where the face meets the ring
    back = p.prism([0, 0, 0], ZF, tv['z'][0], tv['z'][1],
                   _poly([(bx, by), (tx, ty), (px_, py_), (px_ + d[0] * L, py_ + d[1] * L)]),
                   name='flat back face').bodies.item(0)
    body = p.join([body, back])[0]
    p.prism([px_, py_, tv['z'][0]], ZF, -1, tv['z'][1] - tv['z'][0] + 2, sh.circle(1.7), name='pivot bore', op=CUT,
            targets=[body])
    hx, hy = pull_point(0.0)
    zi = P['link']['w'] / 2 + 0.3
    p.prism([0, 0, 0], ZF, -zi, zi, _poly([(hx - 14.0, hy - 6.0), (hx + 20.0, hy - 6.0), (hx + 20.0, hy + FORK_TOP_FRONT),
                                           (hx + 6.0, hy + FORK_TOP_FRONT), (hx + 1.0, hy + FORK_TOP),
                                           (hx - 14.0, hy + FORK_TOP)]), name='link fork', op=CUT,   # open at the back: no skin
            targets=[body])
    p.prism([hx, hy, tv['z'][0] - 1], ZF, 0, tv['z'][1] - tv['z'][0] + 2, sh.circle(1.6), name='pull pin hole', op=CUT,
            targets=[body])
    _soften(p, body, 2.0, lambda e: _mm(e)[1] < hy - 7.0 and _is_sharp(e))      # nothing sharp under the fingers
    body.name = 'trigger (printed)'
    p.finish()
    return 'trigger ok'


def _m3_nyloc(part, c, name):
    """M3 nyloc (5.5 across flats, 4 tall) on the +Z face at c: the screw's thread bites it (fastener_check THREAD)."""
    nut = part.prism(c, ZF, 0, 4.0, sh.hexagon(5.5), name='nut').bodies.item(0)
    part.prism(c, ZF, -1, 6.0, sh.circle(1.5), name='nut bore', op=CUT, targets=[nut])
    nut.name = name
    return nut


def _hw(g):
    """Bought parts: hinge pin, latch plunger, clamp screws, claw pivot pins, tail pins, grip screws + inserts,
    trigger pivot + pull pin, yoke pins + inserts, return spring."""
    hg, c, co, gr, tv = P['hinge'], P['claw'], P['collar'], P['grip'], P['trigger']
    up, down = sh.frame_of([0, -1, 0]), sh.frame_of([0, 1, 0])
    base_hw = Part(g, 'Gripper3 HW base (buy)', color=HWC)
    zt = hg['knuckle_z'] + 0.4 + hg['cheek_t']
    sh.hw_bolt(base_hw, [hg['x'], hg['y'], zt], sh.frame_of([0, 0, -1]), 55.0, (13.0, 8.0),   # head by the plunger,
               'M8 x 55 socket head, fold hinge (buy)', dia=8.0)                              # nut on the open side
    sh.hw_nut(base_hw, [hg['x'], hg['y'], -zt], sh.frame_of([0, 0, -1]), 'M8 nyloc nut, fold hinge (buy)')
    lx = hg['x'] - hg['latch_r']
    pl = base_hw.cyl('z', [lx, hg['y'], zt + 6], 3.9, 12, name='plunger')[0]
    pin = base_hw.cyl('z', [lx, hg['y'], (hg['knuckle_z'] - 1.5 + zt) / 2], 2.5, zt - hg['knuckle_z'] + 1.5, name='pin')[0]
    knob = base_hw.cyl('z', [lx, hg['y'], zt + 17], 7.0, 10, name='knob')[0]
    pl = base_hw.join([pl, pin, knob])[0]
    pl.name = 'index plunger M8-1.25, pull ring, pin 5 mm, screwed into the cheek + its lock nut: fold latch (buy)'
    for xc in P['clips']:                                           # loosen both, slide the gripper, tighten
        sh.hw_bolt(base_hw, [xc, P['base']['y'][1], 0], up, P['base']['y'][1] - g2.P['pipe_r'], (5.5, 3.0),   # tip
                   'M3 x %.0f socket head, pipe clamp (buy)' % CLAMP_SCREW, dia=3.0)          # on the pipe, head up
        ins = base_hw.cyl('y', [xc, P['base']['y'][1] - 2.85, 0], 2.0, 5.7, name='insert')[0]
        ins.name = 'M3 heat-set insert ruthex 5.7, pipe clamp (buy)'
    vc = P['velcro']
    (cx, cy), n = stow_point(vc['x'], P['carrier']['y'][1], 2 * vc['t'])
    base_hw.prism([cx, cy, 0], sh.frame_of([-n[0], -n[1], 0]), 0, vc['t'], sh.circle(vc['d'] / 2),
                  name='dot').bodies.item(0).name = 'hook-and-loop dot %d mm, base side (buy)' % vc['d']
    base_hw.finish()
    car = Part(g, 'Gripper3 HW carrier (buy)', color=HWC)
    ft = PIVOT_HEAD_T
    for al in c['alphas']:
        e = claw_frame(al)[2]
        sh.hw_bolt(car, to_xyz(0, c['rp'], al, -ft), sh.frame_of(e), 30.0, (5.5, 3.0),
                   'M3 x 30 socket head, claw pivot, into an insert in the far slot wall (buy)', dia=3.0)
        car.prism(to_xyz(0, c['rp'], al, PIVOT_INSERT[0]), claw_frame(al), 0, PIVOT_INSERT[1], sh.circle(2.0),
                  name='insert').bodies.item(0).name = 'M3 heat-set insert ruthex 5.7, claw pivot (buy)'
    for xx in GRIP_SCREWS:
        for zz in (-7.0, 7.0):
            sh.hw_bolt(car, [xx, gr['y'][1] - 9, zz], down, 12.0, (5.5, 3.0), 'M3 x 12 socket head, grip (buy)', dia=3.0)
            ins = car.cyl('y', [xx, gr['y'][1] + 2.85, zz], 2.0, 5.7, name='insert')[0]
            ins.name = 'M3 heat-set insert ruthex 5.7, grip (buy)'
    yf = gr['y'][0] + GRIP_FLOOR                                     # the sleeve: one screw up into the post's foot
    sh.hw_bolt(car, [GRIP_POST[0], gr['y'][0] + 3.0, 0], down, 8.0, (5.5, 3.0), 'M3 x 8 socket head, grip sleeve (buy)',
               dia=3.0)
    car.cyl('y', [GRIP_POST[0], yf + 2.85, 0], 2.0, 5.7, name='insert')[0].name =         'M3 heat-set insert ruthex 5.7, grip sleeve (buy)'
    sp, sy = P['spring'], spring_y()
    xa, xb = sp['link_hook'] + 4.0, sp['hub_hook'] - 4.0               # coil between the lugs, hooks through them
    parts = [car.ann('x', [(xa + xb) / 2, sy, 0], sp['od'] / 2, sp['od'] / 2 - 0.8, xb - xa, name='coil')[0]]
    for xh, xe, sg in ((sp['link_hook'], xa, 1), (sp['hub_hook'], xb, -1)):   # loop ends: through each lug's hole
        parts.append(car.cyl('z', [xh, sy, 0], 1.1, 8.0, name='loop')[0])
        parts.append(car.box(min(xh, xe + sg * 0.5), max(xh, xe + sg * 0.5), sy - 0.7, sy + sp['od'] / 2 - 0.4,
                             -0.7, 0.7, name='loop leg')[0])                  # up to the coil's wire
    vc = P['velcro']                                                  # hook-and-loop dot on the bridge top
    car.cyl('y', [vc['x'], P['carrier']['y'][1] + vc['t'] / 2, 0], vc['d'] / 2, vc['t'],
            name='dot')[0].name = 'hook-and-loop dot %d mm, carrier side (buy)' % vc['d']
    nm = ('extension spring 1.2 mm wire x %d OD x 45 long (Keadic kit), loops ~%d apart: trigger return, closes the claws (buy)'
          % (sp['od'], sp['free']))
    for b in car.join(parts):
        b.name = nm
    car.finish()
    px_, py_ = tv['pivot']
    trg = Part(g, 'Gripper3 HW trigger (buy)', color=HWC)
    sh.hw_bolt(trg, [px_, py_, tv['z'][0] - 4.5], sh.frame_of([0, 0, 1]), 35.0, (5.5, 3.0),
               'M3 x 35 socket head, trigger pivot (buy)', dia=3.0)        # through both grip cheeks and the trigger
    _m3_nyloc(trg, [px_, py_, tv['z'][1] + 4.5], 'M3 nyloc nut, trigger pivot (buy)')
    hx, hy = pull_point(0.0)
    sh.hw_bolt(trg, [hx, hy, tv['z'][0]], sh.frame_of([0, 0, 1]), tv['z'][1] - tv['z'][0] + 5.0, (5.5, 3.0),
               'M3 x 25 socket head, pull pin (buy)', dia=3.0)
    _m3_nyloc(trg, [hx, hy, tv['z'][1]], 'M3 nyloc nut, pull pin (buy)')
    trg.finish()
    col = Part(g, 'Gripper3 HW collar (buy)', color=HWC)
    ta, tr = c['tail']
    for al in c['alphas']:
        e = claw_frame(al)[2]
        sh.hw_bolt(col, to_xyz(ta, c['rp'] + tr, al, -TAIL_CHEEK[1]), sh.frame_of(e), 25.0, (5.5, 3.0),
                   'M3 x 25 socket head, claw tail pin, through both cheeks (buy)', dia=3.0)
        nut = col.prism(to_xyz(ta, c['rp'] + tr, al, TAIL_CHEEK[1]), claw_frame(al), 0, 2.4, sh.circle(3.2),
                        name='nut').bodies.item(0)
        col.prism(to_xyz(ta, c['rp'] + tr, al, TAIL_CHEEK[1] - 1), claw_frame(al), 0, 4.4, sh.circle(1.5),
                  name='nut bore', op=CUT, targets=[nut])
        nut.name = 'M3 nyloc nut, claw tail pin (buy)'
    hy, (z0, z1), za = pull_point(0.0)[1], co['lug_z'], P['link']['arm_z'][1]
    for sg in (1, -1):                                              # yoke arm pins, into inserts in the side lugs
        sh.hw_bolt(col, [yoke_pin_x(), hy, sg * za], sh.frame_of([0, 0, -sg]), 12.0, (5.5, 3.0),
                   'M3 x 12 socket head, yoke pin (buy)', dia=3.0)
        col.cyl('z', [yoke_pin_x(), hy, sg * (z1 - 2.85)], 2.0, 5.7,
                name='insert')[0].name = 'M3 heat-set insert ruthex 5.7, yoke pin (buy)'
    col.finish()
    return 'hw ok'


# ------------------------------------------------------------------ motion
def claw_open_deg(squeeze):
    """Trigger squeeze 0..1 -> claw opening (deg): the yoke pulls the collar, the collar drags the tails back."""
    tv, c = P['trigger'], P['claw']
    pull = trigger_pull(squeeze)
    ta, tr = c['tail']
    lo, hi = 0.0, 80.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if claw_point(ta, c['rp'] + tr, mid)[0] > ta - pull:
            lo = mid
        else:
            hi = mid
    return lo


def poses(fold=0.0, squeeze=0.0, claw_deg=None):
    """{component prefix: Matrix3D}. fold: deg the carrier is flipped up and back (0 in use .. 180 stowed); squeeze
    0..1 on the trigger (claws follow unless claw_deg forces them)."""
    M, V, Pt = adsk.core.Matrix3D, adsk.core.Vector3D, adsk.core.Point3D
    hg, c, tv = P['hinge'], P['claw'], P['trigger']
    th = claw_open_deg(squeeze) if claw_deg is None else claw_deg
    pull = c['tail'][0] - claw_point(c['tail'][0], c['rp'] + c['tail'][1], th)[0]

    def rz(deg, cx, cy):
        m = M.create()
        m.setToRotation(math.radians(deg), V.create(0, 0, 1), Pt.create(cx / 10.0, cy / 10.0, 0))
        return m
    F = rz(fold, hg['x'], hg['y'])

    def then_fold(m):
        m = m.copy()
        m.transformBy(F)
        return m
    out = {'Gripper3 carrier': F, 'Gripper3 grip': F, 'Gripper3 HW carrier': F}
    tr_ = M.create()
    tr_.translation = V.create(-pull / 10.0, 0, 0)
    for k in ('Gripper3 collar', 'Gripper3 HW collar'):
        out[k] = then_fold(tr_)
    (hx0, hy0), (hxs, hys) = pull_point(0.0), pull_point(squeeze)       # link: slides back, tilts so its rear end
    xc = yoke_pin_x() - pull                                             # stays on the trigger's swinging pin
    lk = M.create()
    lk.setToRotation(math.atan2(hys - hy0, xc - hxs) * -1, V.create(0, 0, 1), Pt.create(xc / 10.0, hy0 / 10.0, 0))
    lk2 = tr_.copy()
    lk2.transformBy(lk)
    out['Gripper3 link'] = then_fold(lk2)
    ta = squeeze * tv['travel_deg']
    out['Gripper3 trigger'] = then_fold(rz(-ta, *tv['pivot']))
    out['Gripper3 HW trigger'] = then_fold(rz(-ta, *tv['pivot']))
    for k, al in enumerate(c['alphas']):
        m = M.create()
        piv = to_xyz(0, c['rp'], al)
        et = claw_frame(al)[2]
        m.setToRotation(math.radians(th), V.create(*et), Pt.create(*[v / 10.0 for v in piv]))   # + turns X toward the radial: opens
        out['Gripper3 claw %d' % (k + 1)] = then_fold(m)
    return out


def pose(fold=0.0, squeeze=0.0, claw_deg=None):
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    ps = poses(fold, squeeze, claw_deg)
    n = 0
    for o in d.rootComponent.allOccurrences:
        if NAME not in o.fullPathName or o.component.name == NAME:
            continue
        for k, m in sorted(ps.items(), key=lambda kv: -len(kv[0])):
            if o.component.name.startswith(k):
                o.transform2 = m
                n += 1
                break
        else:
            o.transform2 = adsk.core.Matrix3D.create()
    return n


PARTS = {'base': ('Gripper3 base',), 'carrier': ('Gripper3 carrier',), 'claws': ('Gripper3 claw',),
         'collar': ('Gripper3 collar',), 'link': ('Gripper3 link',), 'grip': ('Gripper3 grip',), 'trigger': ('Gripper3 trigger',),
         'hw': ('Gripper3 HW',)}


def rebuild(top, steps):
    g = _group(top)
    out = {}
    for st in [s for s in STEPS if s in steps]:
        for o in list(g.occurrences):
            if o.component.name.startswith(PARTS.get(st, ('~',))):
                o.deleteMe()
        out[st] = build(top, st)
    import re
    for o in list(g.occurrences):                                     # a re-sent build can leave 'name (1)' copies
        if re.search(r' \(\d+\)$', o.component.name):
            o.deleteMe()
    return out


# ------------------------------------------------------------------ design rules (design_rules.py)
F_FINGER = 40.0             # N: a hard squeeze on the trigger, at the finger pad
FINGER_AT = 35.0            # mm below the trigger pivot
BALL_AT = 65.0              # mm ahead of the claw pivots: where a ping-pong ball sits in the closed claws


def _loads():
    tv, c, hg = P['trigger'], P['claw'], P['hinge']
    cable = F_FINGER * FINGER_AT / tv['pull_r']
    tail_f = cable / 3                                   # each tail takes a third of the pull
    return [
        dict(name='trigger lever', force=F_FINGER, arm=FINGER_AT, section=('rect', tv['t'], tv['z'][1] - tv['z'][0]),
             material='PETG along layers'),
        dict(name='trigger fork cheek round the pull pin (each)', force=cable / 2, arm=4.0, section=('rect', 9.0, 6.7),
             material='PETG along layers'),
        dict(name='Y link, 20 N side knock at mid-span of its longest leg (fingers, bumps)', force=KNOCK,
             arm=max(math.hypot(P['link']['kink'] - P['link']['split'], sum(P['link']['arm_z']) / 2),
                     P['link']['split'] - pull_point(0.0)[0], yoke_pin_x() - P['link']['kink']) / 4,
             section=LINK_SECTION, material=LINK_MATERIAL),
        dict(name='Y link angled arm at the split (half the pull, offset to the arm line)', force=cable / 2,
             arm=sum(P['link']['arm_z']) / 2, section=('rect', P['link']['diag_w'], P['link']['h']),
             material='PETG along layers'),
        dict(name='collar side lug (each)', force=cable / 2, arm=P['collar']['lug_z'][1] - 32.0,
             section=('rect', P['collar']['x'][1] - P['collar']['x'][0], 10.0), material='PETG along layers'),
        dict(name='claw slot wall in the nose (pivot load)', force=tail_f * 2, arm=8.0, section=('rect', WALL, 17.0),
             material='PETG across layers'),
        dict(name='fold hinge pin M8 (steel), 60 N on the grip at 100 mm', force=60.0 * 100 / 13.0, arm=6.0,
             section=('round', 8.0), material='steel'),
        dict(name='base hinge cheeks (both), 60 N sideways on the grip, at their neck', force=60.0,
             arm=P['base']['y'][1] - P['grip']['y'][0] / 2, section=('rect', P['hinge']['cheek_t'], 2 * CHEEK_NECK),
             material='PETG along layers'),
        dict(name='base front beam over the wrist (plate + top rib), 60 N at the grip, from the front clamp', force=60.0,
             arm=P['grip']['x'] - P['clips'][1], section=('rect', P['base']['rib'][1] - g2.P['ring_top'],
                                                           2 * P['base']['rib'][2]), material='PETG along layers'),
        dict(name='carrier neck at the knuckle, as built (60 N steering at the grip)', force=60.0, arm=70.0,
             section=('rect', knuckle_neck_mm(), 2 * P['carrier']['z']), material='PETG along layers'),
    ]


def _ball_center():
    return [P['claw']['xp'] + BALL_AT, P['hub']['y'], 0.0]


def r_meet():
    """Inner radius at which the three claws' side faces touch (claws t thick, 120 deg apart)."""
    return P['claw']['t'] / 2 / math.tan(math.radians(60))


def closed_claw_rules():
    """Closed claws (agreed shape, 21 Oct: C-cup, tips meet): the inner surface cups outward like a hand (room for a
    ball) and hooks back in to a short pinch pad where the three wedges meet on the axis, tips first, with teeth along
    the gripping surface."""
    c = P['claw']
    cv = claw_curves(200)
    out = []
    tip = cv[-1][1]
    out.append(('ok  ' if tip <= 0.5 else 'FAIL', 'claws closed: ridges meet at the axis at the tip (%.2f mm off)' % tip,
                'claw_curves'))
    pad = [ri for a, ri, _ in cv if a >= c['pad'] * c['L']]
    out.append(('ok  ' if max(pad) <= 2.0 else 'FAIL',
                'claws closed: tip pad (last %.0f mm) within 2 mm of the axis (worst %.1f)' % ((1 - c['pad']) * c['L'],
                                                                                            max(pad)), 'claw_curves'))
    tipfirst = all(pad[k] >= pad[k + 1] - 1e-6 for k in range(len(pad) - 1))
    out.append(('ok  ' if tipfirst else 'FAIL', 'claws closed: tips touch first (pinch at the tip)', 'claw_curves'))
    chord = lambda a: cv[0][1] + (cv[-1][1] - cv[0][1]) * a / c['L']
    cup = max(ri - chord(a) for a, ri, _ in cv)
    out.append(('ok  ' if cup >= 4.0 else 'FAIL', 'claws: C-cup, inner surface bows %.1f mm out past root-tip line (>= 4)'
                % cup, 'claw_curves'))
    w = c.get('wedge_gap')
    out.append(('ok  ' if w is not None and w <= 0.15 else 'FAIL',
                'claws closed: wedge faces meet at the tips (gap %s mm per face)' % w, 'sector cut'))
    n = len(claw_teeth())
    out.append(('ok  ' if n >= 6 else 'FAIL', 'gripping edge has teeth (%d)' % n, 'claw_outline'))
    return out


MU_SLIDE = 0.25            # PETG on PETG, lightly greased (dry is ~0.3-0.4)


def slide_rules():
    """A collar pulled off its axis cocks like a drawer pulled by one corner, and jams unless its sliding length L
    beats the self-locking limit 2 * mu * e (e = pull offset from the axis). Keep 25 % margin."""
    co, h = P['collar'], P['hub']
    L = co['x'][1] - co['x'][0]
    e = abs(h['y'] - pull_point(0.0)[1])
    need = 2 * MU_SLIDE * e * 1.25
    return [('ok  ' if L >= need else 'FAIL',
             'collar slides without jamming: %.0f mm long, needs >= %.0f (pull %.0f mm off axis, mu %.2f)'
             % (L, need, e, MU_SLIDE), 'collar on hub')]


def tail_cheek_rules():
    """The collar's cheeks carry the claw tails' pins (the spring's pull, all the time): each needs plastic all round
    the pin's slot. The first print's cheeks broke there (27 Oct): 2 mm outside the slot, 2.3 mm in front of it."""
    c, co = P['claw'], P['collar']
    ta, tr = c['tail']
    slot_top = c['rp'] + tr + 0.3 + 1.7                  # the slot: r up to rp + tr + 0.3, 3.4 wide
    sides = dict(outside=co['skirt_r'] - slot_top, front=co['skirt'][0] - (c['xp'] + ta) - 1.7,
                 width=TAIL_CHEEK[1] - TAIL_CHEEK[0])
    need = dict(outside=CHEEK_MIN, front=CHEEK_MIN, width=CHEEK_W)
    return [('ok  ' if v >= need[k] else 'FAIL', 'collar tail cheek %s of the pin slot: %.1f mm (>= %.1f)'
             % (k, v, need[k]), 'collar') for k, v in sides.items()]


def clamp_rules():
    """A clamp screw must reach past the pipe's surface with travel to spare, or its head lands on the base before its
    tip presses (27 Oct: the M3 x 10 thumb screws reached 0.75 mm past the pipe and could not clamp)."""
    reach = CLAMP_SCREW - (P['base']['y'][1] - g2.P['pipe_r'])
    return [('ok  ' if reach >= 1.5 else 'FAIL', 'pipe clamp screw M3 x %.0f reaches %.2f mm past the pipe (>= 1.5)'
             % (CLAMP_SCREW, reach), 'base')]


def spring_rules():
    """The trigger return spring (extension) must already pull at rest, so the claws close and the trigger comes back,
    and must not be stretched past its limit at full squeeze."""
    sp = P['spring']
    rest = sp['hub_hook'] - sp['link_hook']
    full = rest + trigger_pull(1.0)
    return [('ok  ' if rest >= sp['free'] + 3.0 else 'FAIL',
             'return spring: %.1f mm between hooks at rest, pulling (free %.0f)' % (rest, sp['free']), 'spring'),
            ('ok  ' if full - sp['free'] <= sp['max_ext'] else 'FAIL',
             'return spring: stretched %.1f mm at full squeeze (max %.0f)' % (full - sp['free'], sp['max_ext']), 'spring')]


def ring_clear_rules():
    """Wherever the base is clamped along the pipe (its slide range), nothing of it may dip below the wrist ring's top
    over the ring or in front of it (the wrist and hand are there). Runs in Fusion: the base body, slid, against that
    zone."""
    b = P['base']
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    tb = adsk.fusion.TemporaryBRepManager.get()
    base = next((o.component.bRepBodies.item(0) for o in d.rootComponent.allOccurrences
                 if o.component.name.startswith('Gripper3 base (printed)')), None)
    if base is None:
        return [('FAIL', 'base clear of the ring and the wrist: no base body', 'ring_clear_rules')]
    x0, x1, top = g2.P['far_ring_x'][0], b['x1'] + 80.0, g2.P['ring_top']
    c = adsk.core.Point3D.create((x0 + x1) / 20, (top - 60.0) / 20, 0)
    zone = tb.createBox(adsk.core.OrientedBoundingBox3D.create(c, adsk.core.Vector3D.create(1, 0, 0),
                                                                adsk.core.Vector3D.create(0, 1, 0),
                                                                (x1 - x0) / 10, (top + 60.0) / 10, 12.0))
    out = []
    for sl in (b['slide'][0], sum(b['slide']) / 2, b['slide'][1]):
        bb = tb.copy(base)
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(sl / 10, 0, 0)
        tb.transform(bb, m)
        tb.booleanOperation(bb, tb.copy(zone), adsk.fusion.BooleanTypes.IntersectionBooleanType)
        v = bb.volume * 1000
        out.append(('ok  ' if v < 0.5 else 'FAIL',
                    'base clear of the ring and the wrist, slid %+.0f mm: %.0f mm3 below ring top' % (sl, v), 'base'))
    return out


def finray_rules():
    """Claws are fin-ray: open cells between a gripping wall and an outer wall, joined by ribs, so they wrap round
    what they hold. Walls thick enough to print in TPU."""
    cells = claw_cells()
    hs = [min(q[3][1] - q[0][1], q[2][1] - q[1][1]) for q in cells] or [0.0]
    return [('ok  ' if len(cells) >= 5 else 'FAIL', 'claws are fin-ray: %d open cells (>= 5)' % len(cells), 'claw_cells'),
            ('ok  ' if min(hs) >= 2.0 else 'FAIL', 'fin-ray cells at least 2 mm tall (smallest %.1f)' % min(hs),
             'claw_cells')]


def tip_rules():
    """Claw tips must be smooth (no point to poke anyone): every corner of the outline in the last 4 mm turns by
    less than 30 deg."""
    c = P['claw']
    o = claw_outline()
    worst = 0.0
    for i in range(len(o)):
        a, b, d = o[i - 1], o[i], o[(i + 1) % len(o)]
        if b[0] < c['L'] - 4.0:
            continue
        t1, t2 = math.atan2(b[1] - a[1], b[0] - a[0]), math.atan2(d[1] - b[1], d[0] - b[0])
        turn = abs((math.degrees(t2 - t1) + 180) % 360 - 180)
        worst = max(worst, turn)
    return [('ok  ' if worst < 30.0 else 'FAIL', 'claw tips smooth: sharpest corner turns %.0f deg (< 30)' % worst,
             'claw_outline')]


def sharp_edge_rules():
    """No sharp edges where hands and fingers touch: the trigger below its link fork, the bottom of the grip, the
    claw tips, the whole base (it sits on the forearm; hole edges excepted). An edge is sharp when its two faces meet at more than 50 deg. Runs in Fusion, at rest."""
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    hy, c = pull_point(0.0)[1], P['claw']
    zones = [('trigger', 'Gripper3 trigger', lambda q: q[1] < hy - 7.0),
             ('grip bottom', 'Gripper3 grip', lambda q: q[1] < P['grip']['y'][0] + 12.0 and   # outside only (the
              ((q[0] - P['grip']['x']) / P['grip']['r']) ** 2 + (q[2] / (P['grip']['r'] * 1.08)) ** 2 > 0.8),  # bore isn't)
             ('claw tips', 'Gripper3 claw', lambda q: q[0] > c['xp'] + c['L'] - 7.0),   # the cap's front, past teeth + cells
             ('base', 'Gripper3 base', lambda q: True)]                    # all of it (hole edges excepted: fits)
    out = []
    for label, prefix, zone in zones:
        n = 0
        for o in d.rootComponent.allOccurrences:
            if not o.component.name.startswith(prefix):
                continue
            for body in o.component.bRepBodies:
                for e in body.edges:
                    pt = e.pointOnEdge
                    if not zone((pt.x * 10, pt.y * 10, pt.z * 10)) or e.faces.count != 2 or e.length * 10 < 0.2                             or _hole_edge(e):
                        continue                                    # (a zero-length edge is a point, not an edge)
                    ok1, n1 = e.faces.item(0).evaluator.getNormalAtPoint(pt)
                    ok2, n2 = e.faces.item(1).evaluator.getNormalAtPoint(pt)
                    if ok1 and ok2 and math.degrees(n1.angleTo(n2)) > 50.0:
                        n += 1
        out.append(('ok  ' if n == 0 else 'FAIL', 'no sharp edges on the %s (%d sharp)' % (label, n), prefix))
    return out


def grip_force_rules():
    """The return spring is all that closes the claws: at rest it must squeeze a held thing hard enough (>= 0.8 N per
    claw at a ping-pong ball, >= 0.5 N at the tips), while a full squeeze stays easy on the finger (<= 25 N)."""
    sp, c = P['spring'], P['claw']
    rest = sp['hub_hook'] - sp['link_hook']
    f_rest = sp.get('init', 0.0) + sp.get('rate', 1.0) * (rest - sp['free'])
    f_full = f_rest + sp.get('rate', 1.0) * trigger_pull(1.0)
    torque = f_rest / 3 * c['tail'][1]                               # each tail: a third of the spring, on its arm
    at_ball, at_tip = torque / BALL_AT, torque / c['L']
    finger = f_full * P['trigger']['pull_r'] / FINGER_AT
    return [('ok  ' if at_ball >= 0.8 else 'FAIL', 'grip: %.2f N per claw on a ping-pong ball (>= 0.8)' % at_ball, 'spring'),
            ('ok  ' if at_tip >= 0.5 else 'FAIL', 'grip: %.2f N per claw at the tips (>= 0.5)' % at_tip, 'spring'),
            ('ok  ' if finger <= 25.0 else 'FAIL', 'trigger: %.1f N at the finger, fully squeezed (<= 25)' % finger,
             'spring')]


def knuckle_neck_rules():
    """The carrier's hinge knuckle must sit on a broad neck, measured on the real outline: >= 0.8 x the knuckle's
    diameter (user, 21 Oct: it hung on a 3 mm sliver and would snap)."""
    w, need = knuckle_neck_mm(), 1.6 * P['hinge']['knuckle_r']
    return [('ok  ' if w >= need else 'FAIL', 'carrier: knuckle neck %.1f mm wide (>= %.0f)' % (w, need), 'carrier')]


# How each part goes on, in the assembly guide's order: (part, parts already on, direction it slides in, travel mm,
# past mm). It starts `travel` back along that direction and slides home, then `past` mm beyond (parked out of the way
# for the next part); at every mm it must not cut into a part already on. A part already on may be given as
# (prefix, (dx, dy, dz)): parked that far from its seat.
COLLAR_PARK = 7.0           # mm: the collar pushed back past its seat while the claws go in (clears their roots)
def _radial(name):
    al = P['claw']['alphas'][int(name.split('claw ')[1][0]) - 1]
    return (0.0, -math.cos(math.radians(al)), -math.sin(math.radians(al)))   # from outside, inward


INSERTION = [
    ('Gripper3 collar', ('Gripper3 carrier',), lambda n: (-1.0, 0.0, 0.0), 50.0, COLLAR_PARK),   # over the nose,
    ('Gripper3 claw', ('Gripper3 carrier', ('Gripper3 collar', (-COLLAR_PARK, 0.0, 0.0))), _radial, 30.0, 0.0),
    ('Gripper3 collar', ('Gripper3 claw',), lambda n: (1.0, 0.0, 0.0), COLLAR_PARK, 0.0),   # forward over the tails
]                           # back past its seat; claws' roots into their slots; then the collar forward over the tails


def insertion_rules():
    """Every part can be put on: slid in along its INSERTION path, it never cuts more than 1 mm3 into a part already
    on (user, 21 Oct: the collar's bore was smaller than the carrier's nose; it could not go on). Runs in Fusion."""
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    tb = adsk.fusion.TemporaryBRepManager.get()
    INTER = adsk.fusion.BooleanTypes.IntersectionBooleanType

    def bodies(prefix):
        return [(o.component.name, b) for o in d.rootComponent.allOccurrences if o.component.name.startswith(prefix)
                and '(buy)' not in o.component.name for b in o.component.bRepBodies if b.isVisible]
    out = []
    def moved(b, v):
        m = tb.copy(b)
        t = adsk.core.Matrix3D.create()
        t.translation = adsk.core.Vector3D.create(v[0] / 10, v[1] / 10, v[2] / 10)
        tb.transform(m, t)
        return m
    for part, before, way, travel, past in INSERTION:
        fixed = []
        for pre in before:
            pre, off = (pre, (0.0, 0.0, 0.0)) if isinstance(pre, str) else pre
            fixed += [moved(b, off) for _, b in bodies(pre)]
        for name, b in bodies(part):
            u = way(name)
            worst = (0.0, None)
            for k in list(range(1, int(travel) + 1)) + [-j for j in range(1, int(past) + 1)]:
                m = tb.copy(b)
                t = adsk.core.Matrix3D.create()
                t.translation = adsk.core.Vector3D.create(-u[0] * k / 10, -u[1] * k / 10, -u[2] * k / 10)
                tb.transform(m, t)
                for f in fixed:
                    if k == 0:
                        continue
                    probe = tb.copy(f)
                    try:
                        tb.booleanOperation(probe, m, INTER)
                        v = probe.volume * 1000
                    except Exception:
                        v = 0.0
                    if v > max(1.0, worst[0]):
                        worst = (v, k)
            out.append(('ok  ' if worst[1] is None else 'FAIL',
                        '%s goes on: clear all along its path (%d mm in, %d past)' % (name, travel, past)
                        if worst[1] is None else
                        '%s goes on: blocked %d mm out (%.0f mm3 into a part already on; < 0: past its seat)'
                        % (name, worst[1], worst[0]),
                        'INSERTION'))
    return out


def trigger_neck_rules():
    """The trigger's pivot ring must hang on solid material, not on a sliver: between the bottom of the ring and the
    top of the link's fork slot (cut through the middle layers) there must be >= 4 mm, and the fork's side cheeks
    must be >= 4 mm thick."""
    tv, lk = P['trigger'], P['link']
    hy = pull_point(0.0)[1]
    neck = (tv['pivot'][1] - TRIGGER_EYE_R) - (hy + FORK_TOP)
    cheek = (tv['z'][1] - tv['z'][0]) / 2 - (lk['w'] / 2 + 0.3)
    return [('ok  ' if neck >= 4.0 else 'FAIL', 'trigger: %.1f mm solid between the pivot ring and the link slot (>= 4)'
             % neck, 'trigger'),
            ('ok  ' if cheek >= 4.0 else 'FAIL', 'trigger: fork cheeks %.1f mm thick (>= 4)' % cheek, 'trigger')]


def claw_root_rules():
    """No spikes at the claw root: the outline starts square at a = 0, and both of its corners there must sit inside
    the round root disc, or they poke out of it as little teeth (seen in the slicer, 21 Oct)."""
    c, o = P['claw'], claw_outline()
    root = [q for q in o if abs(q[0]) < 1e-6]
    worst = max(math.hypot(q[0], q[1] - c['rp']) for q in root) - CLAW_DISC_R
    return [('ok  ' if worst <= -0.2 else 'FAIL',
             'claw root: outline corners %.1f mm inside the root disc (>= 0.2)' % -worst, 'claw_outline')]


def one_body_rules():
    """Every printed part must be ONE solid: a piece that failed to join stays a separate, overlapping body that the
    slicer prints as a loose lump (trigger neck, 21 Oct). Runs in Fusion."""
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    out = []
    for o in d.rootComponent.allOccurrences:
        n = o.component.name
        if n.startswith('Gripper3') and ('(printed)' in n or '(TPU)' in n):
            k = o.component.bRepBodies.count
            out.append(('ok  ' if k == 1 else 'FAIL', '%s is one body (%d)' % (n, k), n))
    return out


RULES = dict(geometry=[one_body_rules, claw_root_rules, closed_claw_rules, slide_rules, tail_cheek_rules, clamp_rules, spring_rules, ring_clear_rules, finray_rules, tip_rules, grip_force_rules, trigger_neck_rules, insertion_rules, knuckle_neck_rules,
                       sharp_edge_rules], 
    anchor='Gripper3 base',
    rest=(0.0, 0.0),
    meshes=[],
    chains=[('trigger drive', (0.0, 0.0),
             [('trigger (printed)', 'pull pin'), ('pull pin', 'link (printed)'), ('link (printed)', 'yoke pin'),
              ('yoke pin', 'collar'), ('collar', 'tail pin'),
              ('tail pin', 'claw 1'), ('tail pin', 'claw 2'), ('tail pin', 'claw 3')]),
            ('claws closed: tips meet', (0.0, 0.0), [('claw 1', 'claw 2'), ('claw 2', 'claw 3'), ('claw 3', 'claw 1')]),
            ('fold hinge', (0.0, 0.0), [('carrier', 'fold hinge'), ('fold hinge', 'base (printed)')]),
            ('claws held on their pivot screws (in the nose) and tail pins (in the collar)', (0.0, 0.0),
             [('claw pivot', 'carrier (printed)'), ('claw pivot', 'claw 1'), ('claw pivot', 'claw 2'),
              ('claw pivot', 'claw 3'), ('claw tail pin', 'collar (printed)')]),
            ('stowed: the Velcro dots meet', (P['hinge']['stow_deg'], 0.0),
             [('carrier side', 'base side')]),
            ('return spring hooked on the link and the hub', (0.0, 0.0),
             [('trigger return', 'link (printed)'), ('trigger return', 'carrier (printed)')])],
    apart=[('claws fully open', (0.0, 1.0), [('claw 1', 'claw 2'), ('claw 2', 'claw 3'), ('claw 3', 'claw 1')]),
           ('return spring clear of the trigger, squeezed', (0.0, 1.0), [('trigger return', 'trigger (printed)')])],
    balls=[('ping-pong ball', _ball_center(), P['ball_r'], (0.0, 0.0, ball_contact_deg(BALL_AT) - 2.0),
            (0.0, 0.0, ball_contact_deg(BALL_AT) + 2.0), ('claw 1', 'claw 2', 'claw 3'))],
    cables=[],
    loads=_loads,
)
