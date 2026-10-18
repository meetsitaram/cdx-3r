"""Collision test (run inside Fusion on the assembly document; results to a log file).

Every visible solid body of the assembly (printed parts and bought hardware alike) is checked against every other
with Fusion's interference analysis (also two bodies of one component: a hardware component holds many bolts).
Faces that only touch don't count. A pair
whose overlap is at least MIN_VOL mm3 fails unless it is listed in ALLOWED with the reason it is meant to be so
(a press fit, a screw cutting its own thread). Only bodies whose bounding boxes overlap are passed to Fusion, in
small groups, so a run takes seconds, not minutes.

    import collision_check as cc
    cc.run_check(log_path)        # returns the number of failing pairs
"""
import re

import adsk.core
import adsk.fusion

MIN_VOL = 1.0                                             # mm3; below this it is a modelling tolerance
# (regex on body A, regex on body B, why it is fine). Matched both ways round.
ALLOWED = [
    (r'heat-set insert', r'.', 'insert melts into its hole'),
    (r'self-tapping', r'.', 'cuts its own thread'),
    (r'Reference|scan|Harness', r'.', 'not a part'),
    (r'Gas spring (cylinder|rod)', r'Gas spring (cylinder|rod)', 'the bought strut itself: rod in cylinder, end fittings'),
    (r'Clevis pin', r'R-clip', 'the R-clip goes through the pin'),
    (r'hook-and-loop', r'M3 x 8 socket head', 'soft pad over M3 heads 0.5 mm proud (ASSEMBLY step 3 note)'),
]


def _bodies(design):
    out = []
    for o in design.rootComponent.allOccurrences:
        if not o.isVisible or re.search(r'Reference|Harness|scan', o.fullPathName, re.I):
            continue
        for b in o.component.bRepBodies:
            if b.isVisible and b.isSolid:
                out.append((o.fullPathName, b.createForAssemblyContext(o)))
    return out


def _path(body):
    """'component/body name' of a result body. Interference results come back without their assembly context, so
    the occurrence path is empty: name by the owning component (two bodies of one component = one part)."""
    return body.parentComponent.name + '/' + body.name


def _overlap(a, b, pad=0.01):
    a0, a1, b0, b1 = a.minPoint.asArray(), a.maxPoint.asArray(), b.minPoint.asArray(), b.maxPoint.asArray()
    return all(a0[i] - pad <= b1[i] and b0[i] - pad <= a1[i] for i in range(3))


def _allowed(n1, n2):
    for ra, rb, why in ALLOWED:
        if (re.search(ra, n1, re.I) and re.search(rb, n2, re.I)) or (re.search(ra, n2, re.I) and re.search(rb, n1, re.I)):
            return why
    return None


def check(design, min_vol=MIN_VOL, only=None):
    """[(mm3, body A, body B, allowed-reason or None)] for every overlapping pair of bodies from different parts.
    only: regex; if given, at least one body of each pair must match it (path or name)."""
    bodies = _bodies(design)
    boxes = [(p, b, b.boundingBox) for p, b in bodies]
    seen, rows = set(), []
    for i, (p1, b1, bb1) in enumerate(boxes):
        if only and not re.search(only, p1 + ' ' + b1.name, re.I):
            continue
        cand = [(p2, b2) for j, (p2, b2, bb2) in enumerate(boxes) if j != i and _overlap(bb1, bb2)]
        if not cand:
            continue
        coll = adsk.core.ObjectCollection.create()
        coll.add(b1)
        for _, b2 in cand:
            coll.add(b2)
        ii = design.createInterferenceInput(coll)
        ii.areCoincidentFacesIncluded = False
        res = design.analyzeInterference(ii)
        for k in range(res.count):
            r = res.item(k)
            n1, n2 = _path(r.entityOne), _path(r.entityTwo)
            if n1 == n2:
                continue
            key = tuple(sorted([n1, n2]))
            if key in seen:
                continue
            seen.add(key)
            v = r.interferenceBody.volume * 1000
            if v >= min_vol:
                rows.append((round(v, 1), key[0], key[1], _allowed(key[0], key[1])))
    return sorted(rows, reverse=True)


