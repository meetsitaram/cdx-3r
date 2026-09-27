"""CDX-3R elbow as parametric Fusion solids (stage 'elbow' of build.py).

Mirrors cad/elbow/build_stl.py as placed by design.place_elbow: repo world
frame (Y up, Z outboard), elbow datum at (0, -upper_arm_len, 0), forearm +X.
The mechanical parts are driven by Fusion user parameters seeded from
cad/params.json; the cable centrelines are fixed geometry.

Deliberate differences from the mesh source (a mesh union hides these):
- shaft bores are cut clear through the joined plates and hubs;
- 608 cup pockets are cut clear, so the bearings seat;
- strap tabs stay separate bodies: in the source they float in the cuff gap;
- the Bowden barrels are omitted: they sit fully inside the anchor blocks.
"""
import adsk.core
import adsk.fusion
import json
import math
import os

import fxlib as fx

REPO = fx.REPO
VI = adsk.core.ValueInput
NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
PLANES = {'z': 'xYConstructionPlane', 'x': 'yZConstructionPlane', 'y': 'xZConstructionPlane'}
CUPS = [(24, 42), (-24, 42)]

design = None


def mm(v):
    return v / 10.0


def ev(expr):
    """Evaluate a length expression to mm."""
    return design.unitsManager.evaluateExpression(expr, 'mm') * 10.0


# ---------------------------------------------------------------- parameters

def set_param(name, expr, comment):
    prm = design.userParameters.itemByName(name)
    if prm:
        prm.expression = expr
        prm.comment = comment
    else:
        design.userParameters.add(name, VI.createByString(expr), 'mm', comment)


def seed_parameters():
    p = json.load(open(os.path.join(REPO, 'cad', 'params.json')))
    h, c = p['human'], p['cots']
    sh, sc, idl = c['sheave'], c['shoulder_screw'], c['idler_bearing']
    rows = [
        ('upper_arm_len', f"{h['upper_arm_len']} mm", 'params.json human'),
        ('elbow_width', f"{h['elbow_width']} mm", 'params.json human'),
        ('padding', f"{h['padding']} mm", 'params.json human'),
        ('upper_cuff_id', f"{h['upper_cuff_id']} mm", 'params.json human'),
        ('forearm_cuff_id', f"{h['forearm_cuff_id']} mm", 'params.json human'),
        ('cuff_t', '8 mm', 'CUFF_T'),
        ('cuff_gap', '6 mm', 'GAP: air between cuff OD and lateral plate'),
        ('plate_t', '8 mm', 'lateral / distal plate thickness'),
        ('sheave_od', f"{sh['od']} mm", sh['mcmaster']),
        ('sheave_pitch', f"{sh['pitch']} mm", sh['mcmaster']),
        ('sheave_w', f"{sh['width']} mm", sh['mcmaster']),
        ('sheave_bore', f"{sh['bore']} mm", sh['mcmaster']),
        ('screw_dia', f"{sc['shoulder_dia']} mm", sc['mcmaster']),
        ('screw_len', f"{sc['shoulder_len']} mm", sc['mcmaster']),
        ('screw_head_dia', f"{sc['head_dia']} mm", sc['mcmaster']),
        ('idler_od', f"{idl['od']} mm", idl['mcmaster'] + ' 608-2RS'),
        ('idler_id', f"{idl['id']} mm", idl['mcmaster'] + ' 608-2RS'),
        ('idler_w', f"{idl['width']} mm", idl['mcmaster'] + ' 608-2RS'),
        ('z_plate', 'elbow_width/2 + padding + cuff_gap + 4 mm', 'Z_PLATE: plate centre'),
        ('ua_od', 'upper_cuff_id/2 + cuff_t', 'UA_OD: upper cuff outer radius'),
        ('fa_od', 'forearm_cuff_id/2 + cuff_t', 'FA_OD: forearm cuff outer radius'),
    ]
    for row in rows:
        set_param(*row)
    # Z_SHEAVE = max(Z_PLATE + 10, FA_OD + width/2 + 8): keep the sheave outside the forearm cuff.
    for expr in ('max(z_plate + 10 mm; fa_od + sheave_w/2 + 8 mm)',
                 'max(z_plate + 10 mm, fa_od + sheave_w/2 + 8 mm)'):
        try:
            set_param('z_sheave', expr, 'Z_SHEAVE')
            break
        except Exception:
            pass
    else:
        governing = 'fa_od + sheave_w/2 + 8 mm' if ev('fa_od + sheave_w/2 + 8 mm') >= ev('z_plate + 10 mm') else 'z_plate + 10 mm'
        set_param('z_sheave', governing, 'Z_SHEAVE: governing term of max(z_plate + 10, fa_od + sheave_w/2 + 8)')
    set_param('screw_z', 'z_sheave + sheave_w/2 - screw_len/2 + 2 mm', 'shoulder-screw centre in the assembly')


