"""Fusion-side helpers for the CDX-3R rebuild. Inputs are repo millimetres.

Pure-Python math (no numpy/scipy inside Fusion) plus a Part builder that turns
the repo's mesh primitives into Fusion timeline features: extrudes, lofts,
pipes, revolves. Each Part is one component tagged with its repo layer name,
e.g. "Scapula [sh_scapula]", so it can be checked against the reference mesh.
"""
import adsk.core
import adsk.fusion
import json
import math
import os

REPO = r'C:\Users\PC\projects\cdx-3r'
TOP = 'CDX-3R (Fusion)'
VI = adsk.core.ValueInput
NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation

app = None
design = None
PARAMS = json.load(open(os.path.join(REPO, 'cad', 'params.json')))
LAYER_COLORS = json.load(open(os.path.join(REPO, 'cad', 'system', 'stl', 'asm', 'colors.json')))['layers']

# Shared datums (cad/design.py, cad/elbow/build_stl.py, cad/shoulder/build_stl.py).
UA = float(PARAMS['human']['upper_arm_len'])
FA = float(PARAMS['human']['forearm_len'])
ELBOW = [0.0, -UA, 0.0]
MID_Z = -200.0
R_PACK = [[0.0, 0.0, -1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]]
T_PACK = [-145.0, -65.0, MID_Z]
Z_FLEX = 72.0
X_ABD = -78.0
_h, _sh = PARAMS['human'], PARAMS['cots']['sheave']
Z_PLATE = _h['elbow_width'] / 2 + _h['padding'] + 6.0 + 4
Z_SHEAVE = max(Z_PLATE + 10, _h['forearm_cuff_id'] / 2 + 8.0 + _sh['width'] / 2 + 8)
PITCH = _sh['pitch'] / 2


def init():
    global app, design
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    return design


# ---------------------------------------------------------------- vectors

def add(a, b): return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]
def sub(a, b): return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
def mul(a, s): return [a[0] * s, a[1] * s, a[2] * s]
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
def norm(a): return math.sqrt(dot(a, a))
def unit(a): return mul(a, 1.0 / norm(a))
def mat_vec(R, v): return [sum(R[i][j] * v[j] for j in range(3)) for i in range(3)]


