"""Design-rule checks for a mechanism module (gripper first): things the collision and fastener checks can't see.

    import design_rules as dr
    dr.run(path, gripper)          # in Fusion, with the module's document active; returns the number of failures

A module opts in by defining RULES (see gripper.RULES) and pose(*args). Rules:

  floating   every body touches another body (within TOL), and every body links back to the anchor part through
             touching bodies. Catches parts hanging in thin air (a cable housing with no stops, a coil with no spool)
             and sub-assemblies that touch each other but nothing that holds them.
  chains     for each drive chain (in its pose), consecutive links touch: trigger -> wire -> pusher -> ... -> fingers.
             Catches a trigger that drives nothing.
  meshes     a gear that should mesh is modelled as a gear (at least 2 faces per tooth: a plain cylinder fails) and
             sits within TOL of its partner (rack or gear); overlap is the collision check's job.
  cables     a wire must be insertable: wherever its route runs enclosed in printed material (every ray square to
             the route hits printed material within ENCLOSED mm) it must run straight, since a stiff wire can't be
             pushed round a hidden bend. Each end must sit against a body named like the module's anchor word
             (a barrel nipple, a screw nipple). Catches a tunnel that turns inside solid plastic.
  strength   slender printed features under their design load: cantilever bending stress vs PETG yield, across or
             along the layers; safety factor >= SF_MIN. Sections come from the module's parameters, so a thinner
             part fails here first.
"""
import math

import adsk.core
import adsk.fusion

TOL = 0.3                       # mm: "touching" (printed clearances are 0.2-0.3)
SF_MIN = 3.0
YIELD = {'PETG along layers': 45.0, 'PETG across layers': 30.0, 'steel': 600.0,
         'steel threaded rod 4.8': 340.0}   # MPa


def _bodies(name_filter):
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    out = []
    for o in d.rootComponent.allOccurrences:
        if not o.isVisible or name_filter not in o.fullPathName:
            continue
        for b in o.component.bRepBodies:
            if b.isVisible and b.isSolid:
                out.append((o.component.name + '/' + b.name, b.createForAssemblyContext(o)))
    return out


def _boxes(bodies):
    tb = adsk.fusion.TemporaryBRepManager.get()
    out = []
    for n, b in bodies:
        bb = tb.copy(b).boundingBox                    # a temporary copy: its box is in the assembly frame
        out.append((n, b, [x * 10 for x in bb.minPoint.asArray()], [x * 10 for x in bb.maxPoint.asArray()]))
    return out


def _near(b1, b2, tol=TOL):
    lo1, hi1, lo2, hi2 = b1[2], b1[3], b2[2], b2[3]
    return all(lo1[k] - tol <= hi2[k] and lo2[k] - tol <= hi1[k] for k in range(3))


def distance(a, b):
    """Minimum distance (mm) between two body proxies; 0 when they touch or overlap."""
    mm = adsk.core.Application.get().measureManager
    return mm.measureMinimumDistance(a, b).value * 10


def find(boxes, pattern):
    p = pattern.lower()
    hits = [x for x in boxes if p in x[0].lower()]
    return hits


