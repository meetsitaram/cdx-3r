"""Render animation frames of the CDX-3R joints in Fusion (run inside Fusion via MCP)."""
import os, math
import adsk.core, adsk.fusion
import fxlib as fx
import shoulder as sh

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'frames')
CAM = ((0, -15, 118), (0 + 95, -15 - 200, 118 + 40), 110)
FLEX_PARTS = ('Upper-arm link', 'Flexion axle sleeve', 'HW flex (buy)')


def about(axis, deg, c):
    R = fx.rot(axis, deg)
    return fx.matrix(R, fx.sub(c, fx.mat_vec(R, c)))


def occs():
    root = fx.design.rootComponent
    by = {o.component.name: o for o in root.allOccurrences}
    abd = next(o for o in root.allOccurrences if o.component.name.startswith('Abduction side'))
    elbow = next(o for o in root.allOccurrences if o.component.name.startswith('Elbow concept B'))
    top = next(o for o in root.occurrences if o.component.name == sh.TOP)
    return by, abd, elbow, top


def pose(abd_deg, flex_deg):
    """Set world transforms: abduction about scan X through GH, flexion about scan Z through GH."""
    by, abd, elbow, top = occs()
    GH = sh.GH
    W = about('x', -abd_deg, GH)
    W.transformBy(top.transform2)
    abd.transform2 = W
    F = about('z', flex_deg, GH)
    for name in FLEX_PARTS:
        m = F.copy(); m.transformBy(W)
        by[name].transform2 = m
    E = sh.elbow_matrix(); E.transformBy(F); E.transformBy(W)
    elbow.transform2 = E


def camera(vp, target, eye, ext):
    cam = vp.camera
    cam.isFitView = False
    cam.target = adsk.core.Point3D.create(*target)
    cam.eye = adsk.core.Point3D.create(*eye)
    cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
    cam.viewExtents = ext
    vp.camera = cam


def shoulder_frames(seq, start, w=720, h=560):
    fx.init()
    os.makedirs(OUT, exist_ok=True)
    app = adsk.core.Application.get()
    vp = app.activeViewport
    camera(vp, CAM[0], CAM[1], CAM[2])
    n = start
    for a, f in seq:
        pose(a, f)
        vp.refresh()
        vp.saveAsImageFile(os.path.join(OUT, 's%03d.png' % n), w, h)
        n += 1
    return n


def elbow_frames(degs, start, w=720, h=560):
    app = adsk.core.Application.get()
    ed = next(d for d in app.documents if d.name == 'CDX-3R elbow concepts')
    ed.activate()
    des = adsk.fusion.Design.cast(app.activeProduct)
    j = next(jj for o in des.rootComponent.allOccurrences for jj in o.component.asBuiltJoints if jj.name == 'elbow flexion')
    mot = adsk.fusion.RevoluteJointMotion.cast(j.jointMotion)
    vp = app.activeViewport
    n = start
    for dg in degs:
        mot.rotationValue = math.radians(dg)
        vp.refresh()
        vp.saveAsImageFile(os.path.join(OUT, 'e%03d.png' % n), w, h)
        n += 1
    return n


def split_elbow():
    """Replace the static elbow copy by two temporary components (upper-arm side / forearm side), copied at
    elbow flexion 0, so the forearm can be posed about the elbow axis (concept X through the origin)."""
    fx.init()
    app = adsk.core.Application.get()
    root = fx.design.rootComponent
    abd = next(o for o in root.allOccurrences if o.component.name.startswith('Abduction side'))
    for o in list(abd.component.occurrences):
        if o.component.name.startswith(('Elbow concept B', 'ANIM ')):
            o.deleteMe()
    ed = next(d for d in app.documents if d.name == sh.ELBOW_DOC)
    edes = adsk.fusion.Design.cast(ed.products.itemByProductType('DesignProductType'))
    j = next(jj for o in edes.rootComponent.allOccurrences for jj in o.component.asBuiltJoints if jj.name == 'elbow flexion')
    adsk.fusion.RevoluteJointMotion.cast(j.jointMotion).rotationValue = 0
    tb = adsk.fusion.TemporaryBRepManager.get()
    groups = {'ANIM elbow UA': [], 'ANIM elbow FA': []}
    for o in edes.rootComponent.allOccurrences:
        if not o.fullPathName.startswith('B - ') or o.component.bRepBodies.count == 0:
            continue
        key = 'ANIM elbow FA' if o.component.name.startswith(('Forearm', 'Wrist cuff')) else 'ANIM elbow UA'
        for b in o.component.bRepBodies:
            if b.name != 'arm ghost' and b.isVisible:
                groups[key].append((b.name, tb.copy(b.createForAssemblyContext(o))))
    for key, items in groups.items():
        occ = abd.component.occurrences.addNewComponent(sh.elbow_matrix())
        occ.component.name = key
        fx.snapshot()
        comp = occ.component
        bf = comp.features.baseFeatures.add(); bf.startEdit()
        for _, t in items:
            comp.bRepBodies.add(t, bf)
        bf.finishEdit()
        for (name, _), nb in zip(items, list(comp.bRepBodies)):
            col = sh.HW if '(buy)' in name else ('#e9eef2' if 'PVC' in name else ('#8fa3b3' if key.endswith('FA') else sh.PRINT))
            if '6806' in name: col = '#d4a017'
            nb.appearance = fx.appearance(col)
    return {k: len(v) for k, v in groups.items()}


