"""Exploded assembly animations, rendered in Fusion without touching the design.

Every body of the shoulder document (exo + elbow copy + harness meshes) is copied into custom graphics; the real
bodies are hidden while rendering. Each step flies its parts in, one group after another, along a direction
(the part's own axis, or a fixed vector), then holds. Frames go to OUT/<step>_NNN.png.
"""
import os, math, re
import adsk.core, adsk.fusion

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'asm')
GID = 'asm anim'
STATE = {}
ZOOM_OUT = 1.8          # render wide; mkgif crops to where things move

COL = {
    'print': (100, 116, 128), 'forearm': (143, 163, 179), 'pvc': (233, 238, 242), 'steel': (176, 182, 187),
    'bearing': (212, 160, 23), 'insert': (196, 150, 60), 'strap': (45, 48, 52), 'buckle': (15, 15, 15),
    'foam': (63, 111, 143),
}


def design():
    app = adsk.core.Application.get()
    return app, adsk.fusion.Design.cast(app.activeProduct)


def kind(comp, name):
    n = (comp + ' ' + name).lower()
    if '6806' in n or '6808' in n or '608-2rs' in n: return 'bearing'
    if 'foam' in n: return 'foam'
    if 'hook-and-loop' in n or 'gas spring' in n or 'belt' in n: return 'strap'
    if 'insert' in n: return 'insert'
    if '(buy)' in n or 'washer' in n or 'nut' in n or 'pin' in n: return 'steel'
    if 'pvc' in n or n.split()[-2:-1] in (['backbone'], ['beam'], ['diag']) or re.search(r'\b(backbone|beam|diag) [lr]\b', n): return 'pvc'
    if 'webbing' in n: return 'strap'
    if 'buckle' in n: return 'buckle'
    if 'forearm' in n or 'wrist' in n or 'cuff' in n: return 'forearm'
    return 'print'


def _power(cov, v):
    for _ in range(40):
        w = [sum(cov[a][b] * v[b] for b in range(3)) for a in range(3)]
        s = math.sqrt(sum(x * x for x in w)) or 1.0
        v = [x / s for x in w]
    lam = sum(v[a] * sum(cov[a][b] * v[b] for b in range(3)) for a in range(3))
    return v, lam


def principal_axis(cov):
    """Long axis of a rod-like part; the thin (normal) axis of a disc-like one (nut, bearing, washer, pulley)."""
    v1, l1 = _power(cov, [1.0, 0.7, 0.3])
    c2 = [[cov[a][b] - l1 * v1[a] * v1[b] for b in range(3)] for a in range(3)]
    v2, l2 = _power(c2, [0.3, -0.5, 0.8])
    if l1 > 0 and l2 / l1 > 0.6:
        return [v1[1] * v2[2] - v1[2] * v2[1], v1[2] * v2[0] - v1[0] * v2[2], v1[0] * v2[1] - v1[1] * v2[0]]
    return v1


