"""Elbow joint concept B: PVC-pipe arm units on 6806 ball bearings.

Each arm unit is four PVC pipes (21.5/15.5) held by two rings. A ring is a thin
C-band around the arm (anterior opening for donning) with round bosses only
where the pipes pass, so the medial side stays slim. The joint lugs are
separate flat plates that screw onto a pad on the near ring (M4 heat-sets),
so every part prints flat without supports:
  ring   - flat on its face, pipe holes vertical
  lug    - flat on its side, spigot / hub boss up
  cover  - flat
The bearings are bought 6806-2RS (30 x 42 x 7), not printed.

  B   two-sided: a 6806 on the lateral and on the medial side
  B1  lateral-only: two 6806s stacked in one lateral hub, nothing medial

Frame (own document, Z up): X lateral (right arm), Y anterior, Z along the
upper arm. The flexion axis is X through the origin; at 0 deg the forearm
points -Z and flexion swings it toward +Y. Edit P and re-run to iterate.
"""
import math

import adsk.core
import adsk.fusion

import fxlib as fx
from fxlib import Part

P = dict(
    pipe_od=21.5, pipe_id=15.5, pipe_clear=0.4,
    ua_d=120.0,                     # upper arm + padding; placeholder until the flexed-biceps measurement
    fa_d=113.0,                     # forearm 103 mm at its widest (near the elbow) + ~10 mm padding
    wrist_d=80.0,                   # wrist ring bore; placeholder (~70 mm wrist + 10) until measured.
                                    # The forearm pipes lean inward from fa_d to wrist_d.
    padding=10.0,                   # the bores above include ~10 mm of padding over the arm
    band_t=5.0,                     # ring band thickness around the arm
    wall=3.0,                       # material between pipe hole and arm bore / boss rim
    ring_h=25.0,
    # Near (elbow-end) rings cover only the back half, like the shells: the forearm's back half
    # swings into the space in front of the upper arm, so back-half parts can never meet at any
    # flexion. They only have to clear the hubs (hub_r + 0.5) to sit right next to the elbow.
    ring_off=40.0,                  # near ring's face distance from the axis
    near_open=180.0,                # near rings: front half open (the door closes it on the forearm)
    # measured folded, palm up: upper arm 203 inside / 305 outside, forearm 229 / 254 mm;
    # the elbow axis sits about midway, so ~254 mm to the shoulder and ~241 mm to the wrist
    ua_len=254.0, fa_len=241.0,
    ua_far=180.0,                   # far ring 180..205: inside the 203 mm fold-side length, clear of the armpit
    fa_far=200.0,                   # wrist ring 200..225: ~16 mm short of the wrist so it bends freely
    open_deg=130.0,                 # far rings' arm opening, centred anterior (+Y)
    pipe_angles=(225, 270, 315),    # deg from lateral +X toward anterior +Y: three on the back
    lug_w=26.0, lug_t=8.0, hub_r=30.0,
    elbow_half=50.0,                # elbow_width/2 + padding + air: nothing inside this
    edge_fillet=2.0,
    bearing=(30.0, 42.0, 7.0),      # 6806-2RS: bore, OD, width
    rom=(0, 135),
    # forearm door: the front halves of both forearm rings + a 5th pipe; hinged at the wrist ring,
    # pinned shut at the elbow ring. Each joint is a fork and tongue at the ring's side (y = 0):
    # two full-height cheeks on the ring (inner and outer skin) around a slot, the door band's
    # end is the tongue, one 5 mm pin through all three (M5 shoulder bolt / 5 mm quick-release).
    door=True, fa_far_open=180.0, kerf=0.5, door_rom=(0, 100),
    fork_cheek=3.5, fork_slot=5.5, fork_r=10.0, fork_len=20.0, pin_d=5.0,
    # Soft-tissue safety: at full flexion the front of the forearm near the elbow presses on the
    # biceps, so no hard part may sit there. The door keeps only its wrist end (a hinged front
    # clasp, locked by a 3 mm pin through each fork); the elbow end is left for a soft strap.
    door_elbow=False, lock_pin_d=3.0, lock_pin_r=6.5,
    # wrist cuff: barrel hinges along the forearm at both sides of the wrist ring
    cuff_knuckle_r=6.0, cuff_pin_d=4.0,
    # Flexion hard stop: a block on each upper-arm hub catches the forearm shell's leading edge.
    # stop_gap_deg trims where contact happens (the lead estimate is conservative by a few deg);
    # measured: -3.5 touches at 134, +2 at 140, so -2 puts first contact just past 135
    ua_hub_r=44.0, stop_r=(31.0, 40.0), stop_span=20.0, stop_gap_deg=-2.0,
)

UA_COLOR, FA_COLOR, HW_COLOR, BRG_COLOR, GHOST = '#647684', '#8fa3b3', '#c9d2d9', '#d4a017', '#e8c9a8'


def band_out(d):
    return d / 2 + P['band_t']


