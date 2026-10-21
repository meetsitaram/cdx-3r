"""Gripper 3 build steps 11.3-11.4 for review: the collar slides on over the nose and parks back, the claws go into
their slots, the collar comes forward over the claw tails. Run in Fusion with "CDX-3R gripper 3" active:

    import gripper3_collar_anim; gripper3_collar_anim.frames(out_dir)

Only the carrier, collar and claws are shown (bodies hidden, not occurrences: hidden occurrences render blank). The
camera is fitted once with every part at its farthest, then held for every frame."""
import math
import os

import adsk.core
import adsk.fusion

import gripper3 as g3

PARK = g3.COLLAR_PARK
OUT = 40.0                                   # mm: claws start this far out of their slots
C1 = '1. Slide the collar on over the front: its 3 inner pads pass through the 3 claw slots'
C2 = '2. Push it about 7 mm past its seat, up to the bridge (room for the claws)'
C3 = '3. Each claw root into its slot; M3 x 30 pivot through it'
C4 = '4. Slide the collar forward: the claw tails go between its cheeks; M3 x 20 through each'
C5 = 'Done: the collar rides on its pads, 0.3 mm off the hub'
SEQ = ([(x, None, C1) for x in (70, 60, 50, 40, 30, 20, 10, 0)] + [(-PARK / 2, None, C2), (-PARK, None, C2)] * 1 +
       [(-PARK, r, C3) for r in (OUT, 30, 20, 10, 5, 0)] + [(-PARK * 2 / 3, 0, C4), (-PARK / 3, 0, C4), (0, 0, C4)] +
       [(0, 0, C5)] * 3)
VIEW = (1.0, 0.55, 0.75)                     # eye direction in the rail frame: front, above, to the side


def frames(out_dir, size=(1200, 800)):
    a = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(a.activeProduct)
    vp = a.activeViewport
    g3.pose(0, 0)
    grp = next(o for o in d.rootComponent.allOccurrences if o.component.name == g3.NAME)
    native = [o for o in d.rootComponent.allOccurrences                 # proxies: overrides are set from the root
              if g3.NAME in o.fullPathName and o.component.name != g3.NAME]
    collar = next(o for o in native if o.component.name.startswith('Gripper3 collar'))
    claws = [o for o in native if o.component.name.startswith('Gripper3 claw')]
    keep = ('Gripper3 carrier (printed)', 'Gripper3 collar', 'Gripper3 claw')
    hidden = []
    for o in d.rootComponent.allOccurrences:
        if o.component.name.startswith(keep):
            continue
        for b in o.component.bRepBodies:
            if b.isLightBulbOn:
                b.isLightBulbOn = False
                hidden.append(b)
    for b in d.rootComponent.bRepBodies:
        if b.isLightBulbOn:
            b.isLightBulbOn = False
            hidden.append(b)
    home = {o.component.name: o.transform2.copy() for o in [collar] + claws}

    def place(o, v):
        m = home[o.component.name].copy()
        t = m.translation
        t.add(adsk.core.Vector3D.create(v[0] / 10, v[1] / 10, v[2] / 10))
        m.translation = t
        o.transform2 = m

    def claw_dir(o):
        al = math.radians(g3.P['claw']['alphas'][int(o.component.name.split('claw ')[1][0]) - 1])
        return (0.0, math.cos(al), math.sin(al))

    def show_claws(on):
        for o in claws:
            for b in o.component.bRepBodies:
                b.isLightBulbOn = on

    def pose(x, r):
        place(collar, (x, 0, 0))
        show_claws(r is not None)
        for o in claws:
            u = claw_dir(o)
            place(o, tuple(c * (r or 0.0) for c in u))
    try:
        pose(SEQ[0][0], OUT)                                        # everything at its farthest: fit once
        show_claws(True)
        T = grp.transform2
        e = adsk.core.Vector3D.create(*VIEW)
        e.transformBy(T)
        e.normalize()
        up = adsk.core.Vector3D.create(0, 1, 0)
        up.transformBy(T)
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
        for i, (x, r, cap) in enumerate(SEQ):
            pose(x, r)
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
        for o in [collar] + claws:
            o.transform2 = home[o.component.name]
        show_claws(True)
        for b in hidden:
            b.isLightBulbOn = True
        g3.pose(0, 0)
    return len(SEQ)