def collect():
    """Copy every visible body (and the harness meshes) into custom graphics; hide the originals."""
    app, d = design()
    root = d.rootComponent
    for i in range(root.customGraphicsGroups.count - 1, -1, -1):
        g = root.customGraphicsGroups.item(i)
        if g.id in (GID, 'scan reference (smooth)', 'anim arm'):
            g.isVisible = g.id == 'scan reference (smooth)' and False
            if g.id == GID: g.deleteMe()
    grp = root.customGraphicsGroups.add(); grp.id = GID
    parts = []
    for o in root.allOccurrences:
        c = o.component
        if 'Reference' in o.fullPathName or not o.isVisible or c.name.startswith('zz ') or '/zz ' in o.fullPathName:
            continue
        bodies = [(b.name, b, 'brep') for b in c.bRepBodies] + [(b.name, b, 'mesh') for b in c.meshBodies]
        for name, b, t in bodies:
            px = b.createForAssemblyContext(o)
            if t == 'brep':
                calc = px.meshManager.createMeshCalculator()
                calc.setQuality(adsk.fusion.TriangleMeshQualityOptions.NormalQualityTriangleMesh)
                tm = calc.calculate()
            else:
                tm = px.displayMesh
            xyz = list(tm.nodeCoordinatesAsDouble)
            if not xyz:
                continue
            nrm = list(tm.normalVectorsAsDouble)
            idx = list(tm.nodeIndices)
            k = kind(c.name, name)
            m = grp.addMesh(adsk.fusion.CustomGraphicsCoordinates.create(xyz), idx, nrm, idx)
            r, g_, bl = COL[k]
            cc = adsk.core.Color.create(r, g_, bl, 255)
            m.color = adsk.fusion.CustomGraphicsBasicMaterialColorEffect.create(
                cc, cc, adsk.core.Color.create(50, 50, 50, 255), adsk.core.Color.create(0, 0, 0, 255), 25.0, 1.0)
            n = len(xyz) // 3
            cx = [sum(xyz[i::3]) / n for i in range(3)]
            lo = [min(xyz[i::3]) for i in range(3)]; hi = [max(xyz[i::3]) for i in range(3)]
            # principal axis (power iteration on the covariance)
            cov = [[0.0] * 3 for _ in range(3)]
            step = max(1, n // 400)
            for j in range(0, n, step):
                p = [xyz[3 * j + i] - cx[i] for i in range(3)]
                for a in range(3):
                    for bb in range(3):
                        cov[a][bb] += p[a] * p[bb]
            v = principal_axis(cov)
            parts.append(dict(key='%s / %s' % (c.name, name), comp=c.name, name=name, ent=m, c=cx, lo=lo, hi=hi, ax=v))
        for b in c.bRepBodies:
            b.isLightBulbOn = False
        for b in c.meshBodies:
            b.isLightBulbOn = False
    STATE['parts'] = parts
    hide_originals()
    app.activeViewport.refresh()
    return len(parts)


def hide_originals():
    app, d = design()
    root = d.rootComponent
    for o in root.occurrences:
        o.isLightBulbOn = False
    for i in range(root.customGraphicsGroups.count):
        g = root.customGraphicsGroups.item(i)
        g.isVisible = g.id == GID


def ensure_parts():
    if 'parts' not in STATE or not all(p['ent'].isValid for p in STATE['parts'][:3]):
        raise RuntimeError('run collect() first in this Fusion session')
    return STATE['parts']


def select(pattern, exclude=None):
    rx = re.compile(pattern, re.I); ex = re.compile(exclude, re.I) if exclude else None
    return [p for p in ensure_parts() if rx.search(p['key']) and not (ex and ex.search(p['key']))]


def set_offset(p, v):
    m = adsk.core.Matrix3D.create()
    if 'M' in p:
        m = adsk.core.Matrix3D.create(); m.setWithArray(p['M'])
    t = m.translation
    m.translation = adsk.core.Vector3D.create(t.x + v[0], t.y + v[1], t.z + v[2])
    p['ent'].transform = m


def fix_mesh_parts():
    """Mesh-body copies come in local coordinates: give them their occurrence's world transform."""
    app, d = design()
    occ = {o.component.name: o for o in d.rootComponent.allOccurrences}
    for p in ensure_parts():
        if not p['comp'].startswith('Harness'):
            continue
        M = occ[p['comp']].transform2
        p['M'] = list(M.asArray())
        def tr(q):
            pt = adsk.core.Point3D.create(*q); pt.transformBy(M); return [pt.x, pt.y, pt.z]
        p['c'] = tr(p['c'])
        a, b = tr(p['lo']), tr(p['hi'])
        p['lo'] = [min(a[i], b[i]) for i in range(3)]; p['hi'] = [max(a[i], b[i]) for i in range(3)]
        set_offset(p, [0, 0, 0])


PARKED = {}


def park_meshes(on=True):
    """Hidden mesh bodies still draw in this Fusion build: move their occurrences far away (and back)."""
    app, d = design()
    for o in d.rootComponent.allOccurrences:
        if o.component.meshBodies.count == 0:
            continue
        if on and o.fullPathName not in PARKED:
            PARKED[o.fullPathName] = list(o.transform2.asArray())
            m = o.transform2; t = m.translation
            m.translation = adsk.core.Vector3D.create(t.x + 5000, t.y, t.z); o.transform2 = m
        elif not on and o.fullPathName in PARKED:
            m = adsk.core.Matrix3D.create(); m.setWithArray(PARKED.pop(o.fullPathName)); o.transform2 = m


def set_opacity(p, a):
    """Re-colour a part's graphics at opacity a (1 = solid)."""
    if p.get('_op', 1.0) == a:
        return
    r, g_, bl = COL[kind(p['comp'], p['name'])]
    cc = adsk.core.Color.create(r, g_, bl, 255)
    p['ent'].color = adsk.fusion.CustomGraphicsBasicMaterialColorEffect.create(
        cc, cc, adsk.core.Color.create(50, 50, 50, 255), adsk.core.Color.create(0, 0, 0, 255), 25.0, a)
    p['_op'] = a


def unit(v):
    s = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / s for x in v]


def head_dir(p):
    """Unit axis vector pointing to a fastener's head (the end with more mesh: head, ball, knurl)."""
    a = p['ax']; mid = [(p['lo'][i] + p['hi'][i]) / 2 for i in range(3)]
    s = 1 if sum(a[i] * (p['c'][i] - mid[i]) for i in range(3)) >= 0 else -1
    return [s * x for x in a]


