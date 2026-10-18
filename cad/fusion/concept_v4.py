"""Shoulder v4 concept mock-ups (not for print): the shoulder girdle (shrug + forward/back) carried by
V1  a double parallelogram (lift links pivoting about X, then fore-aft links pivoting about Z) on a short mast
    behind/above the shoulder blade, with a gas spring on the lift links;
V2  a passive delta: three legs, one from an arch over the trapezius and two from the frame behind. Each leg is an
    upper arm on a hinge plus a parallelogram rod pair, so the platform (the abduction housing) only translates.
The abduction housing sits on the abduction axis behind GH (as the old mount block did); the existing yoke, link and
elbow (the 'Abduction side' occurrence) follow the housing. build(variant, d) rebuilds the mechanism for a girdle
offset d (mm, scan frame: X fwd, Y up, Z right) and moves the shoulder module; restore() undoes everything.
"""
import math
import adsk.core
import adsk.fusion

import fxlib as fx
from fxlib import Part, add, sub, mul, unit, cross, dot, norm
import shoulder as sh

NAME = 'PROPOSAL v4 (concept, not for print)'
NEW, SPRING, FRAME_C, ROD = '#1d9e75', '#d4a017', '#5b6770', '#c9d2d9'
HIDE = (('Abduction mount blocks', 'block R'), ('HW abd', None), ('Abduction sleeve', None))
H0 = [-158.0, 1345.0, 165.0]          # abduction housing centre at rest: on the abduction axis, behind the yoke root
STATE = {}

# ---- V2 delta: anchors (scan mm), platform attachment points relative to the housing centre
ARCH = [[-211, 1405, 30], [-205, 1470, 55], [-150, 1506, 95], [-62, 1500, 122]]   # over the trapezius, lateral of the strap
D_ANCHOR = [[-62, 1500, 122], [-230, 1425, 42], [-226, 1268, 8]]   # top (arch), high + low near the spine:
                                                                    # the back legs run diagonally, ~180 mm long
D_REL = [[0, 36, -6], [-22, 10, -30], [-22, -30, 16]]
D_LA, D_W, D_ELBOW = 0.55, 18.0, 60.0  # upper arm as a fraction of the anchor-platform distance, half rod
                                       # spacing, elbow bend at rest (deg)


def _top():
    return next(o for o in fx.design.rootComponent.occurrences if o.component.name == sh.TOP)


def _abd():
    return next(o for o in fx.design.rootComponent.allOccurrences if o.component.name.startswith('Abduction side'))


def _hidden_targets():
    root = fx.design.rootComponent
    for o in root.allOccurrences:
        for cp, bp in HIDE:
            if cp in o.component.name:
                for b in o.component.bRepBodies:
                    if bp is None or bp in b.name:
                        yield b
    pvc = next(o for o in root.allOccurrences if o.component.name.startswith('PVC pipes'))
    for b in pvc.component.bRepBodies:                    # the right beam + diagonal that ran to the old block
        c = b.createForAssemblyContext(pvc).boundingBox
        if (c.minPoint.y + c.maxPoint.y) / 2 < -10 and (c.minPoint.z + c.maxPoint.z) / 2 > 125:
            yield b


def _remove_mech():
    top = _top().component
    for o in list(top.occurrences):
        if o.component.name == NAME:
            o.deleteMe()


def move_module(disp, abd_deg=0.0):
    """Shoulder module (yoke, link, elbow) translated by disp (mm) and raised abd_deg about the moved abduction axis."""
    abd = _abd()
    if 'abd_rest' not in STATE:
        STATE['abd_rest'] = list(abd.transform2.asArray())
    gh = add(sh.GH, disp)
    R = fx.rot('x', -abd_deg)
    m = fx.matrix(R, sub(gh, fx.mat_vec(R, gh)))
    t = adsk.core.Matrix3D.create()
    t.translation = adsk.core.Vector3D.create(disp[0] / 10.0, disp[1] / 10.0, disp[2] / 10.0)
    # m rotates about the moved GH; apply the translation first (rest geometry -> moved), then the rotation
    t.transformBy(m)
    t.transformBy(_top().transform2)
    abd.transform2 = t