def check_floating(boxes, anchor):
    """Bodies with no neighbour within TOL, and bodies not linked to the anchor."""
    n = len(boxes)
    adj = [set() for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if _near(boxes[i], boxes[j]) and distance(boxes[i][1], boxes[j][1]) <= TOL:
                adj[i].add(j)
                adj[j].add(i)
    rows = []
    for i in range(n):
        if not adj[i]:
            rows.append(('FAIL', 'floating: touches nothing', boxes[i][0]))
    roots = [i for i in range(n) if anchor.lower() in boxes[i][0].lower()]
    seen, todo = set(roots), list(roots)
    while todo:
        k = todo.pop()
        for j in adj[k] - seen:
            seen.add(j)
            todo.append(j)
    for i in range(n):
        if i not in seen and adj[i]:
            rows.append(('FAIL', 'not linked to %s' % anchor, boxes[i][0]))
    if not roots:
        rows.append(('FAIL', 'anchor part missing', anchor))
    return rows


def check_chain(boxes, label, links):
    rows = []
    for a, b in links:
        ha, hb = find(boxes, a), find(boxes, b)
        if not ha or not hb:
            rows.append(('FAIL', '%s: missing part' % label, '%s -> %s (%s)' % (a, b, 'no ' + (a if not ha else b))))
            continue
        d = min(distance(x[1], y[1]) for x in ha for y in hb)
        rows.append(('ok  ' if d <= TOL else 'FAIL', '%s: %.2f mm' % (label, d), '%s -> %s' % (a, b)))
    return rows


def check_mesh(boxes, gear, partner, teeth):
    hg, hp = find(boxes, gear), find(boxes, partner)
    if not hg or not hp:
        return [('FAIL', 'mesh: missing part', '%s / %s' % (gear, partner))]
    g = hg[0]
    faces = g[1].faces.count
    d = min(distance(g[1], y[1]) for y in hp)
    ok = faces >= 2 * teeth and d <= TOL
    why = []
    if faces < 2 * teeth:
        why.append('%d faces < %d: no teeth modelled' % (faces, 2 * teeth))
    if d > TOL:
        why.append('%.2f mm from its partner' % d)
    return [('ok  ' if ok else 'FAIL', 'mesh %s z%d: %s' % (gear, teeth, '; '.join(why) or '%d faces, %.2f mm' % (faces, d)),
             '%s <> %s' % (gear, partner))]


ENCLOSED = 15.0                 # mm: a ray hitting printed material this close counts as "walled in"
STRAIGHT_DEG = 10.0


def _printed_hit(origin, d, maxlen):
    """Does a ray from origin (mm) along d hit a printed body within maxlen mm?"""
    root = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct).rootComponent
    hits = adsk.core.ObjectCollection.create()
    ents = root.findBRepUsingRay(adsk.core.Point3D.create(*[x / 10 for x in origin]),
                                 adsk.core.Vector3D.create(*d), adsk.fusion.BRepEntityTypes.BRepBodyEntityType,
                                 -1.0, True, hits)
    for i in range(ents.count):
        b = ents.item(i)
        hp = hits.item(i)
        dist = math.sqrt(sum((hp.asArray()[k] * 10 - origin[k]) ** 2 for k in range(3)))
        if dist <= maxlen and '(printed)' in (b.parentComponent.name + b.name):
            return True
    return False


def check_cable(boxes, label, route_world, anchor_word, step=2.0):
    """route_world: polyline in the design's root frame (mm)."""
    rows = []
    samples = []
    for a, b in zip(route_world[:-1], route_world[1:]):
        v = [b[k] - a[k] for k in range(3)]
        L = math.sqrt(sum(x * x for x in v))
        if L < 1e-6:
            continue
        u = [x / L for x in v]
        n = max(1, int(L / step))
        for i in range(n):
            t = (i + 0.5) * L / n
            samples.append(([a[k] + u[k] * t for k in range(3)], u))
    enclosed = []
    for pt, u in samples:
        ref = [1, 0, 0] if abs(u[0]) < 0.9 else [0, 1, 0]
        e1 = [u[1] * ref[2] - u[2] * ref[1], u[2] * ref[0] - u[0] * ref[2], u[0] * ref[1] - u[1] * ref[0]]
        m = math.sqrt(sum(x * x for x in e1))
        e1 = [x / m for x in e1]
        e2 = [u[1] * e1[2] - u[2] * e1[1], u[2] * e1[0] - u[0] * e1[2], u[0] * e1[1] - u[1] * e1[0]]
        ok = True
        for j in range(8):
            ang = j * math.pi / 4
            d = [math.cos(ang) * e1[k] + math.sin(ang) * e2[k] for k in range(3)]
            if not _printed_hit(pt, d, ENCLOSED):
                ok = False
                break
        enclosed.append(ok)
    runs, cur = [], []
    for (pt, u), enc in zip(samples, enclosed):
        if enc:
            cur.append((pt, u))
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    worst = 0.0
    for run in runs:
        for (p1, u1) in run:
            for (p2, u2) in run:
                c = max(-1.0, min(1.0, sum(u1[k] * u2[k] for k in range(3))))
                worst = max(worst, math.degrees(math.acos(c)))
    tunnel = sum(len(r) for r in runs) * step
    rows.append(('ok  ' if worst <= STRAIGHT_DEG else 'FAIL',
                 '%s: enclosed %.0f mm, bends %.0f deg inside' % (label, tunnel, worst),
                 'a stiff wire must be pushable through every enclosed run'))
    ends = find(boxes, anchor_word)
    wire = find(boxes, 'inner wire')
    for which, pt in (('trigger end', route_world[0]), ('far end', route_world[-1])):
        near = [x for x in ends if all(x[2][k] - 1.0 <= pt[k] <= x[3][k] + 1.0 for k in range(3))]
        rows.append(('ok  ' if near else 'FAIL', '%s: %s anchored' % (label, which),
                     'needs a %s at %s' % (anchor_word, [round(c, 1) for c in pt])))
    return rows