# ---------------------------------------------------------------- geometry

class Slab:
    """A sketch on a plane normal to an axis, extruded symmetrically about it."""

    def __init__(self, comp, axis, center, name):
        ci = comp.constructionPlanes.createInput()
        ci.setByOffset(getattr(comp, PLANES[axis]), VI.createByString(center))
        self.plane = comp.constructionPlanes.add(ci)
        self.plane.name = name
        self.plane.isLightBulbOn = False
        self.sk = comp.sketches.add(self.plane)
        self.sk.name = name
        self.sk.isVisible = False
        self.comp, self.axis = comp, axis
        o = self.plane.geometry.origin
        self.pos = {'x': o.x, 'y': o.y, 'z': o.z}[axis] * 10.0

    def p(self, a, b):
        """In-plane mm coords -> sketch point. z: (x, y); x: (y, z); y: (x, z)."""
        x, y, z = {'z': (a, b, self.pos), 'x': (self.pos, a, b), 'y': (a, self.pos, b)}[self.axis]
        return self.sk.modelToSketchSpace(adsk.core.Point3D.create(mm(x), mm(y), mm(z)))

    def rect(self, a0, a1, b0, b1):
        self.sk.sketchCurves.sketchLines.addTwoPointRectangle(self.p(a0, b0), self.p(a1, b1))

    def circle(self, a, b, dia):
        r = ev(dia) / 2
        c = self.sk.sketchCurves.sketchCircles.addByCenterRadius(self.p(a, b), mm(r))
        c.centerSketchPoint.isFixed = True
        self.sk.sketchDimensions.addDiameterDimension(c, self.p(a + r, b + r)).parameter.expression = dia

    def c_ring(self, r_in, r_out, gap_deg, open_deg=70):
        """C-section: open by open_deg, gap centred on gap_deg in the (a, b) plane."""
        a0, am, a1 = gap_deg + open_deg / 2, gap_deg + 180, gap_deg + 360 - open_deg / 2
        arcs = []
        for expr in (r_in, r_out):
            r = ev(expr)
            at = lambda d: self.p(r * math.cos(math.radians(d)), r * math.sin(math.radians(d)))
            arc = self.sk.sketchCurves.sketchArcs.addByThreePoints(at(a0), at(am), at(a1))
            arc.centerSketchPoint.isFixed = True
            self.sk.sketchDimensions.addRadialDimension(arc, at(am)).parameter.expression = expr
            arcs.append(arc)
        ends = lambda arc: [arc.startSketchPoint, arc.endSketchPoint]
        for pi in ends(arcs[0]):
            po = min(ends(arcs[1]), key=lambda q: q.geometry.distanceTo(pi.geometry))
            self.sk.sketchCurves.sketchLines.addByTwoPoints(pi, po)

    def extrude(self, thick, op, body=None, rings=False):
        coll = adsk.core.ObjectCollection.create()
        for i in range(self.sk.profiles.count):
            prof = self.sk.profiles.item(i)
            if not rings or prof.profileLoops.count == 2:
                coll.add(prof)
        ei = self.comp.features.extrudeFeatures.createInput(coll, op)
        ei.setSymmetricExtent(VI.createByString(thick), True)
        if body is not None:
            ei.participantBodies = [body]
        f = self.comp.features.extrudeFeatures.add(ei)
        f.name = self.sk.name
        return f


def block(comp, axis, center, thick, rects, op=NEW, body=None, name='block'):
    s = Slab(comp, axis, center, name)
    for r in rects:
        s.rect(*r)
    return s.extrude(thick, op, body)


def ring(comp, axis, center, od, idd, thick, at=((0, 0),), op=NEW, body=None, name='ring'):
    s = Slab(comp, axis, center, name)
    for a, b in at:
        s.circle(a, b, od)
        s.circle(a, b, idd)
    return s.extrude(thick, op, body, rings=True)


def disc(comp, axis, center, dia, thick, at=((0, 0),), op=NEW, body=None, name='disc'):
    s = Slab(comp, axis, center, name)
    for a, b in at:
        s.circle(a, b, dia)
    return s.extrude(thick, op, body)


