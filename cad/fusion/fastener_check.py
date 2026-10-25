"""Fastener engagement test (run inside Fusion on the assembly; results to a log file).

For every bought fastener (screw, bolt, pin, stud) the shank axis is found from its body, then points are sampled
along it on a ring just outside the shank (radius r + 0.8 mm, 8 directions). An axial station counts as "in
material" when at least 5 of the 8 ring points are inside a printed part. A fastener whose stations in material add up
to less than MIN_GRIP mm in the tip half (the end that must bite; the head half only passes through the clamped part)
fails. "Material" = printed parts, PVC pipe, and bought nuts and inserts (a screw into a trapped nut grips the nut).
A failing fastener ends in nothing: it hangs in the air or barely touches its part. Known case: the old
shoulder-rest lock screw (into a trapped nut) passes with 6 mm, as it should. Grip only:
it does not judge how strong the wall around a nut is (docs/bugs/rest-bracket-attachment.md).

Two more rules (docs/bugs/end-plate-hung-below-its-nut.md: the SCARA end plate sat below the nut of the bolt meant to
hold it, so nothing held it, and the grip test passed because the bolt's tip was in plastic):
  * THREAD: a machine screw must end in a modelled nut or heat-set insert. Self-tapping screws, pins with clips and
    screws named 'cuts its own thread' are exempt. '+ nyloc' in a name is not enough: model the nut.
  * HELD: every printed part a fastener passes must have material between the head and the far face of its nut or
    insert (the clamped stack). A part reached only beyond the nut is not held by it.

    import fastener_check as fc
    fc.run_check(log_path)       # returns the number of failures
"""
import json
import math
import os
import re

import adsk.core
import adsk.fusion

MIN_GRIP = 3.0                                            # mm of the shank's TIP half surrounded by printed material
FASTENER = re.compile(r'(socket head|pan-head|Clevis pin|ball stud|thumb screw|M\d+ x \d+)', re.I)
SKIP = re.compile(r'(nut|insert|washer|spacer|bearing|608|6806|6808|belt|^R-clip|pulley|webbing|buckle)', re.I)
ANCHOR = re.compile(r'(nut|insert)', re.I)                 # what a machine screw's thread bites
NO_ANCHOR_OK = re.compile(r'(self-tapping|Clevis pin|R-clip|cuts its own thread)', re.I)
BEARING = re.compile(r'(608|6806|6808)', re.I)
BEARING_OD = {'6806': 42.0, '6808': 52.0, '608': 22.0}     # mm (6806/6808 first: '608' is in neither)
BEARING_RINGS = [x / 10.0 for x in (5.0, 6.5, 9.0, 16.0, 21.0)]   # cm from the axis: 608 inner ring .. 6808 rings
JOINTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sim_joints.json')