def fillet_vertical(p, body, r):
    """Round every vertical straight edge: C-band ends, boss and pad junctions."""
    edges = []
    for e in body.edges:
        g = e.geometry
        if isinstance(g, adsk.core.Line3D):
            a, b = g.startPoint, g.endPoint
            if abs(a.x - b.x) < 1e-6 and abs(a.y - b.y) < 1e-6:
                edges.append(e)
    if not edges:
        return body
    ff = p.comp.features.filletFeatures
    try:
        fi = ff.createInput()
        try:
            fi.edgeSetInputs.addConstantRadiusEdgeSet(fx.coll(edges), fx.VI.createByReal(r / 10.0), True)
        except AttributeError:
            fi.addConstantRadiusEdgeSet(fx.coll(edges), fx.VI.createByReal(r / 10.0), True)
        ff.add(fi)
    except Exception:
        pass  # rounding is cosmetic; keep the part
    return body


SHELL_OPEN = 150.0   # the elbow shells leave the front open: 15..165 deg


def pipe_lines(d_near, d_far, z_near, z_far, angles):
    """Straight pipe axes from the near ring (bore d_near) to the far ring (bore d_far).
    With a smaller far bore the pipes lean inward; each ring's hole is drilled along the pipe's
    own line, so a straight pipe slides through both. The lean shifts a hole by h/2*tan(lean) at
    the ring faces, so both radii grow by that much to keep the wall to the bore."""
    base = lambda d: d / 2 + P['wall'] + P['pipe_od'] / 2
    lean = math.atan2(abs(base(d_near) - base(d_far)), abs(z_far - z_near))
    extra = P['ring_h'] / 2 * math.tan(lean)
    rn, rf = base(d_near) + extra, base(d_far) + extra
    lines = []
    for a in angles:
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        lines.append(([rn * c, rn * s, z_near], [rf * c, rf * s, z_far]))
    return lines, lean


def point_at(line, z):
    a, b = line
    t = (z - a[2]) / (b[2] - a[2])
    return fx.add(a, fx.mul(fx.sub(b, a), t))


def along(line):
    """A cylinder frame (ex, ey, ez) with ez along the pipe."""
    ez = fx.unit(fx.sub(line[1], line[0]))
    ex = fx.unit(fx.cross(ez, [0, 0, 1])) if abs(ez[2]) < 0.999999 else [1.0, 0.0, 0.0]
    return ex, fx.cross(ez, ex), ez


def ring(p, d, zc, lines, flange=None, open_deg=None):
    """Thin C-band + pipe bosses (+ a posterior flange the elbow shell stands on), holes cut
    along each pipe's line."""
    h = P['ring_h']
    open_deg = open_deg or P['open_deg']
    body = p.cring('z', [0, 0, zc], d / 2, band_out(d), h, 90, open_deg, name='band')
    parts = list(body)
    for line in lines:
        c = point_at(line, zc)
        ez = along(line)[2]
        tilt = math.hypot(ez[0], ez[1]) / abs(ez[2])
        parts += p.cyl('z', c, P['pipe_od'] / 2 + P['wall'] + h / 2 * tilt, h, name='pipe boss')
    if flange:
        parts += p.cring('z', [0, 0, zc], flange[0], flange[1], h, 90, open_deg, name='shell flange')
    body = p.join(parts)[0]
    # round the edges BEFORE drilling: a fillet added afterwards can put a fin back into a
    # leaning hole where it runs close to the arm-side edge
    body = fillet_vertical(p, body, P['edge_fillet'])
    return drill(p, body, lines, zc)


def drill(p, body, lines, zc):
    """Pipe holes along each pipe's own line through the ring at height zc. The cutter overshoots
    each face by 3 mm: with only 1 mm a leaning hole left a 0.04 mm skin at the face."""
    holes = []
    for line in lines:
        ez = along(line)[2]
        holes += p.cyl(along(line), point_at(line, zc), (P['pipe_od'] + P['pipe_clear']) / 2,
                       P['ring_h'] / abs(ez[2]) + 6)
    return p.cut([body], holes)[0]


def pipe(p, line, z0, z1, name='PVC pipe 21.5/15.5'):
    a, b = point_at(line, z0), point_at(line, z1)
    body = p.ann(along(line), fx.mul(fx.add(a, b), 0.5), P['pipe_od'] / 2, P['pipe_id'] / 2, fx.norm(fx.sub(b, a)))[0]
    body.name = name
    return body