def restore():
    fx.init()
    _remove_mech()
    for b in _hidden_targets():
        b.isLightBulbOn = True
    if 'abd_rest' in STATE:
        m = adsk.core.Matrix3D.create()
        m.setWithArray(STATE.pop('abd_rest'))
        _abd().transform2 = m
    return 'restored'


def _leg_solve(A, h, E0, Pi, lr):
    """Delta leg: upper arm A->E turns about h; find E with |E - Pi| = lr (root nearest the rest angle)."""
    la = norm(sub(E0, A))
    u = unit(sub(E0, A))
    v = cross(h, u)
    E = lambda th: add(A, add(mul(u, la * math.cos(th)), mul(v, la * math.sin(th))))
    f = lambda th: norm(sub(E(th), Pi)) - lr
    best, prev = None, None
    for k in range(-120, 121, 3):
        th = math.radians(k)
        fv = f(th)
        if prev is not None and (fv > 0) != (prev[1] > 0):
            lo, hi = prev[0], th
            for _ in range(50):
                mid = (lo + hi) / 2
                if (f(mid) > 0) == (f(lo) > 0):
                    lo = mid
                else:
                    hi = mid
            r = (lo + hi) / 2
            if best is None or abs(r) < abs(best):
                best = r
        prev = (th, fv)
    return None if best is None else E(best)


def _delta_rest():
    legs = []
    for A, rel in zip(D_ANCHOR, D_REL):
        Pi = add(H0, rel)
        h = unit(cross(sub(Pi, A), [0, 1, 0]))
        rej = sub(sub(Pi, A), mul(h, dot(sub(Pi, A), h)))
        u = unit(rej)
        v = cross(h, u)
        a = math.radians(D_ELBOW)
        E0 = add(A, mul(add(mul(u, math.cos(a)), mul(v, math.sin(a))), D_LA * norm(rej)))
        legs.append(dict(A=A, h=h, E0=E0, rel=rel, lr=norm(sub(Pi, E0))))
    return legs


def _rod(p, a, b, r, name):
    return p.polypipe([a, b], r, name=name)