def first(feature, name):
    b = feature.bodies.item(0)
    b.name = name
    return b


# ---------------------------------------------------------------- parts

def cuff_upper(c):
    # Around +Y, y 74..126; the C opens toward -X (place_elbow mirrors the source's +X).
    s = Slab(c, 'y', '100 mm', 'cuff C')
    s.c_ring('upper_cuff_id/2', 'ua_od', 180)
    first(s.extrude('52 mm', NEW), 'cuff')
    f = block(c, 'z', '0 mm', '10 mm', [(-72.5, -58.5, 113.33, 121.33), (-72.5, -58.5, 78.67, 86.67)], name='strap tabs')
    for i in range(f.bodies.count):
        f.bodies.item(i).name = 'strap tab (floats in cuff gap in source)'


def cuff_forearm(c):
    # Around +X, x 66..114; the C opens medial (-Z). In-plane (a, b) = (y, z).
    s = Slab(c, 'x', '90 mm', 'cuff C')
    s.c_ring('forearm_cuff_id/2', 'fa_od', -90)
    first(s.extrude('48 mm', NEW), 'cuff')
    f = block(c, 'y', '0 mm', '10 mm', [(70, 78, -67.5, -53.5), (102, 110, -67.5, -53.5)], name='strap tabs')
    for i in range(f.bodies.count):
        f.bodies.item(i).name = 'strap tab (floats in cuff gap in source)'


BOSS_C = '(fa_od - 2 mm + z_plate + 4 mm)/2'
BOSS_T = 'z_plate + 4 mm - (fa_od - 2 mm)'


def fork_lateral(c):
    b = first(block(c, 'z', 'z_plate', 'plate_t', [(-16, 16, 8, 140)], name='plate'), 'fork lateral')
    ring(c, 'z', 'z_plate', '56 mm', 'sheave_bore + 0.4 mm', 'plate_t', op=JOIN, body=b, name='hub')
    block(c, 'z', BOSS_C, BOSS_T, [(-12, 12, 80, 120)], JOIN, b, 'cuff boss')
    ring(c, 'z', 'z_plate + 6 mm', '28 mm', 'idler_od + 0.3 mm', 'idler_w + 0.4 mm', CUPS, JOIN, b, 'idler cups')
    ring(c, 'z', 'z_plate + 6 mm - (idler_w + 0.4 mm)/2 - 1.2 mm', '28 mm', 'idler_id + 0.3 mm', '2.5 mm',
         CUPS, JOIN, b, 'cup floors')
    disc(c, 'z', 'z_plate', 'sheave_bore + 0.4 mm', 'plate_t + 2 mm', op=CUT, body=b, name='shaft bore')
    disc(c, 'z', 'z_plate + 6 mm', 'idler_od + 0.3 mm', 'idler_w + 0.4 mm', CUPS, CUT, b, 'cup pockets')


def fork_distal(c):
    b = first(block(c, 'z', 'z_plate', 'plate_t', [(8, 130, -16, 16)], name='plate'), 'fork distal')
    ring(c, 'z', 'z_plate', '64 mm', 'sheave_bore + 0.8 mm', '6 mm', op=JOIN, body=b, name='hub')
    block(c, 'z', BOSS_C, BOSS_T, [(70, 110, -12, 12)], JOIN, b, 'cuff boss')
    disc(c, 'z', 'z_plate', 'sheave_bore + 0.8 mm', 'plate_t + 2 mm', op=CUT, body=b, name='shaft bore')


def fork_medial(c):
    b = first(block(c, 'z', '-z_plate', '6 mm', [(-12, 12, 8, 130)], name='plate'), 'fork medial')
    ring(c, 'z', '-z_plate', '44 mm', 'sheave_bore + 0.4 mm', '6 mm', op=JOIN, body=b, name='hub')
    disc(c, 'z', '-z_plate', 'sheave_bore + 0.4 mm', '8 mm', op=CUT, body=b, name='shaft bore')


def hard_stop(c):
    first(block(c, 'z', 'z_plate', '12 mm', [(-22, 22, -36, -20)], name='stop'), 'hard stop')


def bowden_anchor(c):
    f = block(c, 'z', 'z_plate + 12 mm', '16 mm', [(8, 28, 42, 74), (-28, -8, 42, 74)], name='anchor blocks')
    for i in range(f.bodies.count):
        f.bodies.item(i).name = 'bowden anchor'