def unit(parent, name, d, sign, far, color, flange, far_open=None, d_far=None):
    """flange: (r0, r1) of the near ring's posterior flange, matching the elbow shell.
    d_far: a smaller far-ring bore (the wrist); the pipes then lean inward."""
    p = Part(parent, name, color=color)
    h = P['ring_h']
    zn, zf = sign * (P['ring_off'] + h / 2), sign * (far + h / 2)
    lines, lean = pipe_lines(d, d_far or d, zn, zf, P['pipe_angles'])
    near = ring(p, d, zn, lines, flange, P['near_open'])
    far_ring = ring(p, d_far or d, zf, lines, open_deg=far_open)
    near.name, far_ring.name = 'near ring (print flat)', 'far ring (print flat)'
    # a leaning pipe's square-cut end dips by r*tan(lean) on one side: start it that much higher
    # so the end rests on the shell edge instead of cutting into it
    dip = P['pipe_od'] / 2 * math.tan(lean) + (0.1 if lean else 0)
    for line in lines:
        pipe(p, line, sign * (P['ring_off'] + dip), sign * (far + h))
    p.lean = lean
    p.lines, p.ring_z = lines, (zn, zf)
    return p


def redrill(p):
    """Last step for a unit: drill every pipe hole again through both rings, so nothing joined
    or rounded after the rings were made (shell, hubs, knuckles, fillets) can sit in a hole."""
    zn, zf = p.ring_z
    for key, zc in (('near ring', zn), ('far ring', zf)):
        body = next(b for b in p.comp.bRepBodies if key in b.name)
        name = body.name
        drill(p, body, p.lines, zc).name = name
    return p


def fork_x(d):
    """x-ranges at the ring's side (y = 0), where the band's thickness runs along X:
    the tongue is the door band itself; the slot is a little wider; a cheek either side."""
    b0, b1 = d / 2, band_out(d)
    c, half = (b0 + b1) / 2, P['fork_slot'] / 2
    slot = (c - half, c + half)
    inner = (slot[0] - P['fork_cheek'], slot[0])
    outer = (slot[1], slot[1] + P['fork_cheek'])
    return (b0, b1), slot, inner, outer


def fork_plates(p, xr, zr, za, ys):
    """Full-height plate between |x| = xr, from the joint along y = ys, rounded around the pin."""
    out = []
    for s in (1, -1):
        a, b = sorted([s * xr[0], s * xr[1]])
        out += p.join(p.box(a, b, ys[0], ys[1], zr[0], zr[1])
                      + p.cyl('x', [(a + b) / 2, 0, za], P['fork_r'], b - a, name='fork'))
    return out


def around_pin(p, body, xr, za, r, grow=0.0):
    """Cut a cylinder about the pin axis over |x| = xr on both sides."""
    tools = [t for s in (1, -1) for t in
             p.cyl('x', [s * (xr[0] + xr[1]) / 2, 0, za], r, xr[1] - xr[0] + grow)]
    return p.cut([body], tools)[0]


def door(g, fa, d, sign, far, d_far=None):
    """Forearm door: the front halves of both forearm rings + an anterior PVC pipe.
    At each ring side a fork and tongue: the ring end carries two full-height cheeks around a
    local slot, the door band's end slides in as the tongue, one pin through all three.
    The wrist pins sit on the wrist ring's distal face, so the whole door lies on the elbow
    side of that axis and swings outward; at the elbow ring the pins are removable latches."""
    h, kerf = P['ring_h'], P['kerf']
    L, R, pin = P['fork_len'], P['fork_r'], P['pin_d']
    centres = {'elbow': sign * (P['ring_off'] + h / 2), 'wrist': sign * (far + h / 2)}
    axes = {'elbow': centres['elbow'], 'wrist': sign * (far + h)}
    bores = {'elbow': d, 'wrist': d_far or d}
    (line,), _ = pipe_lines(d, d_far or d, centres['elbow'], centres['wrist'], (90,))
    ez = along(line)[2]
    tilt = math.hypot(ez[0], ez[1]) / abs(ez[2])
    dp = Part(g, 'Forearm door (print flat)' if P['door_elbow'] else 'Wrist clasp (print flat)', color=FA_COLOR)
    keys = ('elbow', 'wrist') if P['door_elbow'] else ('wrist',)
    for key in keys:
        zc = centres[key]
        za, zr, db = axes[key], (zc - h / 2, zc + h / 2), bores[key]
        tongue, slot, inner, outer = fork_x(db)
        kerf_deg = math.degrees(kerf / (db / 2 + P['band_t'] / 2))
        pc = point_at(line, zc)
        # door: front-half arc (+ pipe boss) + tongues; clear the cheeks' swing; pin hole
        arc = dp.cring('z', [0, 0, zc], db / 2, band_out(db), h, 270, 180 + 2 * kerf_deg, name='door arc')
        extra = dp.cyl('z', pc, P['pipe_od'] / 2 + P['wall'] + h / 2 * tilt, h) if P['door_elbow'] else []
        body = dp.join(arc + extra + fork_plates(dp, tongue, zr, za, (0, L)))[0]
        if P['door_elbow']:
            body = dp.cut([body], dp.cyl(along(line), pc, (P['pipe_od'] + P['pipe_clear']) / 2, h / abs(ez[2]) + 2))[0]
        for xr in (inner, outer):
            body = around_pin(dp, body, xr, za, R + 0.5, 0.5)
        body = around_pin(dp, body, tongue, za, (pin + 0.2) / 2, 1)
        fillet_vertical(dp, body, P['edge_fillet'])
        body.name = f'door arc, {key} end (print flat)' if P['door_elbow'] else 'wrist clasp (print flat)'
        # ring: cheeks either side, local slot where the tongue sits and turns, pin hole
        ring_body = next(b for b in fa.comp.bRepBodies if ('near ring' if key == 'elbow' else 'far ring') in b.name)
        # a solid block behind the pin ties both cheeks to the band (the wrist ring has no flange);
        # it starts beyond the tongue's circle, so it never meets the door
        bridge = [b for s in (1, -1) for b in
                  fa.box(*sorted([s * inner[0], s * outer[1]]), -L, -(R + 1), zr[0], zr[1])]
        ring_body = fa.join([ring_body] + bridge + fork_plates(fa, inner, zr, za, (-L, 0))
                            + fork_plates(fa, outer, zr, za, (-L, 0)))[0]   # bridge first: it connects the cheeks
        ring_body = around_pin(fa, ring_body, slot, za, R + 0.5)
        ring_body = around_pin(fa, ring_body, (inner[0], outer[1]), za, (pin + 0.2) / 2, 1)
        if not P['door_elbow']:
            # lock pin: through cheek, tongue, cheek, inside the ring height, off the pivot;
            # in place it stops the clasp turning, pulled out the clasp swings open
            zl = za - sign * P['lock_pin_r']
            lock = lambda part, xr: [t for s in (1, -1) for t in
                                     part.cyl('x', [s * (xr[0] + xr[1]) / 2, 0, zl], (P['lock_pin_d'] + 0.2) / 2, xr[1] - xr[0] + 1)]
            fa.cut([ring_body], lock(fa, (inner[0], outer[1])))
            dp.cut([body], lock(dp, tongue))
        for s in (1, -1):
            p = dp.cyl('x', [s * (inner[0] + outer[1]) / 2, 0, za], pin / 2, outer[1] - inner[0])[0]
            p.name = 'hinge pin M5 shoulder bolt (buy)' if key == 'wrist' else 'latch pin 5 mm quick-release (buy)'
            p.appearance = fx.appearance(HW_COLOR)
    if P['door_elbow']:
        pipe(dp, line, sign * P['ring_off'], sign * (far + h), 'PVC pipe 21.5/15.5 (door)')
    return dp, 0.0, axes['wrist']


