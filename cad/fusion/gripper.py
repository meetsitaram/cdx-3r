"""CDX-3R gripper, prototype 2: a two-finger fin-ray gripper that slides out past the fist like Wolverine's claws.

Layout (user brief, 18 Oct 2026):
  * RAIL BASE (printed) clips onto the forearm's middle PVC pipe (the back / little-finger side) and screws to the
    wrist ring. The HANDLE (printed) bolts to its front: an arm forward over the little-finger side of the fist, and a
    pistol-style grip hanging from it, held in the fist (little-finger end at the arm, thumb end free).
  * One 300 mm MGN12 LINEAR RAIL (bought) runs along the base and the handle arm; the GRIPPER HEAD rides on its
    MGN12H carriage, 250 mm of travel: stowed over the forearm behind the wrist ring, slid out with the gear box ahead
    of the trigger and the claws well past the fist.
  * The head: a flat gear box (two meshed spur gears = a gear-synchronised gripper: both fingers always swing
    together, mirror image) and two TPU FIN-RAY fingers.
  * LOCK: a spring-loaded index plunger (bought, pull knob) in a stout block at the front of the handle arm: when
    the head reaches the front, its pin snaps sideways into a hole in the head plate's edge; pull the knob sideways
    and the head is free to go back.
  * RETURN: a constant-force spring (tape spring) pulls the head back; a rotary gear damper on the head rolls along a
    rack (teeth on both sides of the narrow beam, monorail style) so it glides back slowly.
  * TRIGGER: a short spray-bottle trigger for the index and middle fingers, pivoting at the top of the grip under
    the arm (pistol style); the ring and little fingers keep the bare grip. A horn above the pivot pulls a brake-style
    cable along the arm to the PUSHER lever at the front; with the head slid out, the pusher pushes the drive tab
    on the right gear: both fingers open. Let go: a small spring on the head closes them (and pushes everything back).
    Stowed, the head is out of the pusher's reach and stays closed.

Frames (mm):
  WRIST frame (x' toward the fingers, y' toward the palm, z' toward the thumb; origin on the wrist ring's axis, just
  past the ring / pipe ends) is read from the assembly (wrist_frame). The parts are built in the RAIL frame:
    X along the middle pipe, toward the fingers (origin: the pipe's axis where it ends at the wrist ring)
    Y radially outward from the forearm (up off the pipe)
    Z = X x Y (sideways across the pipe)
Hand placement is anthropometric (the scan has no hand): grip axis ~65 mm past the wrist; tune P after a fitting.
Print orientations: rail base upside down (spine top on the bed: clips up); handle on its side; head plate, lid,
gears, trigger, pusher flat; fingers (TPU 95A) flat.

    import split, gripper
    split.new('gripper'); for s in gripper.STEPS: split.build('gripper', s); split.save('gripper')
"""
import math

import adsk.core
import adsk.fusion

import fxlib as fx
import shoulder as sh
from fxlib import Part, add, mul, sub, unit, cross, dot

CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
PRINT, TPU, HWC, SPR, STEEL = '#d9822b', '#2b2b2b', '#c9d2d9', '#c0392b', '#8a9299'
NAME = 'Gripper (prototype 2)'
STEPS = ('frame', 'base', 'rail', 'head', 'gears', 'fingers', 'handle', 'trigger', 'hw')

P = dict(
    gap=0.3,                    # wrist frame origin: this far past the ring / pipe ends
    pipe_r=10.75, bore_r=10.95, ring_top=16.4,   # middle pipe; ring socket bosses reach Y 16.1 over it
    far_ring_x=(-28.5, 0.5), near_ring_x=-159.5,  # rings along X (rail frame); the base clears them by ring_top
    base=dict(x0=-175.0, x1=0.31, y=(15.0, 20.0), z=(-12.0, 12.0), web=(6.0, 12.0)),   # monorail beam: spine + saddle web
    clips=(-124.0, -44.0), clip=dict(w=12.0, ro=14.5, open_y=-7.25),
    tab=dict(x=(0.3, 8.3), y=(6.0, 20.0), z=12.0),          # front tab on the ring's middle-pipe boss
    rail=dict(x=(-165.0, 135.0), y=(20.0, 28.0), w=12.0,     # MGN12 rail, 300 mm
              screws=(-152.5, -102.5, -52.5, 22.5, 72.5, 122.5)),
    carriage=dict(len=45.4, w=27.0, y=(24.0, 33.0), dx=-3.0),  # MGN12H; its centre sits dx from the gear centres
    stroke=250.0,
    head=dict(x_rest=-136.0, plate=(33.0, 39.0), gear=(39.4, 45.4), lid=(45.8, 49.8),
              outline=(-20.0, 8.0, 27.0, 4.0), posts=((-15.5, 19.0), (-15.5, -19.0)), post_r=3.5),   # posts clear the drive arm's sweep
    gear=dict(m=1.0, z=19, pa=20.0, backlash=0.05, zc=9.5),
    lever=dict(len=28.0, w=8.0),
    finger=dict(r0=16.0, r1=30.0, len=120.0, w=34.0, grip=8.5, y=(39.2, 59.2)),   # above the plate: roots swing over it
    drive=dict(len=28.0, w=10.0, pin='steel', pin_len=20.0),  # right-gear drive arm (+Z); its tab is a steel M4 screw
    lock=dict(dx=-6.0, w=12.0, z=(-37.0, -29.0), top=38.8, pin_y=36.0, pin_d=5.0, depth=6.0),   # dx: head-frame x of the pin
    rack=dict(pieces=((-150.0, 0.0), (8.3, 118.0)), face=12.0, y=(16.5, 20.0)),   # above the wrist ring's bosses (Y 16.1); teeth on both side faces of the beam
    damper=dict(x=-6.0, z=-18.75, gear_r=4.4, body_r=7.0, gear_y=(16.8, 19.8), body_y=(20.5, 24.0)),   # on the -Z rack
    spool=dict(x=-164.0, z=22.0, r=5.0, coil_ro=8.0),          # +Z lug at the back of the beam
    tape_z=(14.1, 14.3),
    arm=dict(x=(8.3, 140.0), y=(6.0, 20.0), z=(-12.0, 24.0), bracket=dict(x=(118.0, 131.0), z=(24.0, 64.0), top=24.0)),
    grip=dict(x=65.0, z=6.0, r=16.0, y=(-105.0, 6.0), bore=(73.0, 3.0)),   # handle axis along -Y (thumb end down)
    trigger=dict(pivot=(100.0, -4.0), len=55.0, rest_deg=16.0, travel_deg=15.0, t=8.0, z=(-4.0, 16.0),
                 eye_z=(-4.0, 20.0), horn=18.0, horn_w=10.0, horn_z=(12.0, 20.0)),   # pistol style: pivot at the top, under the arm
    pusher=dict(pivot=(122.5, 58.0), tip=(121.2, 37.5), wire=6.0, y=(24.2, 29.0), w=7.0),   # tip's back face meets the tab
)