FASTENER = re.compile(r'(M\d+ x \d+|#4 x|ball stud|thumb screw|Clevis pin)', re.I)


def mate_bolt(p):
    """The fastener whose shank segment passes closest to p's centre."""
    best, bd = None, 1e9
    for q in ensure_parts():
        if q is p or not FASTENER.search(q['name']):
            continue
        a = q['ax']; d = [p['c'][i] - q['c'][i] for i in range(3)]
        half = abs(sum((q['hi'][i] - q['lo'][i]) * a[i] for i in range(3))) / 2
        t = max(-half, min(half, sum(a[i] * d[i] for i in range(3))))
        r = math.sqrt(sum((d[i] - t * a[i]) ** 2 for i in range(3)))
        if r < bd:
            best, bd = q, r
    return best


def direction(p, rule, center):
    """rule: 'axis' (own axis, away from center), 'out' (away from center), 'head' (fastener: in from its head
    side), 'nut' (in from the far end of the bolt it meets), ('host', parts) (own axis, away from the nearest
    host's centre), ('along', part[, sign]) or a fixed [x,y,z] in cm."""
    if rule == 'head':
        return head_dir(p)
    if rule == 'nut':
        b = mate_bolt(p)
        return [-x for x in head_dir(b)] if b else unit(p['ax'])
    if isinstance(rule, (list, tuple)) and rule and rule[0] == 'vec':
        hs = [head_dir(q) for q in rule[1]]
        sg = rule[2] if len(rule) > 2 else 1
        return unit([sg * sum(h[i] for h in hs) for i in range(3)])
    if isinstance(rule, (list, tuple)) and rule and rule[0] == 'host':
        h = min(rule[1], key=lambda q: sum((q['c'][i] - p['c'][i]) ** 2 for i in range(3)))
        a = p['ax']; d = [p['c'][i] - h['c'][i] for i in range(3)]
        s = 1 if sum(a[i] * d[i] for i in range(3)) >= 0 else -1
        return [s * x for x in a]
    if isinstance(rule, (list, tuple)) and rule and rule[0] == 'along':
        a = rule[1]['ax']; d = [p['c'][i] - center[i] for i in range(3)]
        s = 1 if sum(a[i] * d[i] for i in range(3)) >= 0 else -1
        if len(rule) > 2: s *= rule[2]
        return [s * x for x in a]
    if isinstance(rule, (list, tuple)):
        return unit(rule)
    d = [p['c'][i] - center[i] for i in range(3)]
    if rule == 'axis':
        a = p['ax']
        s = 1 if sum(a[i] * d[i] for i in range(3)) >= 0 else -1
        return [s * x for x in a]
    return unit(d)


def ease(t):
    return t * t * t * (t * (6 * t - 15) + 10)


def camera(vp, target, eye, ext):
    cam = vp.camera
    cam.isFitView = False
    cam.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    cam.target = adsk.core.Point3D.create(*target)
    cam.eye = adsk.core.Point3D.create(*eye)
    cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
    cam.viewExtents = ext
    vp.camera = cam


def offsets(groups, dirs, gi_now, t, dist):
    """Offset of every shown part at (group gi_now, progress t). A group is (parts, rule, dist[, opt]):
    opt 'at' = where the parts land (a staging spot away from the build, cm); rule 'move' carries parts that are
    already shown from where they are to opt 'to' (default: home)."""
    off = {}
    for gi, g in enumerate(groups[:gi_now + 1]):
        parts, rule, dd = g[:3]; opt = g[3] if len(g) > 3 else {}
        tt = 1.0 if gi < gi_now else t
        if rule == 'move':
            to = opt.get('to', [0, 0, 0])
            for p in parts:
                a = off.get(id(p), [0, 0, 0])
                off[id(p)] = [a[i] + (to[i] - a[i]) * tt for i in range(3)]
            continue
        at = opt.get('at', [0, 0, 0]); k = (dd or dist) * (1 - tt)
        for p in parts:
            dv = dirs[gi][id(p)]
            off[id(p)] = [at[i] + dv[i] * k for i in range(3)]
    return off