def build(variant, d=(0.0, 0.0, 0.0), abd_deg=0.0):
    """Rebuild the mechanism for girdle offset d and pose the shoulder module. Returns the housing displacement."""
    fx.init()
    _remove_mech()
    grp = fx.group(_top().component, NAME)
    for b in _hidden_targets():
        b.isLightBulbOn = False
    d = list(d)
    frame = Part(grp, 'frame extension', color=FRAME_C)
    mech = Part(grp, 'mechanism (new joints)', color=NEW)
    spring = Part(grp, 'gas spring', color=SPRING)
    if variant == 'V1':
        # short mast from the top node up behind the shoulder blade, base block for the lift links
        frame.polypipe([[-211, 1405, 30], [-208, 1440, 45], [-202, 1462, 52]], 11, name='mast')
        frame.box(-215, -185, 1428, 1492, 44, 64)
        L, L2 = 110.0, 125.0
        th = math.asin(max(-0.95, min(0.95, d[1] / L)))
        zc = 55 + L * math.cos(th)
        for y in (1478, 1443):
            b0, b1 = [-200, y, 55], [-200, y + d[1], zc]
            _rod(mech, b0, b1, 6, 'lift link')
            for q in (b0, b1):
                mech.cyl('x', q, 7, 26, name='pivot (6806 / 608)')
        mech.box(-214, -186, 1433 + d[1], 1500 + d[1], zc - 8, zc + 8)          # lift carriage
        mech.box(-214, -150, 1488 + d[1], 1500 + d[1], zc - 8, zc + 8)          # its forward arm
        ph = math.asin(max(-0.95, min(0.95, d[0] / L2)))
        bots = []
        for x in (-200, -165):
            t = [x, 1494 + d[1], zc]
            b = [x + L2 * math.sin(ph), t[1] - L2 * math.cos(ph), zc]
            _rod(mech, t, b, 6, 'fore-aft link')
            for q in (t, b):
                mech.cyl('z', q, 7, 22, name='pivot')
            bots.append(b)
        H = add(bots[1], [7, -24, 0])
        mech.box(bots[0][0] - 8, bots[1][0] + 8, bots[0][1] - 10, bots[0][1] + 10, zc - 10, zc + 10)
        mech.box(H[0] - 12, H[0] + 12, H[1], bots[1][1], zc - 10, zc + 10)        # drop to the housing
        spring.polypipe([[-196, 1418, 50], [-196, 1443 + d[1] / 2, (55 + zc) / 2]], 6, name='gas spring')
    elif variant == 'V3':
        # V1's mast + lift parallelogram, then a SCARA arm (two vertical pivots) under the lift carriage: the
        # housing moves forward/back AND in/out; a parallel link keeps it from turning. All joints on bearings.
        frame.polypipe([[-211, 1405, 30], [-208, 1440, 45], [-202, 1462, 52]], 11, name='mast')
        frame.box(-215, -185, 1428, 1492, 44, 64)
        L = 110.0
        th = math.asin(max(-0.95, min(0.95, d[1] / L)))
        zc = 55 + L * math.cos(th)
        for y in (1478, 1443):
            b0, b1 = [-200, y, 55], [-200, y + d[1], zc]
            _rod(mech, b0, b1, 6, 'lift link')
            for q in (b0, b1):
                mech.cyl('x', q, 7, 26, name='pivot')
        mech.box(-214, -186, 1433 + d[1], 1500 + d[1], zc - 8, zc + 8)          # lift carriage
        S0 = [-215, 1422 + d[1], zc - 60]                                       # SCARA pivot 1 (vertical axis)
        mech.box(-224, -206, S0[1] - 6, 1433 + d[1], S0[2] - 8, zc + 8)          # bracket under the carriage
        H = add(H0, d)
        E = [H[0] - 20, S0[1], H[2]]
        L1 = L2 = 65.0
        dx, dz = E[0] - S0[0], E[2] - S0[2]
        dd = math.hypot(dx, dz)
        if dd > L1 + L2 - 1 or dd < 5:
            raise RuntimeError('SCARA cannot reach (%.0f mm)' % dd)
        a0 = math.atan2(dz, dx)
        cang = math.acos((L1 * L1 + dd * dd - L2 * L2) / (2 * L1 * dd))
        cands = [[S0[0] + L1 * math.cos(a0 + s * cang), S0[1], S0[2] + L1 * math.sin(a0 + s * cang)] for s in (1, -1)]
        C = min(cands, key=lambda q: q[0])                                     # elbow behind, away from the back
        for p_, q_ in ((S0, C), (C, E)):
            _rod(mech, p_, q_, 7, 'SCARA link')
            _rod(mech, add(p_, [0, 14, 0]), add(q_, [0, 14, 0]), 3, 'parallel link (keeps the housing square)')
        for q in (S0, C, E):
            mech.cyl('y', q, 9, 26, name='SCARA pivot (bearings)')
        drop = [E[0], H[1] + 28, E[2]]
        _rod(mech, E, drop, 8, 'drop to the housing')
        _rod(mech, drop, [H[0] - 12, H[1] + 28, H[2]], 8, 'housing bracket')
        spring.polypipe([[-196, 1418, 50], [-196, 1443 + d[1] / 2, (55 + zc) / 2]], 6, name='gas spring')
    else:
        frame.polypipe(ARCH, 11, name='arch over the trapezius')
        frame.polypipe([[-211, 1268, 30], [-226, 1268, 8]], 9, name='lower anchor arm')
        frame.polypipe([[-211, 1415, 30], [-230, 1425, 42]], 9, name='upper anchor arm')
        H = add(H0, d)
        for leg in _delta_rest():
            Pi = add(H, leg['rel'])
            E = _leg_solve(leg['A'], leg['h'], leg['E0'], Pi, leg['lr'])
            if E is None:
                raise RuntimeError('delta leg cannot reach %s' % [round(c) for c in Pi])
            h, w = leg['h'], D_W
            mech.cyl(sh.frame_of(h), leg['A'], 8, 30, name='leg hinge')
            _rod(mech, leg['A'], E, 6, 'upper arm')
            _rod(mech, add(E, mul(h, -w)), add(E, mul(h, w)), 4, 'elbow bar')
            _rod(mech, add(Pi, mul(h, -w)), add(Pi, mul(h, w)), 4, 'platform bar')
            for s in (-1, 1):
                _rod(mech, add(E, mul(h, s * w)), add(Pi, mul(h, s * w)), 3.5, 'parallel rod (ball ends)')
            _rod(mech, Pi, H, 6, 'platform strut')
        spring.polypipe([[-120, 1503, 105], add(H, [0, 30, -20])], 5, name='gas spring')
    mech.cyl('x', H, 30, 25, name='abduction housing (2 x 6806)')
    for p in (frame, mech, spring):
        p.finish()
    disp = sub(H, H0)
    move_module(disp, abd_deg)
    return [round(c, 1) for c in disp]