def forward_sign(motion, body, occ, deg):
    """+1 if a positive joint rotation moves body forward (+Y), else -1.
    Bounding boxes can be stale inside a script; the measure manager is not. Distance from the
    body to a point far in front of the arm shrinks when the body moves forward."""
    mm = adsk.core.Application.get().measureManager
    target = adsk.core.Point3D.create(0, 200.0, 0)   # 2 m in front (cm); every variant sits well behind it
    # measure in root context: find this component's occurrence path from the root
    top = next(o for o in fx.design.rootComponent.allOccurrences if o.component == occ.component)
    proxy = body.createForAssemblyContext(top)

    def dist():
        adsk.doEvents()
        return mm.measureMinimumDistance(proxy, target).value
    d0 = dist()
    motion.rotationValue = math.radians(deg)
    if abs(math.degrees(motion.rotationValue) - deg) > 0.5:
        raise RuntimeError('joint does not move; check grounding')
    d1 = dist()
    if abs(d1 - d0) < 0.05:
        raise RuntimeError('could not see the part move; direction unknown')
    return 1 if d1 < d0 else -1


def wrist_cuff(g, fa, d, sign, far):
    """Wrist cuff: the wrist ring's front half swings open sideways like a bracelet.
    Both ends are barrel hinges along the forearm: three interleaved knuckles (ring, cuff, ring)
    on a vertical pin. The inner (medial, -X) one is the hinge; on the outer (+X) one the pin is
    a 4 mm quick-release: pull it and the cuff swings open around the medial pin."""
    h, kerf, kr, gz = P['ring_h'], P['kerf'], P['cuff_knuckle_r'], 0.4
    zc = sign * (far + h / 2)
    z0, z1 = zc - h / 2, zc + h / 2
    xk = band_out(d) + kr - 2                       # barrel overlaps the band by 2 mm
    third = (h - 2 * gz) / 3
    ring_z = [(z0, z0 + third), (z1 - third, z1)]
    cuff_z = [(z0 + third + gz, z1 - third - gz)]
    kerf_deg = math.degrees(kerf / (d / 2 + P['band_t'] / 2))

    def barrels(p, zs, r, grow=0.0):
        return [b for s in (1, -1) for a, c in zs for b in
                p.cyl('z', [s * xk, 0, (a + c) / 2], r, c - a + grow, name='knuckle')]

    cp = Part(g, 'Wrist cuff (print flat)', color=FA_COLOR)
    arc = cp.cring('z', [0, 0, zc], d / 2, band_out(d), h, 270, 180 + 2 * kerf_deg, name='cuff arc')
    body = cp.join(arc + barrels(cp, cuff_z, kr))[0]
    body = cp.cut([body], barrels(cp, ring_z, kr + 0.5, 0.8))[0]            # room for the ring's knuckles
    body = cp.cut([body], barrels(cp, [(z0 - 1, z1 + 1)], (P['cuff_pin_d'] + 0.2) / 2))[0]
    fillet_vertical(cp, body, P['edge_fillet'])
    body.name = 'wrist cuff (print flat)'

    ring = next(b for b in fa.comp.bRepBodies if 'far ring' in b.name)
    ring = fa.join([ring] + barrels(fa, ring_z, kr))[0]
    ring = fa.cut([ring], barrels(fa, cuff_z, kr + 0.5, 0.8))[0]               # room for the cuff's knuckle
    fa.cut([ring], barrels(fa, [(z0 - 1, z1 + 1)], (P['cuff_pin_d'] + 0.2) / 2))

    pin = cp.cyl('z', [-xk, 0, zc], P['cuff_pin_d'] / 2, h)[0]
    pin.name = 'hinge pin 4 mm (buy); the +X side takes a 4 mm quick-release pin'
    pin.appearance = fx.appearance(HW_COLOR)
    cp.hinge = ([-xk, 0.0, zc], 'z')                 # medial barrel: the cuff opens about this
    return cp


