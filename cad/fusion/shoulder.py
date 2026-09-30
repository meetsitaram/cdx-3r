"""CDX-3R shoulder + back system on the exoarm2 body scan (Fusion).

World frame = the scan layout (exoarm2-scan/tools/layout.py): mm, X forward, Y up, Z right,
floor at Y = 0.  Everything lives in one top component rotated so scan-Y is Fusion-Z.

Stage 1 (frame): PVC backbone (2 pipes, hip belt to load-lifter stays), upper beam and
diagonal to the abduction mount block, printed top / mid / bottom nodes with pipe sockets
and webbing slots, mount block with the abduction bearing housing (2 x 6806).
Reference: scanned torso, posed right arm, printable shoulder rest (mesh bodies).
"""
import json
import math
import os

import adsk.core
import adsk.fusion

import fxlib as fx
from fxlib import Part, NEW, JOIN, CUT, add, sub, mul, unit, cross, dot, norm

SCAN = r'C:\Users\PC\projects\exoarm2-scan\out'
LAY = json.load(open(os.path.join(SCAN, 'layout', 'layout.json')))
D = LAY['derived']
GH = LAY['landmarks']['GH']
MID_Z = LAY['landmarks']['MID_Z']

S = dict(
    pipe_od=21.5, pipe_bore=21.9, socket_depth=30.0, boss_wall=6.0,
    node_socket_depth=25.0,
    # bought hardware (mm)
    m8=dict(clear=8.5, shcs_head=(13.0, 8.0), low_head=(13.0, 5.0), low_cbore=(14.5, 5.5), nut_af=13.0, nut_h=8.0,
            fender=(30.0, 8.4, 1.5), cbore=(14.5, 8.5)),                 # fender washer: OD, ID, t
    ring_land=33.0,                                        # 6806 inner-ring land: bosses/washers stay <= this
    flex_bearing=(40.0, 52.0, 7.0), flex_ring_land=43.0,   # shoulder flexion: 6808-2RS (40 x 52 x 7), bigger than
                                                           # the elbow's 6806: the shoulder carries the whole arm
    pipe_screw=dict(hole=3.2, len=12.0),                   # #4 x 3/8" (2.9 x 9.5) pan-head self-tapping into the PVC
    m3=dict(clear=3.4, cbore=6.5, under_head=4.0, head=(5.5, 3.0), screw_len=8.0,    # M3 x 8 into inserts; cbore also
            insert=(4.0, 7.0), insert_len=5.7),       # takes the #4 pipe screw's Ø5.6 head. ruthex RX-M3 x 5.7                                # top/mid node sockets: keeps those nodes < 250 mm
    node_depth=36.0, node_h=(64.0, 36.0, 40.0),          # bottom, mid, top
    # webbing anchors (tabs with a slot the strap loops through; buckles / ladder locks live on the straps)
    tab_t=10.0, tab_len=30.0, tab_edge=4.0, tab_flare=10.0,   # tabs: 10 thick, base 2 x 10 mm wider than the slot end
    # Bambu P1S bed is 256 mm: the bottom node (376 mm) prints as two halves + a splice plate on its back face
    splice=dict(t=6.0, flange=5.0, half_w=50.0, holes=((-16.0, 30.0), (16.0, 30.0)),   # (dy, dz from MID_Z)
                flange_holes=(30.0,),                                                 # dz of the top/bottom M4s
                m4_clear=3.4, m4_insert=(4.0, 7.0), cb=2.0),   # M3 x 8 into ruthex 5.7 (Ø4 x 7 holes; names kept)
    shoulder_tab=dict(w=36.0, slot=(26.0, 5.0)),          # 25 mm webbing: shoulder straps, top and bottom ends
    waist_tab=dict(w=52.0, slot=(40.0, 5.0)),             # 38 mm webbing: waist strap
    bearing=(30.0, 42.0, 7.0), bearing_clear=0.1,          # 6806-2RS
    housing_r=40.0, housing_len=25.0,
    block=(44.0, 150.0, 80.0),                             # X, Y, Z
    yoke_t=24.0,                                           # yoke band radial thickness
    yoke_gap=1.0,                                          # yoke root face to housing face
)
HWLOG = []
FRAME, HW, PRINT, REF = '#5b6770', '#c9d2d9', '#647684', '#e8c9a8'
TOP = 'CDX-3R shoulder + back'


def derived():
    """Frame points in the world frame, with the housing moved behind the yoke root."""
    yoke_root_x = GH[0] - D['yoke_ra']                     # yoke band centre on the abduction axis
    h1 = yoke_root_x - S['yoke_t'] / 2 - S['yoke_gap']     # housing front face
    h0 = h1 - S['housing_len']
    bx = h0 - S['block'][0] / 2                            # block centre X
    return dict(yoke_root_x=yoke_root_x, h0=h0, h1=h1, block=[bx, GH[1], GH[2]])


def top_component():
    root = fx.design.rootComponent
    for o in list(root.occurrences):
        if o.component.name == TOP:
            o.deleteMe()
    occ = root.occurrences.addNewComponent(fx.matrix(fx.rot('x', 90)))
    occ.component.name = TOP
    fx.snapshot()
    occ.isGroundToParent = True
    return occ.component


def reference(parent):
    comp = fx.group(parent, 'Reference (scan)')
    bf = comp.features.baseFeatures.add()
    bf.startEdit()
    for name, f, col in (('torso (hips to neck, no left arm)', 'layout/body_torso_trim.stl', REF), ('right arm to wrist (rest pose)', 'layout/body_arm_trim.stl', REF)):
        mb = comp.meshBodies.add(os.path.join(SCAN, f), adsk.fusion.MeshUnits.MillimeterMeshUnit, bf).item(0)
        mb.name = name
        mb.appearance = fx.appearance(col)
    bf.finishEdit()
    return comp


def frame_of(d):
    """(ex, ey, ez) with ez along d."""
    ez = unit(d)
    a = [1, 0, 0] if abs(ez[0]) < 0.9 else [0, 1, 0]
    ex = unit(cross(a, ez))
    return ex, cross(ez, ex), ez


def circle(r):
    return lambda sk, to: sk.sketchCurves.sketchCircles.addByCenterRadius(to(0, 0), r / 10.0)


def rect(u0, u1, v0, v1):
    return lambda sk, to: sk.sketchCurves.sketchLines.addTwoPointRectangle(to(u0, v0), to(u1, v1))


def clear_start(d, gap=2.0):
    """Distance along d (from a backbone axis, which is vertical) at which a pipe of the same OD clears it."""
    u = unit(d)
    sin_a = math.sqrt(max(1e-9, 1 - u[1] ** 2))
    return (S['pipe_od'] + gap) / sin_a


def socket_boss(p, start, d, t0, t1, body, bore_from=None, depth=None):
    """Boss Ø(bore + 2 wall) along d from start (t0..t1), joined to body, then a blind
    pipe socket from the boss end back to bore_from (default t1 - depth)."""
    fr = frame_of(d)
    ro = S['pipe_bore'] / 2 + S['boss_wall']
    p.prism(start, fr, t0, t1, circle(ro), name='socket boss', op=JOIN, targets=[body])
    b0 = bore_from if bore_from is not None else t1 - (depth or S['socket_depth'])
    p.prism(start, fr, b0, t1 + 1, circle(S['pipe_bore'] / 2), name='pipe socket', op=CUT, targets=[body])
    pipe_screws(p, body, start, d, (t1 - 7, t1 - 20), [-1, 0, 0], S['boss_wall'])
    return add(start, mul(unit(d), b0))                     # socket bottom = pipe end


def strap_tab(p, body, root, d, spec, name, base_max=None):
    """Flat tab in the frame's YZ plane (thickness along X), from root (y, z) along d, with a webbing slot.
    The base flares tab_flare wider each side and tapers to the slot end: the strap load spreads into the node."""
    xf, t, L = D['xf'], S['tab_t'], S['tab_len']
    n = (-d[1], d[0]); w = spec['w'] / 2
    wb = w + S['tab_flare'] if base_max is None else min(w + S['tab_flare'], base_max)
    pt = lambda a, b: (root[0] + d[0] * a + n[0] * b, root[1] + d[1] * a + n[1] * b)
    def poly(pts):
        def draw(sk, to):
            ln = sk.sketchCurves.sketchLines
            q = [to(*c) for c in pts]
            for i in range(len(q)):
                ln.addByTwoPoints(q[i], q[(i + 1) % len(q)])
        return draw
    taper = L - S['tab_edge'] - spec['slot'][1] - 4         # full width from just below the slot
    p.prism([xf, 0, 0], fx.AX['x'], -t / 2, t / 2,
            poly([pt(0, -wb), pt(taper, -w), pt(L, -w), pt(L, w), pt(taper, w), pt(0, wb)]),
            name=name, op=JOIN, targets=[body])
    sl, sw = spec['slot']
    c = L - S['tab_edge'] - sw / 2
    p.prism([xf, 0, 0], fx.AX['x'], -t, t, poly([pt(c - sw / 2, -sl / 2), pt(c + sw / 2, -sl / 2),
                                                 pt(c + sw / 2, sl / 2), pt(c - sw / 2, sl / 2)]),
            name=name + ' slot', op=CUT, targets=[body])


