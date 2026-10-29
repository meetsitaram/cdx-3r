"""Wrist ring v2 latch for the assembly guide: the cuff open, pull the plunger's ring, swing the cuff shut, let go and the
pin drops into the cuff's knuckle. Run in Fusion with "CDX-3R elbow concepts" active:

    import wrist_latch_anim; wrist_latch_anim.frames(out_dir)

Only the wrist ring, the cuff, the plunger, its nut and the hinge dowel are shown (bodies hidden). The plunger is a body
inside the forearm unit, so a copy of it goes into a temporary component that can be lifted; the original is hidden
meanwhile. The cuff swings on its own joint. Nothing is saved: everything is put back at the end."""
import os

import adsk.core
import adsk.fusion

import concepts

PULL = 5.0                                   # mm: the pin lifts clear of the cuff's knuckle
C1 = '1. Cuff open (it swings on the 4 mm dowel on the far side)'
C2 = '2. Pull the plunger\'s ring: its pin lifts out of the way'
C3 = '3. Swing the cuff shut, still holding the ring'
C4 = '4. Let go: the spring pushes the pin down into the cuff\'s knuckle'
C5 = 'Locked. To open: pull the ring and swing the cuff out'
SEQ = ([(80, 0, C1)] * 2 + [(80, PULL, C2)] * 2 + [(a, PULL, C3) for a in (60, 40, 20, 8, 0)] +
       [(0, 0, C4)] * 2 + [(0, 0, C5)] * 3)
VIEW = (1.0, 0.9, 0.55)                      # eye direction: from the latch side (+X), in front (+Y), above (+Z)


def frames(out_dir, size=(1100, 800)):
    a = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(a.activeProduct)
    vp = a.activeViewport
    root = d.rootComponent
    occs = [o for o in root.allOccurrences if 'B - ' in o.fullPathName]
    fa = next(o for o in occs if o.component.name == 'Forearm unit')
    cuff = next(o for o in occs if o.component.name.startswith('Wrist cuff'))
    joint = next(j for o in [root] + [x.component for x in root.allOccurrences] for j in o.asBuiltJoints
                 if j.occurrenceOne and j.occurrenceOne.component == cuff.component)
    rev = adsk.fusion.RevoluteJointMotion.cast(joint.jointMotion)
    keep = ('far ring', 'wrist cuff', 'index plunger', 'M8 lock nut', 'hinge pin 4 x 25')
    hidden = []
    for o in root.allOccurrences:
        for b in o.component.bRepBodies:
            if b.isLightBulbOn and not b.name.startswith(keep):
                b.isLightBulbOn = False
                hidden.append(b)
    for b in root.bRepBodies:
        if b.isLightBulbOn:
            b.isLightBulbOn = False
            hidden.append(b)
    folders = []                                     # joint, sketch and construction glyphs: off (they spoil the fit)
    for c in [root] + [o.component for o in root.allOccurrences]:
        for attr in ('isJointsFolderLightBulbOn', 'isSketchFolderLightBulbOn', 'isConstructionFolderLightBulbOn'):
            if getattr(c, attr, False):
                setattr(c, attr, False)
                folders.append((c, attr))
    plunger = next(b for b in fa.component.bRepBodies if b.name.startswith('index plunger'))
    tmp = adsk.fusion.TemporaryBRepManager.get().copy(plunger.createForAssemblyContext(fa))
    anim = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    anim.component.name = 'ANIM plunger'
    bf = anim.component.features.baseFeatures.add()
    bf.startEdit()
    anim.component.bRepBodies.add(tmp, bf)
    bf.finishEdit()
    anim.component.bRepBodies.item(0).appearance = plunger.appearance
    plunger.isLightBulbOn = False
    v0 = rev.rotationValue
    s = _open_sign(rev, cuff)

    def pose(deg, lift):
        rev.rotationValue = s * deg * 3.14159265 / 180
        m = adsk.core.Matrix3D.create()
        up = adsk.core.Vector3D.create(0, 0, 1)                    # the arm axis (concept frame Z), toward the elbow
        up.transformBy(fa.transform2)
        up.scaleBy(lift / 10)
        m.translation = up
        anim.transform2 = m
        adsk.doEvents()
    try:
        pose(80, PULL)                                              # everything at its widest: fit once
        e = adsk.core.Vector3D.create(*VIEW)
        e.transformBy(fa.transform2)
        e.normalize()
        up = adsk.core.Vector3D.create(0, 0, 1)
        up.transformBy(fa.transform2)
        k = up.dotProduct(e)
        up = adsk.core.Vector3D.create(up.x - k * e.x, up.y - k * e.y, up.z - k * e.z)
        up.normalize()
        cam = vp.camera
        cam.cameraType = adsk.core.CameraTypes.OrthographicCameraType
        t = cam.target
        e.scaleBy(100)
        cam.eye = adsk.core.Point3D.create(t.x + e.x, t.y + e.y, t.z + e.z)
        cam.upVector = up
        cam.isFitView = True
        vp.camera = cam
        vp.fit()
        fit = vp.camera
        os.makedirs(out_dir, exist_ok=True)
        caps = []
        for i, (deg, lift, cap) in enumerate(SEQ):
            pose(deg, lift)
            c = vp.camera
            c.cameraType, c.target, c.eye, c.upVector, c.isFitView = (fit.cameraType, fit.target, fit.eye, fit.upVector,
                                                                      False)
            c.setExtents(*fit.getExtents()[1:])
            vp.camera = c
            vp.refresh()
            vp.saveAsImageFile(os.path.join(out_dir, 'f%02d.png' % i), *size)
            caps.append(cap)
        open(os.path.join(out_dir, 'captions.txt'), 'w').write('\n'.join(caps))
    finally:
        rev.rotationValue = v0
        anim.deleteMe()
        plunger.isLightBulbOn = True
        for b in hidden:
            b.isLightBulbOn = True
        for c, attr in folders:
            setattr(c, attr, True)
    return len(SEQ)


def _open_sign(rev, cuff):
    """+1 or -1: the rotation that swings the cuff's latch end out to the front (+Y), not into the ring."""
    rev.rotationValue = 0.0
    adsk.doEvents()
    y0 = max(b.boundingBox.maxPoint.y for b in cuff.bRepBodies)
    rev.rotationValue = 0.5
    adsk.doEvents()
    y1 = max(b.boundingBox.maxPoint.y for b in cuff.bRepBodies)
    rev.rotationValue = 0.0
    return 1 if y1 > y0 else -1
