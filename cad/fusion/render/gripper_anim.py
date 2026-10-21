"""Gripper motion frames for review: slide out, squeeze (claws open), release, slide back. Run in Fusion with the
"CDX-3R gripper" document active:

    import gripper_anim; gripper_anim.frames(out_dir, 'top')      # and 'under' (grip + trigger side)

The camera is fitted once at the fully open pose, then held fixed for every frame (a per-frame fit makes the
picture jump). Views are given in the rail frame (X along the rail, Y up off the pipe, Z across)."""
import os

import adsk.core
import adsk.fusion

import gripper as gr
import shoulder as sh

SEQ = ([(k / 10.0, 0.0) for k in range(11)] + [(1.0, k / 6.0) for k in range(1, 7)] + [(1.0, 1.0)] * 2 +
       [(1.0, k / 6.0) for k in range(5, -1, -1)] + [(1.0 - k / 10.0, 0.0) for k in range(1, 11)])
CAPTIONS = (['Stowed over the forearm, behind the wrist'] + ['Sliding forward on the rail'] * 10 +
            ['Locked forward. Squeezing the trigger: claws open'] * 6 + ['Fully open (~30 deg each)'] * 2 +
            ['Trigger released: the spring closes the claws'] * 6 + ['Lock released: the head glides back home'] * 10)
VIEWS = {'top': ((0.45, -0.65, 0.6), (1, 0, 0)), 'under': ((0.35, 0.75, -0.55), (1, 0, 0)),
         'side': ((0.15, -1.0, 0.1), (1, 0, 0))}             # side profile (rail vertical; rotate the frame -90 deg)


def frames(out_dir, view, size=900):
    a = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(a.activeProduct)
    vp = a.activeViewport
    topo = next(o for o in d.rootComponent.occurrences if o.component.name == sh.TOP)
    grp = next(o for o in topo.component.occurrences if o.component.name == gr.NAME)
    T = topo.transform2.copy()
    T.transformBy(grp.transform2)

    def wv(v):
        q = adsk.core.Vector3D.create(*v)
        q.transformBy(T)
        q.normalize()
        return q
    dirn, upv = VIEWS[view]
    gr.pose(1, 1)
    e, up = wv(dirn), wv(upv)
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
    _, w, h = fit.getExtents()
    os.makedirs(out_dir, exist_ok=True)
    for i, (s, q) in enumerate(SEQ):
        gr.pose(s, q)
        c = vp.camera
        c.cameraType, c.target, c.eye, c.upVector, c.isFitView = fit.cameraType, fit.target, fit.eye, fit.upVector, False
        c.setExtents(w * 1.12, h * 1.12)
        vp.camera = c
        vp.refresh()
        vp.saveAsImageFile(os.path.join(out_dir, '%s_%03d.png' % (view, i)), size, size)
    gr.pose(0, 0)
    return len(SEQ)


def closeup(path, pose, focus, context, view='top', zoom=2.2, size=900):
    """One still: fit the camera on the `focus` parts (component-name prefixes), then show `context` too and zoom out
    by `zoom`. Everything else in the gripper is hidden for the shot, then shown again."""
    a = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(a.activeProduct)
    vp = a.activeViewport
    topo = next(o for o in d.rootComponent.occurrences if o.component.name == sh.TOP)
    grp = next(o for o in topo.component.occurrences if o.component.name == gr.NAME)
    T = topo.transform2.copy()
    T.transformBy(grp.transform2)
    gr.pose(*pose)
    occs = [o for o in grp.component.occurrences]
    keep = {o.component.name: o.isLightBulbOn for o in occs}
    try:
        for o in occs:
            o.isLightBulbOn = o.component.name.startswith(tuple(focus))
        dirn, upv = VIEWS[view]
        e = adsk.core.Vector3D.create(*dirn)
        e.transformBy(T)
        e.normalize()
        up = adsk.core.Vector3D.create(*upv)
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
        _, w, h = fit.getExtents()
        for o in occs:
            o.isLightBulbOn = o.component.name.startswith(tuple(focus) + tuple(context))
        c = vp.camera
        c.isFitView = False
        c.setExtents(w * zoom, h * zoom)
        vp.camera = c
        vp.refresh()
        vp.saveAsImageFile(path, size, size)
    finally:
        for o in occs:
            o.isLightBulbOn = keep[o.component.name]
        gr.pose(0, 0)