def merge_all(p, sliver=0.05):
    """Join every body of the part into the largest (drop slivers): robust against stale body references."""
    bodies_ = sorted(p.comp.bRepBodies, key=lambda b: -b.volume)
    for b in bodies_[1:]:
        if b.volume < sliver:
            p.comp.features.removeFeatures.add(b)
    main_ = bodies_[0]
    rest = [b for b in p.comp.bRepBodies if b != main_]
    if rest:
        cf = p.comp.features.combineFeatures
        ci = cf.createInput(main_, fx.coll(rest))
        ci.operation = JOIN; ci.isKeepToolBodies = False
        cf.add(ci)
    return p.comp.bRepBodies.item(0)


def hexagon(af):
    r = af / math.sqrt(3)                                  # circumradius of a hex with across-flats af
    def draw(sk, to):
        ln = sk.sketchCurves.sketchLines
        q = [to(r * math.cos(math.radians(30 + 60 * i)), r * math.sin(math.radians(30 + 60 * i))) for i in range(6)]
        for i in range(6):
            ln.addByTwoPoints(q[i], q[(i + 1) % 6])
    return draw


def pipe_screws(p, body, start, d, ts, out_dir, wall):
    """Radial self-tapping screw holes into a PVC pipe along axis start + t*d, one per t, on the side
    out_dir (made square to the pipe), from inside the pipe wall out through the boss."""
    d = unit(d)
    o = unit(sub(out_dir, mul(d, dot(out_dir, d))))
    r0 = S['pipe_od'] / 2 - 1
    seat = S['pipe_od'] / 2 + S['m3']['under_head']              # head seat, from the pipe axis
    for t in ts:
        c = add(add(start, mul(d, t)), mul(o, r0))
        p.prism(c, frame_of(o), 0, wall + 2, circle(S['pipe_screw']['hole'] / 2), name='pipe screw hole', op=CUT,
                targets=[body])
        if r0 + wall > seat - r0 + r0:                        # thick wall: sink the head so M3 x 8 reaches the pipe
            p.prism(c, frame_of(o), seat - r0, wall + 8, circle(S['m3']['cbore'] / 2), name='pipe screw counterbore',
                    op=CUT, targets=[body])


def hw_bearing(p, c, frame, name='6806-2RS (buy)', brg=None):
    bi, bo, bw = brg or S['bearing']
    b = p.ann(frame, c, bo / 2, bi / 2, bw, name=name)[0]
    b.name = name
    return b


def hw_bolt(p, c_head, frame, length, head, name, dia=8.0):
    """Bolt along frame's ez: head from c_head backwards (-ez), shank (dia) from c_head forwards (+ez)."""
    hd, hh = head
    b = p.prism(c_head, frame, -hh, 0, circle(hd / 2), name=name).bodies.item(0)
    p.prism(c_head, frame, 0, length, circle(dia / 2), name=name + ' shank', op=JOIN, targets=[b])
    b.name = name
    return b


def hw_nut(p, c, frame, name='M8 nyloc nut (buy)'):
    b = p.prism(c, frame, 0, S['m8']['nut_h'], hexagon(S['m8']['nut_af']), name=name).bodies.item(0)
    p.prism(c, frame, -1, S['m8']['nut_h'] + 1, circle(4.0), name='thread', op=CUT, targets=[b])
    b.name = name
    return b


def hw_washer(p, c, frame, od, idia, t, name):
    b = p.ann(frame, add(c, mul(unit(frame[2]), t / 2)), od / 2, idia / 2, t, name=name)[0]
    b.name = name
    return b


def node(parent, name, y, h, z_lo, z_hi):
    p = Part(parent, name, color=PRINT)
    xf, dx = D['xf'], S['node_depth'] / 2
    body = p.box(xf - dx, xf + dx, y - h / 2, y + h / 2, z_lo, z_hi, name='block')[0]
    return p, body


def midplane(comp):
    """Construction plane on the body midline (Z = MID_Z): the mirror plane for left/right symmetry."""
    ci = comp.constructionPlanes.createInput()
    ci.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByString('%.4f mm' % MID_Z))
    pl = comp.constructionPlanes.add(ci)
    pl.name = 'body midline (mirror)'
    pl.isLightBulbOn = False
    return pl


def mirror_bodies(p, bodies, combine, name):
    """Associative Fusion mirror across the midline: editing the right-side features updates the left."""
    mf = p.comp.features.mirrorFeatures
    mi = mf.createInput(fx.coll(bodies), midplane(p.comp))
    try:
        mi.isCombine = combine
    except Exception:
        pass
    f = mf.add(mi)
    f.name = name
    return f


def _concave_small_cylinder(f, r_max):
    """A hole / socket / bearing pocket: a cylindrical face (r < r_max mm) whose normal points at its axis."""
    g = f.geometry
    if not isinstance(g, adsk.core.Cylinder) or g.radius * 10 >= r_max:
        return False
    pt = f.pointOnFace
    ok, nrm = f.evaluator.getNormalAtPoint(pt)
    if not ok:
        return True
    a = g.axis; a.normalize()
    v = g.origin.vectorTo(pt)
    radial = v.copy(); t = a.copy(); t.scaleBy(v.dotProduct(a)); radial.subtract(t)
    return nrm.dotProduct(radial) < 0


def round_edges(p, body, r=2.0, r_hole=30.0, seam_z=None, min_len=3.0):
    """Round every sharp edge except hole / socket / pocket edges (fits stay exact) and the mirror seam."""
    cb = _cb()
    edges = []
    for e in body.edges:
        if e.length * 10 < min_len or not cb.is_sharp(e):
            continue
        if any(_concave_small_cylinder(f, r_hole) for f in e.faces):
            continue
        if seam_z is not None:
            a, b = e.startVertex.geometry, e.endVertex.geometry
            if abs(a.z * 10 - seam_z) < 0.05 and abs(b.z * 10 - seam_z) < 0.05:
                continue
        edges.append(e)
    return cb._fillet(p, edges, r)


