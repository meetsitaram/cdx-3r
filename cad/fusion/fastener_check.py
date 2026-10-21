"""Fastener engagement test (run inside Fusion on the assembly; results to a log file).

For every bought fastener (screw, bolt, pin, stud) the shank axis is found from its body, then points are sampled
along it on a ring just outside the shank (radius r + 0.8 mm, 8 directions). An axial station counts as "in
material" when at least 5 of the 8 ring points are inside a printed part. A fastener whose stations in material add up
to less than MIN_GRIP mm in the tip half (the end that must bite; the head half only passes through the clamped part)
fails. "Material" = printed parts, PVC pipe, and bought nuts and inserts (a screw into a trapped nut grips the nut).
A failing fastener ends in nothing: it hangs in the air or barely touches its part. Known case: the old
shoulder-rest lock screw (into a trapped nut) passes with 6 mm, as it should. Grip only:
it does not judge how strong the wall around a nut is (docs/bugs/rest-bracket-attachment.md).

    import fastener_check as fc
    fc.run_check(log_path)       # returns the number of failures
"""
import math
import re

import adsk.core
import adsk.fusion

MIN_GRIP = 3.0                                            # mm of the shank's TIP half surrounded by printed material
FASTENER = re.compile(r'(socket head|pan-head|Clevis pin|ball stud|thumb screw|M\d+ x \d+)', re.I)
SKIP = re.compile(r'(nut|insert|washer|spacer|bearing|608|6806|6808|belt|^R-clip|pulley|webbing|buckle)', re.I)


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
    printed, fasteners = [], []
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
        out.append((comp, name, round(grip * 10, 1)))
    return out


def run_check(log_path, min_grip=MIN_GRIP):
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    res = check(d, min_grip)
    bad = [r for r in res if r[2] < min_grip]
    with open(log_path, 'w') as f:
        f.write('fasteners %d, failing %d (grip < %.1f mm)\n' % (len(res), len(bad), min_grip))
        for comp, name, g in sorted(res, key=lambda r: r[2]):
            f.write('%s %6.1f mm  %s / %s\n' % ('FAIL' if g < min_grip else 'ok  ', g, comp[:34], name[:44]))
    return len(bad)
