"""Motion animation of the whole exo (v3b girdle + shoulder hinges + elbow) on the scanned body. Run inside Fusion.

1. record(seq)  in the shoulder document: poses the real model for every frame (girdle_b.pose for the girdle and
   the arm module, plus the flexion hinge) and stores each moving occurrence's world motion (delta from rest).
2. stage()      copies the parts into custom graphics in a temp document (asm.collect + migrate), adds the torso and
   the scanned arm split at the elbow.
3. frames(i0, i1, prefix) applies the recorded motion (plus the elbow bend, about its measured axis) and saves
   frames to out/motion/<prefix>_NNN.png.
Joint axes come from the bearings themselves (6806 pair = abduction / elbow, 6808 pair = flexion).
"""
import math
import os
import sys

import adsk.core
import adsk.fusion

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import asm  # noqa: E402

OUT = os.path.join(HERE, 'out', 'motion')
STATE = {}
ARM_MODULE = ('Yoke', 'Abduction sleeve', 'HW abd (buy)', 'Upper-arm link', 'Flexion axle sleeve', 'HW flex (buy)')
FLEX = ('Upper-arm link', 'Flexion axle sleeve', 'HW flex (buy)')
# (label, girdle displacement mm (x fwd, y up, z right), abduction deg (+ = out/up), flexion deg (+ = forward), elbow deg)
SEQ = [('Rest', (0, 0, 0), 0, 0, 0),
       ('Shoulder up (shrug)', (0, 60, 0), 0, 0, 0), ('Rest', (0, 0, 0), 0, 0, 0),
       ('Shoulder down', (0, -20, 0), 0, 0, 0), ('Rest', (0, 0, 0), 0, 0, 0),
       ('Shoulder forward (reach)', (35, 0, 0), 0, 0, 0), ('Shoulder back (squeeze)', (-35, 0, 0), 0, 0, 0),
       ('Rest', (0, 0, 0), 0, 0, 0),
       ('Shoulder out', (0, 0, 25), 0, 0, 0), ('Shoulder in', (0, 0, -25), 0, 0, 0), ('Rest', (0, 0, 0), 0, 0, 0),
       ('Arm out to the side', (0, 0, 0), 55, 0, 0), ('Rest', (0, 0, 0), 0, 0, 0),
       ('Arm forward', (0, 0, 0), 0, 70, 0), ('Rest', (0, 0, 0), 0, 0, 0),
       ('Elbow bend', (0, 0, 0), 0, 0, 100), ('Rest', (0, 0, 0), 0, 0, 0)]
STEPS = 8


def sequence():
    out = []
    for a, b in zip(SEQ, SEQ[1:]):
        for k in range(STEPS):
            e = 0.5 - 0.5 * math.cos(math.pi * k / STEPS)
            lab = b[0] if b[0] != 'Rest' else a[0]
            out.append((lab, tuple(a[1][i] + (b[1][i] - a[1][i]) * e for i in range(3)),
                        a[2] + (b[2] - a[2]) * e, a[3] + (b[3] - a[3]) * e, a[4] + (b[4] - a[4]) * e))
    out.append(SEQ[-1])
    return out


def _m(arr):
    m = adsk.core.Matrix3D.create()
    m.setWithArray(arr)
    return m


def _delta(rest, now):
    d = rest.copy()
    d.invert()
    d.transformBy(now)
    return d


def _rot(deg, axis, origin):
    m = adsk.core.Matrix3D.create()
    m.setToRotation(math.radians(deg), adsk.core.Vector3D.create(*axis), adsk.core.Point3D.create(*origin))
    return m


def _axis(parts, pattern):
    """Axis through the centres of the two bearing bodies whose names match (world cm)."""
    import re
    bs = [p for p in parts if re.search(pattern, p['key'])]
    a, b = bs[0]['c'], bs[-1]['c']
    d = [b[i] - a[i] for i in range(3)]
    n = math.sqrt(sum(x * x for x in d))
    return [x / n for x in d], [(a[i] + b[i]) / 2 for i in range(3)]