def build_frame(parent):
    """Right halves only; every left side is a Fusion mirror feature of the right."""
    g = derived()
    xf, zb = D['xf'], D['zb']
    zr = zb[1]                                               # right backbone pipe
    y_bot, y_mid, y_top, y_stay = D['y_bot'], D['y_mid'], D['y_top'], D['y_stay']
    hb, hm, ht = S['node_h']
    bore = S['pipe_bore'] / 2
    frame = fx.group(parent, 'Frame')
    parts = {}
    blk = g['block']; bx0 = blk[0]
    zin = blk[2] - S['block'][2] / 2                         # block medial face
    diag = ([xf, y_mid, zr], [bx0, GH[1] - 50, zin])
    beam = ([xf, y_top, zr], [bx0, GH[1] + 50, zin])

    # ---- bottom node: backbone socket, shoulder-strap (bottom) + waist-strap anchors ----
    p, body = node(frame, 'Bottom node', y_bot, hb, MID_Z, MID_Z + 160)
    top_y = y_bot + hb / 2
    p.prism([xf, top_y, zr], fx.AX['y'], -S['socket_depth'], 1, circle(bore), name='backbone socket',
            op=CUT, targets=[body])
    pipe_screws(p, body, [xf, top_y, zr], [0, -1, 0], (8, 20), [-1, 0, 0], S['node_depth'] / 2)
    strap_tab(p, body, (top_y - 2, MID_Z + 115), (1, 0), S['shoulder_tab'], 'shoulder strap anchor (bottom)')
    strap_tab(p, body, (y_bot, MID_Z + 158), (0, 1), S['waist_tab'], 'waist strap anchor', base_max=hb / 2)
    sp = S['splice']
    xb_face = xf - S['node_depth'] / 2                       # back face (away from the body)
    for dy, dz in sp['holes']:
        p.prism([0, y_bot + dy, MID_Z + dz], fx.AX['x'], xb_face - 1, xb_face + sp['m4_insert'][1],
                circle(sp['m4_insert'][0] / 2), name='M4 insert (splice)', op=CUT, targets=[body])
    for dz in sp['flange_holes']:                        # into the top and bottom faces, for the channel flanges
        for ys, sgn in ((y_bot + hb / 2, -1), (y_bot - hb / 2, 1)):
            p.prism([xf, ys, MID_Z + dz], fx.AX['y'], min(0, sgn * sp['m4_insert'][1]) - 1 * (sgn > 0),
                    max(0, sgn * sp['m4_insert'][1]) + 1 * (sgn < 0),
                    circle(sp['m4_insert'][0] / 2), name='M4 insert (splice flange)', op=CUT, targets=[body])
    body.name = 'Bottom node R'
    round_edges(p, p.comp.bRepBodies.item(0), seam_z=MID_Z)
    mf = mirror_bodies(p, [p.comp.bRepBodies.item(0)], False, 'mirror to left (printed as 2 halves)')
    mf.bodies.item(0).name = 'Bottom node L'
    parts['bottom'] = p
    q = Part(frame, 'Bottom node splice plate', color=PRINT)
    fl = sp['flange']
    x_front = xf + S['node_depth'] / 2                      # the node's body-side face: the channel stops there
    yt, yb_ = y_bot + hb / 2, y_bot - hb / 2
    def channel(sk, to):                                    # U section in (X, Y): back web + top + bottom flanges
        pts = [(xb_face - sp['t'], yb_ - fl), (x_front, yb_ - fl), (x_front, yb_), (xb_face, yb_), (xb_face, yt),
               (x_front, yt), (x_front, yt + fl), (xb_face - sp['t'], yt + fl)]
        ln = sk.sketchCurves.sketchLines
        q_ = [to(a_, b_) for a_, b_ in pts]
        for i in range(len(q_)):
            ln.addByTwoPoints(q_[i], q_[(i + 1) % len(q_)])
    pb = q.prism([0, 0, 0], fx.AX['z'], MID_Z, MID_Z + sp['half_w'], channel, name='channel').bodies.item(0)
    cbd = S['m3']['cbore']
    for dy, dz in sp['holes']:
        q.prism([0, y_bot + dy, MID_Z + dz], fx.AX['x'], xb_face - sp['t'] - 1, xb_face + 1,
                circle(sp['m4_clear'] / 2), name='M3 clearance', op=CUT, targets=[pb])
        q.prism([0, y_bot + dy, MID_Z + dz], fx.AX['x'], xb_face - sp['t'] - 1, xb_face - sp['t'] + sp['cb'],
                circle(cbd / 2), name='M3 head counterbore', op=CUT, targets=[pb])
    for dz in sp['flange_holes']:
        q.prism([xf, 0, MID_Z + dz], fx.AX['y'], yb_ - fl - 1, yt + fl + 1, circle(sp['m4_clear'] / 2),
                name='M3 clearance (flanges)', op=CUT, targets=[pb])
        for y0, y1 in ((yb_ - fl - 1, yb_ - fl + sp['cb']), (yt + fl - sp['cb'], yt + fl + 1)):
            q.prism([xf, 0, MID_Z + dz], fx.AX['y'], y0, y1, circle(cbd / 2), name='M3 head counterbore', op=CUT,
                    targets=[pb])
    round_edges(q, q.comp.bRepBodies.item(0), r=1.5, seam_z=MID_Z)
    mirror_bodies(q, [q.comp.bRepBodies.item(0)], True, 'mirror to left')
    parts['splice'] = q
    hw = Part(frame, 'HW frame (buy)', color='#b0b6bb')
    L4 = S['m3']['screw_len']
    for dy, dz in sp['holes']:
        for sz in (1, -1):
            zz = MID_Z + sz * dz
            hw_bolt(hw, [xb_face - sp['t'] + sp['cb'], y_bot + dy, zz], fx.AX['x'], L4, S['m3']['head'],
                    'M3 x 8 socket head (buy)', dia=3.0)
            ins = hw.ann(fx.AX['x'], [xb_face + 2.85, y_bot + dy, zz], 2.0, 1.5, 5.7, name='M3 insert')[0]
            ins.name = 'M3 heat-set insert ruthex 5.7 (buy)'
    for dz in sp['flange_holes']:
        for sz in (1, -1):
            zz = MID_Z + sz * dz
            for ys, fr, sg in ((yt + fl - sp['cb'], ([1, 0, 0], [0, 0, 1], [0, -1, 0]), 1),
                               (yb_ - fl + sp['cb'], fx.AX['y'], -1)):
                hw_bolt(hw, [xf, ys, zz], fr, L4, S['m3']['head'], 'M3 x 8 socket head (buy)', dia=3.0)
                c_ins = [xf, (yt - 2.85) if sg > 0 else (yb_ + 2.85), zz]
                ins = hw.ann(fx.AX['y'], c_ins, 2.0, 1.5, 5.7, name='M3 insert')[0]
                ins.name = 'M3 heat-set insert ruthex 5.7 (buy)'
    HWLOG.append(('splice M3 x 8 (back)', L4, 'web %.0f - %.0f counterbore = %.0f plastic, %.0f into the insert'
                  % (sp['t'], sp['cb'], sp['t'] - sp['cb'], L4 - sp['t'] + sp['cb'])))
    HWLOG.append(('splice M3 x 8 (flanges)', L4, 'flange %.0f - %.0f = %.0f plastic, %.0f into the insert'
                  % (fl, sp['cb'], fl - sp['cb'], L4 - fl + sp['cb'])))
    pipe_lo = top_y - S['socket_depth']

    # ---- mid node: backbone through, diagonal socket ----
    p, body = node(frame, 'Mid node', y_mid, hm, MID_Z, MID_Z + 90)
    tb = clear_start(sub(diag[1], diag[0]))
    diag_p0 = socket_boss(p, diag[0], sub(diag[1], diag[0]), 8, tb + S['node_socket_depth'], body, depth=S['node_socket_depth'])
    p.prism([xf, y_mid, zr], fx.AX['y'], -hm, hm, circle(bore), name='backbone bore', op=CUT, targets=[body])
    pipe_screws(p, body, [xf, y_mid, zr], [0, 1, 0], (0,), [-1, 0, 0], S['node_depth'] / 2)
    round_edges(p, p.comp.bRepBodies.item(0), seam_z=MID_Z)
    mirror_bodies(p, [p.comp.bRepBodies.item(0)], True, 'mirror to left')
    parts['mid'] = p

    # ---- top node: backbone through (stays continue up), upper-beam socket, shoulder-strap (top) anchor ----
    p, body = node(frame, 'Top node', y_top, ht, MID_Z, MID_Z + 90)
    tb = clear_start(sub(beam[1], beam[0]))
    beam_p0 = socket_boss(p, beam[0], sub(beam[1], beam[0]), 8, tb + S['node_socket_depth'], body, depth=S['node_socket_depth'])
    p.prism([xf, y_top, zr], fx.AX['y'], -ht, ht, circle(bore), name='backbone bore', op=CUT, targets=[body])
    pipe_screws(p, body, [xf, y_top, zr], [0, 1, 0], (0,), [-1, 0, 0], S['node_depth'] / 2)
    strap_tab(p, body, (y_top + ht / 2 - 2, MID_Z + 30), (1, 0), S['shoulder_tab'], 'shoulder strap anchor (top)')
    round_edges(p, p.comp.bRepBodies.item(0), seam_z=MID_Z)
    mirror_bodies(p, [p.comp.bRepBodies.item(0)], True, 'mirror to left')
    parts['top'] = p

    # ---- abduction mount block + bearing housing (axis X through GH); left = mirror ----
    p = Part(frame, 'Abduction mount blocks', color=PRINT)
    bx, by, bz = S['block']
    body = p.box(bx0 - bx / 2, bx0 + bx / 2, blk[1] - by / 2, blk[1] + by / 2, blk[2] - bz / 2, blk[2] + bz / 2,
                 name='block')[0]
    ax_c = [0, GH[1], GH[2]]
    bi, bo, bwid = S['bearing']
    p.prism(ax_c, fx.AX['x'], g['h0'], g['h1'], circle(S['housing_r']), name='housing', op=JOIN, targets=[body])
    p.prism(ax_c, fx.AX['x'], bx0 - bx / 2 - 1, g['h1'] + 1, circle(bi / 2 + 2), name='axle bore', op=CUT, targets=[body])
    for x0, x1 in ((g['h1'] - bwid, g['h1'] + 1), (bx0 - bx / 2 - 1, bx0 - bx / 2 + bwid)):
        p.prism(ax_c, fx.AX['x'], x0, x1, circle(bo / 2 + S['bearing_clear']), name='bearing pocket', op=CUT,
                targets=[body])
    ends = {}
    for key, (a, b) in (('beam', beam), ('diag', diag)):   # pipe sockets into the block's medial face
        d = unit(sub(b, a))
        ends[key] = add(b, mul(d, S['socket_depth'] - 2))
        p.prism(b, frame_of(d), -15, S['socket_depth'], circle(bore), name='pipe socket', op=CUT, targets=[body])  # starts
        pipe_screws(p, body, b, d, (8, 20), [-1, 0, 0], 12)
        # in the air: the pipe meets the face at an angle, its rim reaches the block before the socket axis does
    round_edges(p, p.comp.bRepBodies.item(0))
    p.comp.bRepBodies.item(0).name = 'Abduction mount block R'
    mf = mirror_bodies(p, [p.comp.bRepBodies.item(0)], False, 'mirror to left')
    mf.bodies.item(0).name = 'Abduction mount block L'
    parts['block'] = p

    # ---- PVC pipes (buy): right side modelled, left mirrored ----
    pp = Part(frame, 'PVC pipes 21.5/15.5 (buy)', color='#e9eef2')
    cut, right = [], []
    a, b = [xf, pipe_lo, zr], [xf, y_top + ht / 2 - 1, zr]          # ends 1 mm under the top node's top face (no stays)
    right += pp.pipe([a, b], S['pipe_od'] / 2, name='backbone'); cut.append(('backbone', norm(sub(b, a))))
    for key, a in (('beam', beam_p0), ('diag', diag_p0)):
        right += pp.pipe([a, ends[key]], S['pipe_od'] / 2, name=key); cut.append((key, norm(sub(ends[key], a))))
    mirror_bodies(pp, right, False, 'mirror to left')
    cut = [(k + ' x2', v) for k, v in cut]
    for q in parts.values():
        q.finish()
    pp.finish()
    return parts, cut, g