def door_hinge(g, dp, fa, yh=None, zw=None):
    dp.occ.isGroundToParent = False
    sk = g.sketches.add(g.xYConstructionPlane)
    sk.isVisible = False
    if hasattr(dp, 'hinge'):                      # wrist cuff: barrel hinge along the forearm
        (hx, hy, hz), axis = dp.hinge
    else:                                         # door: pins across the arm
        (hx, hy, hz), axis = (0.0, yh, zw), 'x'
    pt = sk.sketchPoints.add(adsk.core.Point3D.create(hx / 10, hy / 10, hz / 10))
    ji = g.asBuiltJoints.createInput(dp.occ, fa.occ, adsk.fusion.JointGeometry.createByPoint(pt))
    ji.setAsRevoluteJointMotion({'x': adsk.fusion.JointDirections.XAxisJointDirection,
                                 'z': adsk.fusion.JointDirections.ZAxisJointDirection}[axis])
    j = g.asBuiltJoints.add(ji)
    j.name = 'forearm door'
    motion = adsk.fusion.RevoluteJointMotion.cast(j.jointMotion)

    arc = next(b for b in dp.comp.bRepBodies if b.name.startswith(('door arc', 'wrist clasp', 'wrist cuff')))
    sign = forward_sign(motion, arc, dp.occ, 30)   # opening swings it outward (+Y), away from the arm
    motion.rotationValue = 0
    lo, hi = sorted(sign * math.radians(a) for a in P['door_rom'])
    lim = motion.rotationLimits
    lim.isMinimumValueEnabled, lim.minimumValue = True, lo
    lim.isMaximumValueEnabled, lim.maximumValue = True, hi
    return j, sign


UA_SHELL_OPEN = 180.0  # the upper-arm shell stops at the sides: anything further forward sits in
                       # the forearm shell's layer and gets swept by it near full flexion


def shell(p, r0, r1, z0, z1, open_deg=SHELL_OPEN):
    """Elbow shell: a cylindrical sector around the arm, open at the front."""
    return p.cring('z', [0, 0, (z0 + z1) / 2], r0, r1, abs(z1 - z0), 90, open_deg, name='elbow shell')


def hub_disc(p, s, x0, x1, r=None):
    return p.cyl('x', [s * (x0 + x1) / 2, 0, 0], r or P['hub_r'], x1 - x0, name='hub')


def flexion_stops(p, fx0, fx1, ux0):
    """Hard stop at full flexion: a block on each upper-arm hub, reaching into the forearm hub's
    layer. The forearm shell's leading edge (the front of its side strip) swings round and meets
    the block's face at rom[1]. Angles phi are measured like flexion: phi = 0 points down the
    straight forearm (-Z), phi = 90 points forward (+Y), phi = 180 up the upper arm."""
    r0, r1 = P['stop_r']
    # how far ahead of the forearm axis the strip's leading edge sits at the block's inner radius
    edge = math.radians(90 - SHELL_OPEN / 2)
    y_lead = max(min(x * math.tan(edge), math.sqrt(max(fx1 ** 2 - x ** 2, 0)))
                 for x in [fx0 + k * (fx1 - fx0) / 40 for k in range(41)])
    lead = math.degrees(math.asin(min(1.0, y_lead / r0)))
    phi0 = P['rom'][1] + lead + P['stop_gap_deg']
    alpha_c = phi0 + P['stop_span'] / 2 - 90          # cring measures from +Y toward +Z
    return [b for s in (1, -1) for b in
            p.cring('x', [s * (fx0 + 0.5 + ux0) / 2, 0, 0], r0, r1, ux0 - fx0 - 0.5,
                    alpha_c - 180, 360 - P['stop_span'], name='flexion stop')]