def wrist_frame():
    """(origin, R) of the wrist frame in the shoulder TOP's design frame, read from the forearm's far ring in the
    assembly (open in Fusion). R's columns are x', y', z'."""
    app = adsk.core.Application.get()
    doc = next(d for d in app.documents if d.name == 'CDX-3R assembly')
    d = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    ring = near = None
    front = []                                           # whatever ends at the wrist: the ring and the pipes
    for o in d.rootComponent.allOccurrences:
        for b in o.component.bRepBodies:
            if 'far ring' in b.name and 'Forearm' in b.name:
                ring = b.createForAssemblyContext(o)
                front.append(ring)
            elif 'PVC pipe' in b.name and 'Forearm' in b.name:
                front.append(b.createForAssemblyContext(o))
            if 'forearm: near ring' in b.name:
                near = b.createForAssemblyContext(o)
    cylf = next(f for f in ring.faces if isinstance(f.geometry, adsk.core.Cylinder) and abs(f.geometry.radius - 4.0) < 1e-3)
    g = cylf.geometry
    u = [g.axis.x, g.axis.y, g.axis.z]
    c0 = [g.origin.x * 10, g.origin.y * 10, g.origin.z * 10]
    nb = near.boundingBox
    nc = [(nb.minPoint.x + nb.maxPoint.x) * 5, (nb.minPoint.y + nb.maxPoint.y) * 5, (nb.minPoint.z + nb.maxPoint.z) * 5]
    if dot(u, sub(c0, nc)) < 0:
        u = mul(u, -1)                                   # point distally (away from the elbow)
    u = unit(u)
    far = -1e9
    for b in front:
        m = b.meshManager.createMeshCalculator()
        m.setQuality(adsk.fusion.TriangleMeshQualityOptions.HighQualityTriangleMesh)
        pts = m.calculate().nodeCoordinatesAsDouble
        far = max(far, max(dot(u, [pts[i] * 10, pts[i + 1] * 10, pts[i + 2] * 10]) for i in range(0, len(pts), 3)))
    ow = add(c0, mul(u, far + P['gap'] - dot(u, c0)))   # world (mm): just past the ring / pipe ends, on the axis
    zw = unit(sub([0, 0, 1], mul(u, u[2])))            # thumb up: world +z, square to the axis
    yw = cross(zw, u)                                    # toward the palm
    w2d = lambda v: [v[0], v[2], -v[1]]                  # world -> design frame (design: x fwd, y up, z right)
    xs, ys, zs = w2d(u), w2d(yw), w2d(zw)
    R = [[xs[i], ys[i], zs[i]] for i in range(3)]
    return w2d(ow), R


def rail_frame():
    """(origin, R) of the rail frame in the shoulder TOP's design frame: origin on the middle pipe's axis at the wrist
    end, X along that pipe toward the fingers, Y radially out, Z = X x Y."""
    o, R = wrist_frame()
    app = adsk.core.Application.get()
    doc = next(d for d in app.documents if d.name == 'CDX-3R assembly')
    d = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    w2d = lambda v: [v[0], v[2], -v[1]]
    to_w = lambda p: [sum((p[i] - o[i]) * R[i][j] for i in range(3)) for j in range(3)]   # design -> wrist
    dir_w = lambda v: [sum(v[i] * R[i][j] for i in range(3)) for j in range(3)]
    pipes = []
    for oc in d.rootComponent.allOccurrences:
        for b in oc.component.bRepBodies:
            if 'PVC pipe' in b.name and 'Forearm' in b.name:
                px = b.createForAssemblyContext(oc)
                f = max((f for f in px.faces if isinstance(f.geometry, adsk.core.Cylinder)),
                        key=lambda f: f.geometry.radius)
                g = f.geometry
                c = to_w(w2d([g.origin.x * 10, g.origin.y * 10, g.origin.z * 10]))
                a = unit(dir_w(w2d([g.axis.x, g.axis.y, g.axis.z])))
                if a[0] < 0:
                    a = mul(a, -1)
                p = add(c, mul(a, -c[0] / a[0]))                  # where the axis meets x' = 0
                pipes.append((math.atan2(p[2], p[1]) % (2 * math.pi), p, a))
    pipes.sort()
    _, p0, u = pipes[1]                                            # the middle one
    n0 = unit([0, p0[1], p0[2]])
    n = unit(sub(n0, mul(u, dot(n0, u))))
    z = cross(u, n)
    org = add(o, [sum(R[i][j] * p0[j] for j in range(3)) for i in range(3)])
    cols = [[sum(R[i][j] * v[j] for j in range(3)) for i in range(3)] for v in (u, n, z)]
    RL = [[cols[k][i] for k in range(3)] for i in range(3)]
    return org, RL


# ------------------------------------------------------------------ sketch helpers
ZF = ([1, 0, 0], [0, 1, 0], [0, 0, 1])                 # sketch (X, Y), extrude along Z
XF = ([0, 1, 0], [0, 0, 1], [1, 0, 0])                 # sketch (Y, Z), extrude along X
YF = ([0, 0, 1], [1, 0, 0], [0, 1, 0])                 # sketch (Z, X), extrude along Y


def _poly(pts):
    def draw(sk, to):
        ln = sk.sketchCurves.sketchLines
        q = [to(*p) for p in pts]
        for i in range(len(q)):
            ln.addByTwoPoints(q[i], q[(i + 1) % len(q)])
    return draw


def _xz(pts):
    """Polygon given as (X, Z) points, for a YF sketch."""
    return _poly([(zz, xx) for xx, zz in pts])