def pose3(abd_deg, flex_deg, elb_deg):
    by, abd, _, top = occs2()
    GH = sh.GH
    W = about('x', -abd_deg, GH); W.transformBy(top.transform2)
    abd.transform2 = W
    F = about('z', flex_deg, GH)
    for name in FLEX_PARTS:
        m = F.copy(); m.transformBy(W); by[name].transform2 = m
    E = sh.elbow_matrix(); E.transformBy(F); E.transformBy(W)
    by['ANIM elbow UA'].transform2 = E
    Ef = fx.matrix(fx.rot('x', elb_deg)); Ef.transformBy(E)
    by['ANIM elbow FA'].transform2 = Ef


def occs2():
    root = fx.design.rootComponent
    by = {o.component.name: o for o in root.allOccurrences}
    abd = next(o for o in root.allOccurrences if o.component.name.startswith('Abduction side'))
    top = next(o for o in root.occurrences if o.component.name == sh.TOP)
    return by, abd, None, top


def combo_frames(seq, start, w=760, h=600):
    fx.init()
    os.makedirs(OUT, exist_ok=True)
    vp = adsk.core.Application.get().activeViewport
    camera(vp, CAM[0], CAM[1], CAM[2])
    n = start
    for a, f, e in seq:
        pose3(a, f, e)
        vp.refresh()
        vp.saveAsImageFile(os.path.join(OUT, 'c%03d.png' % n), w, h)
        n += 1
    return n


def frames2(seq, cams, start, prefix, w=720, h=720):
    """seq: [(abd, flex, elbow)], cams: [(target, eye, ext)] per frame."""
    fx.init()
    os.makedirs(OUT, exist_ok=True)
    vp = adsk.core.Application.get().activeViewport
    n = start
    for (a, f, e), (t, ey, ext) in zip(seq, cams):
        pose3(a, f, e)
        camera(vp, t, ey, ext)
        vp.refresh()
        vp.saveAsImageFile(os.path.join(OUT, '%s%03d.png' % (prefix, n)), w, h)
        n += 1
    return n


def cam_frames(cams, start, prefix, w=720, h=720):
    """Camera-only frames: the model stays as it is (rest pose, arm visible)."""
    fx.init()
    vp = adsk.core.Application.get().activeViewport
    n = start
    for t, ey, ext in cams:
        camera(vp, t, ey, ext)
        vp.refresh()
        vp.saveAsImageFile(os.path.join(OUT, '%s%03d.png' % (prefix, n)), w, h)
        n += 1
    return n


ARM = {}


def add_arm_meshes():
    """Draw the split scanned arm (scan pose) as two custom-graphics meshes; hide the static arm."""
    import json
    fx.init()
    root = fx.design.rootComponent
    g = next(root.customGraphicsGroups.item(i) for i in range(root.customGraphicsGroups.count)
             if root.customGraphicsGroups.item(i).id == 'scan reference (smooth)')
    g.item(1).isVisible = False                       # the static (rest-pose) right arm
    for i in range(root.customGraphicsGroups.count - 1, -1, -1):
        if root.customGraphicsGroups.item(i).id == 'anim arm':
            root.customGraphicsGroups.item(i).deleteMe()
    ga = root.customGraphicsGroups.add(); ga.id = 'anim arm'
    data = json.load(open(os.path.join(os.path.dirname(OUT), 'arm_split.json')))
    col = adsk.core.Color.create(214, 170, 150, 255)
    for k in ('ua', 'fa'):
        d = data[k]
        coords = adsk.fusion.CustomGraphicsCoordinates.create([x / 10.0 for x in d['v']])
        m = ga.addMesh(coords, d['f'], d['n'], d['f'])
        m.color = adsk.fusion.CustomGraphicsBasicMaterialColorEffect.create(col, col, adsk.core.Color.create(40, 40, 40, 255),
                                                                          adsk.core.Color.create(0, 0, 0, 255), 20.0, 0.75)
        ARM[k] = m
    return len(ARM)


def arm_meshes():
    if not ARM or not all(v.isValid for v in ARM.values()):
        root = fx.design.rootComponent
        ga = next(root.customGraphicsGroups.item(i) for i in range(root.customGraphicsGroups.count)
                  if root.customGraphicsGroups.item(i).id == 'anim arm')
        ARM['ua'], ARM['fa'] = ga.item(0), ga.item(1)
    return ARM


def pose_all(a, f, e):
    """Exo (pose3) + scanned arm: upper arm follows the shoulder, forearm also the elbow."""
    pose3(a, f, e)
    _, _, _, top = occs2()
    GH = sh.GH
    W = about('x', -a, GH); W.transformBy(top.transform2)
    F = about('z', f, GH)
    UA = F.copy(); UA.transformBy(W)
    Em = sh.elbow_matrix()
    Einv = Em.copy(); Einv.invert()
    B = Einv.copy()                                   # scan -> concept, bend about concept X, back to scan
    B.transformBy(fx.matrix(fx.rot('x', e - sh.scan_elbow_flex())))
    B.transformBy(Em)
    FA = B.copy(); FA.transformBy(UA)
    m = arm_meshes()
    m['ua'].transform = UA
    m['fa'].transform = FA


def single_frames(seq, cams, start, prefix='s', w=1280, h=720):
    fx.init()
    vp = adsk.core.Application.get().activeViewport
    n = start
    for (a, f, e), (t, ey, ext) in zip(seq, cams):
        pose_all(a, f, e)
        camera(vp, t, ey, ext)
        vp.refresh()
        vp.saveAsImageFile(os.path.join(OUT, '%s%03d.png' % (prefix, n)), w, h)
        n += 1
    return n
