"""Clearance diagnostics in Fusion: distance from exo parts to the scanned torso, at rest and with the arm
lowered (abduction about the scan X axis through GH). Scan frame: mm, X forward, Y up, Z right."""
import math
import adsk.core
import adsk.fusion

import fxlib as fx
import shoulder as sh

CELL = 20.0


def _to_scan(p):
    """Fusion world (cm, Z up) -> scan (mm, Y up)."""
    return (p.x * 10.0, p.z * 10.0, -p.y * 10.0)


def torso_points(step=1):
    root = fx.design.rootComponent
    ref = next(o for o in root.allOccurrences if o.component.name == 'Reference (scan)')
    mb = next(b for b in ref.component.meshBodies if b.name.startswith('torso'))
    tm = mb.displayMesh
    tr = ref.transform2
    pts = []
    nodes, nrm = tm.nodeCoordinates, tm.normalVectors
    for i in range(0, len(nodes), step):
        p = nodes[i].copy()
        p.transformBy(tr)
        n = nrm[i].copy()
        n.transformBy(tr)
        pts.append(_to_scan(p) + (n.x, n.z, -n.y))
    return pts


def grid(pts):
    g = {}
    for p in pts:
        g.setdefault(tuple(int(math.floor(c / CELL)) for c in p[:3]), []).append(p)
    return g


def nearest(g, p, rmax=6):
    k = tuple(int(math.floor(c / CELL)) for c in p)
    best, bp = 1e9, None
    for r in range(rmax + 1):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if max(abs(dx), abs(dy), abs(dz)) != r:
                        continue
                    for q in g.get((k[0] + dx, k[1] + dy, k[2] + dz), ()):
                        d = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2
                        if d < best:
                            best, bp = d, q
        if bp is not None and math.sqrt(best) < r * CELL:
            break
    return math.sqrt(best), bp


def body_points(pattern_comp, pattern_body=None, include_hidden=False):
    """Tessellated points (scan mm) of bodies whose component name contains pattern_comp."""
    root = fx.design.rootComponent
    out = {}
    for o in root.allOccurrences:
        if pattern_comp not in o.component.name:
            continue
        for b in o.component.bRepBodies:
            if pattern_body and pattern_body not in b.name:
                continue
            if not b.isVisible and not include_hidden:
                continue
            px = b.createForAssemblyContext(o)
            calc = px.meshManager.createMeshCalculator()
            calc.setQuality(adsk.fusion.TriangleMeshQualityOptions.LowQualityTriangleMesh)
            m = calc.calculate()
            out['%s / %s' % (o.component.name[:28], b.name[:40])] = [_to_scan(p) for p in m.nodeCoordinates]
    return out


def rot_x(p, deg, c):
    a = math.radians(deg)
    y, z = p[1] - c[1], p[2] - c[2]
    return (p[0], c[1] + y * math.cos(a) - z * math.sin(a), c[2] + y * math.sin(a) + z * math.cos(a))


def clearance(groups, abd_deltas=(0,), moving=()):
    """min distance per body at each abduction change (deg, + = arm lowered toward the body if moving)."""
    fx.init()
    g = grid(torso_points())
    GH = sh.GH
    rows = []
    for k, pts in groups.items():
        mv = any(s in k for s in moving)
        for da in (abd_deltas if mv else (0,)):
            best = (1e9, None, None)
            for p in pts[::2]:
                q = rot_x(p, da, GH) if da else p
                d, t = nearest(g, q)
                if t is None:
                    continue
                side = sum((q[i] - t[i]) * t[3 + i] for i in range(3))
                sd = d if side >= 0 else -d                # negative = inside the torso (overlap depth)
                if sd < best[0]:
                    best = (sd, q, t)
            rows.append((k, da, round(best[0], 1), [round(c) for c in best[1]] if best[1] else None))
    return rows


def overlap_sectors(groups, da, axis_pt, axis_dir, moving=()):
    """For each body, the angles (deg, around axis_dir through axis_pt) of its points that sit inside the torso
    after lowering the arm by da. 0 deg = lateral (+Z projected), 90 deg = forward."""
    fx.init()
    g = grid(torso_points())
    GH = sh.GH
    u = axis_dir
    ex = [0.0, 0.0, 1.0]
    k = sum(ex[i] * u[i] for i in range(3))
    ex = [ex[i] - k * u[i] for i in range(3)]
    n = math.sqrt(sum(c * c for c in ex))
    ex = [c / n for c in ex]
    ey = [u[1] * ex[2] - u[2] * ex[1], u[2] * ex[0] - u[0] * ex[2], u[0] * ex[1] - u[1] * ex[0]]
    res = {}
    for name, pts in groups.items():
        mv = any(s in name for s in moving)
        hits = []
        for p in pts[::2]:
            q = rot_x(p, da, GH) if (mv and da) else p
            d, t = nearest(g, q)
            if t is None:
                continue
            if sum((q[i] - t[i]) * t[3 + i] for i in range(3)) < 0:
                r = [p[i] - axis_pt[i] for i in range(3)]
                a = math.degrees(math.atan2(sum(r[i] * ey[i] for i in range(3)), sum(r[i] * ex[i] for i in range(3))))
                h = sum(r[i] * u[i] for i in range(3))
                hits.append((round(a), round(h), round(d, 1)))
        if hits:
            angs = sorted(x[0] for x in hits)
            res[name] = dict(n=len(hits), ang=(angs[0], angs[-1]), depth=max(x[2] for x in hits),
                             along=(min(x[1] for x in hits), max(x[1] for x in hits)))
    return res