def record(start=0, count=None):
    """Pose the real model for frames start..start+count and store each occurrence's world delta from rest."""
    import girdle_b as gb
    seq = sequence()
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    occ = {o.component.name: o for o in d.rootComponent.allOccurrences if o.isVisible and not o.component.name.startswith('zz')}
    names = [n for n in occ if gb._role(n) or n.startswith(ARM_MODULE) or n.startswith('Elbow concept')]
    if 'rest' not in STATE:
        gb.pose((0, 0, 0), 0)
        STATE['rest'] = {n: list(occ[n].transform2.asArray()) for n in names}
        STATE['frames'] = {}
    end = len(seq) if count is None else min(len(seq), start + count)
    for i in range(start, end):
        lab, disp, abd, flex, elb = seq[i]
        gb.pose(disp, abd)                                   # girdle_b.pose: positive = arm out to the side (checked in renders)
        STATE['frames'][i] = {n: list(_delta(_m(STATE['rest'][n]), occ[n].transform2).asArray()) for n in names}
    gb.pose((0, 0, 0), 0)
    return len(seq), end


def stage():
    """Custom-graphics copy of the exo in a temp doc + torso + scanned arm split at the elbow."""
    import shoulder as sh
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    ref = next(o for o in d.rootComponent.allOccurrences if o.component.name.startswith('Reference'))
    meshes = {}
    M = ref.transform2                                        # mesh bodies come in local coordinates
    R = M.copy(); R.translation = adsk.core.Vector3D.create(0, 0, 0)
    for mb in ref.component.meshBodies:
        dm = mb.displayMesh
        xyz, nr = list(dm.nodeCoordinatesAsDouble), list(dm.normalVectorsAsDouble)
        for j in range(0, len(xyz), 3):
            pt = adsk.core.Point3D.create(*xyz[j:j + 3]); pt.transformBy(M); xyz[j:j + 3] = [pt.x, pt.y, pt.z]
            v = adsk.core.Vector3D.create(*nr[j:j + 3]); v.transformBy(R); nr[j:j + 3] = [v.x, v.y, v.z]
        meshes[mb.name] = (xyz, list(dm.nodeIndices), nr)
    top = next(o for o in d.rootComponent.occurrences if o.component.name == sh.TOP).transform2

    def world(p):
        pt = adsk.core.Point3D.create(p[0] / 10, p[1] / 10, p[2] / 10)
        pt.transformBy(top)
        return [pt.x, pt.y, pt.z]
    gh, el, wr = world(sh.GH), world(sh.LAY['landmarks']['EL']), world(sh.LAY['landmarks']['WR'])
    asm.collect()
    asm.migrate()
    parts = asm.ensure_parts()
    for p in parts:                                          # harness illustration is not part of this movie
        p['ent'].isVisible = not p['comp'].startswith('Harness')
    d2 = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    grp = d2.rootComponent.customGraphicsGroups.item(0)
    skin = adsk.core.Color.create(222, 184, 160, 255)
    eff = adsk.fusion.CustomGraphicsBasicMaterialColorEffect.create(skin, skin, adsk.core.Color.create(30, 30, 30, 255),
                                                                     adsk.core.Color.create(0, 0, 0, 255), 10.0, 1.0)
    u = [el[i] - gh[i] for i in range(3)]
    L = math.sqrt(sum(x * x for x in u))
    u = [x / L for x in u]
    body = {}
    for name, (xyz, idx, nr) in meshes.items():
        if not name.startswith('right arm'):
            m = grp.addMesh(adsk.fusion.CustomGraphicsCoordinates.create(xyz), idx, nr, idx)
            m.color = eff
            body['torso'] = m
            continue
        for part in ('ua', 'fa'):                            # split the arm at the elbow (by triangle centroid)
            keep = []
            for k in range(0, len(idx), 3):
                c = [sum(xyz[3 * idx[k + j] + i] for j in range(3)) / 3 for i in range(3)]
                t = sum((c[i] - gh[i]) * u[i] for i in range(3)) / L
                if (t <= 1.0) == (part == 'ua'):
                    keep += idx[k:k + 3]
            m = grp.addMesh(adsk.fusion.CustomGraphicsCoordinates.create(xyz), keep, nr, keep)
            m.color = eff
            body[part] = m
    STATE['body'] = body
    STATE['body_wrist'] = wr
    STATE['flex_axis'] = _axis(parts, r'HW flex.*6808')
    STATE['elbow_axis'] = _axis(parts, r'Elbow concept.*6806-2')
    # the elbow copy in this document is not at the scanned arm's bend: turn the exo forearm (about its own axis) onto
    # the scan's elbow-to-wrist line, so at rest the exo and the arm agree
    import re
    n, c = STATE['elbow_axis']
    ring = [p for p in parts if re.search(r'Forearm unit: far ring', p['key'])][0]['c']
    def perp(v):
        k = sum(v[i] * n[i] for i in range(3))
        return [v[i] - k * n[i] for i in range(3)]
    v1, v2 = perp([ring[i] - c[i] for i in range(3)]), perp([wr[i] - el[i] for i in range(3)])
    cr = [v1[1] * v2[2] - v1[2] * v2[1], v1[2] * v2[0] - v1[0] * v2[2], v1[0] * v2[1] - v1[1] * v2[0]]
    STATE['elbow_rest'] = math.degrees(math.atan2(sum(cr[i] * n[i] for i in range(3)), sum(v1[i] * v2[i] for i in range(3))))
    return len(parts), list(body)