def cut_axis(p, body, d, xa, xb, r_extra=0.0):
    a, b = sorted([xa, xb])
    return p.cut([body], p.cyl('x', [(a + b) / 2, 0, 0], d / 2 + r_extra, b - a))[0]


def variant(parent, key, offset):
    """Two-sided 6806 joint. Each unit's near ring, elbow shell and hubs are one printed part
    (ring face down, shell rising, hubs on top); the forearm shell's posterior ledge meets the
    upper-arm shell at full extension: a hard stop against hyperextension."""
    bore, od, w = P['bearing']
    e, off, gap = P['elbow_half'], P['ring_off'], 0.5
    fx0 = max(e, band_out(P['fa_d']))           # forearm shell / hub, radially inside
    fx1 = fx0 + P['lug_t']
    ux0 = max(fx1 + gap, band_out(P['ua_d']))   # upper-arm shell / hub, radially outside
    ux1 = ux0 + w + 3                           # housing: bearing + 3 mm retaining lip
    g = fx.group(parent, f'{key} - two-sided 6806, elbow shells', t=offset)
    fa = unit(g, 'Forearm unit', P['fa_d'], -1, P['fa_far'], FA_COLOR, (band_out(P['fa_d']) - 1, fx1),
              P['fa_far_open'] if P['door'] else None, P['wrist_d'])
    ua = unit(g, 'Upper-arm unit', P['ua_d'], 1, P['ua_far'], UA_COLOR, (band_out(P['ua_d']) - 1, ux1))
    hw = Part(g, 'Hardware (6806 bearings, covers)', color=HW_COLOR)

    # forearm: near ring + shell + hubs + hyperextension ledge, one part
    near = next(b for b in fa.comp.bRepBodies if b.name.startswith('near ring'))
    parts = [near] + shell(fa, fx0, fx1, -off, -gap)
    parts += [b for s in (1, -1) for b in hub_disc(fa, s, fx0, fx1)]
    # hyperextension ledge: full width at the top (the stop face), then 2 mm steps inward going down,
    # a 45 deg staircase so it prints without support when the part stands ring-down
    top, step = -0.75, 2.0
    r_out = ux1 - 1
    while r_out > fx1 + 0.5:
        parts += fa.cring('z', [0, 0, top - step / 2], fx1 - 0.5, r_out, step, 90, 270, name='stop ledge')
        top, r_out = top - step, r_out - step
    fbody = fa.join(parts)[0]
    for s in (1, -1):
        fbody = cut_axis(fa, fbody, 8.4, s * (fx0 - 1), s * (fx1 + 1))
    fbody = fillet_vertical(fa, fbody, P['edge_fillet'])
    fbody.name = 'forearm: near ring + elbow shell + hubs (print ring down)'

    # upper arm: near ring + shell + bearing housings, one part; clearance where the forearm hub turns
    near = next(b for b in ua.comp.bRepBodies if b.name.startswith('near ring'))
    parts = [near] + shell(ua, ux0, ux1, gap, off, UA_SHELL_OPEN)
    parts += [b for s in (1, -1) for b in hub_disc(ua, s, ux0, ux1, P['ua_hub_r'])]
    parts += flexion_stops(ua, fx0, fx1, ux0)
    ubody = ua.join(parts)[0]
    for s in (1, -1):
        ubody = cut_axis(ua, ubody, 2 * P['hub_r'], s * (fx0 - gap), s * (fx1 + gap), r_extra=0.5)
        ubody = cut_axis(ua, ubody, od + 0.05, s * (ux0 - 1), s * (ux0 + w + 0.1))          # bearing pocket
        ubody = cut_axis(ua, ubody, od - 6, s * (ux0 + w + 0.1), s * (ux1 + 1))             # retaining lip
    ubody = fillet_vertical(ua, ubody, P['edge_fillet'])
    ubody.name = 'upper arm: near ring + elbow shell + bearing housings (print ring down)'

    for s in (1, -1):
        # axle through the bearing: separate flat-printed part on the forearm hub, clamped by the M8
        ax = fa.cyl('x', [s * (fx1 + (w + gap) / 2), 0, 0], bore / 2, w + gap)[0]
        cut_axis(fa, ax, 8.4, s * fx1, s * (fx1 + w + gap + 1)).name = 'bearing axle (print flat, M8 through)'
        b = hw.ann('x', [s * (ux0 + w / 2), 0, 0], od / 2, bore / 2, w, name='6806-2RS')[0]
        b.name = '6806-2RS bearing (buy)'
        b.appearance = fx.appearance(BRG_COLOR)
        cover = hw.cyl('x', [s * (ux1 + 1.5), 0, 0], P['hub_r'], 3)[0]
        pcd = [(25 * math.cos(math.radians(k * 60)), 25 * math.sin(math.radians(k * 60))) for k in range(6)]
        tools = [t for y, z in pcd for t in hw.cyl('x', [s * (ux1 + 1.5), y, z], 1.7, 5)]
        tools += hw.cyl('x', [s * (ux1 + 1.5), 0, 0], 4.2, 5)
        hw.cut([cover], tools)[0].name = 'cover (print flat)'
    for part in (ua, fa):
        a = fx.appearance(UA_COLOR if part is ua else FA_COLOR)
        for b in part.comp.bRepBodies:
            b.appearance = a
    dp = None
    if P['door'] and not P['door_elbow']:
        dp = wrist_cuff(g, fa, P['wrist_d'], -1, P['fa_far'])
        dp.door_axis = ()
    elif P['door']:
        dp, yh, zw = door(g, fa, P['fa_d'], -1, P['fa_far'], P['wrist_d'])
        dp.door_axis = (yh, zw)
    for part in (ua, fa):
        redrill(part)
    # arm stand-ins at the real size (bore minus the ~10 mm padding): used for the soft-tissue check
    tissue = {'ua': (P['ua_d'] - P['padding']) / 2, 'fa': (P['fa_d'] - P['padding']) / 2}
    for part, sign, r, L in ((ua, 1, tissue['ua'], P['ua_len']), (fa, -1, tissue['fa'], P['fa_len'])):
        gb = part.cyl('z', [0, 0, sign * L / 2], r, L, name='arm ghost')[0]
        gb.name = 'arm ghost'
        gb.appearance = fx.appearance(GHOST)
        gb.opacity = 0.3
    return g, ua, fa, hw, dp