def step_frames(name, base, groups, view, nfly=10, hold=8, dist=12.0, w=900, h=700, start=0, count=None, frame_also=None):
    """base: parts shown assembled from the start. groups: see offsets(). view: (dir to eye [x,y,z], extent
    scale). Renders frames start..start+count (for batching)."""
    app, d = design()
    vp = app.activeViewport
    allp = [p for p in ensure_parts()]
    boxes = []
    for g in groups:
        at = (g[3] if len(g) > 3 else {}).get('at', [0, 0, 0])
        for q in g[0]:
            boxes.append(([q['lo'][i] + at[i] for i in range(3)], [q['hi'][i] + at[i] for i in range(3)]))
            boxes.append((q['lo'], q['hi']))
    for q in frame_also or []:
        boxes.append((q['lo'], q['hi']))
    lo = [min(b[0][i] for b in boxes) for i in range(3)]; hi = [max(b[1][i] for b in boxes) for i in range(3)]
    ctr = [(lo[i] + hi[i]) / 2 for i in range(3)]
    vdir, scale = view
    dz = unit(vdir); up = [0, 0, 1]
    rx = unit([up[1] * dz[2] - up[2] * dz[1], up[2] * dz[0] - up[0] * dz[2], up[0] * dz[1] - up[1] * dz[0]])
    ry = [dz[1] * rx[2] - dz[2] * rx[1], dz[2] * rx[0] - dz[0] * rx[2], dz[0] * rx[1] - dz[1] * rx[0]]
    corners = [[(lo, hi)[(k >> i) & 1][i] for i in range(3)] for k in range(8)]
    sx = max(abs(sum((c[i] - ctr[i]) * rx[i] for i in range(3))) for c in corners) * 2
    sy = max(abs(sum((c[i] - ctr[i]) * ry[i] for i in range(3))) for c in corners) * 2
    h = int(round(w * vp.height / vp.width))
    span = max(sy, sx * vp.height / vp.width)
    eye = [ctr[i] + dz[i] * 300 for i in range(3)]
    camera(vp, ctr, eye, span * scale * ZOOM_OUT)
    total = len(groups) * nfly + hold
    dirs = []
    for parts, rule, dd, *_ in groups:
        c = [sum(p['c'][i] for p in parts) / len(parts) for i in range(3)] if parts else [0, 0, 0]
        dirs.append({id(p): (direction(p, rule, c) if rule != 'move' else None) for p in parts})
    baseids = {id(p) for p in base}
    os.makedirs(OUT, exist_ok=True)
    end = total if count is None else min(total, start + count)
    for f in range(start, end):
        gi_now = min(f // nfly, len(groups) - 1)
        t = 1.0 if f >= len(groups) * nfly else ease((f % nfly) / (nfly - 1))
        off = offsets(groups, dirs, gi_now, t, dist)
        ghost = {id(q) for q in (groups[gi_now][3].get('ghost', []) if groups and len(groups[gi_now]) > 3 else [])}
        if f >= len(groups) * nfly:
            ghost = set()
        for p in allp:
            set_opacity(p, 0.25 if id(p) in ghost else 1.0)
        for p in allp:
            if id(p) in off:
                p['ent'].isVisible = True; set_offset(p, off[id(p)])
            elif id(p) in baseids:
                p['ent'].isVisible = True; set_offset(p, [0, 0, 0])
            else:
                p['ent'].isVisible = False
        vp.refresh()
        vp.saveAsImageFile(os.path.join(OUT, '%s_%03d.png' % (name, f)), w, h)
    return total, end


def still(name, parts, view, w=1200):
    """One frame of the given parts, assembled."""
    return step_frames(name, parts, [], view, nfly=1, hold=1, w=w, frame_also=parts)


def restore():
    park_meshes(False)
    app, d = design()
    root = d.rootComponent
    for i in range(root.customGraphicsGroups.count - 1, -1, -1):
        g = root.customGraphicsGroups.item(i)
        if g.id == GID: g.deleteMe()
        else: g.isVisible = True
    for o in root.occurrences:
        o.isLightBulbOn = True
    for o in root.allOccurrences:
        for b in o.component.bRepBodies: b.isLightBulbOn = True
        for b in o.component.meshBodies: b.isLightBulbOn = True
    app.activeViewport.refresh()


def steps():
    """Assembly steps: (name, base parts, [(parts, rule, dist_cm)], view)."""
    S = select
    frame = S(r'^(Bottom node|Mid node|Top node|Abduction mount blocks|PVC pipes|HW frame)')
    shoulder = S(r'^(Yoke|Abduction sleeve|HW abd|Upper-arm link|Flexion axle sleeve|HW flex)')
    elbow = S(r'^Elbow concept')
    E = lambda pat, ex=None: S(r'^Elbow concept.* / .*' + pat, ex)
    pvc = S(r'^PVC'); backbone = [p for p in pvc if abs(p['ax'][2]) > 0.9]; bracing = [p for p in pvc if p not in backbone]
    fa_pipe = E(r'Forearm unit: PVC')
    ua_pipe = E(r'Upper-arm unit: PVC')
    st = {}
    st['1-elbow'] = ([], [
        (E(r'Upper-arm unit: upper arm'), 'out', 0.01),
        (E(r'Hardware.*insert'), 'axis', 2.5),
        (E(r'6806-2RS bearing'), 'axis', 6),
        (E(r'Forearm unit: forearm: near ring'), ('along', fa_pipe[0]), 10),
        (E(r'Forearm unit: M3 heat-set'), 'axis', 2.5),
        (E(r'bearing axle'), 'axis', 6),
        (E(r'Forearm unit: M3 x 8'), 'axis', 4),
        (E(r': cover \(print'), 'axis', 5),
        (E(r'Hardware.*M3 x 8'), 'axis', 4),
        (fa_pipe, 'axis', 14),
        (E(r'far ring'), ('along', fa_pipe[0]), 10),
        (E(r'Wrist cuff'), 'out', 8),
        (ua_pipe, 'axis', 14),
    ], ([0.45, -1.0, 0.25], 1.15))
    st['2-frame'] = ([], [
        (S(r'^Bottom node / Bottom node R'), [0, -1, 0], 10),
        (S(r'^Bottom node / Bottom node L'), [0, 1, 0], 10),
        (S(r'^HW frame.*insert'), 'axis', 2.5),
        (S(r'^Bottom node splice'), [-1, 0, 0], 8),
        (S(r'^HW frame.*M3 x 8'), 'axis', 3),
        (backbone, 'axis', 20),
        (S(r'^Mid node'), [0, 0, 1], 25),
        (S(r'^Top node'), [0, 0, 1], 15),
        (bracing, 'axis', 10),
        (S(r'^Abduction mount blocks'), 'out', 10),
    ], ([-1.0, -0.45, 0.35], 1.1))
    st['3-shoulder'] = (frame, [
        (S(r'^HW abd.*6806'), 'axis', 6),
        (S(r'^Abduction sleeve'), 'axis', 10),
        (S(r'^Yoke'), [1, 0, 0], 8),
        (S(r'^HW abd.*M8 x'), 'axis', 12),
        (S(r'^HW abd.*washer'), 'axis', 5),
        (S(r'^HW abd.*nyloc'), 'axis', 5),
        (S(r'^HW flex.*6808'), 'axis', 6),
        (S(r'^Flexion axle sleeve'), ('vec', S(r'^HW flex.*M8 x')), 8),
        (S(r'^HW flex.*nyloc'), 'axis', 6),
        (S(r'^Upper-arm link'), [0, -1, 0], 10),
        (S(r'^HW flex.*M8 x'), 'axis', 10),
    ], ([-0.7, -1.0, 0.55], 1.25))
    st['4-join'] = (frame + shoulder, [(elbow, ('along', ua_pipe[0], -1), 14)], ([0.35, -1.0, 0.2], 1.3), S(r'^(Upper-arm link|Yoke)'))
    st['5-harness'] = (frame + shoulder + elbow, [(S(r'^Harness'), 'out', 4)], ([0.8, -0.8, 0.35], 1.1), frame + shoulder + elbow)
    return st


def inbox(parts, hosts, tol=0.05):
    """Parts whose centre lies inside the hosts' combined bounding box."""
    lo = [min(h['lo'][i] for h in hosts) - tol for i in range(3)]; hi = [max(h['hi'][i] for h in hosts) + tol for i in range(3)]
    return [p for p in parts if all(lo[i] <= p['c'][i] <= hi[i] for i in range(3))]


def near(p, cands):
    return min(cands, key=lambda q: sum((q['c'][i] - p['c'][i]) ** 2 for i in range(3)))


def steps_v3():
    """Assembly steps for the v3b girdle + shoulder rest build (see docs/ASSEMBLY.md). Hardware comes in from
    the side it is really fitted from; sub-assemblies are built at a staging spot, then carried into place."""
    S = select
    frame_l = S(r'^(Bottom node|Mid node|Top node|Abduction mount blocks|PVC pipes|HW frame|Back pad)')
    pvc = S(r'^PVC'); backbone = [p for p in pvc if abs(p['ax'][2]) > 0.9]; bracing = [p for p in pvc if p not in backbone]
    tower = S(r'^Shoulder tower'); thw = lambda pat: S(r'^Tower HW.* / .*(?:' + pat + ')')
    up, dn = [0, 0, 1], [0, 0, -1]
    vert = lambda ps: [p for p in ps if abs(p['ax'][2]) > 0.8]
    horz = lambda ps: [p for p in ps if abs(p['ax'][2]) <= 0.8]
    st = {}
    st['2-frame'] = ([], [
        (S(r'^Bottom node / Bottom node R'), [0, -1, 0], 10),
        (S(r'^Bottom node / Bottom node L'), [0, 1, 0], 10),
        (S(r'^HW frame.*insert'), ('host', S(r'^Bottom node / ')), 2.5),
        (S(r'^Bottom node splice'), [-1, 0, 0], 8),
        (S(r'^HW frame.*M3 x 8'), 'head', 3),
        (backbone, 'axis', 20),
        (S(r'^Mid node'), up, 25),
        (S(r'^Top node'), up, 15),
        (bracing, 'axis', 10),
        (S(r'^Abduction mount blocks'), 'out', 10),
        (S(r'^Back pad'), [1, 0, 0], 6),
    ], ([-1.0, -0.45, 0.35], 1.1))

    # 3: the tower's hidden nuts go in while it is still off the frame, then it slides down
    T = [0, 0, 14]
    m6 = S(r'^Rest HW.* / M6 hex nut'); t_strut_nut = thw(r'M6 hex nut')
    st['3-tower'] = (frame_l, [
        (thw(r'insert'), ('host', S(r'^Top node')), 3),
        (tower, up, 10, {'at': T}),
        (m6 + t_strut_nut, 'nut', 5, {'at': T, 'ghost': tower}),
        (tower + m6 + t_strut_nut, 'move', None),
        (thw(r'M3 x 8'), 'head', 4),
        (thw(r'#4'), 'head', 4),
    ], ([0.9, -0.9, 0.5], 1.2), tower)

    # 4: links drop into the forks from above / below; the carriage gets its two hidden nuts, then rises in
    lu, ll = S(r'^Lift link upper / '), S(r'^Lift link lower / ')
    lub, llb = S(r'^Lift link upper HW'), S(r'^Lift link lower HW')
    carr = S(r'^Lift carriage'); chw = lambda pat: S(r'^Carriage HW.* / .*(?:' + pat + ')')
    t_piv, t_nut = thw(r'M8 x 55'), thw(r'nyloc nut \(buy\)( \(1\))?$')
    c_bolts = chw(r'M8 x 55'); s0_bolt = vert(c_bolts); c_piv = horz(c_bolts)
    c_nuts = chw(r'nyloc'); c_strut_nut = chw(r'M6 hex nut')
    s0_nut = [p for p in c_nuts if p not in c_strut_nut and abs(mate_bolt(p)['ax'][2]) > 0.8]
    c_piv_nut = [p for p in c_nuts if p not in s0_nut + c_strut_nut]
    studs = thw(r'M6 x 16') + chw(r'M6 x 16')
    strut = S(r'^Gas spring')
    U, L, C = [0, 0, 6], [0, 0, -6], [0, 0, -9]
    st['4-lift'] = (frame_l + tower + thw(r'(insert|M3 x 8|#4)') + m6 + t_strut_nut, [
        (lu, up, 4, {'at': U}),
        (lub, ('host', lu), 3, {'at': U}),
        (ll, dn, 4, {'at': L}),
        (llb, ('host', ll), 3, {'at': L}),
        (lu + lub + ll + llb, 'move', None),
        (t_piv, 'head', 8, {'ghost': lu + ll + tower}),
        (t_nut, 'nut', 5),
        (carr, dn, 4, {'at': C}),
        (s0_nut + c_strut_nut, 'nut', 5, {'at': C, 'ghost': carr}),
        (carr + s0_nut + c_strut_nut, 'move', None),
        (c_piv, 'head', 8, {'ghost': lu + ll + carr}),
        (c_piv_nut, 'nut', 5),
        (strut, ('vec', studs), 5),
        (studs, 'head', 5, {'ghost': strut}),
    ], ([0.9, -1.0, 0.45], 1.0), tower + carr)

    # 4b: close-up of the strut going on (eyelets into the forks, then the thumb screws)
    st['4b-strut'] = ([p for p in st['4-lift'][0] + lu + lub + ll + llb + carr + t_piv + t_nut + c_piv + c_piv_nut + s0_nut + c_strut_nut], [
        (strut, ('vec', studs), 4),
        (studs, 'head', 4, {'ghost': strut}),
    ], ([0.9, -0.6, 0.3], 0.9), strut + studs)

    # 5: each SCARA link is built below, then lifted into place and bolted
    l1t, l1l = S(r'^SCARA link 1 / .*tray'), S(r'^SCARA link 1 / .*lid')
    l2t, l2l = S(r'^SCARA link 2 / .*tray'), S(r'^SCARA link 2 / .*lid')
    l1hw = lambda pat: S(r'^SCARA link 1 HW.* / .*(?:' + pat + ')')
    l2hw = lambda pat: S(r'^SCARA link 2 HW.* / .*(?:' + pat + ')')
    spool = S(r'^Elbow spool'); end = S(r'^SCARA end plate'); ehw = lambda pat: S(r'^End plate HW.* / .*(?:' + pat + ')')
    inner = lambda ps: [p for p in ps if re.search(r'pulley|inner-ring', p['name'])]
    stack1 = inbox(inner(chw(r'.') + spool), l1t + l1l)
    stack2 = inbox(inner(spool + ehw(r'.')), l2t + l2l)
    brg_t1 = [p for p in l1hw(r'608') if near(p, l1t + l1l) in l1t]; brg_l1 = [p for p in l1hw(r'608') if p not in brg_t1]
    brg_t2 = [p for p in l2hw(r'608') if near(p, l2t + l2l) in l2t]; brg_l2 = [p for p in l2hw(r'608') if p not in brg_t2]
    lid_dir = lambda lid, tray: [0, 0, 1 if lid[0]['c'][2] > tray[0]['c'][2] else -1]
    c_shim = chw(r'nut spacer')
    sp = lambda pat: [p for p in spool if re.search(pat, p['name'])]
    e_nut, e_bolt = ehw(r'nyloc'), ehw(r'M8 x 55')
    e_shims = ehw(r'nut spacer|head spacer')
    A, B, E = [0, 0, -6], [0, 0, -6], [0, 0, -5]
    link1 = l1t + brg_t1 + l1hw(r'insert') + stack1 + l1hw(r'belt') + l1l + brg_l1 + l1hw(r'M3 x 12')
    link2 = l2t + brg_t2 + l2hw(r'insert') + stack2 + l2hw(r'belt') + l2l + brg_l2 + l2hw(r'M3 x 12')
    girdle_base = frame_l + tower + lu + ll + lub + llb + carr + strut + thw(r'.') + m6 + \
        [p for p in chw(r'.') if p not in stack1 + c_shim + s0_bolt]
    st['5-scara'] = (girdle_base, [
        (l1t, dn, 3, {'at': A}),
        (brg_t1, ('host', l1t), 3, {'at': A}),
        (l1hw(r'insert'), ('host', l1t), 3, {'at': A}),
        (stack1, lid_dir(l1l, l1t), 5, {'at': A}),
        (l1hw(r'belt'), lid_dir(l1l, l1t), 4, {'at': A}),
        (l1l + brg_l1, lid_dir(l1l, l1t), 5, {'at': A}),
        (l1hw(r'M3 x 12'), 'head', 4, {'at': A}),
        (link1, 'move', None),
        (c_shim, [0, -1, 0], 4),
        (s0_bolt, 'head', 8, {'ghost': l1t + l1l + carr}),
        (l2t, dn, 3, {'at': B}),
        (brg_t2, ('host', l2t), 3, {'at': B}),
        (l2hw(r'insert'), ('host', l2t), 3, {'at': B}),
        (stack2, lid_dir(l2l, l2t), 5, {'at': B}),
        (l2hw(r'belt'), lid_dir(l2l, l2t), 4, {'at': B}),
        (l2l + brg_l2, lid_dir(l2l, l2t), 5, {'at': B}),
        (l2hw(r'M3 x 12'), 'head', 4, {'at': B}),
        (link2, 'move', None),
        (sp(r'link spacer'), [0, -1, 0], 4),
        (sp(r'head spacer'), ('vec', sp(r'M8 x 100')), 6),
        (sp(r'M8 x 100'), 'head', 10, {'ghost': l1t + l1l + l2t + l2l}),
        (sp(r'nut spacer') + sp(r'nyloc'), ('vec', sp(r'M8 x 100'), -1), 5),
        (end, dn, 3, {'at': E}),
        (e_nut, up, 4, {'at': E, 'ghost': end}),
        (end + e_nut, 'move', None),
        (ehw(r'nut spacer'), [0, -1, 0], 4),
        (ehw(r'head spacer'), ('vec', e_bolt), 6),
        (e_bolt, 'head', 8, {'ghost': l2t + l2l + end}),
    ], ([0.9, -1.0, 0.45], 1.1), l1t + l2t + end + carr + tower)

    shoulder = S(r'^(Yoke|Abduction sleeve|HW abd|Upper-arm link|Flexion axle sleeve|HW flex)')
    girdle = girdle_base + link1 + link2 + c_shim + s0_bolt + spool + end + ehw(r'.')
    st['6-hinge'] = (frame_l + girdle, [
        (S(r'^HW abd.*6806'), ('host', S(r'^Abduction sleeve')), 6),
        (S(r'^Abduction sleeve'), 'axis', 10),
        (S(r'^Yoke'), [1, 0, 0], 8),
        (S(r'^HW abd.*M8 x'), 'head', 12, {'ghost': end + S(r'^Yoke') + S(r'^Abduction sleeve')}),
        (S(r'^HW abd.*washer'), 'nut', 5),
        (S(r'^HW abd.*nyloc'), 'nut', 5),
        (S(r'^HW flex.*6808'), ('host', S(r'^Flexion axle sleeve')), 6),
        (S(r'^Flexion axle sleeve'), ('vec', S(r'^HW flex.*M8 x')), 8),
        (S(r'^Upper-arm link'), [0, -1, 0], 6, {'at': [0, -10, 0]}),
        (S(r'^HW flex.*nyloc'), 'nut', 5, {'at': [0, -10, 0], 'ghost': S(r'^Upper-arm link')}),
        (S(r'^(Upper-arm link|HW flex.*nyloc)'), 'move', None),
        (S(r'^HW flex.*M8 x'), 'head', 10, {'ghost': S(r'^(Yoke|Upper-arm link)')}),
    ], ([-0.7, -1.0, 0.55], 1.25), end + shoulder)

    # 7: chain built piece by piece; each pin goes in as soon as its piece is on
    rhw = lambda pat: S(r'^Rest HW.* / .*(?:' + pat + ')')
    brk = S(r'^Rest bracket'); thumb = rhw(r'M6 x 65')
    pieces = [S(r'^Rest root arm'), S(r'^Rest blade 1'), S(r'^Rest blade 2'), S(r'^Rest blade 3')]
    pins = sorted(rhw(r'Clevis'), key=lambda p: sum((p['c'][i] - brk[0]['c'][i]) ** 2 for i in range(3)))
    clips = rhw(r'R-clip / split')
    rest_groups = [(brk, ('vec', thumb), 6), (thumb, 'head', 5)]
    for i, pc in enumerate(pieces):
        rest_groups += [(pc, [1, 0, 0.3], 6), ([pins[i]], 'head', 7), ([near(pins[i], clips)], ('host', [pins[i]]), 3)]
    rest = brk + [q for pc in pieces for q in pc]
    rest_groups += [(S(r'^Rest (hook|foam)'), dn, 4), (S(r'^Rest buckle'), [1, 0, -0.5], 5)]
    st['7-rest'] = (frame_l + girdle, rest_groups, ([0.5, -1.0, 0.8], 1.15), rest)
    elbow = S(r'^Elbow concept')
    ua_pipe = S(r'^Elbow concept.* / .*Upper-arm unit: PVC')
    rest_all = rest + S(r'^Rest (HW|hook|foam|buckle)')
    st['8-join'] = (frame_l + girdle + shoulder + rest_all,
                    [(elbow, ('along', ua_pipe[0], -1), 14)], ([0.35, -1.0, 0.2], 1.3), shoulder + elbow)
    st['all'] = frame_l + girdle + shoulder + rest_all + elbow
    return st


def migrate():
    """Move the part meshes into a new empty design (stale graphics in the shoulder doc can't be cleared)."""
    app, d = design()
    data = []
    for p in ensure_parts():
        m = p['ent']
        xyz = list(m.coordinates.coordinates)
        if 'M' in p:
            M = adsk.core.Matrix3D.create(); M.setWithArray(p['M'])
            for j in range(0, len(xyz), 3):
                pt = adsk.core.Point3D.create(*xyz[j:j + 3]); pt.transformBy(M); xyz[j:j + 3] = [pt.x, pt.y, pt.z]
            nr = list(m.normalVectors)
            R = M.copy(); R.translation = adsk.core.Vector3D.create(0, 0, 0)
            for j in range(0, len(nr), 3):
                v = adsk.core.Vector3D.create(*nr[j:j + 3]); v.transformBy(R); nr[j:j + 3] = [v.x, v.y, v.z]
        else:
            nr = list(m.normalVectors)
        data.append((p, xyz, list(m.vertexIndexList), nr, list(m.normalIndexList) or list(m.vertexIndexList)))
    park_meshes(False)
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = 'asm render (temp)' if hasattr(doc, 'name') and False else doc.name
    d2 = adsk.fusion.Design.cast(app.activeProduct)
    grp = d2.rootComponent.customGraphicsGroups.add(); grp.id = GID
    for p, xyz, idx, nr, nidx in data:
        k = kind(p['comp'], p['name'])
        e = grp.addMesh(adsk.fusion.CustomGraphicsCoordinates.create(xyz), idx, nr, nidx)
        r, g_, bl = COL[k]
        cc = adsk.core.Color.create(r, g_, bl, 255)
        e.color = adsk.fusion.CustomGraphicsBasicMaterialColorEffect.create(
            cc, cc, adsk.core.Color.create(50, 50, 50, 255), adsk.core.Color.create(0, 0, 0, 255), 25.0, 1.0)
        p['ent'] = e
        p.pop('M', None)
    app.activeViewport.refresh()
    return len(data)


def render(name, nfly=10, hold=8, w=1600, start=0, count=None, prefix='', v3=True):
    st = (steps_v3() if v3 else steps())[name]
    if name == 'all':
        return still(prefix + 'all', st, ([0.9, -1.0, 0.35], 1.05 / ZOOM_OUT), w=w)
    return step_frames(prefix + name, st[0], st[1], st[2], nfly=nfly, hold=hold, w=w, start=start, count=count,
                       frame_also=st[3] if len(st) > 3 else None)