def _signed(axis_pt, deg, probe, want):
    """Rotation about axis_pt by deg, sign chosen so that the probe point moves along +want (world)."""
    ax, o = axis_pt
    r = _rot(5, ax, o)
    q = adsk.core.Point3D.create(*probe)
    q.transformBy(r)
    s = 1 if sum((q.asArray()[i] - probe[i]) * want[i] for i in range(3)) > 0 else -1
    return _rot(s * deg, ax, o)


def pose_frame(i):
    seq = sequence()
    lab, disp, abd, flex, elb = seq[i]
    deltas = {n: _m(a) for n, a in STATE['frames'][i].items()}
    parts = asm.ensure_parts()
    import re
    fa = re.compile(r'Forearm unit|Wrist cuff')
    elbow_c = STATE['elbow_axis'][1]
    wrist = STATE['body_wrist']
    F = _signed(STATE['flex_axis'], flex, elbow_c, [1, 0, 0])          # forward = +x world
    E = _signed(STATE['elbow_axis'], elb, wrist, [0, 0, 1])          # the forearm rests pointing forward: bending lifts the wrist
    for p in parts:
        if not p['ent'].isVisible:
            continue
        D = deltas.get(p['comp'])
        if D is None:
            continue
        M = adsk.core.Matrix3D.create()                       # world motion, applied right to left: E, F, then D
        if p['comp'].startswith('Elbow concept') and fa.search(p['key']):
            M.transformBy(_rot(STATE['elbow_rest'], *STATE['elbow_axis']))
            M.transformBy(E)
        if p['comp'].startswith(FLEX) or p['comp'].startswith('Elbow concept'):
            M.transformBy(F)
        M.transformBy(D)
        p['ent'].transform = M
    elbow = deltas[next(n for n in deltas if n.startswith('Elbow concept'))]
    ua = F.copy(); ua.transformBy(elbow)
    fam = E.copy(); fam.transformBy(F); fam.transformBy(elbow)
    STATE['body']['ua'].transform = ua
    STATE['body']['fa'].transform = fam
    return lab