def main():
    fx.init()
    top = top_component()
    reference(top)
    parts, cut, g = build_frame(top)
    return dict(cut_list_mm=[(k, round(v, 1)) for k, v in cut], housing=(round(g['h0'], 1), round(g['h1'], 1)),
                block=[round(v, 1) for v in g['block']])


# ---------------------------------------------------------------- stage 2: moving side
S.update(dict(
    rest_abd=LAY['params']['rest_abd'],
    yoke_h=36.0,                                           # yoke band height (Y)
    root_r=28.0, flex_housing_r=44.0,                     # = the elbow hub (r 44): matching outer rings
    flex_housing_inner=(31.0, 10.0),                      # arm-side step: r34 for 10 mm (fork clears the deltoid)
    brace=dict(pipe=270.0, at=0.55, over=0.0, height=160.0, skin=2.0),   # brace wall: band grown up to the link
    axle_flange=(50.0, 5.0), m3_pcd=40.0, m3_insert=(4.0, 5.5), m3_clear=3.4,
    link_t=18.0, link_w=50.0, link_gap=2.0,                # link outer plate: 50 x 18 section
    hub_spokes=(5, 23.5, 38.0, 16.0),                       # flexion hub: n spokes, window r in/out, spoke deg
    link_hub_r=44.0, inner_top=31.0,   # = the round inner plate: gusset sides run tangent into it
    link_end_r=25.0, inner_t=8.0, inner_gap=5.0, y_sag=6.0,   # hub r = housing r: one clean cylinder   # fork: inner plate + bridge below the housing
    boss=(33.0, 2.0),                                      # plate bosses clamp the 6806 inner rings
    head_h=35.0, head_cap=3.0, head_band_extra=5.0, web=40.0,   # pipe head is part of the link: blind 32 mm sockets
    pad_r=17.0, m4_clear=4.5, m4_pitch=16.0,              # link foot: 2 x M4 into a lug on the far ring
))


def arm_frame(u):
    lat = [0, 0, 1]
    e = unit(sub(lat, mul(u, dot(lat, u))))
    n = cross(u, e)
    if n[0] < 0: n = mul(n, -1)
    return e, n


def foot_point():
    """Link foot = the upper-arm pipe head's lug (scan frame, before rest abduction)."""
    return head_geometry()['o_scan'], D['u']


def m3_ring(p, centre, frame, z0, z1, body, d, count=3, r=None, name='M3'):
    r = r or S['m3_pcd'] / 2
    for i in range(count):
        a = math.radians(90 + 360.0 * i / count)
        p.prism(centre, frame, z0, z1, (lambda sk, to, a=a: sk.sketchCurves.sketchCircles.addByCenterRadius(
            to(r * math.cos(a), r * math.sin(a)), d / 20.0)), name=name, op=CUT, targets=[body])