def check_ball(module, label, center, radius, grip_pose, clear_pose, parts):
    """A ball (e.g. a ping-pong ball) between the claws: in grip_pose (closed a little past first contact) every claw
    must press into it; in clear_pose (opened a little before contact) none may touch it. Together: they close on it."""
    tb = adsk.fusion.TemporaryBRepManager.get()
    ball = tb.createSphere(adsk.core.Point3D.create(*[v / 10.0 for v in center]), radius / 10.0)
    rows = []
    for which, pose, want in (('grips', grip_pose, True), ('clear before contact', clear_pose, False)):
        module.pose(*pose)
        for n, b in _bodies(module.NAME):
            if not any(p.lower() in n.lower() for p in parts):
                continue
            x = tb.copy(b)
            tb.booleanOperation(x, tb.copy(ball), adsk.fusion.BooleanTypes.IntersectionBooleanType)
            v = x.volume * 1000
            ok = (v > 0.5) if want else (v < 0.5)
            rows.append(('ok  ' if ok else 'FAIL', '%s (%s): %.1f mm3 overlap' % (label, which, v), n.split('/')[0]))
    return rows


def section_modulus(sec):
    if sec[0] == 'round':
        return math.pi * sec[1] ** 3 / 32
    _, depth, width = sec                              # depth: in the bending direction
    return width * depth ** 2 / 6


def check_strength(loads):
    rows = []
    for ld in loads:
        z = section_modulus(ld['section'])
        stress = ld['force'] * ld['arm'] / z
        sf = YIELD[ld['material']] / stress
        rows.append(('ok  ' if sf >= SF_MIN else 'FAIL', 'strength SF %.1f (%.1f MPa, %s)' % (sf, stress, ld['material']),
                     '%s: %g N at %g mm' % (ld['name'], ld['force'], ld['arm'])))
    return rows


def run(path, module):
    """Run every rule of module.RULES; write the report to path; return the number of failures."""
    R = module.RULES
    rows = []
    module.pose(*R['rest'])
    boxes = _boxes(_bodies(module.NAME))
    rows += check_floating(boxes, R['anchor'])
    for gear, partner, teeth in R['meshes']:
        rows += check_mesh(boxes, gear, partner, teeth)
    for label, pose, links in R['chains']:
        module.pose(*pose)
        rows += check_chain(_boxes(_bodies(module.NAME)), label, links)
    module.pose(*R['rest'])
    for label, route, anchor_word in R.get('cables', []):
        rows += check_cable(boxes, label, route(), anchor_word)   # body and ray queries share the module's frame
    for label, pose, pairs in R.get('apart', []):                 # parts that must NOT touch in this pose
        module.pose(*pose)
        bx = _boxes(_bodies(module.NAME))
        for a, b in pairs:
            d = min(distance(x[1], y[1]) for x in find(bx, a) for y in find(bx, b))
            rows.append(('ok  ' if d > TOL else 'FAIL', '%s: %.2f mm apart' % (label, d), '%s / %s' % (a, b)))
    for label, center, radius, grip_pose, clear_pose, parts in R.get('balls', []):
        rows += check_ball(module, label, center, radius, grip_pose, clear_pose, parts)
    module.pose(*R['rest'])
    for fn in R.get('geometry', []):                    # module's own pure-geometry rules: (status, label, detail)
        rows += fn()
    rows += check_strength(R['loads']())
    bad = [r for r in rows if r[0] == 'FAIL']
    with open(path, 'w') as f:
        f.write('design rules %d, failing %d (touch <= %.1f mm, safety factor >= %.0f)\n' % (len(rows), len(bad), TOL, SF_MIN))
        for r in sorted(rows, key=lambda r: r[0] != 'FAIL'):
            f.write('%s %-58s %s\n' % r)
    return len(bad)
