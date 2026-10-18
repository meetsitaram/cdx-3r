"""Print-orientation check, run inside Fusion (fusion_mcp script). For each part listed in PARTS ('component' or
'component || body') and each of the 6 axis directions as "up": flat base area on the bed, overhang area (faces more
than 60 deg past vertical) and the part of that overhang whose support would land ON the part (a ray straight down
hits the part): those supports end up inside holes and pockets. Pick the orientation with a big base and ~0 ON.
World axes: x forward, y left, z up (design y)."""
import adsk.core, adsk.fusion, math, random
PARTS = ['Lift carriage + SCARA root', 'Shoulder tower', 'Top node']   # edit: 'component' or 'component || body'
DIRS = {'+z': [0, 0, 1], '-z': [0, 0, -1], '+x': [1, 0, 0], '-x': [-1, 0, 0], '+y': [0, 1, 0], '-y': [0, -1, 0]}


def run(_context: str):
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    occs = [o for o in d.rootComponent.allOccurrences if o.isLightBulbOn and o.isVisible and not o.component.name.startswith('zz')]
    for line in PARTS:
        cn, bn = (line.split(' || ') + [''])[:2]
        o = next(o for o in occs if o.component.name == cn)
        b0 = next(b for b in o.component.bRepBodies if (not bn or b.name == bn))
        body = b0.createForAssemblyContext(o)
        calc = body.meshManager.createMeshCalculator()
        calc.setQuality(adsk.fusion.TriangleMeshQualityOptions.LowQualityTriangleMesh)
        m = calc.calculate(); P = m.nodeCoordinatesAsDouble; I = m.nodeIndices
        tris = []
        for k in range(0, len(I), 3):
            a, b, c = [[P[3 * I[k + j] + i] for i in range(3)] for j in range(3)]
            u = [b[i] - a[i] for i in range(3)]; v = [c[i] - a[i] for i in range(3)]
            n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
            A = math.sqrt(sum(x * x for x in n)) / 2
            if A > 1e-6:
                tris.append(([(a[i] + b[i] + c[i]) / 3 for i in range(3)], [x / (2 * A) for x in n], A))
        res = []
        random.seed(2)
        for dn, up in DIRS.items():
            h = [sum(t[0][i] * up[i] for i in range(3)) for t in tris]
            h0 = min(h)
            base = sum(t[2] for t, hh in zip(tris, h) if hh < h0 + 0.03 and sum(t[1][i] * up[i] for i in range(3)) < -0.99) * 100
            over = [t for t, hh in zip(tris, h) if sum(t[1][i] * up[i] for i in range(3)) < -0.866 and hh > h0 + 0.03]
            area = sum(t[2] for t in over) * 100
            samp = over if len(over) <= 120 else random.sample(over, 120)
            on = 0.0
            for t in samp:
                org = adsk.core.Point3D.create(*[t[0][i] - up[i] * 0.02 for i in range(3)])
                hits = d.rootComponent.findBRepUsingRay(org, adsk.core.Vector3D.create(*[-x for x in up]),
                                                         adsk.fusion.BRepEntityTypes.BRepBodyEntityType, -1.0, True)
                if any(e.name == b0.name and e.assemblyContext and e.assemblyContext.component.name == cn for e in hits):
                    on += t[2]
            on = on * 100 * len(over) / max(1, len(samp))
            res.append((dn, round(base), round(area), round(on)))
        print(cn[:28], bn[:18], ' '.join('%s base%5d over%5d ON%5d |' % r for r in res))