def build_moving(parent, g):
    ra, rl = D['yoke_ra'], D['yoke_rl']
    t, hy = S['yoke_t'], S['yoke_h']
    bi, bo, bwid = S['bearing']
    R = fx.rot('x', -S['rest_abd'])                        # abduction: swings the arm outboard
    tr = sub(GH, fx.mat_vec(R, GH))
    abd = fx.group(parent, 'Abduction side (rest %g deg)' % S['rest_abd'], R, tr)
    out = {}

    # ---- yoke: flat elliptical band at GH height, root on the abduction axis, tip = flexion housing ----
    p = Part(abd, 'Yoke', color=PRINT)
    def band(sk, to):
        spl = sk.sketchCurves.sketchFittedSplines
        arcs = []
        for k in (+1, -1):
            pts = [to(GH[0] + (ra + k * t / 2) * math.cos(th), GH[2] + (rl + k * t / 2) * math.sin(th))
                   for th in [math.radians(180 - 90 * i / 24) for i in range(25)]]
            arcs.append(spl.add(fx.coll(pts)))
        ln = sk.sketchCurves.sketchLines
        ln.addByTwoPoints(arcs[0].startSketchPoint, arcs[1].startSketchPoint)
        ln.addByTwoPoints(arcs[0].endSketchPoint, arcs[1].endSketchPoint)
    body = p.prism([0, GH[1], 0], fx.AX['y'], -hy / 2, hy / 2, band, name='band').bodies.item(0)
    ax_c = [0, GH[1], GH[2]]
    x0, x1 = g['yoke_root_x'] - t / 2, g['yoke_root_x'] + t / 2
    p.prism(ax_c, fx.AX['x'], x0, x1, circle(S['root_r']), name='root boss', op=JOIN, targets=[body])
    # abduction hinge = same as flexion: sleeve through both 6806, M8 through-bolt; the yoke root's boss
    # presses the front bearing's inner ring, a fender washer + nyloc the rear one
    h1 = g['h1']
    p.prism(ax_c, fx.AX['x'], h1, x0, circle(S['ring_land'] / 2), name='inner-ring boss', op=JOIN, targets=[body])
    p.prism(ax_c, fx.AX['x'], h1 - 1, x1 + 1, circle(S['m8']['clear'] / 2), name='M8 bore', op=CUT, targets=[body])
    cbd, cbh = S['m8']['cbore']
    p.prism(ax_c, fx.AX['x'], x1 - cbh, x1 + 1, circle(cbd / 2), name='M8 head counterbore', op=CUT, targets=[body])
    fz0 = D['flex_hub_face_z']; fz1 = fz0 + LAY['params']['flex_hub_w']
    fl_c = [GH[0], GH[1], 0]
    r_in_h, step_h = S['flex_housing_inner']               # stepped: r34 on the arm side, r44 (elbow size) outside
    p.prism(fl_c, fx.AX['z'], fz0, fz1, circle(r_in_h), name='flexion housing (arm side)', op=JOIN, targets=[body])
    p.prism(fl_c, fx.AX['z'], fz0 + step_h, fz1, circle(S['flex_housing_r']), name='flexion housing (outer ring)',
            op=JOIN, targets=[body])
    fbi, fbo, fbw = S['flex_bearing']
    p.prism(fl_c, fx.AX['z'], fz0 - 1, fz1 + 1, circle(fbi / 2 + 2), name='flexion bore', op=CUT, targets=[body])
    for z0, z1 in ((fz0 - 1, fz0 + fbw), (fz1 - fbw, fz1 + 1)):
        p.prism(fl_c, fx.AX['z'], z0, z1, circle(fbo / 2 + S['bearing_clear']), name='bearing pocket', op=CUT,
                targets=[body])
    round_edges(p, p.comp.bRepBodies.item(0))
    out['yoke'] = p

    # ---- abduction sleeve (printed): through both bearings, clamped yoke boss <-> rear washer ----
    rear = g['h0'] - S['block'][0]                         # block rear face = rear bearing's outer face
    p = Part(abd, 'Abduction sleeve', color=HW)
    sb_ = p.prism(ax_c, fx.AX['x'], rear, h1, circle(bi / 2), name='sleeve').bodies.item(0)
    p.prism(ax_c, fx.AX['x'], rear - 1, h1 + 1, circle(S['m8']['clear'] / 2), name='bore', op=CUT, targets=[sb_])
    out['abd_sleeve'] = p
    # ---- bought hardware, abduction hinge ----
    hw = Part(abd, 'HW abd (buy)', color='#b0b6bb')
    xr = (-1, 0, 0)
    fx_neg = ([0, 1, 0], [0, 0, 1], [-1, 0, 0])            # ez = -X (bolt runs from the front to the back)
    hw_bearing(hw, [h1 - bwid / 2, GH[1], GH[2]], fx.AX['x'], '6806-2RS front (buy)')
    hw_bearing(hw, [rear + bwid / 2, GH[1], GH[2]], fx.AX['x'], '6806-2RS rear (buy)')
    fo, fi, ftk = S['m8']['fender']
    hw_washer(hw, [rear, GH[1], GH[2]], fx_neg, fo, fi, ftk, 'M8 fender washer 30 OD (buy)')
    nut0 = rear - ftk
    hw_nut(hw, [nut0, GH[1], GH[2]], fx_neg)
    head_seat = x1 - cbh
    L_abd = head_seat - (nut0 - S['m8']['nut_h'] - 2)          # 2 threads past the nut
    L_abd = 5 * math.ceil(L_abd / 5)
    hw_bolt(hw, [head_seat, GH[1], GH[2]], fx_neg, L_abd, S['m8']['shcs_head'], 'M8 x %d socket head (buy)' % L_abd)
    out['hw_abd'] = hw
    HWLOG.append(('abduction M8 socket head', L_abd, 'stack %.1f + nut %.0f' % (head_seat - nut0, S['m8']['nut_h'])))

    # ---- upper-arm link: plate outboard of the flexion housing, axle printed upright, pipe clamp ----
    # ---- upper-arm link + pipe head, ONE printed part: the UA pipes run straight into it ----
    cb = _cb(); CP = cb.P
    u = D['u']; e, n = arm_frame(u)
    EL = LAY['landmarks']['EL']
    hh, cap = S['head_h'], S['head_cap']
    z_top = CP['ua_pipe_top'] + cap
    zc = z_top - hh / 2                                    # head centre along the arm (concept Z)
    hc = add(EL, mul(u, zc))
    af = (e, n, u)                                        # arm frame: angles from lateral toward anterior
    d = CP['ua_d']; rp = d / 2 + CP['wall'] + CP['pipe_od'] / 2
    z0 = fz1 + S['link_gap']; z1 = z0 + S['link_t']
    zi1 = fz0 - S['inner_gap']; zi0 = zi1 - S['inner_t']       # inner plate: clear of the yoke band
    lat = add(hc, mul(e, cb.band_out(d)))                 # head's outer lateral point
    ey = unit([u[0], u[1], 0]); ex = [-ey[1], ey[0], 0]    # in the link plane: along the arm / across it
    w = S['link_w'] / 2
    def quad(a2, b2, half):
        def draw(sk, to):
            q = [add(a2, mul(ex, half)), add(b2, mul(ex, half)), add(b2, mul(ex, -half)), add(a2, mul(ex, -half))]
            ln = sk.sketchCurves.sketchLines
            pts = [to(v[0], v[1]) for v in q]
            for i in range(4):
                ln.addByTwoPoints(pts[i], pts[(i + 1) % 4])
        return draw
    hub2 = [GH[0], GH[1], 0]; lat2 = [lat[0], lat[1], 0]
    p = Part(abd, 'Upper-arm link', color=PRINT)
    # ONE smooth outline (crank-arm style): hub disc R_h at the hinge, round end r_e at the pipe head,
    # joined by the two external tangent lines. Plate, web, fork plate and Y wedge are all cut from it,
    # so every side is flush: no steps.
    R_h, r_e = S['link_hub_r'], S['link_end_r']
    dl = unit(sub(lat2, hub2))                            # down the link, in its plane
    def outline(sk, to):
        D_ = norm(sub(lat2, hub2)); beta = math.acos((R_h - r_e) / D_)
        ang = math.atan2(dl[1], dl[0])
        pt = lambda c, r, a: [c[0] + r * math.cos(a), c[1] + r * math.sin(a)]
        t1a, t1b = pt(hub2, R_h, ang + beta), pt(hub2, R_h, ang - beta)
        t2a, t2b = pt(lat2, r_e, ang + beta), pt(lat2, r_e, ang - beta)
        ln, ar = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
        P2 = lambda q: to(q[0], q[1])
        l1 = ln.addByTwoPoints(P2(t1a), P2(t2a)); l2 = ln.addByTwoPoints(P2(t1b), P2(t2b))
        ar.addByThreePoints(l1.startSketchPoint, P2(pt(hub2, R_h, ang + math.pi)), l2.startSketchPoint)
        ar.addByThreePoints(l1.endSketchPoint, P2(pt(lat2, r_e, ang)), l2.endSketchPoint)
    body = p.prism([0, 0, 0], fx.AX['z'], z0, z1, outline, name='link plate').bodies.item(0)
    lat_o = add(hc, mul(e, cb.band_out(d) + S['head_band_extra']))   # web: the plate's round end, extended
    p.prism([lat2[0], lat2[1], 0], fx.AX['z'], lat_o[2] - 4, z0, circle(r_e), name='web', op=JOIN,  # down 4 mm
            targets=[body])                                          # into the 10 mm head band (never the arm)
    head = p.cring(af, hc, d / 2, cb.band_out(d) + S['head_band_extra'], hh, HEAD['gap'][0], HEAD['gap'][1],
                   name='pipe head band')[0]
    body = p.join([body, head])[0]
    for a in CP['pipe_angles']:
        c = add(hc, add(mul(e, rp * math.cos(math.radians(a))), mul(n, rp * math.sin(math.radians(a)))))
        p.prism(c, af, -hh / 2, hh / 2, circle(rp - d / 2 - 0.5), name='pipe boss', op=JOIN,   # stops 0.5 mm
                targets=[body])                                                                  # short of the bore
    # fork: the same outline, kept only where wanted (intersect), so its sides are flush with the plate.
    # Inner plate beside the hub; Y wedge below the housing sweeping out into the plate (the yoke band comes
    # in from behind, so nothing below the housing meets it over flexion -20..120).
    r_b = S['flex_housing_inner'][0]                      # the slope starts where the round top ends (tangent line)
    sb = norm(sub(lat2, hub2)) + r_e + 1                  # the Y slope runs all the way to the link's end
    side = (dl, [0, 0, 1], cross(dl, [0, 0, 1]))          # side profile: (along the link, Z), extruded across
    def poly(pts):
        def draw(sk, to):
            q = [to(a_, b_) for a_, b_ in pts]
            ln = sk.sketchCurves.sketchLines
            for i in range(len(q)):
                ln.addByTwoPoints(q[i], q[(i + 1) % len(q)])
        return draw
    def y_curve(sk, to):
        # the Y's inner edge: an arc from the fork plate's corner to the link's end, bowed outward
        # (away from the arm) by y_sag so the middle clears the deltoid bulge
        a_, b_ = (r_b, zi0), (sb, z0 + 0.5)
        L_ = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
        nrm = (-(b_[1] - a_[1]) / L_, (b_[0] - a_[0]) / L_)          # points to +Z (outward)
        m_ = ((a_[0] + b_[0]) / 2 + nrm[0] * S['y_sag'], (a_[1] + b_[1]) / 2 + nrm[1] * S['y_sag'])
        pa, pb = to(*a_), to(*b_)
        ar = sk.sketchCurves.sketchArcs.addByThreePoints(pa, to(*m_), pb)
        # Fusion orders arc ends counter-clockwise, not as given: pick each end by position
        ends = [ar.startSketchPoint, ar.endSketchPoint]
        ea = min(ends, key=lambda q: q.geometry.distanceTo(pa)); eb = ends[1] if ea is ends[0] else ends[0]
        ln = sk.sketchCurves.sketchLines
        c1 = ln.addByTwoPoints(eb, to(sb, z1))
        c2 = ln.addByTwoPoints(c1.endSketchPoint, to(r_b, z1))
        ln.addByTwoPoints(c2.endSketchPoint, ea)
    cf = p.comp.features.combineFeatures
    for nm, pts in (('Y join', y_curve),):                                              # Y first: it touches the  # ends
                                                                                   # where the slope starts: no ledge
        half = S['inner_top']                              # fork (inner plate + Y) stays +-30 wide: clear of the
                                                           # yoke band and the deltoid; the outer plate keeps r44
        region = p.prism(hub2, side, -half, half, pts if callable(pts) else poly(pts), name=nm + ' region').bodies.item(0)
        tool = p.prism([0, 0, 0], fx.AX['z'], zi0, z1, outline, name=nm + ' outline').bodies.item(0)
        ci = cf.createInput(region, fx.coll([tool]))
        ci.operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
        ci.isKeepToolBodies = False
        piece = cf.add(ci).bodies.item(0)
        cj = cf.createInput(body, fx.coll([piece]))
        cj.operation = JOIN
        cj.isKeepToolBodies = False
        body = cf.add(cj).bodies.item(0)
    # brace wall: the pipe head's band continues upward between the rear pipe and the link, one solid curved
    # wall; its top is trimmed by a plane through the rear boss top and the link's back edge (the brace path)
    br = S['brace']
    ab = math.radians(br['pipe'])
    radb = add(mul(e, math.cos(ab)), mul(n, math.sin(ab)))
    p_boss = add(add(hc, mul(radb, rp)), mul(u, hh / 2))
    Dl = norm(sub(lat2, hub2)); sE = br['at'] * Dl
    half_s = R_h + (r_e - R_h) * sE / Dl
    back = cross(dl, [0, 0, 1])
    if back[0] > 0: back = mul(back, -1)
    p_edge = add(add(hub2, mul(dl, sE)), mul(back, 0.7 * half_s)); p_edge[2] = (z0 + z1) / 2
    a_lo, a_hi = br['pipe'] - 8, 360 + br['over']            # wall arc: rear pipe -> past lateral into the web
    span = a_hi - a_lo
    Hw = br['height']
    wc = add(hc, mul(u, Hw / 2 - hh / 2))                    # wall from the head's bottom up Hw (full overlap)
    wall = p.cring(af, wc, d / 2 + br['skin'], cb.band_out(d) + S['head_band_extra'], Hw,
                   (a_lo + a_hi) / 2 + 180, 360 - span, name='brace wall')[0]
    ac = math.radians(200.0)                                 # 3rd plane point: low, round the back
    p_low = add(add(hc, mul(add(mul(e, math.cos(ac)), mul(n, math.sin(ac))), rp)), mul(u, hh / 2))
    nz = unit(cross(sub(p_edge, p_boss), sub(p_low, p_boss)))
    if dot(nz, u) < 0: nz = mul(nz, -1)                      # normal points up the arm: cut that side
    ex_ = unit(sub(p_edge, p_boss)); ey_ = cross(nz, ex_)
    p.prism(p_boss, (ex_, ey_, nz), 0, 400, rect(-400, 400, -400, 400), name='brace trim', op=CUT, targets=[wall])
    # the trim can split the wall (a sliver + the wall): drop slivers, join every other piece
    bodies_ = sorted(p.comp.bRepBodies, key=lambda b: -b.volume)
    main_, rest = bodies_[0], [b for b in bodies_[1:]]
    for b in rest:
        if b.volume < 0.05:
            p.comp.features.removeFeatures.add(b)
    cf = p.comp.features.combineFeatures
    rest = [b for b in p.comp.bRepBodies if b != main_]
    if rest:
        ci = cf.createInput(main_, fx.coll(rest))
        ci.operation = JOIN; ci.isKeepToolBodies = False
        cf.add(ci)
    body = p.comp.bRepBodies.item(0)
    # fork inner plate: round on top (concentric with the housing's arm-side ring, same r34), square below:
    # a rectangle as wide as the circle runs straight down (tangent sides) into the Y's slope
    r_ip = S['flex_housing_inner'][0]
    p.prism(fl_c, fx.AX['z'], zi0, zi1, circle(r_ip), name='fork inner plate (round top)', op=JOIN,
            targets=[p.comp.bRepBodies.item(0)])
    p.prism([0, 0, 0], fx.AX['z'], zi0, zi1, quad(hub2, add(hub2, mul(dl, r_b + 1)), r_ip),
            name='fork inner plate (square bottom)', op=NEW)
    merge_all(p)
    # running clearance round the stepped housing (2 mm), cut before the bearing bosses go on
    r_in_h, step_h = S['flex_housing_inner']
    body = p.comp.bRepBodies.item(0)
    p.prism(fl_c, fx.AX['z'], zi1, fz0 + step_h - 2, circle(r_in_h + 2), name='housing clearance (arm side)', op=CUT,
            targets=[body])
    p.prism(fl_c, fx.AX['z'], fz0 + step_h - 2, z0, circle(S['flex_housing_r'] + 2), name='housing clearance (ring)',
            op=CUT, targets=[p.comp.bRepBodies.item(0)])
    body = p.comp.bRepBodies.item(0)
    bd = S['flex_ring_land']                              # bosses reach the 6808 inner rings
    p.prism(fl_c, fx.AX['z'], fz1, z0, circle(bd / 2), name='inner-ring boss (outer plate)', op=JOIN, targets=[body])
    p.prism(fl_c, fx.AX['z'], zi1, fz0, circle(bd / 2), name='inner-ring boss (inner plate)', op=JOIN, targets=[body])
    p.prism(fl_c, fx.AX['z'], zi0 - 1, z1 + 1, circle(S['m8']['clear'] / 2), name='M8 through-bolt', op=CUT,
            targets=[body])
    lcd, lch = S['m8']['cbore']                             # socket-head M8 sunk flush on the arm side
    p.prism(fl_c, fx.AX['z'], zi0 - 1, zi0 + lch, circle(lcd / 2), name='M8 low-head counterbore', op=CUT,
            targets=[body])

    # blind pipe sockets + 2 screws each (nothing reaches into the arm, so no bore cut is needed)
    for a in CP['pipe_angles']:
        c = add(hc, add(mul(e, rp * math.cos(math.radians(a))), mul(n, rp * math.sin(math.radians(a)))))
        p.prism(c, af, -hh / 2 - 1, hh / 2 - cap, circle((CP['pipe_od'] + CP['pipe_clear']) / 2), name='pipe socket',
                op=CUT, targets=[body])
        rad = add(mul(e, math.cos(math.radians(a))), mul(n, math.sin(math.radians(a))))
        for dz in (-8.0, 4.0):
            cc = add(add(c, mul(u, dz)), mul(rad, CP['pipe_od'] / 2 - 1))
            p.prism(cc, frame_of(rad), 0, CP['pipe_od'] / 2 + CP['wall'] + 3, circle(CP['pipe_screw_hole'] / 2),
                    name='pipe screw hole', op=CUT, targets=[body])
    round_edges(p, p.comp.bRepBodies.item(0))
    p.prism(fl_c, fx.AX['z'], z1 - S['m8']['nut_h'], z1 + 1, hexagon(S['m8']['nut_af'] + 0.3), name='captured nut',
            op=CUT, targets=[p.comp.bRepBodies.item(0)])   # after rounding: sharp pocket corners fit the nut
    n_sp, r_in, r_out, spoke = S['hub_spokes']             # spoked hub: curved windows between n spokes,
    win = 360.0 / n_sp - spoke                              # the bearing turns behind them
    for i in range(n_sp):
        a0 = math.radians(90 + spoke / 2 + 360.0 * i / n_sp); a1 = a0 + math.radians(win)
        def sector(sk, to, a0=a0, a1=a1):
            P_ = lambda r, a: to(r * math.cos(a), r * math.sin(a))
            arcs = sk.sketchCurves.sketchArcs; ln = sk.sketchCurves.sketchLines
            outer = arcs.addByThreePoints(P_(r_out, a0), P_(r_out, (a0 + a1) / 2), P_(r_out, a1))
            inner = arcs.addByThreePoints(P_(r_in, a0), P_(r_in, (a0 + a1) / 2), P_(r_in, a1))
            ends = lambda arc: [arc.startSketchPoint, arc.endSketchPoint]
            for po in ends(outer):                          # join each outer end to the nearest inner end
                pi = min(ends(inner), key=lambda q: q.geometry.distanceTo(po.geometry))
                ln.addByTwoPoints(po, pi)
        p.prism(fl_c, fx.AX['z'], z0 - 1, z1 + 1, sector, name='hub window', op=CUT,
                targets=[p.comp.bRepBodies.item(0)])
    cp = lat
    q = Part(abd, 'Flexion axle sleeve', color=HW)          # through both bearings, clamped by the plate bosses
    sb = q.prism(fl_c, fx.AX['z'], fz0, fz1, circle(S['flex_bearing'][0] / 2), name='sleeve').bodies.item(0)
    q.prism(fl_c, fx.AX['z'], fz0 - 1, fz1 + 1, circle(S['m8']['clear'] / 2), name='bore', op=CUT, targets=[sb])
    out['sleeve'] = q
    hw = Part(abd, 'HW flex (buy)', color='#b0b6bb')
    fbw = S['flex_bearing'][2]
    hw_bearing(hw, [GH[0], GH[1], fz0 + fbw / 2], fx.AX['z'], '6808-2RS inner (buy)', S['flex_bearing'])
    hw_bearing(hw, [GH[0], GH[1], fz1 - fbw / 2], fx.AX['z'], '6808-2RS outer (buy)', S['flex_bearing'])
    hw_nut(hw, [GH[0], GH[1], z1 - S['m8']['nut_h']], fx.AX['z'])
    seat = zi0 + S['m8']['cbore'][1]                           # head sunk flush in the inner plate
    L_fl = 5 * math.ceil((z1 + 1.5 - seat) / 5)                 # through the captured nut
    hw_bolt(hw, [GH[0], GH[1], seat], fx.AX['z'], L_fl, S['m8']['low_head'], 'M8 x %d socket head (buy)' % L_fl)
    out['hw_flex'] = hw
    HWLOG.append(('flexion M8 socket head', L_fl, 'grip %.1f, nut in a hex pocket in the outer plate' % (z1 - seat)))
    out['link'] = p

    for q in out.values():
        q.finish(None if '(buy)' in q.comp.name else q.comp.name)   # keep the hardware's own body names
    for q in out.values():                                   # bearings in gold: they show through the spokes
        for b in q.comp.bRepBodies:
            if '680' in b.name:
                b.appearance = fx.appearance('#d4a017')
    return out, cp