def rot(axis, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return {'x': [[1, 0, 0], [0, c, -s], [0, s, c]],
            'y': [[c, 0, s], [0, 1, 0], [-s, 0, c]],
            'z': [[c, -s, 0], [s, c, 0], [0, 0, 1]]}[axis]


def pack_point(p):
    return add(mat_vec(R_PACK, p), T_PACK)


def linspace(a, b, n):
    return [a + (b - a) * i / (n - 1) for i in range(n)] if n > 1 else [a]


def interp(x, xs, ys):
    """numpy.interp: clamps outside the table."""
    if x <= xs[0]:
        return ys[0]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            f = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + f * (ys[i] - ys[i - 1])
    return ys[-1]


def _sign(v):
    return (v > 0) - (v < 0)


def _pchip_slopes(x, y):
    n = len(x)
    h = [x[i + 1] - x[i] for i in range(n - 1)]
    d = [(y[i + 1] - y[i]) / h[i] for i in range(n - 1)]
    if n == 2:
        return [d[0], d[0]]
    m = [0.0] * n
    for k in range(1, n - 1):
        if _sign(d[k - 1]) != _sign(d[k]) or d[k - 1] == 0 or d[k] == 0:
            m[k] = 0.0
        else:
            w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
            m[k] = (w1 + w2) / (w1 / d[k - 1] + w2 / d[k])

    def edge(h0, h1, m0, m1):
        e = ((2 * h0 + h1) * m0 - h0 * m1) / (h0 + h1)
        if _sign(e) != _sign(m0):
            return 0.0
        if _sign(m0) != _sign(m1) and abs(e) > abs(3 * m0):
            return 3 * m0
        return e

    m[0] = edge(h[0], h[1], d[0], d[1])
    m[-1] = edge(h[-1], h[-2], d[-1], d[-2])
    return m


def curve(points, samples=60):
    """surfaces.curve: PCHIP through points, parameterised by chord length."""
    s = [0.0]
    for a, b in zip(points[:-1], points[1:]):
        s.append(s[-1] + norm(sub(b, a)))
    slopes = [_pchip_slopes(s, [p[c] for p in points]) for c in range(3)]
    out = []
    for q in linspace(0, s[-1], samples):
        k = min(max(i for i in range(len(s) - 1) if s[i] <= q + 1e-12), len(s) - 2)
        h = s[k + 1] - s[k]
        t = (q - s[k]) / h
        h00, h10, h01, h11 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t, -2 * t**3 + 3 * t**2, t**3 - t**2
        out.append([h00 * points[k][c] + h10 * h * slopes[c][k] + h01 * points[k + 1][c] + h11 * h * slopes[c][k + 1]
                    for c in range(3)])
    return out


# ---------------------------------------------------------------- Fusion basics

def P(p):
    return adsk.core.Point3D.create(p[0] / 10.0, p[1] / 10.0, p[2] / 10.0)


def matrix(R=None, t=(0, 0, 0)):
    m = adsk.core.Matrix3D.create()
    if R is not None:
        cols = [[R[0][j], R[1][j], R[2][j]] for j in range(3)]
        m.setWithCoordinateSystem(P(t), *[adsk.core.Vector3D.create(*c) for c in cols])
    else:
        m.translation = adsk.core.Vector3D.create(t[0] / 10.0, t[1] / 10.0, t[2] / 10.0)
    return m


def coll(items):
    c = adsk.core.ObjectCollection.create()
    for i in items:
        c.add(i)
    return c


def appearance(hexcol):
    name = 'cdx ' + hexcol
    a = design.appearances.itemByName(name)
    if a:
        return a
    lib = app.materialLibraries.itemByName('Fusion Appearance Library')
    base = next(lib.appearances.item(i) for i in range(lib.appearances.count)
                if lib.appearances.item(i).name.startswith('Plastic - Matte'))
    a = design.appearances.addByCopy(base, name)
    h = hexcol.lstrip('#')
    prop = adsk.core.ColorProperty.cast(a.appearanceProperties.itemById('opaque_albedo'))
    prop.value = adsk.core.Color.create(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
    return a


def top_occurrence(create=True):
    root = design.rootComponent
    for o in root.occurrences:
        if o.component.name == TOP:
            return o
    if not create:
        return None
    m = matrix(rot('x', 90))
    occ = root.occurrences.addNewComponent(m)
    occ.component.name = TOP
    snapshot()
    occ.isGroundToParent = True
    return occ


def snapshot():
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()


def group(parent, name, R=None, t=(0, 0, 0)):
    """An empty component used to hold parts, optionally in its own frame."""
    for o in list(parent.occurrences):
        if o.component.name == name:
            o.deleteMe()
    occ = parent.occurrences.addNewComponent(matrix(R, t))
    occ.component.name = name
    snapshot()
    return occ.component


AX = {'z': ([1, 0, 0], [0, 1, 0], [0, 0, 1]),
      'x': ([0, 1, 0], [0, 0, 1], [1, 0, 0]),
      'y': ([1, 0, 0], [0, 0, 1], [0, 1, 0])}
BASES = (([0, 0, 1], 'xYConstructionPlane'), ([1, 0, 0], 'yZConstructionPlane'), ([0, 1, 0], 'xZConstructionPlane'))


# ---------------------------------------------------------------- Part builder

class Part:
    """One component = one repo layer. Coordinates are in the parent frame (mm)."""

    def __init__(self, parent, name, layer=None, color=None):
        occ = parent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        self.occ, self.comp = occ, occ.component
        self.comp.name = f'{name} [{layer}]' if layer else name
        self.color = color or (LAYER_COLORS.get(layer) if layer else None)
        self._planes, self._refs, self._paths = {}, None, {}

    # -- planes and sketches
    def _hidden_sketch(self, plane, name):
        sk = self.comp.sketches.add(plane)
        sk.name = name
        sk.isVisible = False
        return sk

    def refs(self):
        if self._refs is None:
            self._refs = self._hidden_sketch(self.comp.xYConstructionPlane, 'refs')
        return self._refs

    def plane(self, origin, ez, ex):
        """A plane through origin with normal ez."""
        ez = unit(ez)
        for axis, base in BASES:
            if abs(abs(dot(ez, axis)) - 1) < 1e-9:
                bp = getattr(self.comp, base)
                g = bp.geometry.normal
                d = dot(origin, [g.x, g.y, g.z])
                key = (base, round(d, 4))
                if key not in self._planes:
                    if abs(d) < 1e-6:
                        self._planes[key] = bp
                    else:
                        ci = self.comp.constructionPlanes.createInput()
                        ci.setByOffset(bp, VI.createByString(f'{d:.4f} mm'))
                        pl = self.comp.constructionPlanes.add(ci)
                        pl.isLightBulbOn = False
                        self._planes[key] = pl
                return self._planes[key]
        ey = cross(ez, ex)
        rs = self.refs()
        pts = [origin, add(origin, mul(unit(ex), 20)), add(origin, mul(unit(ey), 20))]
        sps = [rs.sketchPoints.add(rs.modelToSketchSpace(P(p))) for p in pts]
        ci = self.comp.constructionPlanes.createInput()
        ci.setByThreePoints(*sps)
        pl = self.comp.constructionPlanes.add(ci)
        pl.isLightBulbOn = False
        return pl

    # -- extrusions
    def prism(self, origin, frame, z0, z1, draw, pick=None, name='prism'):
        """Sketch in the plane origin + z0*ez, extrude to z1 along ez. draw(sketch, to)."""
        ex, ey, ez = [unit(v) for v in frame]
        o = add(origin, mul(ez, z0))
        pl = self.plane(o, ez, ex)
        sk = self._hidden_sketch(pl, name)
        to = lambda u, v: sk.modelToSketchSpace(P(add(o, add(mul(ex, u), mul(ey, v)))))
        draw(sk, to)
        profs = [sk.profiles.item(i) for i in range(sk.profiles.count)]
        if pick:
            profs = pick(profs)
        ei = self.comp.features.extrudeFeatures.createInput(coll(profs), NEW)
        zs = sk.transform.getAsCoordinateSystem()[3]
        direction = (adsk.fusion.ExtentDirections.PositiveExtentDirection if dot([zs.x, zs.y, zs.z], ez) > 0
                     else adsk.fusion.ExtentDirections.NegativeExtentDirection)
        ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VI.createByReal((z1 - z0) / 10.0)), direction)
        f = self.comp.features.extrudeFeatures.add(ei)
        f.name = name
        return f

    def box(self, x0, x1, y0, y1, z0, z1, name='box'):
        f = self.prism([0, 0, 0], AX['z'], z0, z1,
                       lambda sk, to: sk.sketchCurves.sketchLines.addTwoPointRectangle(to(x0, y0), to(x1, y1)),
                       name=name)
        return list(f.bodies)

    def _frame(self, axis):
        return AX[axis] if isinstance(axis, str) else axis

    def cyl(self, axis, c, r, length, name='cylinder'):
        f = self.prism(c, self._frame(axis), -length / 2, length / 2,
                       lambda sk, to: sk.sketchCurves.sketchCircles.addByCenterRadius(to(0, 0), r / 10.0), name=name)
        return list(f.bodies)

    def ann(self, axis, c, ro, ri, length, chamfer=0.0, name='ring'):
        def draw(sk, to):
            sk.sketchCurves.sketchCircles.addByCenterRadius(to(0, 0), ro / 10.0)
            sk.sketchCurves.sketchCircles.addByCenterRadius(to(0, 0), ri / 10.0)
        f = self.prism(c, self._frame(axis), -length / 2, length / 2, draw,
                       lambda ps: [p for p in ps if p.profileLoops.count == 2], name=name)
        if chamfer:
            self.chamfer(f, chamfer)
        return list(f.bodies)

    def cring(self, axis, c, r_in, r_out, length, gap_deg, open_deg, name='C-ring'):
        """cuff_c: an annulus opened by open_deg, gap centred on gap_deg in the plane's (u, v)."""
        a0, am, a1 = gap_deg + open_deg / 2, gap_deg + 180, gap_deg + 360 - open_deg / 2

        def draw(sk, to):
            arcs = []
            for r in (r_in, r_out):
                at = lambda d: to(r * math.cos(math.radians(d)), r * math.sin(math.radians(d)))
                arcs.append(sk.sketchCurves.sketchArcs.addByThreePoints(at(a0), at(am), at(a1)))
            ends = lambda arc: [arc.startSketchPoint, arc.endSketchPoint]
            for pi in ends(arcs[0]):
                po = min(ends(arcs[1]), key=lambda q: q.geometry.distanceTo(pi.geometry))
                sk.sketchCurves.sketchLines.addByTwoPoints(pi, po)
        f = self.prism(c, self._frame(axis), -length / 2, length / 2, draw, name=name)
        return list(f.bodies)

    def plate(self, outline, z0, thickness, bevel, origin=(0, 0, 0), frame=None, name='plate'):
        """surfaces.plate: polygon outline extruded from z0, top and bottom edges chamfered."""
        def draw(sk, to):
            lines = sk.sketchCurves.sketchLines
            pts = [to(u, v) for u, v in outline]
            first = prev = lines.addByTwoPoints(pts[0], pts[1])
            for p in pts[2:]:
                prev = lines.addByTwoPoints(prev.endSketchPoint, p)
            lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
        f = self.prism(list(origin), frame or AX['z'], z0, z0 + thickness, draw, name=name)
        if bevel:
            self.chamfer(f, bevel)
        return list(f.bodies)

    def chamfer(self, f, d):
        edges = [e for faces in (f.startFaces, f.endFaces) for face in faces for e in face.edges]
        ch = self.comp.features.chamferFeatures
        try:
            try:
                ci = ch.createInput2()
                ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(coll(edges), VI.createByReal(d / 10.0), True)
            except AttributeError:
                ci = ch.createInput(coll(edges), True)
                ci.setToEqualDistance(VI.createByReal(d / 10.0))
            ch.add(ci)
        except Exception:
            pass  # a chamfer that cannot be built is cosmetic; keep the solid

    # -- sweeps
    def paths(self):
        if 'xy' not in self._paths:
            self._paths['xy'] = self._hidden_sketch(self.comp.xYConstructionPlane, 'paths')
        return self._paths['xy']

    def _pipe(self, curve_entity, r, name):
        path = self.comp.features.createPath(curve_entity, False)
        pi = self.comp.features.pipeFeatures.createInput(path, NEW)
        pi.sectionSize = VI.createByReal(2 * r / 10.0)
        f = self.comp.features.pipeFeatures.add(pi)
        f.name = name
        return list(f.bodies)

    def pipe(self, points, r, step=2, name='pipe'):
        """surfaces.tube along sampled points: a fitted spline through them, or a line for two.

        A spline that bends tighter than the tube radius self-intersects; then retry
        through every sample, and finally fall back to joined straight segments
        (what the mesh source is).
        """
        sk = self.paths()
        if len(points) == 2:
            ent = sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(P(points[0])),
                                                             sk.modelToSketchSpace(P(points[1])))
            return self._pipe(ent, r, name)
        for s in (step, 1) if step > 1 else (1,):
            pts = points[::s]
            if pts[-1] is not points[-1]:
                pts.append(points[-1])
            ent = sk.sketchCurves.sketchFittedSplines.add(coll([sk.modelToSketchSpace(P(p)) for p in pts]))
            try:
                return self._pipe(ent, r, name)
            except RuntimeError:
                ent.deleteMe()
        return self.polypipe(points, r, name + ' (segmented)')

    def polypipe(self, points, r, name='rod'):
        """elbow polyline(): one straight rod per segment, joined."""
        bodies = []
        for a, b in zip(points[:-1], points[1:]):
            if norm(sub(b, a)) >= 0.8:
                bodies += self.pipe([a, b], r, name=name)
        return self.join(bodies)

    def arc_pipe(self, center, radius, z, a0, a1, r, name='arc'):
        """armor ring_arc: tube along a circular arc in the plane z = const."""
        o = [center[0], center[1], center[2] + z]
        pl = self.plane(o, [0, 0, 1], [1, 0, 0])
        sk = self._hidden_sketch(pl, name)
        to = lambda u, v: sk.modelToSketchSpace(P([o[0] + u, o[1] + v, o[2]]))
        start = to(radius * math.cos(math.radians(a0)), radius * math.sin(math.radians(a0)))
        arc = sk.sketchCurves.sketchArcs.addByCenterStartSweep(to(0, 0), start, math.radians(a1 - a0))
        return self._pipe(arc, r, name)

    # -- lofts and revolves
    def loft(self, sections, name='loft'):
        """sections: [(origin, ex, ey, outer_pts, inner_pts)], each section planar, both skins as 3D points."""
        li = self.comp.features.loftFeatures.createInput(NEW)
        for origin, ex, ey, outer, inner in sections:
            pl = self.plane(origin, cross(ex, ey), ex)
            sk = self._hidden_sketch(pl, name)
            spline = lambda pts: sk.sketchCurves.sketchFittedSplines.add(coll([sk.modelToSketchSpace(P(p)) for p in pts]))
            a, b = spline(outer), spline(inner)
            sk.sketchCurves.sketchLines.addByTwoPoints(a.startSketchPoint, b.startSketchPoint)
            sk.sketchCurves.sketchLines.addByTwoPoints(a.endSketchPoint, b.endSketchPoint)
            profs = [sk.profiles.item(i) for i in range(sk.profiles.count)]
            li.loftSections.add(max(profs, key=lambda p: p.areaProperties().area))
        li.isSolid = True
        f = self.comp.features.loftFeatures.add(li)
        f.name = name
        return list(f.bodies)

    def ellipsoid(self, center, radii, name='ellipsoid'):
        pl = self.plane(center, [0, 0, 1], [1, 0, 0])
        sk = self._hidden_sketch(pl, name)
        to = lambda u, v: sk.modelToSketchSpace(P([center[0] + u, center[1] + v, center[2]]))
        r0 = 10.0
        arc = sk.sketchCurves.sketchArcs.addByThreePoints(to(-r0, 0), to(0, r0), to(r0, 0))
        axis = sk.sketchCurves.sketchLines.addByTwoPoints(arc.startSketchPoint, arc.endSketchPoint)
        rv = self.comp.features.revolveFeatures
        ri = rv.createInput(sk.profiles.item(0), axis, NEW)
        ri.setAngleExtent(False, VI.createByString('360 deg'))
        body = rv.add(ri).bodies.item(0)
        sc = self.comp.features.scaleFeatures
        si = sc.createInput(coll([body]), arc.centerSketchPoint, VI.createByReal(1.0))
        si.setToNonUniform(*[VI.createByReal(r / r0) for r in radii])
        sc.add(si).name = name
        return [self.comp.bRepBodies.item(self.comp.bRepBodies.count - 1)]

    # -- bodies
    def join(self, bodies):
        """Join into bodies[0]; any tool that cannot be joined stays a separate body."""
        bodies = [b for b in bodies if b and b.isValid]
        if len(bodies) < 2:
            return bodies
        target, left = bodies[0], []
        cf = self.comp.features.combineFeatures
        for tool in bodies[1:]:
            try:
                ci = cf.createInput(target, coll([tool]))
                ci.operation = JOIN
                ci.isKeepToolBodies = False
                target = cf.add(ci).bodies.item(0)
            except Exception:
                left.append(tool)
        return [target] + left

    def cut(self, targets, tools):
        """Subtract tool bodies from each target; tools are consumed."""
        cf = self.comp.features.combineFeatures
        out = []
        for t in targets:
            ci = cf.createInput(t, coll(tools))
            ci.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
            ci.isKeepToolBodies = True
            out.append(cf.add(ci).bodies.item(0))
        for tool in tools:
            if tool.isValid:
                self.comp.features.removeFeatures.add(tool)
        return out

    def finish(self, body_name=None):
        a = appearance(self.color) if self.color else None
        n = self.comp.bRepBodies.count
        for i in range(n):
            b = self.comp.bRepBodies.item(i)
            if body_name:
                b.name = body_name if n == 1 else f'{body_name} {i + 1}'
            if a:
                b.appearance = a
        return self