def run_check(log_path, min_vol=MIN_VOL, only=None):
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    rows = check(d, min_vol, only)
    bad = [r for r in rows if not r[3]]
    with open(log_path, 'w') as f:
        f.write('collisions %d, failing %d (overlap >= %.1f mm3)%s\n' % (len(rows), len(bad), min_vol,
                                                                       ' only ' + only if only else ''))
        for v, a, b, why in rows:
            f.write('%s %8.1f mm3  %s  <>  %s%s\n' % ('ok  ' if why else 'FAIL', v, a[-60:], b[-60:],
                                                     '  (' + why + ')' if why else ''))
    return len(bad)


# ------------------------------------------------------------------ moving parts: the same test through the motion range
# Poses: (label, girdle displacement mm (x fwd, y up, z right), abduction deg from rest (+ out), flexion deg (+ fwd)).
# Ranges from LESSONS / motion.py: shrug 60, down 20, reach 35, squeeze 35, out/in 25; abduction rest 20 -> stop 95;
# flexion -20 .. 120.
POSES = [('shrug', (0, 60, 0), 0, 0), ('down', (0, -20, 0), 0, 0), ('reach', (35, 0, 0), 0, 0),
         ('squeeze', (-35, 0, 0), 0, 0), ('out', (0, 0, 25), 0, 0), ('in', (0, 0, -25), 0, 0),
         ('abduct 25', (0, 0, 0), 25, 0), ('abduct 35', (0, 0, 0), 35, 0), ('abduct 45', (0, 0, 0), 45, 0),
         ('abduct 55', (0, 0, 0), 55, 0), ('abduct 65', (0, 0, 0), 65, 0), ('abduct 75', (0, 0, 0), 75, 0), ('abduct 75 + shrug', (0, 60, 0), 75, 0),
         ('abduct 75 + reach', (35, 0, 0), 75, 0), ('abduct 75 + squeeze', (-35, 0, 0), 75, 0),
         ('abduct 75 + in', (0, 0, -25), 75, 0), ('abduct 40 + out', (0, 0, 25), 40, 0),
         ('flex 120', (0, 0, 0), 0, 120), ('flex -20', (0, 0, 0), 0, -20), ('abduct 40 + flex 120', (0, 0, 0), 40, 120),
         ('shrug + flex 120', (0, 60, 0), 0, 120), ('squeeze + flex -20', (-35, 0, 0), 0, -20)]
# Known, open findings in the motion sweep: (pose regex, body A regex, body B regex, reason). Only those poses and pairs
# pass; anything new still fails. Remove an entry when its bug is fixed.
MOTION_KNOWN = [
    (r'^abduct (65|75)', r'Yoke|Abduction sleeve|HW abd|Upper-arm link|Flexion axle sleeve|HW flex',
     r'Shoulder rest \(right\)', 'open: docs/bugs/raised-arm-hits-shoulder-rest.md'),
    (r'shrug', r'Lift link lower', r'Lift carriage', 'open: docs/bugs/full-shrug-lift-link-touches-carriage.md'),
]


def _known(lab, n1, n2):
    for pose, ra, rb, why in MOTION_KNOWN:
        if re.search(pose, lab) and ((re.search(ra, n1) and re.search(rb, n2)) or (re.search(ra, n2) and re.search(rb, n1))):
            return why
    return None


ARM = ('Yoke', 'Abduction sleeve', 'HW abd (buy)', 'Upper-arm link', 'Flexion axle sleeve', 'HW flex (buy)')
FLEX = ('Upper-arm link', 'Flexion axle sleeve', 'HW flex (buy)', 'Elbow concept')


def record_poses(path, start=0, count=None):
    """In the full shoulder document (the only one holding girdle and arm together): pose the girdle + abduction
    (girdle_b.pose) and store each moving component's world motion from rest in a JSON file."""
    import json
    import girdle_b as gb
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    occ = {}
    for o in d.rootComponent.allOccurrences:
        if o.isVisible and not o.component.name.startswith('zz'):
            occ.setdefault(o.component.name, o)
    names = [n for n in occ if gb._role(n) or n.startswith(ARM) or n.startswith('Elbow concept')]
    gb.pose((0, 0, 0), 0)
    rest = {n: occ[n].transform2.copy() for n in names}
    try:
        data = json.load(open(path))
    except (OSError, ValueError):
        data = {}
    end = len(POSES) if count is None else min(len(POSES), start + count)
    for lab, disp, abd, flex in POSES[start:end]:
        gb.pose(disp, abd)
        data[lab] = {}
        for n in names:
            m = rest[n].copy()
            m.invert()
            m.transformBy(occ[n].transform2)
            data[lab][n] = list(m.asArray())
    gb.pose((0, 0, 0), 0)
    json.dump(data, open(path, 'w'))
    return end