def _axis(body):
    """Shank axis of a fastener body: the longest of its bounding-box diagonal directions, via its mesh."""
    calc = body.meshManager.createMeshCalculator()
    calc.setQuality(adsk.fusion.TriangleMeshQualityOptions.LowQualityTriangleMesh)
    m = calc.calculate()
    P = m.nodeCoordinatesAsDouble
    n = len(P) // 3
    c = [sum(P[i::3]) / n for i in range(3)]
    cov = [[0.0] * 3 for _ in range(3)]
    for j in range(n):
        d = [P[3 * j + i] - c[i] for i in range(3)]
        for a in range(3):
            for b in range(3):
                cov[a][b] += d[a] * d[b]
    v = [1.0, 0.6, 0.3]
    for _ in range(40):
        w = [sum(cov[a][b] * v[b] for b in range(3)) for a in range(3)]
        s = math.sqrt(sum(x * x for x in w)) or 1.0
        v = [x / s for x in w]
    t = [sum((P[3 * j + i] - c[i]) * v[i] for i in range(3)) for j in range(n)]
    # shank radius: median distance from the axis over the half of the points away from the head
    rad = sorted(math.sqrt(max(0.0, sum((P[3 * j + i] - c[i]) ** 2 for i in range(3)) - t[j] ** 2)) for j in range(n))
    t0, t1 = min(t), max(t)
    # the head end carries more mesh: the mean of t leans toward it. Orient the axis so t runs head -> tip.
    if sum(t) / n > (t0 + t1) / 2:
        v = [-x for x in v]
        t0, t1 = -t1, -t0
    return c, v, t0, t1, rad[len(rad) // 3]


def check(design, min_grip=MIN_GRIP):
    printed, fasteners, anchors, bearings = [], [], [], []
    for o in design.rootComponent.allOccurrences:
        if not o.isVisible or 'Reference' in o.fullPathName or 'Harness' in o.fullPathName:
            continue
        for b in o.component.bRepBodies:
            if not b.isVisible:
                continue
            px = b.createForAssemblyContext(o)
            buy = '(buy)' in o.component.name or '(buy)' in b.name
            if buy and FASTENER.search(b.name) and not SKIP.search(b.name):
                fasteners.append((o.component.name, b.name, px))
            elif (not buy or 'printed' in b.name or 'PVC' in b.name or 'PVC' in o.component.name
                  or re.search(r'(nut|insert|carriage)', b.name, re.I)):
                printed.append(px)                         # what a screw can bite: printed parts, PVC, nuts, inserts
            if buy and ANCHOR.search(b.name) and not FASTENER.search(b.name):
                anchors.append(px)
            if buy and BEARING.search(b.name):
                bearings.append((b.name, px))
    out = []
    boxes = [(b, b.boundingBox) for b in printed]
    for comp, name, px in fasteners:
        fb = px.boundingBox
        near = [b for b, bb in boxes if all(bb.minPoint.asArray()[i] - 0.2 <= fb.maxPoint.asArray()[i] and
                                            fb.minPoint.asArray()[i] <= bb.maxPoint.asArray()[i] + 0.2 for i in range(3))]
        c, v, t0, t1, r = _axis(px)
        u = [1.0, 0.0, 0.0] if abs(v[0]) < 0.9 else [0.0, 1.0, 0.0]
        e1 = [v[1] * u[2] - v[2] * u[1], v[2] * u[0] - v[0] * u[2], v[0] * u[1] - v[1] * u[0]]
        s = math.sqrt(sum(x * x for x in e1))
        e1 = [x / s for x in e1]
        e2 = [v[1] * e1[2] - v[2] * e1[1], v[2] * e1[0] - v[0] * e1[2], v[0] * e1[1] - v[1] * e1[0]]
        rr = r + 0.08                                     # cm: 0.8 mm outside the shank
        step = 0.1                                        # cm (1 mm)
        grip = 0.0
        k = t0
        while k <= t1:
            inside = 0
            for a in range(8):
                ang = a * math.pi / 4
                q = [c[i] + v[i] * k + rr * (math.cos(ang) * e1[i] + math.sin(ang) * e2[i]) for i in range(3)]
                pt = adsk.core.Point3D.create(*q)
                if any(b.pointContainment(pt) == adsk.fusion.PointContainment.PointInsidePointContainment for b in near):
                    inside += 1
                    if inside >= 5:
                        break
            if inside >= 5 and k >= (t0 + t1) / 2:             # only the tip half counts: that is where it must bite
                grip += step
            k += step
        probs, info = _held(px, c, v, t0, t1, r, near, anchors, bearings, printed, name)
        out.append((comp, name, round(grip * 10, 1), probs, info))
    return out


def _inside(b, q):
    pt = adsk.core.Point3D.create(*q)
    return b.boundingBox.contains(pt) and \
        b.pointContainment(pt) == adsk.fusion.PointContainment.PointInsidePointContainment


def _held(px, c, v, t0, t1, r, near, anchors, bearings, printed, name):
    """THREAD and HELD rules for one fastener: (problems, info). info is its clamped stack, for joint_check: 'parts'
    (component name -> stations, mm from the head end, of printed material next to the shank), 'far' (far face of
    the nut / insert; None without one), 'bearings' (bearing name -> (stations, component names of the printed parts
    round its outer ring))."""
    u = [1.0, 0.0, 0.0] if abs(v[0]) < 0.9 else [0.0, 1.0, 0.0]
    e1 = [v[1] * u[2] - v[2] * u[1], v[2] * u[0] - v[0] * u[2], v[0] * u[1] - v[1] * u[0]]
    s = math.sqrt(sum(x * x for x in e1))
    e1 = [x / s for x in e1]
    e2 = [v[1] * e1[2] - v[2] * e1[1], v[2] * e1[0] - v[0] * e1[2], v[0] * e1[1] - v[1] * e1[0]]
    fb = px.boundingBox
    mine = [a for a in anchors if a.boundingBox.intersects(fb)]

    def ring(k, rr, n=8):
        return [[c[i] + v[i] * k + rr * (math.cos(a * 2 * math.pi / n) * e1[i] + math.sin(a * 2 * math.pi / n) * e2[i])
                 for i in range(3)] for a in range(n)]
    hits, anc, brg_st = {}, [], {}                          # printed body index -> stations (mm from the head end)
    brg = [(n, b) for n, b in bearings if b.boundingBox.intersects(fb)]
    k, step = t0, 0.1
    while k <= t1 + 1e-9:
        mm = (k - t0) * 10
        for rr in (r + 0.08, r + 0.25):                     # just outside the shank, and outside a nut or insert
            for q in ring(k, rr):
                for j, b in enumerate(near):
                    if b not in mine and _inside(b, q):
                        hits.setdefault(j, set()).add(round(mm))
        if any(_inside(a, q) for a in mine for q in ring(k, r + 0.03, 4)):
            anc.append(mm)
        for bn, b in brg:                                   # bearings on this axis, out to a 6808's rings
            if any(_inside(b, q) for rr in BEARING_RINGS for q in ring(k, rr, 6)):
                brg_st.setdefault(bn, set()).add(round(mm))
        k += step

    def comp_of(b):
        o = b.assemblyContext
        return o.component.name if o else b.name
    parts = {}
    for j, st in hits.items():
        parts.setdefault(comp_of(near[j]), set()).update(st)
    held_by = {}
    for bn, st in brg_st.items():                           # who holds each bearing: printed material just outside
        od = next((x for k_, x in BEARING_OD.items() if k_ in bn), 22.0) / 20.0 + 0.06    # its outer ring (cm)
        mid = t0 + (min(st) + max(st)) / 20.0
        holders = set()
        for q in ring(mid, od, 12):
            for b in printed:
                if _inside(b, q):
                    holders.add(comp_of(b))
        held_by[bn] = (st, holders)
    info = dict(parts=parts, far=max(anc) if anc else None, bearings=held_by)
    probs = []
    if not anc:
        if not NO_ANCHOR_OK.search(name):
            probs.append('THREAD: ends in no nut or insert (model one, or name it "cuts its own thread")')
        return probs, info
    far = max(anc)                                          # far face of the nut / insert
    for j, st in hits.items():
        if min(st) > far:
            probs.append('HELD: %s is reached only beyond the nut/insert (%d..%d mm from the head, nut ends at %d): '
                         'nothing holds it' % (comp_of(near[j])[:40], min(st), max(st), far))
    return probs, info


def run_check(log_path, min_grip=MIN_GRIP, joints=True):
    """joints: also check the sim's joints against their hardware (the whole assembly; off for a module alone)."""
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    res = check(d, min_grip)
    bad = [r for r in res if r[2] < min_grip or r[3]]
    jres = joint_check(res) if joints else []
    jbad = [j for j in jres if j[1] == 'FAIL']
    with open(log_path, 'w') as f:
        f.write('fasteners %d, failing %d (grip < %.1f mm; THREAD: ends in a nut or insert; HELD: every part it passes '
                'is clamped; JOINTS: every sim joint is real hardware)\n' % (len(res), len(bad) + len(jbad), min_grip))
        for comp, name, g, probs, _ in sorted(res, key=lambda r: (not r[3], r[2])):
            f.write('%s %6.1f mm  %s / %s\n' % ('FAIL' if g < min_grip or probs else 'ok  ', g, comp[:34], name[:44]))
            for x in probs:
                f.write('            %s\n' % x)
        if joints:
            f.write('sim joints (cad/sim/exo_sim.py) against their hardware (sim_joints.json):\n')
        for j, st, msg in jres:
            f.write('%-4s  %-6s %s\n' % (st, j, msg))
    return len(bad) + len(jbad)


def joint_check(res, spec=None):
    """Every joint in the MuJoCo sim must be made by real, modelled hardware (sim_joints.json): its bolt exists and
    passes, the parts it should clamp are in its clamped stack (head to nut), and each bearing sits on the stack and
    is held by the named part. The sim's joints are ideal hinges that can't come apart, so the sim itself can't see a
    missing connection (the end plate, 25 Oct). Only fasteners present in this design are checked: a joint whose bolt
    is in another document is reported as not found."""
    spec = spec or json.load(open(JOINTS))
    by = {(c_, n_): (probs, info) for c_, n_, g, probs, info in res}
    out = []
    for jn, entries in spec.items():
        if jn.startswith('_'):
            continue
        for e in entries:
            if 'open' in e:
                out.append((jn, 'OPEN', e['open']))
                continue
            comp, bolt = e['bolt']
            hit = [v_ for k, v_ in by.items() if k[0].startswith(comp) and k[1] == bolt]
            if len(hit) != 1:
                out.append((jn, 'FAIL', '%s / %s: %d such bolts in the model' % (comp, bolt, len(hit))))
                continue
            probs, info = hit[0]
            errs = list(probs)
            far = info['far'] if info['far'] is not None else 1e9
            for part in e['clamped']:
                st = [x for k, v_ in info['parts'].items() if k.startswith(part) for x in v_]
                if not st:
                    errs.append('%s is not on the bolt' % part)
                elif min(st) > far:
                    errs.append('%s is only beyond the nut: not clamped' % part)
            for bpat, holder in e['bearings']:
                bs = [(st, h) for bn, (st, h) in info['bearings'].items() if bpat in bn and min(st) <= far]
                if not bs:
                    errs.append('no %s bearing on the clamped stack' % bpat)
                elif not any(any(x.startswith(holder) for x in h) for st, h in bs):
                    errs.append('%s holds none of its %s bearings (held by: %s)'
                                % (holder, bpat, ', '.join(sorted({x for _, h in bs for x in h})) or 'nothing'))
            out.append((jn, 'FAIL' if errs else 'ok', '%s / %s%s' % (comp, bolt, (': ' + '; '.join(errs)) if errs else '')))
    return out