# ---------------------------------------------------------------- checks

def world_bbox(bodies, occ):
    """Bounding box in root space (mm). Assembly-context proxies are reliable for
    nested occurrences, where transform2 is not."""
    lo, hi = [1e9] * 3, [-1e9] * 3
    for b in bodies:
        proxy = b.createForAssemblyContext(occ)
        if isinstance(proxy, adsk.fusion.BRepBody):
            # boundingBox (and the oriented box) can come back short on swept splines;
            # the extent of a fine tessellation is reliable.
            calc = proxy.meshManager.createMeshCalculator()
            calc.setQuality(adsk.fusion.TriangleMeshQualityOptions.NormalQualityTriangleMesh)
            xyz = calc.calculate().nodeCoordinatesAsDouble
            box = ([min(xyz[i::3]) for i in range(3)], [max(xyz[i::3]) for i in range(3)])
        else:
            bb = proxy.boundingBox
            box = (bb.minPoint.asArray(), bb.maxPoint.asArray())
        for i in range(3):
            lo[i], hi[i] = min(lo[i], box[0][i] * 10), max(hi[i], box[1][i] * 10)
    return lo, hi


def check(tolerance=1.0, prefix=None):
    """Compare every tagged Fusion part with the reference mesh of the same layer."""
    root = design.rootComponent
    refs, parts = {}, []
    for o in root.allOccurrences:
        path = o.fullPathName
        if path.startswith('CDX-3R reference'):
            for i in range(o.component.meshBodies.count):
                mb = o.component.meshBodies.item(i)
                refs[mb.name] = (mb, o)
        elif path.startswith(TOP) and o.component.name.endswith(']'):
            parts.append(o)
    rows = []
    for o in parts:
        layer = o.component.name.rsplit('[', 1)[1][:-1]
        if prefix and not layer.startswith(prefix):
            continue
        bodies = [o.component.bRepBodies.item(i) for i in range(o.component.bRepBodies.count)]
        if layer not in refs or not bodies:
            rows.append((1e9, layer, 'no reference' if bodies else 'no bodies'))
            continue
        lo, hi = world_bbox(bodies, o)
        rlo, rhi = world_bbox([refs[layer][0]], refs[layer][1])
        dev = max(abs(a - b) for a, b in zip(lo + hi, rlo + rhi))
        rows.append((dev, layer, f'{len(bodies)} bodies'))
    rows.sort(reverse=True)
    done = {r[1] for r in rows}
    missing = sorted(set(refs) - done - {n for n in refs if prefix and not n.startswith(prefix)})
    return rows, missing