def hinge(g, ua, fa):
    ua.occ.isGroundToParent = True
    fa.occ.isGroundToParent = False  # new occurrences can come in grounded; the forearm must be free
    sk = g.sketches.add(g.xYConstructionPlane)
    sk.isVisible = False
    pt = sk.sketchPoints.add(adsk.core.Point3D.create(0, 0, 0))
    ji = g.asBuiltJoints.createInput(fa.occ, ua.occ, adsk.fusion.JointGeometry.createByPoint(pt))  # first one moves
    ji.setAsRevoluteJointMotion(adsk.fusion.JointDirections.XAxisJointDirection)
    j = g.asBuiltJoints.add(ji)
    j.name = 'elbow flexion'
    motion = adsk.fusion.RevoluteJointMotion.cast(j.jointMotion)

    wrist = next(b for b in fa.comp.bRepBodies if 'far ring' in b.name)   # moves the most
    sign = forward_sign(motion, wrist, fa.occ, 30)
    motion.rotationValue = 0
    lo, hi = sorted(sign * math.radians(a) for a in P['rom'])
    lim = motion.rotationLimits
    lim.isMinimumValueEnabled, lim.minimumValue = True, lo
    lim.isMaximumValueEnabled, lim.maximumValue = True, hi
    return j, sign


def flex(joint, sign, deg):
    adsk.fusion.RevoluteJointMotion.cast(joint.jointMotion).rotationValue = sign * math.radians(deg)


def solids(parts):
    items = adsk.core.ObjectCollection.create()
    for o in parts:
        for b in o.comp.bRepBodies:
            if b.name != 'arm ghost':
                items.add(b.createForAssemblyContext(o.occ))
    return items


def owner(e):
    return e.assemblyContext.component if e.assemblyContext else e.parentComponent


def sweep(design, parts, joint, sign, rom, step=15):
    """Interference between parts that should never touch while joint runs through rom.
    Bearing/spigot/housing and pin fits are line-to-line by design; ignored below 5 mm3."""
    rows = []
    for deg in range(rom[0], rom[1] + 1, step):
        flex(joint, sign, deg)
        actual = abs(math.degrees(adsk.fusion.RevoluteJointMotion.cast(joint.jointMotion).rotationValue))
        if abs(actual - deg) > 0.5:
            raise RuntimeError(f'{joint.name} at {actual:.1f} deg, asked for {deg}')
        ii = design.createInterferenceInput(solids(parts))
        ii.areCoincidentFacesIncluded = False
        res = design.analyzeInterference(ii)
        pairs = []
        for i in range(res.count):
            r = res.item(i)
            v = round(r.interferenceBody.volume * 1000)
            if owner(r.entityOne) != owner(r.entityTwo) and v >= 5:
                pairs.append((v, r.entityOne.name, r.entityTwo.name))
        rows.append((deg, pairs))
    return rows


def medial_extent(parts):
    """How far the device reaches toward the body (-X), measured from the arm axis."""
    lo = 0.0
    for o in parts:
        for b in o.comp.bRepBodies:
            if b.name != 'arm ghost':
                lo = min(lo, b.createForAssemblyContext(o.occ).boundingBox.minPoint.x * 10)
    return -lo