CAM = ([-0.75, -1.0, 0.45], 1.45)


def frames(i0, i1, prefix='m', w=1280, h=720, cam=None):
    os.makedirs(OUT, exist_ok=True)
    vp = adsk.core.Application.get().activeViewport
    if 'cam' not in STATE or cam:
        parts = [p for p in asm.ensure_parts() if p['ent'].isVisible]
        lo = [min(p['lo'][k] for p in parts) for k in range(3)]
        hi = [max(p['hi'][k] for p in parts) for k in range(3)]
        ctr = [(lo[k] + hi[k]) / 2 for k in range(3)]
        vd, sc = cam or CAM
        n = math.sqrt(sum(x * x for x in vd))
        vd = [x / n for x in vd]
        ctr[2] -= (hi[2] - lo[2]) * 0.12                    # the arm hangs below the exo's bounding box
        STATE['cam'] = (ctr, [ctr[k] + vd[k] * 300 for k in range(3)], (hi[2] - lo[2]) * sc)
    ctr, eye, ext = STATE['cam']
    asm.camera(vp, ctr, eye, ext)
    labels = []
    for i in range(i0, min(i1, len(sequence()))):
        labels.append(pose_frame(i))
        vp.refresh()
        vp.saveAsImageFile(os.path.join(OUT, '%s_%03d.png' % (prefix, i)), w, h)
    return labels


STILLS = {   # name: (view direction to the eye, parts regex the camera frames, extent scale, include body)
    'exo-on-body-back': ([-0.75, -1.0, 0.45], r'.', 1.15, True),
    'exo-on-body-front': ([1.0, -0.9, 0.35], r'.', 1.15, True),
    'shoulder-close': ([-0.6, -1.0, 0.55], r'^(Shoulder tower|Lift |Carriage|Gas spring|SCARA|Elbow spool|End plate|Yoke|Abduction sleeve|HW abd|Upper-arm link|Flexion|HW flex|Rest )', 1.4, False),
    'elbow-close': ([0.2, -1.0, 0.25], r'^Elbow concept', 1.35, False),
}


def stills(names=None, w=1600, h=1100):
    """README stills at rest (frame 0 of the recorded motion)."""
    import re
    vp = adsk.core.Application.get().activeViewport
    pose_frame(0)
    parts = asm.ensure_parts()
    out = []
    for name in names or STILLS:
        vd, rx, sc, body = STILLS[name]
        for m in STATE['body'].values():
            m.isVisible = body
        sel = [p for p in parts if p['ent'].isVisible and re.search(rx, p['key'])]
        hidden = []
        if name == 'elbow-close':                            # the elbow alone: the frame behind it is clutter
            hidden = [p for p in parts if p['ent'].isVisible and p not in sel]
            for p in hidden:
                p['ent'].isVisible = False
        pts = []                                             # posed bounding-box corners (parts move at rest too)
        for p in sel:
            for k in range(8):
                q = adsk.core.Point3D.create(*[(p['lo'], p['hi'])[(k >> i) & 1][i] for i in range(3)])
                q.transformBy(p['ent'].transform)
                pts.append(q.asArray())
        if body:
            pts.append(STATE['body_wrist'])
        lo = [min(q[k] for q in pts) for k in range(3)]
        hi = [max(q[k] for q in pts) for k in range(3)]
        ctr = [(lo[k] + hi[k]) / 2 for k in range(3)]
        n = math.sqrt(sum(x * x for x in vd))
        eye = [ctr[k] + vd[k] / n * 300 for k in range(3)]
        span = max(hi[k] - lo[k] for k in range(3))
        asm.camera(vp, ctr, eye, span * sc)
        vp.refresh()
        path = os.path.join(OUT, name + '.png')
        vp.saveAsImageFile(path, w, h)
        out.append(path)
        for p in hidden:
            p['ent'].isVisible = True
    for m in STATE['body'].values():
        m.isVisible = True
    return out