def ghost(comp, opacity=0.35):
    for o in fx.design.rootComponent.allOccurrences:
        if o.component.name == 'Reference (scan)':
            o.opacity = opacity


def main2():
    fx.init()
    root = fx.design.rootComponent
    top = next(o.component for o in root.occurrences if o.component.name == TOP)
    out, cp = build_moving(top, derived())
    ghost(top)
    return dict(foot=[round(v, 1) for v in cp])


def export_parts(out_dir):
    """One STL per part occurrence (world coordinates, mm), for the scan-side clearance checks."""
    os.makedirs(out_dir, exist_ok=True)
    em = fx.design.exportManager
    rows = []
    for o in fx.design.rootComponent.allOccurrences:
        c = o.component
        if c.bRepBodies.count == 0 or 'Reference' in o.fullPathName:
            continue
        f = os.path.join(out_dir, c.name.replace('/', '-').replace(' ', '_') + '.stl')
        opt = em.createSTLExportOptions(o, f)
        opt.isBinaryFormat = True
        opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
        em.execute(opt)
        rows.append((c.name, os.path.getsize(f)))
    return rows


def refresh_reference():
    """Re-import the scan reference meshes only (e.g. after trimming them)."""
    fx.init()
    top = next(o.component for o in fx.design.rootComponent.occurrences if o.component.name == TOP)
    comp = reference(top)
    return [(comp.meshBodies.item(i).name, comp.meshBodies.item(i).mesh.triangleCount) for i in range(comp.meshBodies.count)]