def coupons(parent):
    """Quick fit tests before the long prints. Holes / pockets increase left to right;
    the number of dots beside each one gives its order (1 = smallest)."""
    g = fx.group(parent, 'Fit coupons', t=[0, -400.0, 0])

    def dots(p, x, y, n, z):
        return [b for k in range(n) for b in p.cyl('z', [x + (k - (n - 1) / 2) * 4, y, z], 1.0, 1.2)]

    p = Part(g, 'Pipe hole coupon', color=UA_COLOR)
    plate = p.box(-56, 56, -18, 18, 0, 10)[0]
    sizes = (21.7, 21.9, 22.1, 22.3)
    tools = []
    for k, dia in enumerate(sizes):
        x = -42 + k * 28
        tools += p.cyl('z', [x, -2, 5], dia / 2, 12) + dots(p, x, 14, k + 1, 9.6)
    p.cut([plate], tools)[0].name = 'pipe hole coupon 21.7 / 21.9 / 22.1 / 22.3'

    bore, od, w = P['bearing']
    p = Part(g, 'Bearing pocket coupon', color=UA_COLOR)
    plate = p.box(-78, 78, -30, 30, 0, 10)[0]
    sizes = (od - 0.1, od + 0.05, od + 0.2)
    tools = []
    for k, dia in enumerate(sizes):
        x = -52 + k * 52
        tools += p.cyl('z', [x, -3, 10 - (w + 0.1) / 2], dia / 2, w + 0.1)      # pocket from the top
        tools += p.cyl('z', [x, -3, 5], (od - 6) / 2, 12)                         # retaining lip, as on the part
        tools += dots(p, x, 26, k + 1, 9.6)
    p.cut([plate], tools)[0].name = 'bearing pocket coupon 41.9 / 42.05 / 42.2'


def export_stls(out_dir, include_door=True):
    """Elbow test-print set as binary STL (mm). Returns [(file, triangles, bbox mm)]."""
    import os
    os.makedirs(out_dir, exist_ok=True)
    d = fx.design
    root = d.rootComponent
    grp = next(o for o in root.occurrences if o.component.name.startswith('B - '))
    parts = {o.component.name: o for o in grp.childOccurrences}
    coup = next(o for o in root.occurrences if o.component.name == 'Fit coupons')
    coup_parts = {o.component.name: o for o in coup.childOccurrences}

    def body(occ, key):
        return next(b for b in occ.component.bRepBodies if key in b.name)
    wanted = [
        ('01_upper_arm_elbow_piece', body(parts['Upper-arm unit'], 'upper arm: near ring')),
        ('02_forearm_elbow_piece', body(parts['Forearm unit'], 'forearm: near ring')),
        ('03_bearing_axle_print2', body(parts['Forearm unit'], 'bearing axle')),
        ('04_bearing_cover_print2', body(parts['Hardware (6806 bearings, covers)'], 'cover')),
        ('00_fit_coupon_pipe_holes', body(coup_parts['Pipe hole coupon'], 'coupon')),
        ('00_fit_coupon_bearing_pockets', body(coup_parts['Bearing pocket coupon'], 'coupon')),
    ]
    if include_door:
        wanted.append(('05_door_elbow_end_optional', body(parts['Forearm door (print flat)'], 'door arc, elbow end')))
    em = d.exportManager
    out = []
    for name, b in wanted:
        f = os.path.join(out_dir, name + '.stl')
        opt = em.createSTLExportOptions(b, f)
        opt.isBinaryFormat = True
        opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        em.execute(opt)
        bb = b.boundingBox
        size = [round((bb.maxPoint.asArray()[i] - bb.minPoint.asArray()[i]) * 10, 1) for i in range(3)]
        out.append((os.path.basename(f), os.path.getsize(f), size))
    return out


def main(keys=('B',), new_document=False, pose=90, door_pose=0, remove=('A - ', 'B - ', 'B1 - ', 'C - ')):
    """Build, then check: elbow sweep with the door shut, and door sweep at elbow 0 and 90 deg."""
    if new_document:
        adsk.core.Application.get().documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    d = fx.init()
    root = d.rootComponent
    for o in list(root.occurrences):
        if o.component.name.startswith(remove):
            o.deleteMe()
    out, joints = [], []
    for i, k in enumerate(keys):
        g, ua, fa, hw, dp = variant(root, k, [0, i * 400.0, 0])
        j, sign = hinge(g, ua, fa)
        dj, dsign = door_hinge(g, dp, fa, *dp.door_axis) if dp else (None, 1)
        parts = [p for p in (ua, fa, hw, dp) if p]
        report = {'elbow (door shut)': sweep(d, parts, j, sign, P['rom']), 'medial': medial_extent((ua, fa, hw))}
        if dp:
            for elbow_deg in (0, 90):
                flex(j, sign, elbow_deg)
                report[f'door at elbow {elbow_deg}'] = sweep(d, parts, dj, dsign, P['door_rom'])
                flex(dj, dsign, 0)
        out.append((k, report))
        joints.append((j, sign, dj, dsign))
    for j, sign, dj, dsign in joints:
        flex(j, sign, pose)
        if dj:
            flex(dj, dsign, door_pose)
    fx.snapshot()
    return out