def view(path, which='back', w=900, h=700):
    vp = adsk.core.Application.get().activeViewport
    cams = {'back': ((-12, -13, 135), (-150, -75, 168), 40), 'side': ((-9, -16, 132), (0, -125, 140), 44),
            'top': ((-10, -12, 138), (-30, -18, 230), 34)}
    t, e, x = cams[which]
    c = vp.camera
    c.isFitView = False
    c.cameraType = adsk.core.CameraTypes.PerspectiveCameraType
    c.target = adsk.core.Point3D.create(*t)
    c.eye = adsk.core.Point3D.create(*e)
    c.upVector = adsk.core.Vector3D.create(0, 0, 1)
    c.viewExtents = x
    vp.camera = c
    vp.refresh()
    vp.saveAsImageFile(path, w, h)


def check(variant, d, abds=(-60, -30, 0, 20)):
    """Clearances at girdle offset d (after build): mechanism vs torso (signed, mm) and vs the shoulder strap,
    and the arm module (yoke, link) vs the mechanism while the arm is raised (abd < 0 raises) / lowered."""
    import diag
    fx.init()
    g_torso = diag.grid(diag.torso_points())
    root = fx.design.rootComponent
    harn = next(o for o in root.allOccurrences if o.component.name.startswith('Harness'))
    web = next(b for b in harn.component.meshBodies if b.name.startswith('webbing'))
    tr = harn.transform2
    strap = []
    for p in web.displayMesh.nodeCoordinates:
        q = p.copy(); q.transformBy(tr); strap.append(diag._to_scan(q))
    g_strap = diag.grid(strap)
    mech = {}
    for pat in ('mechanism (new joints)', 'frame extension', 'gas spring'):
        mech.update(diag.body_points(pat))
    H = add(H0, d)
    out = {}
    worst = (1e9, None)
    for k, pts in mech.items():
        for p in pts[::2]:
            dd, t = diag.nearest(g_torso, p)
            if t is None:
                continue
            sd = dd if sum((p[i] - t[i]) * t[3 + i] for i in range(3)) >= 0 else -dd
            if sd < worst[0]:
                worst = (sd, [round(c) for c in p])
    out['mech_to_body'] = (round(worst[0], 1), worst[1])
    ws = (1e9, None)
    for pts in mech.values():
        for p in pts[::2]:
            dd, t = diag.nearest(g_strap, p, rmax=4)
            if t is not None and dd < ws[0]:
                ws = (dd, [round(c) for c in p])
    out['mech_to_strap'] = (round(ws[0], 1) if ws[1] else '>80', ws[1])
    mpts = [p for pts in mech.values() for p in pts[::2]
            if not (abs(p[0] - H[0]) < 22 and math.hypot(p[1] - H[1], p[2] - H[2]) < 40)]
    g_mech = diag.grid(mpts)
    arm = {}
    for pat in ('Yoke', 'Upper-arm link'):
        arm.update(diag.body_points(pat))
    gh = add(sh.GH, d)
    for da in abds:
        best = (1e9, None)
        for k, pts in arm.items():
            for p in pts[::3]:
                q = diag.rot_x(p, da, gh) if da else p
                dd, t = diag.nearest(g_mech, q, rmax=3)
                if t is not None and dd < best[0]:
                    best = (dd, k.split(' / ')[0])
        out['arm %+d' % (-da)] = (round(best[0], 1) if best[1] else '>60', best[1])
    return out