PRINT_ORIENT = {                                            # how each part goes on the P1S bed
    'Bottom node R': 'back face (the splice-plate side) down; tabs stand up, no supports except the socket',
    'Bottom node L': 'back face down, as R',
    'Bottom node splice plate': 'flat',
    'Mid node': 'back face down; support under the angled diagonal socket',
    'Top node': 'back face down; support under the angled beam socket',
    'Abduction mount block R': 'rear face down (bearing axis vertical: round pockets)',
    'Abduction mount block L': 'rear face down, as R',
    'Yoke': 'flexion-housing axis vertical (round bearing pockets); support the root boss',
    'Abduction sleeve': 'on end (bore vertical)',
    'Flexion axle sleeve': 'on end (bore vertical)',
    'Upper-arm link': 'outer plate flat on the bed; support the fork gap and the pipe head',
}


def export_print(out_dir):
    """One binary STL per printed body (world frame; orient in Bambu Studio per PRINT_ORIENT)."""
    os.makedirs(out_dir, exist_ok=True)
    em = fx.design.exportManager
    rows = []
    for o in fx.design.rootComponent.allOccurrences:
        c = o.component
        if 'Reference' in o.fullPathName or '(buy)' in c.name:
            continue
        for i in range(c.bRepBodies.count):
            b = c.bRepBodies.item(i)
            name = b.name if b.name in PRINT_ORIENT else c.name
            f = os.path.join(out_dir, name.replace(' ', '_') + '.stl')
            opt = em.createSTLExportOptions(b, f)
            opt.isBinaryFormat = True
            opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            em.execute(opt)
            bb = b.boundingBox
            rows.append((name, round(b.volume, 1), [round((bb.maxPoint.asArray()[k] - bb.minPoint.asArray()[k]) * 10, 1) for k in range(3)]))
    return rows


# ---------------------------------------------------------------- elbow concept B on the scanned arm
ELBOW_DOC = 'CDX-3R elbow concepts'


def scan_elbow_flex():
    """Elbow flexion of the scanned relaxed arm: angle between the upper-arm line (reversed) and the forearm."""
    u, f = D['u'], D['f']
    return math.degrees(math.acos(max(-1.0, min(1.0, -dot(u, f)))))


def elbow_matrix():
    """Concept frame (X lateral, Y anterior, Z up the upper arm, flexion axis = X through the origin)
    -> scan frame on the scanned elbow, before the rest abduction (the parent group applies that)."""
    u = D['u']; e, n = arm_frame(u)
    R = [[e[i], n[i], u[i]] for i in range(3)]              # columns = concept X, Y, Z in scan coords
    return fx.matrix(R, LAY['landmarks']['EL'])


def set_elbow_pose(deg):
    """Pose the elbow document's flexion joint (positive = flexion) and save it."""
    app = adsk.core.Application.get()
    doc = next(d for d in app.documents if d.name == ELBOW_DOC)
    des = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    for o in des.rootComponent.allOccurrences:
        for j in o.component.asBuiltJoints:
            if j.name == 'elbow flexion':
                adsk.fusion.RevoluteJointMotion.cast(j.jointMotion).rotationValue = math.radians(deg)
    if des.snapshots.hasPendingSnapshot:                     # capture the position or the save drops it
        des.snapshots.add()
    doc.save('posed at %.0f deg (scanned relaxed arm) for the shoulder assembly' % deg)