def _flex_matrix(bodies, deg):
    """Flexion: rotation about the 6808 pair's axis (rest pose), signed so +deg swings the elbow forward (+x world)."""
    import math
    brg = [b for p, b in bodies if '6808' in b.name]
    c = [[(b.boundingBox.minPoint.asArray()[i] + b.boundingBox.maxPoint.asArray()[i]) / 2 for i in range(3)]
         for b in brg[:2]]
    ax = adsk.core.Vector3D.create(*[c[1][i] - c[0][i] for i in range(3)])
    org = adsk.core.Point3D.create(*[(c[0][i] + c[1][i]) / 2 for i in range(3)])
    el = [b for p, b in bodies if p.find('Elbow concept') >= 0]
    pe = [sum((b.boundingBox.minPoint.asArray()[i] + b.boundingBox.maxPoint.asArray()[i]) / 2 for b in el) / len(el)
          for i in range(3)]
    m = adsk.core.Matrix3D.create()
    m.setToRotation(math.radians(30), ax, org)                 # which way is forward?
    q = adsk.core.Point3D.create(*pe)
    q.transformBy(m)
    sign = 1 if q.x > pe[0] else -1
    m.setToRotation(math.radians(sign * deg), ax, org)
    return m


def sweep(path, log_path, min_vol=MIN_VOL, labels=None):
    """In the assembly: move temporary copies of the moving parts into each recorded pose (plus flexion) and
    intersect them with every other body. Returns the number of failing (pose, pair)."""
    import json
    data = json.load(open(path))
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    tb = adsk.fusion.TemporaryBRepManager.get()
    bodies = _bodies(d)
    rows = []
    for lab, disp, abd, flex in POSES:
        if lab not in data or (labels and lab not in labels):
            continue
        F = _flex_matrix(bodies, flex) if flex else None
        cur = []                                               # (name, temp body, motion key)
        for p, b in bodies:
            cn = b.parentComponent.name                        # not split from the path: names contain '+'
            D = data[lab].get(cn)
            fl = F is not None and cn.startswith(FLEX)
            if D is None and not fl:
                cur.append((p + '/' + b.name, b, None))
                continue
            M = adsk.core.Matrix3D.create()
            if fl:
                M.transformBy(F)
            if D is not None:
                m = adsk.core.Matrix3D.create()
                m.setWithArray(D)
                M.transformBy(m)
            t = tb.copy(b)
            tb.transform(t, M)
            cur.append((p + '/' + b.name, t, (tuple(round(v, 6) for v in M.asArray()))))
        boxes = [(n, t, k, t.boundingBox) for n, t, k in cur]
        for i, (n1, t1, k1, bb1) in enumerate(boxes):
            if k1 is None:
                continue
            for j, (n2, t2, k2, bb2) in enumerate(boxes):
                if j == i or (k2 is not None and (j < i or k2 == k1)) or not _overlap(bb1, bb2, 0.0):
                    continue                                   # moving vs static, and moving pairs that move apart
                a = tb.copy(t1)
                tb.booleanOperation(a, tb.copy(t2), adsk.fusion.BooleanTypes.IntersectionBooleanType)
                v = a.volume * 1000
                if v >= min_vol:
                    why = _allowed(n1, n2) or _known(lab, n1, n2)
                    rows.append((lab, round(v, 1), n1, n2, why))
    missing = [p[0] for p in POSES if p[0] not in data]           # POSES changed since the last recording
    bad = [r for r in rows if not r[4]] + missing
    with open(log_path, 'w') as f:
        f.write('motion poses %d, collisions %d, failing %d (overlap >= %.1f mm3)\n'
                % (len(POSES) - len(missing), len(rows), len(bad), min_vol))
        for m in missing:
            f.write('FAIL pose not recorded: %s (run checks.record_poses())\n' % m)
        for lab, v, a, b, why in sorted(rows, key=lambda r: (r[4] is not None, -r[1])):
            f.write('%s %-22s %8.1f mm3  %s  <>  %s%s\n' % ('ok  ' if why else 'FAIL', lab, v, a[-55:], b[-55:],
                                                           '  (' + why + ')' if why else ''))
    return len(bad)