def _round_rect(x0, x1, z0, z1, r, n=6):
    pts = []
    for cx, cz, a0 in ((x1 - r, z1 - r, 0), (x0 + r, z1 - r, 90), (x0 + r, z0 + r, 180), (x1 - r, z0 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def _rot(pts, c, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(c[0] + (x - c[0]) * ca - (z - c[1]) * sa, c[1] + (x - c[0]) * sa + (z - c[1]) * ca) for x, z in pts]


def gear_pts(m, z, pa, backlash, phase_deg, c):
    """Involute spur gear outline (X, Z) centred at c, a tooth centred at phase_deg."""
    rp = m * z / 2
    rb = rp * math.cos(math.radians(pa))
    ra, rf = rp + m, rp - 1.25 * m
    inv = lambda a: math.tan(a) - a
    a0 = math.radians(pa)

    def half(r):
        ar = math.acos(min(1.0, rb / r))
        return math.pi / (2 * z) + inv(a0) - inv(ar) - backlash / (2 * rp)
    rs = [rb + (ra - rb) * k / 6 for k in range(7)]
    pts = []
    for k in range(z):
        cang = math.radians(phase_deg) + 2 * math.pi * k / z
        side = [(r, half(r)) for r in rs]
        flank_l = [(rf, half(rb))] + side                                      # root -> tip
        tooth = [(r, cang - h) for r, h in flank_l] + [(r, cang + h) for r, h in reversed(flank_l)]
        pts += tooth
        nxt = cang + 2 * math.pi / z - half(rb)
        a1 = cang + half(rb)
        for t in (1 / 3, 2 / 3):
            pts.append((rf, a1 + (nxt - a1) * t))
    return [(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for r, a in pts]


def rack_pts(m, x0, x1, zp, back, xref=None):
    """Rack along X, teeth pointing -Z, pitch line at zp; solid back to Z = back. Teeth sit on a pitch grid from xref,
    so two rack pieces (base and handle arm) stay in phase across the gap between them."""
    p = math.pi * m
    t = math.tan(math.radians(20))
    pts = [(x0, back), (x0, zp + 1.25 * m)]
    xref = x0 if xref is None else xref
    x = xref + p / 2 + math.ceil((x0 + 1.3 - (xref + p / 2)) / p) * p
    while x + p / 2 <= x1:
        hb, ht = p / 4 + t * 1.25 * m, p / 4 - t * m
        pts += [(x - hb, zp + 1.25 * m), (x - ht, zp - m), (x + ht, zp - m), (x + hb, zp + 1.25 * m)]
        x += p
    pts += [(x1, zp + 1.25 * m), (x1, back)]
    return pts


def finger_pts(f):
    """Fin-ray finger outline and rib pockets in its own (a, b) frame: a from the finger root toward the tip, b
    outward (away from the other finger). Grip face at b = -grip; back curve from b = w - grip at the root to the tip."""
    L, g, w = f['len'], f['grip'], f['w']
    back = lambda a: -g + 2 + (w - 2) * (1 - (max(a, 0.0) / L) ** 1.8)
    a_root = -(f['r1'] - f['r0'])
    outline = [(a_root, -g), (L, -g), (L + 1.6, -g + 1.0), (L, -g + 2.0)]
    outline += [(a, back(a)) for a in [L - 5 * k for k in range(1, int(L / 5) + 1)] if a > 0]
    outline += [(0, back(0)), (a_root, back(0))]
    pockets = []
    beam, rib, slant, a_i = 1.8, 1.5, 4.0, 6.0
    while True:
        a_n = a_i + 10.0
        top = lambda a: back(a) - beam
        p0, p1 = a_i + rib / 2, a_n - rib / 2
        if top(p1 - slant) - (-g + beam) < 3.0:
            break
        pk = [(p0, -g + beam), (p1, -g + beam)]
        pk += [(a - slant, top(a - slant)) for a in (p1, (p0 + p1) / 2, p0)]
        pockets.append(pk)
        a_i = a_n
    return outline, pockets


def _finger_world(pts, side, gz, r1, deg):
    """Finger (a, b) points -> head (x, z): root frame at r1 from the gear centre (0, gz), rotated deg (+ toward +Z)."""
    out = []
    for a, b in pts:
        x, z = r1 + a, side * b
        out.append((x, gz + z))
    return _rot(out, (0.0, gz), deg)


# ------------------------------------------------------------------ build
PARTS = {'base': ('Gripper rail base',), 'rail': ('Gripper rail', 'Gripper carriage'), 'head': ('Gripper head',),
         'gears': ('Gripper gear',), 'fingers': ('Gripper finger',), 'handle': ('Gripper handle',),
         'trigger': ('Gripper trigger', 'Gripper pusher'),
         'hw': ('Gripper HW', 'Gripper damper gear', 'Gripper spool')}
FLANGE = ((5.0, 9.5), (8.0, 16.5))
CABLE_X = 62.0                                       # where the cable leaves the arm's side
LUG_X = (98.5, 104.5)                                # cable housing stop at the arm's front
CABLE = dict(y=13.5, wall=(89.0, 93.5), pocket_x=(55.0, 89.0), loop_r=20.0,   # wire height; wall the housing seats on;
             nipple=(6.0, 6.0), screw_nipple=(6.5, 8.0))  # pocket open to the arm's +Z side; barrel / screw nipples                   # (Z, Y) of the handle flange screws


def rebuild(top, steps):
    """Delete the parts the given steps make, then build them again (in STEPS order)."""
    g = _group(top)
    out = {}
    for st in [s for s in STEPS if s in steps]:
        for o in list(g.occurrences):
            n = o.component.name
            if n.startswith(PARTS[st]) and not (st == 'rail' and n.startswith('Gripper rail base')):
                o.deleteMe()
        out[st] = build(top, st)
    return out


def _group(top):
    return next(o.component for o in top.occurrences if o.component.name == NAME)


def build(top, step):
    if step == 'frame':
        o, R = rail_frame()
        fx.group(top, NAME, R, o)
        return dict(origin=o, frame=R)
    g = _group(top)
    return globals()['_' + step](g)


def _rack(p, x0, x1):
    """Racks on both side faces of the beam (teeth outward): -Z drives the damper, +Z is free for a motor pinion."""
    rk, m = P['rack'], P['gear']['m']
    zp = rk['face'] + 1.25 * m                                    # pitch line: root on the beam face
    pts = rack_pts(m, x0, x1, -zp, -rk['face'] + 0.5, xref=rk['pieces'][0][0])
    out = []
    for sgn in (1, -1):
        q = [(x, z * -sgn) for x, z in pts] if sgn > 0 else pts
        out.append(p.prism([0, rk['y'][0], 0], YF, 0, rk['y'][1] - rk['y'][0] - 0.01, _xz(q), name='rack')
                   .bodies.item(0))
    return out


def _base(g):
    """Rail base (printed): spine plate on a saddle over the middle pipe, two snap clips round the pipe, a front tab on
    the wrist ring's pipe boss, the rear of the damper rack (+Z), the spool boss. Print upside down (spine top down)."""
    b, c = P['base'], P['clip']
    p = Part(g, 'Gripper rail base (printed)', color=PRINT)
    spine = p.prism([b['x0'], 0, 0], XF, 0, b['x1'] - b['x0'],
                    _poly([(b['y'][0], b['z'][0]), (b['y'][1], b['z'][0]), (b['y'][1], b['z'][1]), (b['y'][0], b['z'][1]),
                           (b['y'][0], b['web'][1]), (b['web'][0], b['web'][1]), (b['web'][0], -b['web'][1]),
                           (b['y'][0], -b['web'][1])]), name='spine').bodies.item(0)
    parts = [spine]
    for xc in P['clips']:
        parts += p.ann('x', [xc, 0, 0], c['ro'], P['bore_r'], c['w'], name='pipe clip')
    t = P['tab']
    parts.append(p.box(t['x'][0], t['x'][1], t['y'][0], t['y'][1], -t['z'], t['z'], name='front tab')[0])
    parts += _rack(p, *P['rack']['pieces'][0])
    sp = P['spool']
    parts.append(p.box(b['x0'], b['x0'] + 21, b['y'][0], b['y'][1], b['z'][1] - 0.01, sp['z'] + 10, name='spool lug')[0])
    parts += p.cyl('y', [sp['x'], b['y'][1] + 4.25, sp['z']], 4.0, 8.5, name='spool boss')
    body = p.join(parts)[0]
    p.prism([b['x0'] - 1, 0, 0], XF, 0, b['x1'] - b['x0'] + 2, sh.circle(P['bore_r']), name='pipe bore', op=CUT,
            targets=[body])
    for x0, x1 in (P['far_ring_x'], (b['x0'] - 1, P['near_ring_x'])):
        p.prism([x0, 0, 0], XF, 0, x1 - x0, sh.rect(-30, P['ring_top'], -40, 40), name='ring clearance', op=CUT,
                targets=[body])
    p.prism([0, 0, 0], ZF, -20, 20, sh.rect(-200, 20, -30, c['open_y']), name='clip openings', op=CUT, targets=[body])
    for xc in P['clips']:                                           # #4 self-tapper into the pipe, head sunk
        p.prism([xc, b['y'][1], 0], YF, -12, 1, sh.circle(1.65), name='pipe screw hole', op=CUT, targets=[body])
        p.prism([xc, b['y'][1], 0], YF, -6.5, 1, sh.circle(3.4), name='pipe screw counterbore', op=CUT, targets=[body])
    p.prism([t['x'][1], 13.5, 0], XF, -t['x'][1] - 1, 1, sh.circle(1.65), name='ring screw hole', op=CUT, targets=[body])
    p.prism([t['x'][1], 13.5, 0], XF, -5.3, 1, sh.circle(3.4), name='ring screw counterbore', op=CUT, targets=[body])
    for zz, yy in FLANGE:                                           # handle flange inserts
        p.prism([t['x'][1], yy, zz], XF, -5.9, 1, sh.circle(2.0), name='insert hole', op=CUT, targets=[body])
    for xs in P['rail']['screws']:
        if xs < 0:
            p.prism([xs, b['y'][1], 0], YF, -7.0, 1, sh.circle(2.0), name='rail insert hole', op=CUT, targets=[body])
    p.prism([sp['x'], b['y'][1] + 8.5, sp['z']], YF, -8.5, 1, sh.circle(2.0), name='spool insert hole', op=CUT,
            targets=[body])
    body.name = 'rail base (printed)'
    p.finish()
    return 'rail base: %d bodies' % p.comp.bRepBodies.count


def lock_x():
    """X of the lock pin (rail frame): through the plunger block, into the head plate's -Z edge with the head forward."""
    return _head_x() + P['stroke'] + P['lock']['dx']


def _head_x():
    return P['head']['x_rest']


def _rail(g):
    """MGN12 rail (300 mm) and MGN12H carriage (bought), stowed."""
    r, c = P['rail'], P['carriage']
    p = Part(g, 'Gripper rail MGN12 (buy)', color=STEEL)
    rb = p.box(r['x'][0], r['x'][1], r['y'][0], r['y'][1], -r['w'] / 2, r['w'] / 2, name='rail')[0]
    for xs in r['screws']:
        p.prism([xs, r['y'][1], 0], YF, -3.5, 1, sh.circle(3.0), name='screw counterbore', op=CUT, targets=[rb])
        p.prism([xs, r['y'][0], 0], YF, -1, r['y'][1] - r['y'][0] + 1, sh.circle(1.75), name='screw hole', op=CUT,
                targets=[rb])
    rb.name = 'MGN12 linear rail, 300 mm (buy)'
    p.finish()
    q = Part(g, 'Gripper carriage MGN12H (buy)', color=STEEL)
    xc = _head_x() + c['dx']
    cb = q.box(xc - c['len'] / 2, xc + c['len'] / 2, c['y'][0], c['y'][1], -c['w'] / 2, c['w'] / 2, name='carriage')[0]
    q.prism([xc - c['len'] / 2 - 1, 0, 0], XF, 0, c['len'] + 2, sh.rect(c['y'][0] - 1, r['y'][1] + 0.2, -r['w'] / 2 - 0.2,
                                                                       r['w'] / 2 + 0.2), name='rail slot', op=CUT,
            targets=[cb])
    for dx in (-10.0, 10.0):
        for zz in (-10.0, 10.0):
            q.prism([xc + dx, c['y'][1], zz], YF, -6.0, 1, sh.circle(1.25), name='M3 tap hole', op=CUT, targets=[cb])
    cb.name = 'MGN12H carriage, M3 threaded holes (buy)'
    q.finish()
    return 'rail + carriage ok'


def _head(g):
    """Gear box (printed): bottom plate on the carriage + 2 posts, and a lid. Flat prints."""
    h, c = P['head'], P['carriage']
    X = _head_x()
    x0, x1, zw, r = h['outline']
    out = _round_rect(X + x0, X + x1, -zw, zw, r)
    p = Part(g, 'Gripper head plate (printed)', color=PRINT)
    py0, py1 = h['plate']
    plate = p.prism([0, py0, 0], YF, 0, py1 - py0, _xz(out), name='plate').bodies.item(0)
    lug = p.prism([0, py0, 0], YF, 0, py1 - py0, _xz(_round_rect(X + 3, X + 12, zw - 6, zw + 6, 2.5)),
                  name='spring lug').bodies.item(0)
    tab = p.box(X + x0, X + x0 + 6, 21.0, py0 + 0.01, P['tape_z'][1] + 0.2, P['tape_z'][1] + 2.4, name='tape tab')[0]
    dm = P['damper']
    hang = p.box(X + dm['x'] - 5, X + dm['x'] + 5, dm['body_y'][1] - 0.01, py0 + 0.01, -zw, dm['z'] - 4.5,
                 name='damper hanger')[0]
    posts = []
    for px_, pz in h['posts']:
        posts += p.cyl('y', [X + px_, (py1 + h['lid'][0]) / 2, pz], h['post_r'], h['lid'][0] - py1 + 0.02, name='post')
    body = p.join([plate, lug, tab, hang] + posts)[0]
    gz = P['gear']['zc']
    for zz in (gz, -gz):                                            # gear axle inserts (from the top)
        p.prism([X, py1, zz], YF, -5.7, 1, sh.circle(2.0), name='axle insert hole', op=CUT, targets=[body])
    xc = X + c['dx']
    for dx in (-10.0, 10.0):                                        # 4 x M3 into the carriage, heads sunk
        for zz in (-10.0, 10.0):
            p.prism([xc + dx, py0, zz], YF, -1, py1 - py0 + 1, sh.circle(1.7), name='carriage screw hole', op=CUT,
                    targets=[body])
            p.prism([xc + dx, py1, zz], YF, -3.2, 1, sh.circle(3.0), name='carriage screw counterbore', op=CUT,
                    targets=[body])
    for px_, pz in h['posts']:
        p.prism([X + px_, h['lid'][0], pz], YF, -5.7, 1, sh.circle(2.0), name='post insert hole', op=CUT, targets=[body])
    p.prism([X + 9, py0, zw + 2.5], YF, -1, 8, sh.circle(1.6), name='spring pin hole', op=CUT, targets=[body])
    lk = P['lock']
    p.prism([X + lk['dx'], lk['pin_y'], -zw - 1], ZF, 0, lk['depth'] + 1.5, sh.circle(lk['pin_d'] / 2 + 0.3),
            name='lock pin hole', op=CUT, targets=[body])
    body.name = 'head plate (printed)'
    p.finish()
    q = Part(g, 'Gripper head lid (printed)', color=PRINT)
    lid = q.prism([0, h['lid'][0], 0], YF, 0, h['lid'][1] - h['lid'][0], _xz(out), name='lid').bodies.item(0)
    for zz in (gz, -gz):
        q.prism([X, h['lid'][0], zz], YF, -1, 5, sh.circle(1.7), name='axle hole', op=CUT, targets=[lid])
    for px_, pz in h['posts']:
        q.prism([X + px_, h['lid'][0], pz], YF, -1, 5, sh.circle(1.7), name='screw hole', op=CUT, targets=[lid])
    lid.name = 'head lid (printed)'
    q.finish()
    return 'head ok'


def _gears(g):
    """Two meshed spur gears (printed), each with the tongue its finger slides onto; the right one also carries the
    drive arm (+Z) whose tab pin the pusher pushes. Flat prints."""
    ge, lv, dv, h = P['gear'], P['lever'], P['drive'], P['head']
    X = _head_x()
    y0, y1 = h['gear']
    names = []
    for side in (1, -1):
        gzc = side * ge['zc']
        phase = -90.0 if side > 0 else 90.0 + 180.0 / ge['z']
        p = Part(g, 'Gripper gear %s (printed)' % ('R' if side > 0 else 'L'), color='#2b9d8f')
        gb = p.prism([0, y0, 0], YF, 0, y1 - y0, _xz(gear_pts(ge['m'], ge['z'], ge['pa'], ge['backlash'], phase,
                                                            (X, gzc))), name='gear').bodies.item(0)
        w = lv['w'] / 2
        tg = p.prism([0, y0, 0], YF, 0, y1 - y0, _xz([(X + 5, gzc - w), (X + lv['len'], gzc - w),
                                                      (X + lv['len'], gzc + w), (X + 5, gzc + w)]),
                     name='finger tongue').bodies.item(0)
        parts = [gb, tg]
        if side > 0:
            dw = dv['w'] / 2
            parts.append(p.prism([0, y0, 0], YF, 0, y1 - y0,
                                 _xz([(X - dw, gzc + 5), (X + dw, gzc + 5), (X + dw, gzc + dv['len'] + dw),
                                      (X - dw, gzc + dv['len'] + dw)]), name='drive arm').bodies.item(0))   # past the pin
        body = p.join(parts)[0]
        if side > 0:
            p.prism([X, y0, gzc + dv['len']], YF, -1, y1 - y0 + 2, sh.circle(2.15), name='drive pin hole', op=CUT,
                    targets=[body])
        p.prism([X, y0, gzc], YF, -1, y1 - y0 + 1, sh.circle(1.7), name='axle bore', op=CUT, targets=[body])
        fr = P['finger']
        p.prism([X + fr['r1'] - 8, y1, gzc], YF, -7.0, 1, sh.circle(2.0), name='finger insert hole', op=CUT,
                targets=[body])
        body.name = 'gear %s, m1 z%d (printed)' % ('R + drive arm' if side > 0 else 'L', ge['z'])
        p.finish()
        names.append(body.name)
    return names


def _fingers(g):
    """Fin-ray fingers (TPU 95A), flat prints: slide onto the gear tongues, one M3 x 8 each into the tongue's insert."""
    fr, ge, h = P['finger'], P['gear'], P['head']
    X = _head_x()
    outline, pockets = finger_pts(fr)
    for side in (1, -1):
        gzc = side * ge['zc']
        p = Part(g, 'Gripper finger %s (TPU)' % ('R' if side > 0 else 'L'), color=TPU)
        pts = [(X + x, z) for x, z in _finger_world(outline, side, gzc, fr['r1'], 0)]
        body = p.prism([0, fr['y'][0], 0], YF, 0, fr['y'][1] - fr['y'][0], _xz(pts), name='finger').bodies.item(0)
        for pk in pockets:
            q = [(X + x, z) for x, z in _finger_world(pk, side, gzc, fr['r1'], 0)]
            p.prism([0, fr['y'][0] - 1, 0], YF, 0, fr['y'][1] - fr['y'][0] + 2, _xz(q), name='rib pocket', op=CUT,
                    targets=[body])
        w = P['lever']['w'] / 2 + 0.2
        p.prism([0, h['gear'][0] - 0.2, 0], YF, 0, h['gear'][1] - h['gear'][0] + 0.4,
                _xz([(X + fr['r0'] - 1, gzc - w), (X + P['lever']['len'] + 0.2, gzc - w),
                     (X + P['lever']['len'] + 0.2, gzc + w), (X + fr['r0'] - 1, gzc + w)]), name='tongue slot', op=CUT,
                targets=[body])
        p.prism([X + fr['r1'] - 8, fr['y'][1], gzc], YF, -(fr['y'][1] - h['gear'][1]) - 0.5, 1, sh.circle(1.7),
                name='screw hole', op=CUT,
                targets=[body])
        body.name = 'fin-ray finger %s (TPU)' % ('R' if side > 0 else 'L')
        p.finish()
    return 'fingers: %d pockets each' % len(pockets)


def _handle(g):
    """Handle (printed, on its side): flange on the base's front tab; arm forward over the little-finger side of the
    fist carrying the rail's front half, the front of the racks, the lock plunger block (-Z) and the pusher bracket (+Z);
    the grip hanging from it like a pistol grip; two cheeks under the arm in front of the grip carry the trigger pivot,
    a slot in the arm takes the trigger's horn, and a channel leads the cable out of the arm's +Z side."""
    a, gr, tv, lk = P['arm'], P['grip'], P['trigger'], P['lock']
    p = Part(g, 'Gripper handle (printed)', color=PRINT)
    arm = p.box(a['x'][0], a['x'][1], a['y'][0], a['y'][1], a['z'][0], a['z'][1], name='arm')[0]
    bk = a['bracket']
    br = p.box(bk['x'][0], bk['x'][1], a['y'][0], bk['top'], bk['z'][0] - 0.01, bk['z'][1], name='pusher bracket')[0]
    grip = p.prism([0, gr['y'][1], 0], YF, gr['y'][0] - gr['y'][1], 0.01,
                   _xz([(gr['x'] + gr['r'] * math.cos(math.radians(k * 15)),
                         gr['z'] + gr['r'] * 1.08 * math.sin(math.radians(k * 15))) for k in range(24)]),
                   name='grip').bodies.item(0)
    px_, py_ = tv['pivot']
    cheeks = [p.box(gr['x'] + gr['r'] + 0.5, px_ + 8, py_ - 6, a['y'][0] + 0.01, z0, z1, name='trigger cheek')[0]
              for z0, z1 in ((tv['eye_z'][0] - 4.5, tv['eye_z'][0] - 0.5), (tv['eye_z'][1] + 0.5, a['z'][1]))]
    racks = _rack(p, *P['rack']['pieces'][1])
    lx = lock_x()
    bridge = p.box(lx - lk['w'] / 2, lx + lk['w'] / 2, a['y'][0], 12.0, lk['z'][0], a['z'][0] + 0.01,
                   name='lock bridge')[0]                       # low, under the damper's path
    block = p.box(lx - lk['w'] / 2, lx + lk['w'] / 2, a['y'][0], lk['top'], lk['z'][0], lk['z'][1],
                  name='lock block')[0]                         # stout: 12 x 8 mm, beside the head's path
    pu = P['pusher']
    wz = pu['pivot'][1] + (pu['tip'][1] - pu['pivot'][1]) * pu['wire'] / math.hypot(pu['tip'][0] - pu['pivot'][0],
                                                                                     pu['tip'][1] - pu['pivot'][1])
    stop_bar = p.box(LUG_X[0], LUG_X[1], a['y'][0], 16.01, a['z'][1] - 0.01, wz + 5, name='cable stop bar')[0]
    yw = sum(pu['y']) / 2
    stop = p.box(LUG_X[0], LUG_X[1], 16.0, yw + 5, wz - 5, wz + 5, name='cable stop')[0]   # housing seats on its back
    body = p.join([arm, br, grip, bridge, block, stop_bar, stop] + racks + cheeks)[0]
    p.prism([LUG_X[0] - 1, yw, wz], XF, 0, LUG_X[1] - LUG_X[0] + 2, sh.circle(1.0), name='wire hole', op=CUT,
            targets=[body])
    wx_, wz_ = _wire_point()
    p.prism([0, 0, 0], YF, 22.0, bk['top'] + 1, _xz(_round_rect(wx_ - 2, wx_ + 18, wz_ - 8, wz_ + 8, 2.0)),
            name='nipple relief', op=CUT, targets=[body])          # the screw nipple swings over the bracket
    p.prism([lx, lk['pin_y'], lk['z'][0] - 1], ZF, 0, lk['z'][1] - lk['z'][0] + 2, sh.circle(4.0), name='plunger hole',
            op=CUT, targets=[body])
    # pivot hole through both cheeks; slot in the arm for the horn's swing
    p.prism([px_, py_, tv['eye_z'][0] - 6], ZF, 0, tv['eye_z'][1] - tv['eye_z'][0] + 12, sh.circle(1.7),
            name='pivot hole', op=CUT, targets=[body])
    hz = tv['horn_z']
    p.prism([0, 0, 0], ZF, hz[0] - 0.5, hz[1] + 0.5, sh.rect(px_ - tv['horn_w'] / 2 - 1.5, px_ + tv['horn_w'] / 2 + 13, a['y'][0] - 1, py_ + tv['horn'] + 4.5),
            name='horn slot', op=CUT, targets=[body])
    # cable: the housing lies in a pocket open to the arm's +Z side and seats on a wall; the wire goes straight
    # through the wall into the horn slot (the only enclosed run: straight, so a stiff wire pushes through)
    cy, cz = CABLE['y'], sum(hz) / 2
    x0, x1 = CABLE['pocket_x']
    p.prism([0, 0, 0], ZF, cz - 2.7, a['z'][1] + 1, sh.rect(x0, x1, cy - 2.7, cy + 2.7), name='housing pocket', op=CUT,
            targets=[body])
    p.prism([CABLE['wall'][0] - 1, cy, cz], XF, 0, CABLE['wall'][1] - CABLE['wall'][0] + 2, sh.circle(1.0),
            name='wire hole', op=CUT, targets=[body])
    for zz, yy in FLANGE:                                          # flange screws into the tab's inserts
        p.prism([a['x'][0], yy, zz], XF, -1, 25, sh.circle(1.7), name='flange screw hole', op=CUT, targets=[body])
        p.prism([a['x'][0] + 4, yy, zz], XF, 0, a['x'][1] - a['x'][0], sh.circle(3.2), name='flange screw tunnel',
                op=CUT, targets=[body])                         # open at the arm's front end: a hex key reaches
    for xs in P['rail']['screws']:
        if xs > 0:
            p.prism([xs, a['y'][1], 0], YF, -7.0, 1, sh.circle(2.0), name='rail insert hole', op=CUT, targets=[body])
    pu = P['pusher']
    p.prism([pu['pivot'][0], bk['top'], pu['pivot'][1]], YF, -6.0, 1, sh.circle(2.0), name='pusher insert hole',
            op=CUT, targets=[body])
    body.name = 'handle (printed)'
    p.finish()
    return 'handle: %d bodies' % p.comp.bRepBodies.count


def trigger_pt(deg_from_rest, pt):
    """A point of the trigger (rest pose) after it turns deg_from_rest toward the grip (about +Z at the pivot)."""
    px_, py_ = P['trigger']['pivot']
    a = math.radians(deg_from_rest)
    x, y = pt[0] - px_, pt[1] - py_
    return px_ + x * math.cos(a) - y * math.sin(a), py_ + x * math.sin(a) + y * math.cos(a)


def _trigger(g):
    """Spray-bottle trigger (printed, flat): a short curved lever for the index and middle fingers, hanging from the
    pivot at the top of the grip (under the arm); a horn goes up from the pivot into the arm and pulls the cable when
    the trigger is squeezed. And the pusher lever (printed, flat) on the arm's front bracket."""
    tv = P['trigger']
    px_, py_ = tv['pivot']
    a = math.radians(tv['rest_deg'])
    d, n = (math.sin(a), -math.cos(a)), (math.cos(a), math.sin(a))     # along the lever (down, leaning forward), forward
    T, L = tv['t'], tv['len']
    pts = []
    for k in range(9):                                                  # front edge bows forward (finger rest)
        s = L * k / 8
        bow = 2.5 * math.sin(math.pi * k / 8)
        pts.append((px_ + d[0] * s + n[0] * (T / 2 + bow), py_ + d[1] * s + n[1] * (T / 2 + bow)))
    pts += [(px_ + d[0] * L - n[0] * T / 2, py_ + d[1] * L - n[1] * T / 2), (px_ - n[0] * T / 2, py_ - n[1] * T / 2)]
    p = Part(g, 'Gripper trigger (printed)', color='#2b9d8f')
    lever = p.prism([0, 0, 0], ZF, tv['z'][0], tv['z'][1], _poly(pts), name='lever').bodies.item(0)
    eye = p.cyl('z', [px_, py_, sum(tv['eye_z']) / 2], 5.0, tv['eye_z'][1] - tv['eye_z'][0] - 0.02, name='eye')[0]
    hz = tv['horn_z']
    hw_ = tv['horn_w'] / 2
    horn = p.prism([0, 0, 0], ZF, hz[0], hz[1], _poly([(px_ - hw_, py_), (px_ + hw_, py_), (px_ + hw_, py_ + tv['horn'] + 3),
                                                       (px_ - hw_, py_ + tv['horn'] + 3)]), name='cable horn').bodies.item(0)
    body = p.join([lever, eye, horn])[0]
    p.prism([px_, py_, tv['eye_z'][0]], ZF, -1, tv['eye_z'][1] - tv['eye_z'][0] + 2, sh.circle(1.7), name='pivot bore',
            op=CUT, targets=[body])
    p.prism([0, 0, sum(hz) / 2], ZF, -0.9, 0.9, sh.rect(px_ - hw_ - 1, px_ + hw_ + 1, CABLE['y'] - 0.9, py_ + tv['horn'] + 4),
            name='wire slot', op=CUT, targets=[body])               # open at the top: the wire drops in
    body.name = 'trigger (printed)'
    p.finish()
    pu = P['pusher']
    q = Part(g, 'Gripper pusher (printed)', color='#2b9d8f')
    (x0, z0), (x1, z1) = pu['pivot'], pu['tip']
    dl = unit([x1 - x0, 0, z1 - z0])
    nw = [-dl[2] * pu['w'] / 2, 0, dl[0] * pu['w'] / 2]
    lv = q.prism([0, pu['y'][0], 0], YF, 0, pu['y'][1] - pu['y'][0],
                 _xz([(x0 + nw[0], z0 + nw[2]), (x1 + nw[0], z1 + nw[2]), (x1 - nw[0], z1 - nw[2]),
                      (x0 - nw[0], z0 - nw[2])]), name='lever').bodies.item(0)
    hub = q.cyl('y', [x0, sum(pu['y']) / 2, z0], 5.0, pu['y'][1] - pu['y'][0], name='hub')[0]
    body = q.join([lv, hub])[0]
    q.prism([x0, pu['y'][0], z0], YF, -1, 6, sh.circle(1.7), name='pivot hole', op=CUT, targets=[body])
    wx, wz = x0 + dl[0] * pu['wire'], z0 + dl[2] * pu['wire']
    q.prism([wx, sum(pu['y']) / 2, wz], XF, -6, 6, sh.circle(0.9), name='cable hole', op=CUT, targets=[body])
    body.name = 'pusher lever (printed)'
    q.finish()
    return 'trigger + pusher ok'


def _wire_point():
    """Where the wire attaches on the pusher lever (rail frame X, Z)."""
    pu = P['pusher']
    L = math.hypot(pu['tip'][0] - pu['pivot'][0], pu['tip'][1] - pu['pivot'][1])
    return (pu['pivot'][0] + (pu['tip'][0] - pu['pivot'][0]) * pu['wire'] / L,
            pu['pivot'][1] + (pu['tip'][1] - pu['pivot'][1]) * pu['wire'] / L)


def _loop(x_start, y0, z0, y1, r, z_free, n=10):
    """Housing U-turn: from (x_start, y0, z0) heading -X, round a radius r in the X-Z plane to heading +X. It stays at
    y0 while inside the arm's side pocket (z below z_free), then rises to y1."""
    pts = []
    for k in range(n + 1):
        t = math.pi * k / n
        z = z0 + r * (1 - math.cos(t))
        f = 0.0 if z < z_free else min(1.0, (z - z_free) / (z0 + 2 * r - z_free))
        pts.append([x_start - r * math.sin(t), y0 + (y1 - y0) * f, z])
    return pts


def cable_housing():
    """Housing: seated on the pocket's wall, back along the pocket, out of its open side in a U-turn, forward to
    the cable stop at the arm's front."""
    tv = P['trigger']
    wx, wz = _wire_point()
    cz, yc = sum(tv['horn_z']) / 2, sum(P['pusher']['y']) / 2      # the housing ends level with the pusher's hole
    w0 = CABLE['wall'][0]
    return [[w0, CABLE['y'], cz]] + _loop(w0 - 12, CABLE['y'], cz, yc, CABLE['loop_r'], P['arm']['z'][1] + 3) + \
        [[LUG_X[0] - 8, yc, wz], [LUG_X[0], yc, wz]]


def cable_route():
    """The trigger cable's inner wire, trigger end first (rail frame, mm, rest pose): barrel nipple behind the horn,
    through the horn's open slot and the wall, inside the housing, through the cable stop, through the pusher lever
    to the screw nipple. Built from this and checked against it (design_rules: cables)."""
    tv, pu = P['trigger'], P['pusher']
    wx, wz = _wire_point()
    yw = sum(pu['y']) / 2
    cz = sum(tv['horn_z']) / 2
    nip = tv['pivot'][0] + tv['horn_w'] / 2 + 0.2 + CABLE['nipple'][1] / 2
    return [[nip, CABLE['y'], cz]] + cable_housing() + [[LUG_X[1], yw, wz], [wx, yw, wz],
                                                        [wx + 4.7 + CABLE['screw_nipple'][1] / 2, yw, wz]]


def _damper_gear(g, X):
    """The rotary damper's own gear (m1, 11 teeth) on its shaft, phased to mesh with the -Z rack at the stowed spot."""
    dm, ge, rk = P['damper'], P['gear'], P['rack']
    xc = X + dm['x']
    rp = ge['m'] * 11 / 2
    p_ = math.pi * ge['m']
    xg = rk['pieces'][0][0] + round((xc - rk['pieces'][0][0]) / p_) * p_      # a rack gap (between teeth)
    phase = math.degrees(math.acos((xg - xc) / rp))                         # a tooth points into it
    q = Part(g, 'Gripper damper gear (buy)', color=HWC)
    gb = q.prism([0, dm['gear_y'][0], 0], YF, 0, dm['gear_y'][1] - dm['gear_y'][0],
                 _xz(gear_pts(ge['m'], 11, ge['pa'], 0.1, phase, (xc, dm['z']))), name='gear').bodies.item(0)
    shaft = q.cyl('y', [xc, (dm['gear_y'][1] + dm['body_y'][0]) / 2, dm['z']], 1.5,
                  dm['body_y'][0] - dm['gear_y'][1] + 0.02, name='shaft')
    gb = q.join([gb] + shaft)[0]
    gb.name = 'damper gear 11T m1 + shaft (buy, part of the rotary damper)'
    q.finish()


def _spool(g):
    """Printed spool on the base's post: the constant-force spring's coil sits on it."""
    sp, b = P['spool'], P['base']
    q = Part(g, 'Gripper spool (printed)', color=PRINT)
    hub = q.ann('y', [sp['x'], b['y'][1] + 4.1, sp['z']], sp['r'] + 0.2, 4.2, 7.8, name='hub')[0]
    fl = q.ann('y', [sp['x'], b['y'][1] + 8.0, sp['z']], sp['coil_ro'], 4.2, 1.0, name='flange')[0]
    body = q.join([hub, fl])[0]
    body.name = 'spool (printed): the constant-force spring coils on it'
    q.finish()


def _hw(g):
    """Bought parts: screws, inserts, axles, damper, return spring, closing spring, trigger cable."""
    h, ge, b, r = P['head'], P['gear'], P['base'], P['rail']
    X = _head_x()
    p = Part(g, 'Gripper HW fixed (buy)', color=HWC)
    q = Part(g, 'Gripper HW head (buy)', color=HWC)
    up, down = sh.frame_of([0, -1, 0]), sh.frame_of([0, 1, 0])

    def ins(part, c, d_dir, name):                                 # insert from c, 5.7 deep along d_dir
        bd = part.cyl('y', add(c, [0, d_dir * 2.85, 0]), 2.0, 5.7, name='insert')[0]
        bd.name = 'M3 heat-set insert ruthex 5.7, %s (buy)' % name
    for xc in P['clips']:
        sh.hw_bolt(p, [xc, b['y'][1] - 6.5, 0], up, 9.5, (5.6, 2.4), '#4 x 3/8" pan-head self-tapping screw, pipe (buy)',
                   dia=2.9)
    t = P['tab']
    sh.hw_bolt(p, [t['x'][1] - 5.3, 13.5, 0], sh.frame_of([-1, 0, 0]), 9.5, (5.6, 2.4),
               '#4 x 3/8" pan-head self-tapping screw, ring (buy)', dia=2.9)
    for xs in r['screws']:                                         # rail: heads in its counterbores
        sh.hw_bolt(p, [xs, r['y'][1] - 3.5, 0], up, 8.0, (5.5, 3.0), 'M3 x 8 socket head, rail (buy)', dia=3.0)
        ins(p, [xs, r['y'][0], 0], -1, 'rail')
    sp = P['spool']
    sh.hw_bolt(p, [sp['x'], b['y'][1] + 8.5, sp['z']], up, 8.0, (5.5, 3.0), 'M3 x 8 socket head, spool (buy)', dia=3.0)
    ins(p, [sp['x'], b['y'][1] + 8.5, sp['z']], -1, 'spool')
    for zz, yy in FLANGE:
        sh.hw_bolt(p, [t['x'][1] + 4, yy, zz], sh.frame_of([-1, 0, 0]), 8.0, (5.5, 3.0),
                   'M3 x 8 socket head, handle flange (buy)', dia=3.0)
        bd = p.cyl('x', [t['x'][1] - 2.85, yy, zz], 2.0, 5.7, name='insert')[0]
        bd.name = 'M3 heat-set insert ruthex 5.7, handle flange (buy)'
    _spool(g)
    coil = p.ann('y', [sp['x'], b['y'][1] + 4.0, sp['z']], sp['coil_ro'], sp['r'] + 0.2, 6.0, name='coil')[0]
    coil.name = 'constant-force spring ~3 N, 6 mm wide (buy)'
    tape = p.box(sp['x'], X + h['outline'][0], b['y'][1] + 1.0, b['y'][1] + 7.0, P['tape_z'][0], P['tape_z'][1],
                 name='tape')[0]
    tape.name = 'constant-force spring tape (buy)'
    # pusher pivot
    pu, bk = P['pusher'], P['arm']['bracket']
    sh.hw_bolt(p, [pu['pivot'][0], pu['y'][1], pu['pivot'][1]], up, 10.0, (5.5, 3.0), 'M3 x 10 socket head, pusher pivot (buy)',
               dia=3.0)
    ins(p, [pu['pivot'][0], bk['top'], pu['pivot'][1]], -1, 'pusher')
    lk, zw = P['lock'], h['outline'][2]
    lx = lock_x()
    pl = p.cyl('z', [lx, lk['pin_y'], (lk['z'][0] - 2 + lk['z'][1]) / 2], 3.9, lk['z'][1] - lk['z'][0] + 2, name='plunger')[0]
    pin = p.cyl('z', [lx, lk['pin_y'], (lk['z'][1] - zw + lk['depth']) / 2], lk['pin_d'] / 2, -zw + lk['depth'] - lk['z'][1],
                name='pin')[0]
    knob = p.cyl('z', [lx, lk['pin_y'], lk['z'][0] - 2 - 5], 7.0, 10.0, name='knob')[0]
    pl = p.join([pl, pin, knob])[0]
    pl.name = 'index plunger M8, pull knob, pin 5 mm (buy)'
    # trigger pivot (through the cheeks under the arm and the trigger's eye; nyloc not modelled)
    tv = P['trigger']
    px_, py_ = tv['pivot']
    sh.hw_bolt(p, [px_, py_, tv['eye_z'][0] - 4.5], sh.frame_of([0, 0, 1]), 40.0, (5.5, 3.0),
               'M3 x 40 socket head, trigger pivot (buy)', dia=3.0)
    # cable: housing from the arm's side to the pusher; inside the grip it runs bare in the bore (not modelled)
    gr, a = P['grip'], P['arm']
    wx = pu['pivot'][0] + (pu['tip'][0] - pu['pivot'][0]) * pu['wire'] / math.hypot(pu['tip'][0] - pu['pivot'][0], pu['tip'][1] - pu['pivot'][1])
    wz = pu['pivot'][1] + (pu['tip'][1] - pu['pivot'][1]) * pu['wire'] / math.hypot(pu['tip'][0] - pu['pivot'][0], pu['tip'][1] - pu['pivot'][1])
    yc = 22.0                                             # under the drive tab's path
    cy, cz = tv['pivot'][1] + tv['horn'], sum(tv['horn_z']) / 2
    zh = a['z'][1] + 2.5                                  # housing seated on the arm's side face
    hs = p.polypipe(cable_housing(), 2.5, name='cable housing')[0]
    hs.name = 'brake cable housing 5 mm (buy)'
    wire = p.polypipe(cable_route(), 0.75, name='inner wire')[0]
    rt = cable_route()
    tn = Part(g, 'Gripper HW trigger nipple (buy)', color=HWC)
    tn.cyl('x', rt[0], CABLE['nipple'][0] / 2, CABLE['nipple'][1])[0].name = 'brake cable barrel nipple 6 x 6 (buy, on the wire)'
    tn.finish()
    pn = Part(g, 'Gripper HW pusher nipple (buy)', color=HWC)
    pn.cyl('x', rt[-1], CABLE['screw_nipple'][0] / 2, CABLE['screw_nipple'][1])[0].name = \
        'solderless screw nipple 6.5 x 8 (buy): clamps the wire, sets the tension'
    pn.finish()
    wire.name = 'brake cable inner wire 1.5 mm (buy)'
    # head hardware
    for zz in (ge['zc'], -ge['zc']):
        sh.hw_bolt(q, [X, h['lid'][1], zz], up, 16.0, (5.5, 3.0), 'M3 x 16 socket head, gear axle (buy)', dia=3.0)
        ins(q, [X, h['plate'][1], zz], -1, 'gear axle')
    for px2, pz in h['posts']:
        sh.hw_bolt(q, [X + px2, h['lid'][1], pz], up, 8.0, (5.5, 3.0), 'M3 x 8 socket head, lid (buy)', dia=3.0)
        ins(q, [X + px2, h['lid'][0], pz], -1, 'lid')
    xc = X + P['carriage']['dx']
    for dx in (-10.0, 10.0):
        for zz in (-10.0, 10.0):
            sh.hw_bolt(q, [xc + dx, h['plate'][1] - 3.2, zz], up, 8.0, (5.5, 3.0), 'M3 x 8 socket head, carriage (buy)',
                       dia=3.0)
    fr = P['finger']
    for side in (1, -1):
        f = Part(g, 'Gripper HW finger %s (buy)' % ('R' if side > 0 else 'L'), color=HWC)
        c = [X + fr['r1'] - 8, fr['y'][1], side * ge['zc']]
        sh.hw_bolt(f, c, up, 16.0, (5.5, 3.0), 'M3 x 16 socket head, finger (buy)', dia=3.0)
        ins(f, [c[0], h['gear'][1], c[2]], -1, 'finger')
        f.finish()
    dm = P['damper']
    _damper_gear(g, X)
    db = q.cyl('y', [X + dm['x'], sum(dm['body_y']) / 2, dm['z']], dm['body_r'], dm['body_y'][1] - dm['body_y'][0],
               name='damper body')[0]
    db.name = 'rotary gear damper, body (buy)'
    dv, zw = P['drive'], h['outline'][2]
    f = Part(g, 'Gripper HW drive pin (buy)', color=HWC)
    # head down: the pusher bears on the steel head; the shank goes up through the arm into a nyloc on top
    pc = [X, h['gear'][1], ge['zc'] + dv['len']]
    yh = h['gear'][1] + 3.6 - dv['pin_len']                       # under-head face
    sh.hw_bolt(f, [pc[0], yh, pc[2]], down, dv['pin_len'], (7.0, 4.0), 'M4 x 20 socket head, drive pin (buy)', dia=4.0)
    nut = f.prism(pc, YF, 0, 3.2, sh.hexagon(7.0), name='nut').bodies.item(0)
    f.prism(pc, YF, -1, 5, sh.circle(2.0), name='thread', op=CUT, targets=[nut])
    nut.name = 'M4 nyloc nut, drive pin (buy)'
    f.finish()
    ys = sum(h['plate']) / 2
    sp_ = q.polypipe([[X + 4.6, ys, ge['zc'] + dv['len'] - 1.0], [X + 9, ys, zw + 2.5]], 1.6, name='closing spring')[0]
    sp_.name = 'extension spring 4 x 12, closes the fingers (buy)'
    for part in (p, q):
        part.finish()
    return 'hw ok'


# ------------------------------------------------------------------ motion
def _chain(squeeze):
    """Trigger squeeze 0..1 -> (trigger deg, pusher deg, finger deg each) with the head slid forward."""
    tv, pu, dv = P['trigger'], P['pusher'], P['drive']
    ta = squeeze * tv['travel_deg']
    pull = tv['horn'] * math.sin(math.radians(ta))                  # the horn drops: cable pulled
    pa = math.degrees(pull / pu['wire'])
    L = math.hypot(pu['tip'][0] - pu['pivot'][0], pu['tip'][1] - pu['pivot'][1])
    a0 = math.atan2(pu['tip'][1] - pu['pivot'][1], pu['tip'][0] - pu['pivot'][0])
    dx = L * (math.cos(a0) - math.cos(a0 - math.radians(pa)))      # how far the tip moves back (-X)
    th = math.degrees(math.asin(max(0.0, min(1.0, dx / dv['len']))))
    return ta, pa, th


def open_deg(squeeze):
    return _chain(squeeze)[2]


def poses(s, squeeze=0.0):
    """{component name prefix: Matrix3D in the rail frame} for slide-out s (0 stowed .. 1 forward) and trigger squeeze
    (0..1). The fingers open only with the head forward (the pusher reaches the drive tab only there)."""
    M, V, Pt = adsk.core.Matrix3D, adsk.core.Vector3D, adsk.core.Point3D
    ta, pa, th = _chain(squeeze)
    if s < 0.999:
        th = 0.0                                # stowed: the pusher swings but meets nothing

    def tr(dx):
        m = M.create()
        m.translation = V.create(dx / 10.0, 0, 0)
        return m

    def rot_y(deg, cx, cz, dx=0.0):             # +deg turns +X toward +Z, about a Y axis through (cx, cz)
        m = M.create()
        m.setToRotation(math.radians(-deg), V.create(0, 1, 0), Pt.create(cx / 10.0, 0, cz / 10.0))
        m.transformBy(tr(dx))
        return m
    dx = s * P['stroke']
    gz = P['gear']['zc']
    X = _head_x()
    dm = P['damper']
    out = {'Gripper carriage': tr(dx), 'Gripper head': tr(dx), 'Gripper HW head': tr(dx),
           'Gripper damper gear': rot_y(math.degrees(dx / (P['gear']['m'] * 11 / 2)), X + dm['x'], dm['z'], dx),
           'Gripper HW drive pin': rot_y(th, X, gz, dx),
           'Gripper gear R': rot_y(th, X, gz, dx), 'Gripper finger R': rot_y(th, X, gz, dx),
           'Gripper HW finger R': rot_y(th, X, gz, dx),
           'Gripper gear L': rot_y(-th, X, -gz, dx), 'Gripper finger L': rot_y(-th, X, -gz, dx),
           'Gripper HW finger L': rot_y(-th, X, -gz, dx)}
    tv, pu = P['trigger'], P['pusher']
    m = M.create()
    m.setToRotation(math.radians(-ta), V.create(0, 0, 1), Pt.create(tv['pivot'][0] / 10.0, tv['pivot'][1] / 10.0, 0))
    out['Gripper trigger'] = m
    out['Gripper HW trigger nipple'] = m
    out['Gripper pusher'] = rot_y(-pa, pu['pivot'][0], pu['pivot'][1])
    out['Gripper HW pusher nipple'] = rot_y(-pa, pu['pivot'][0], pu['pivot'][1])
    return out


def pose(s, squeeze=0.0):
    """Pose the gripper in the open document (through root proxies; see LESSONS)."""
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    ps = poses(s, squeeze)
    n = 0
    for o in d.rootComponent.allOccurrences:
        if NAME not in o.fullPathName or o.component.name == NAME:
            continue
        for k, m in ps.items():
            if o.component.name.startswith(k):
                o.transform2 = m
                n += 1
                break
        else:
            o.transform2 = adsk.core.Matrix3D.create()
    return n


# ------------------------------------------------------------------ design rules (design_rules.py)
F_FINGER = 40.0             # N: a hard squeeze on the trigger, at the finger pad
FINGER_AT = 35.0            # mm below the trigger pivot


def _loads():
    """Design loads on the slender printed (and pin) features, from P: a hard squeeze, carried down the chain."""
    tv, pu, dv = P['trigger'], P['pusher'], P['drive']
    cable = F_FINGER * FINGER_AT / tv['horn']                              # horn pulls the cable
    tip = math.hypot(pu['tip'][0] - pu['pivot'][0], pu['tip'][1] - pu['pivot'][1])
    tab = cable * pu['wire'] / tip                                         # pusher on the drive tab
    pin_len = P['head']['gear'][0] - sum(P['pusher']['y']) / 2             # arm to where the pusher bears on the head
    hz = tv['horn_z']
    pin_steel = dv.get('pin', 'printed') == 'steel'
    return [
        dict(name='trigger lever', force=F_FINGER, arm=FINGER_AT, section=('rect', tv['t'], tv['z'][1] - tv['z'][0]),
             material='PETG along layers'),
        dict(name='trigger horn (pulls the cable)', force=cable, arm=tv['horn'],
             section=('rect', tv.get('horn_w', 6.0), hz[1] - hz[0]), material='PETG along layers'),
        dict(name='pusher lever', force=tab, arm=tip, section=('rect', pu['w'], pu['y'][1] - pu['y'][0]),
             material='PETG along layers'),
        dict(name='gear R drive arm', force=tab, arm=dv['len'] - 5,
             section=('rect', dv['w'], P['head']['gear'][1] - P['head']['gear'][0]), material='PETG along layers'),
        dict(name='drive tab pin (%s)' % ('steel M4' if pin_steel else 'printed, upright'), force=tab, arm=pin_len,
             section=('round', 4.0 if pin_steel else 6.0),
             material='steel' if pin_steel else 'PETG across layers'),
    ]


RULES = dict(
    anchor='Gripper rail base',
    rest=(0.0, 0.0),
    meshes=[('damper gear 11T', 'rail base', 11), ('gear R', 'gear L', P['gear']['z'])],
    chains=[('trigger drive (head forward)', (1.0, 0.0),
             [('trigger (printed)', 'inner wire'), ('inner wire', 'pusher lever'), ('pusher lever', 'drive pin'),
              ('drive pin', 'gear R'),
              ('gear R', 'gear L'), ('gear R', 'finger R'), ('gear L', 'finger L')]),
            ('trigger pivot', (0.0, 0.0), [('trigger (printed)', 'trigger pivot'), ('trigger pivot', 'handle')])],
    cables=[('trigger cable', cable_route, 'nipple')],
    loads=_loads,
)