def place_elbow():
    """Copy concept B's solids out of the elbow document (as posed there) into a component on the
    scanned elbow, inside the abduction side.  A static copy: re-run after changing the elbow design.
    (A live reference re-solves the elbow's two ungrounded units unpredictably, so it is not used.)"""
    fx.init()
    app = adsk.core.Application.get()
    root = fx.design.rootComponent
    abd = next(o for o in root.allOccurrences if o.component.name.startswith('Abduction side'))
    for o in list(abd.component.occurrences):
        if o.component.name.startswith((ELBOW_DOC, 'Elbow concept B')):
            o.deleteMe()
    ed = next(d for d in app.documents if d.name == ELBOW_DOC)
    edes = adsk.fusion.Design.cast(ed.products.itemByProductType('DesignProductType'))
    tb = adsk.fusion.TemporaryBRepManager.get()
    items = []
    for o in edes.rootComponent.allOccurrences:
        if not o.fullPathName.startswith('B - ') or o.component.bRepBodies.count == 0:
            continue
        for b in o.component.bRepBodies:
            if b.name == 'arm ghost' or not b.isVisible:
                continue
            items.append((o.component.name, b.name, tb.copy(b.createForAssemblyContext(o))))
    occ = abd.component.occurrences.addNewComponent(elbow_matrix())
    occ.component.name = 'Elbow concept B (copy of %s, %d deg)' % (ELBOW_DOC, round(scan_elbow_flex()))
    fx.snapshot()
    comp = occ.component
    bf = comp.features.baseFeatures.add()
    bf.startEdit()
    for unit, name, tmp in items:
        comp.bRepBodies.add(tmp, bf)
    bf.finishEdit()
    for (unit, name, _), nb in zip(items, list(comp.bRepBodies)):      # names/appearances set after the edit stick
        nb.name = '%s: %s' % (unit, name)
        col = HW if '(buy)' in name else ('#e9eef2' if 'PVC' in name else ('#8fa3b3' if 'Forearm' in unit else PRINT))
        nb.appearance = fx.appearance(col)
    return occ.component.name, len(items)


# ---------------------------------------------------------------- upper-arm pipe head (top of the UA pipes)
HEAD = dict(gap=(105.0, 200.0),            # (centre, width) deg of the opening: anterior + medial open, strap closes
            lug=(34.0, 30.0), lug_back=4.0, m4_insert=(5.7, 8.0), m4_pitch=16.0)


def _cb():
    import concepts
    return concepts


def head_geometry():
    """Pipe head in the concept frame, and the link-foot contact (scan frame, before rest abduction)."""
    cb = _cb(); CP = cb.P
    u = D['u']; e, n = arm_frame(u)
    EL = LAY['landmarks']['EL']
    zc = CP['ua_pipe_top'] - CP['ring_h'] / 2
    nc = [e[2], n[2], u[2]]                                  # scan Z (flexion axis) in the concept frame
    fz1 = D['flex_hub_face_z'] + LAY['params']['flex_hub_w']
    z_face = fz1 + S['link_gap']                             # the link plate's inner face (scan Z)
    lat = [cb.band_out(CP['ua_d']), 0.0, zc]                 # head's outer lateral point
    t = (z_face - EL[2]) - dot(nc, lat)
    o = add(lat, mul(nc, t))                                 # lug face centre, on the link plane
    ey = unit(sub([0, 0, 1], mul(nc, nc[2])))                # arm direction within the lug face
    o_scan = add(EL, add(mul(e, o[0]), add(mul(n, o[1]), mul(u, o[2]))))
    return dict(zc=zc, nc=nc, o=o, t=t, ey=ey, o_scan=o_scan)


def build_head(abd_comp):
    cb = _cb(); CP = cb.P
    hg = head_geometry()
    u = D['u']; e, n = arm_frame(u)
    R = [[e[i], n[i], u[i]] for i in range(3)]
    grp = fx.group(abd_comp, 'Upper-arm pipe head (concept frame)', R, LAY['landmarks']['EL'])
    p = Part(grp, 'Upper-arm pipe head', color=PRINT)
    d, h, zc = CP['ua_d'], CP['ring_h'], hg['zc']
    body = p.cring('z', [0, 0, zc], d / 2, cb.band_out(d), h, HEAD['gap'][0], HEAD['gap'][1], name='band')[0]
    rp = d / 2 + CP['wall'] + CP['pipe_od'] / 2
    for a in CP['pipe_angles']:
        c = [rp * math.cos(math.radians(a)), rp * math.sin(math.radians(a)), zc]
        p.prism(c, fx.AX['z'], -h / 2, h / 2, circle(CP['pipe_od'] / 2 + CP['wall']), name='pipe boss', op=JOIN,
                targets=[body])
    # lug: from inside the band out to the link plane, normal = the flexion axis
    ez = hg['nc']; ey = hg['ey']; ex = cross(ey, ez)
    lw, lh = HEAD['lug']
    p.prism(hg['o'], (ex, ey, ez), -(hg['t'] + HEAD['lug_back']), 0,
            rect(-lh / 2, lh / 2, -lw / 2, lw / 2), name='link lug', op=JOIN, targets=[body])
    for s_ in (-1, 1):
        p.prism(add(hg['o'], mul(ey, s_ * HEAD['m4_pitch'] / 2)), (ex, ey, ez), -HEAD['m4_insert'][1], 1,
                circle(HEAD['m4_insert'][0] / 2), name='M4 insert (link)', op=CUT, targets=[body])
    for a in CP['pipe_angles']:                              # pipe sockets (through) + a self-tapping screw each
        c = [rp * math.cos(math.radians(a)), rp * math.sin(math.radians(a)), zc]
        p.prism(c, fx.AX['z'], -h, h, circle((CP['pipe_od'] + CP['pipe_clear']) / 2), name='pipe socket', op=CUT,
                targets=[body])
        out = [math.cos(math.radians(a)), math.sin(math.radians(a)), 0]
        p.prism(add(c, mul(out, CP['pipe_od'] / 2 - 1)), frame_of(out), 0, CP['pipe_od'] / 2 + CP['wall'] + 2,
                circle(CP['pipe_screw_hole'] / 2), name='pipe screw hole', op=CUT, targets=[body])
    p.finish('Upper-arm pipe head')
    return p, hg


def add_harness():
    """Straps + buckles (illustration, from exoarm2-scan/tools/harness.py) as mesh bodies; drawn smooth
    by show_reference_smooth."""
    fx.init()
    top = next(o.component for o in fx.design.rootComponent.occurrences if o.component.name == TOP)
    comp = fx.group(top, 'Harness (illustration)')
    bf = comp.features.baseFeatures.add()
    bf.startEdit()
    for f in ('harness_webbing', 'harness_buckles'):
        comp.meshBodies.add(os.path.join(SCAN, 'layout', f + '.stl'), adsk.fusion.MeshUnits.MillimeterMeshUnit, bf)
    bf.finishEdit()
    for mb, nm in zip(comp.meshBodies, ('webbing 25 / 38 / 20 mm', 'buckles + ladder-locks')):
        mb.name = nm
    return comp.meshBodies.count


def show_reference_smooth(opacity=0.55, on=True):
    """Draw the scan reference as smooth custom graphics (no triangle edges) and hide the mesh bodies.
    Custom graphics are not saved with the document: run again after reopening. on=False restores the meshes."""
    fx.init()
    root = fx.design.rootComponent
    for i in range(root.customGraphicsGroups.count - 1, -1, -1):
        g = root.customGraphicsGroups.item(i)
        if g.id == 'scan reference (smooth)':
            g.deleteMe()
    refs = [o for o in root.allOccurrences if o.component.name in ('Reference (scan)', 'Harness (illustration)')]
    for ref in refs:
        for i in range(ref.component.meshBodies.count):
            ref.component.meshBodies.item(i).isLightBulbOn = not on
    if not on:
        return 'meshes restored'
    grp = root.customGraphicsGroups.add()
    grp.id = 'scan reference (smooth)'
    colors = {'torso': (232, 201, 168), 'right': (214, 170, 150), 'webbing': (40, 44, 48), 'buckles': (12, 12, 12)}
    items = [(ref, ref.component.meshBodies.item(i)) for ref in refs for i in range(ref.component.meshBodies.count)]
    for ref, mb in items:
        tr = ref.transform2
        tm = mb.displayMesh
        flat = []
        for p_ in tm.nodeCoordinates:
            p_.transformBy(tr)
            flat += [p_.x, p_.y, p_.z]
        coords = adsk.fusion.CustomGraphicsCoordinates.create(flat)
        nv = tm.normalVectors
        for v in nv:
            v.transformBy(tr)
        normals = []
        for v in nv:
            normals += [v.x, v.y, v.z]
        m = grp.addMesh(coords, tm.nodeIndices, normals, tm.nodeIndices)
        rgb = next((c for k, c in colors.items() if mb.name.startswith(k)), (220, 200, 180))
        col = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 255)
        op = opacity if ref.component.name == 'Reference (scan)' else 1.0
        m.color = adsk.fusion.CustomGraphicsBasicMaterialColorEffect.create(col, col, adsk.core.Color.create(40, 40, 40, 255),
                                                                           adsk.core.Color.create(0, 0, 0, 255), 20.0, op)
    adsk.core.Application.get().activeViewport.refresh()
    return 'smooth reference drawn (%d meshes)' % len(items)
