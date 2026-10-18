"""Animation frames of the v3b shoulder girdle (run inside Fusion via MCP, a few frames per call).

KEYS are (label, (dx, dy, dz) mm, abduction deg); frames are eased between them. frames(i0, i1) poses and saves
frames i0..i1-1 for every view into out/girdle/<view>_NNN.png. Run girdle_b.pose() afterwards to return to rest.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import girdle_b as gb  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'girdle')
KEYS = [('Rest', (0, 0, 0), 0), ('Shrug up 60', (0, 60, 0), 0), ('Rest', (0, 0, 0), 0),
        ('Drop 20', (0, -20, 0), 0), ('Rest', (0, 0, 0), 0), ('Reach 40 fwd, 25 out', (40, 0, 25), 0),
        ('Squeeze 40 back, 25 in', (-40, 0, -25), 0), ('Rest', (0, 0, 0), 0),
        ('Reach + shrug 50', (40, 50, 25), 0), ('Squeeze + shrug 50', (-40, 50, -25), 0), ('Rest', (0, 0, 0), 0),
        ('Arm raised 60', (0, 0, 0), -60), ('Arm raised + shrug 50', (0, 50, 0), -60), ('Rest', (0, 0, 0), 0)]
STEPS = 6                                   # frames per segment
# camera (target, eye, up, extent) in Fusion world cm: x fwd, -y right, z up
CAMS = {'back': ((-16, -19, 141), (-150, -80, 175), (0, 0, 1), 50),
        'side': ((-17, -16, 140), (-17, -140, 145), (0, 0, 1), 46),
        'plan': ((-21, -14, 140), (-21.01, -14, 260), (1, 0, 0), 40)}
VIEWS = ('back', 'side', 'plan')


def view(path, which, w=720, h=560):
    import adsk.core
    t, e, u, x = CAMS[which]
    vp = adsk.core.Application.get().activeViewport
    c = vp.camera
    c.isFitView = False
    c.cameraType = adsk.core.CameraTypes.PerspectiveCameraType
    c.target = adsk.core.Point3D.create(*t)
    c.eye = adsk.core.Point3D.create(*e)
    c.upVector = adsk.core.Vector3D.create(*u)
    c.viewExtents = x
    vp.camera = c
    vp.refresh()
    vp.saveAsImageFile(path, w, h)


def seq():
    out = []
    for (la, a, ra), (lb, b, rb) in zip(KEYS, KEYS[1:]):
        for k in range(STEPS):
            t = k / STEPS
            e = 0.5 - 0.5 * math.cos(math.pi * t)
            lab = la if k < STEPS // 2 else lb
            out.append((lab, tuple(a[i] + (b[i] - a[i]) * e for i in range(3)), ra + (rb - ra) * e))
    out.append((KEYS[-1][0], KEYS[-1][1], KEYS[-1][2]))
    return out


def frames(i0, i1):
    os.makedirs(OUT, exist_ok=True)
    s = seq()
    for i in range(i0, min(i1, len(s))):
        _, d, abd = s[i]
        gb.pose(d, abd)
        for v in VIEWS:
            view(os.path.join(OUT, '%s_%03d.png' % (v, i)), v)
    return len(s)