def sheave(c):
    first(ring(c, 'z', 'z_sheave', 'sheave_od', 'sheave_bore', 'sheave_w', name='sheave'), 'sheave 3434T121')


def shoulder_screw(c):
    b = first(disc(c, 'z', 'screw_z', 'screw_dia', 'screw_len', name='shoulder'), 'shoulder screw 91273A274')
    disc(c, 'z', 'screw_z + screw_len/2 + 6.25 mm', 'screw_head_dia', '12.5 mm', op=JOIN, body=b, name='head')
    disc(c, 'z', 'screw_z - screw_len/2 - 8 mm', '18.8 mm', '16 mm', op=JOIN, body=b, name='thread stub')


def nylock(c):
    first(disc(c, 'z', 'z_plate - 10 mm', '29 mm', '10 mm', name='nylock'), 'nylock 90640A125')


def bearings(c):
    f = ring(c, 'z', 'z_plate + 6 mm', 'idler_od', 'idler_id', 'idler_w', CUPS, name='608')
    for i in range(f.bodies.count):
        f.bodies.item(i).name = '608-2RS 6455K44'


PARTS = [
    ('Cuff upper', 'el_cuff_upper', cuff_upper),
    ('Cuff forearm', 'el_cuff_forearm', cuff_forearm),
    ('Fork lateral', 'el_lateral', fork_lateral),
    ('Fork distal', 'el_distal', fork_distal),
    ('Fork medial', 'el_medial', fork_medial),
    ('Hard stop', 'el_stop', hard_stop),
    ('Bowden anchor', 'el_anchor', bowden_anchor),
    ('Sheave 3434T121', 'el_sheave', sheave),
    ('Shoulder screw 91273A274', 'el_screw', shoulder_screw),
    ('Nylock 90640A125', 'el_nylock', nylock),
    ('608 bearings 6455K44', 'el_bearing', bearings),
]


# ---------------------------------------------------------------- cables (fixed geometry)

def arc_pts(radius, z, deg0, deg1, steps=14):
    return [[radius * math.cos(math.radians(a)), radius * math.sin(math.radians(a)), z]
            for a in fx.linspace(deg0, deg1, steps)]


def mirror(points):
    """place_elbow mirrors X; this component is the mirrored elbow frame."""
    return [[-p[0], p[1], p[2]] for p in points]


def cables(parent):
    r, zg, zp = fx.PITCH, fx.Z_SHEAVE, fx.Z_PLATE
    flex = [[18.0, 210.0, zp + 10], [18.0, 58.0, zp + 10], [24.0, 42.0, zp + 6], [8.0, r + 2, zg],
            *arc_pts(r, zg, 85, -10)]
    ext = [[-18.0, 210.0, zp + 10], [-18.0, 58.0, zp + 10], [-24.0, 42.0, zp + 6], [-8.0, r + 2, zg],
           *arc_pts(r, zg, 95, 190)]
    for name, layer, pts in (('Cable flexor', 'el_cable_flex', flex), ('Cable extensor', 'el_cable_ext', ext)):
        p = fx.Part(parent, name, layer)
        p.polypipe(mirror(pts), 1.6)
        p.finish(name.lower())
    p = fx.Part(parent, 'Cable clamps', 'el_clamp')
    rc = r + 4
    for x, y, _ in mirror([[-rc, 0, 0], [rc * 0.15, -rc * 0.9, 0]]):
        p.box(x - 5, x + 5, y - 5, y + 5, zg - 5, zg + 5)
    p.finish('cable clamp')


def build(parent):
    """Stage entry: an 'Elbow' group at the elbow datum holding every elbow layer."""
    global design
    design = fx.design
    seed_parameters()
    t = [0, -design.userParameters.itemByName('upper_arm_len').value * 10, 0]
    elbow = fx.group(parent, 'Elbow', t=t)
    report = []
    for name, layer, fn in PARTS:
        occ = elbow.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        c = occ.component
        c.name = f'{name} [{layer}]'
        fn(c)
        a = fx.appearance(fx.LAYER_COLORS[layer])
        for i in range(c.bRepBodies.count):
            c.bRepBodies.item(i).appearance = a
        report.append(f'{layer}: {c.bRepBodies.count} bodies')
    cables(elbow)
    z = design.userParameters.itemByName('z_sheave')
    report.append(f'z_sheave = {z.expression} -> {z.value * 10:.2f} mm')
    return report
