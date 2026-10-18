"""Small documents for Fusion Simulation studies (run inside Fusion via MCP).

A study analyses everything in its document, and the assembly has ~220 parts (scan, PVC, arm...). So each study gets
its own document holding copies of just the parts it needs, at their assembly positions, one component per part (so
each can get its own material). The study itself (material, constraints, loads, solve) is set up in Fusion's
Simulation workspace by hand: the API has no simulation objects. Rebuild after a design change, then re-solve.

    import fea
    fea.build('rest bracket')     # with "CDX-3R assembly" open; creates + saves the document in split.FOLDER
"""
import re

import adsk.core
import adsk.fusion

ASSEMBLY = 'CDX-3R assembly'
# study -> (document name, [(component name, body-name regex)])
STUDIES = {
    'rest bracket': ('CDX-3R FEA rest bracket', [
        ('Tower', r'^Shoulder tower/Body1$'),
        ('Rest bracket', r'^Rest bracket \(on the tower\)/'),
        ('Pivot bolt M6 x 65', r'/M6 x 65 socket head, bracket pivot'),
        ('Washer front', r'/rest washer, front$'),
        ('Washer back', r'/rest washer, back$'),
        ('Nut 1', r'/M6 hex nut, bracket pivot \(buy\)$'),
        ('Nut 2', r'/M6 hex nut, bracket pivot \(buy\) \(1\)$'),
        # the tower hangs from the top node by 4 x M3 into heat-set inserts: fix the node's far end, so the load
        # goes through the screws and the tower's flanges (where it could snap off)
        ('Top node', r'^Top node/Top node$'),
    ] + [('M3 screw %d' % k, r'^Tower HW \(buy\)/M3 x 8 socket head \(buy\)%s$' % sfx)
         for k, sfx in enumerate(('', r' \(1\)', r' \(2\)', r' \(3\)'), 1)]
      + [('M3 insert %d' % k, r'^Tower HW \(buy\)/M3 heat-set insert ruthex 5.7 \(buy\)%s$' % sfx)
         for k, sfx in enumerate(('', r' \(1\)', r' \(2\)', r' \(3\)'), 1)]),
}


# Whole-module studies: every visible solid of the module (path match), minus parts that only slow the mesh down
# or have nothing to hold (belts; pipe screws without their pipe), plus extra single parts. One component per body.
SETS = {
    'girdle': ('CDX-3R FEA shoulder girdle', r'Shoulder girdle', r'(GT2|belt|self-tapping)', [r'^Top node/Top node$']),
}


def _printed(name):
    return '(buy)' not in name or '(printed)' in name


def build_set(key):
    """New study document holding a whole module (SETS[key]) at its assembly position; PETG on printed parts."""
    import split
    app = adsk.core.Application.get()
    src_doc = next(d for d in app.documents if d.name == ASSEMBLY)
    sd = adsk.fusion.Design.cast(src_doc.products.itemByProductType('DesignProductType'))
    doc_name, inc, exc, extra = SETS[key]
    picked = []
    for o in sd.rootComponent.allOccurrences:
        if not o.isVisible or not re.search(inc, o.fullPathName):
            continue
        for b in o.component.bRepBodies:
            n = o.component.name + ' - ' + b.name
            if b.isSolid and b.isVisible and not re.search(exc, n):
                picked.append((n, b.createForAssemblyContext(o)))
    src = _source_bodies(sd)
    for rx in extra:
        hits = [(n, b) for n, b in src if re.search(rx, n)]
        if len(hits) != 1:
            raise RuntimeError('%d bodies match %r' % (len(hits), rx))
        picked.append((hits[0][0].split('/')[0], hits[0][1]))
    tb = adsk.fusion.TemporaryBRepManager.get()
    copies = [(n, tb.copy(b)) for n, b in picked]
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    d = adsk.fusion.Design.cast(app.activeProduct)
    d.designType = adsk.fusion.DesignTypes.DirectDesignType
    for n, body in copies:
        occ = d.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        occ.component.name = n
        occ.component.bRepBodies.add(body).name = n
    set_materials(d, printed=lambda n: _printed(n))
    ok = doc.saveAs(doc_name, split.folder(), 'Whole %s for stress studies (cad/fusion/fea.py)' % key, '')
    return doc_name, ok, len(copies)


def _source_bodies(design):
    out = []
    for o in design.rootComponent.allOccurrences:
        for b in o.component.bRepBodies:
            if b.isSolid:
                out.append((o.component.name + '/' + b.name, b.createForAssemblyContext(o)))
    return out


def build(study):
    import split
    app = adsk.core.Application.get()
    src_doc = next(d for d in app.documents if d.name == ASSEMBLY)
    src_doc.activate()
    src = _source_bodies(adsk.fusion.Design.cast(app.activeProduct))
    doc_name, parts = STUDIES[study]
    tb = adsk.fusion.TemporaryBRepManager.get()
    picked = []
    for comp, rx in parts:
        hits = [b for n, b in src if re.search(rx, n)]
        if len(hits) != 1:
            raise RuntimeError('%s: %d bodies match %r' % (comp, len(hits), rx))
        picked.append((comp, tb.copy(hits[0])))              # world position (assembly context)
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    d = adsk.fusion.Design.cast(app.activeProduct)
    d.designType = adsk.fusion.DesignTypes.DirectDesignType  # plain bodies, no timeline
    root = d.rootComponent
    for comp, body in picked:
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        occ.component.name = comp
        occ.component.bRepBodies.add(body).name = comp
    ok = doc.saveAs(doc_name, split.folder(), 'Copies of the parts for the %s stress study (cad/fusion/fea.py)' % study, '')
    return doc_name, ok, [c for c, _ in picked]


# Printed PETG as the slicer makes it (Bambu "0.20mm Strength": 6 walls, 5 top / 3 bottom layers, 25 % grid). Plates
# of 6-7 mm come out nearly solid (6 walls = ~2.5 mm a side), so near-solid stiffness; strength is the layer-to-layer
# value (weaker than the 50 MPa of solid PETG). Units as Fusion stores them: kPa, kg/m3.
PETG = dict(name='PETG, printed (6 walls, 25% grid)', E=1.9e6, nu=0.38, yield_=30000.0, tensile=40000.0, rho=1150.0)
PRINTED = ('Tower', 'Rest bracket', 'Washer front', 'Washer back', 'Top node')


def set_materials(design=None, printed=None):
    """Adds the printed-PETG material to the open study document and gives it to the printed parts."""
    app = adsk.core.Application.get()
    d = design or adsk.fusion.Design.cast(app.activeProduct)
    m = d.materials.itemByName(PETG['name'])
    new = m is None
    if new:                                   # properties can only be set before the material is in use
        base = app.materialLibraries.itemByName('Fusion Material Library').materials.itemByName('ABS Plastic')
        m = d.materials.addByCopy(base, PETG['name'])
    props = m.materialProperties
    G = PETG['E'] / (2 * (1 + PETG['nu']))
    for pid, v in () if not new else (('structural_Young_modulus', PETG['E']), ('structural_Poisson_ratio', PETG['nu']),
                   ('structural_Shear_modulus', G), ('structural_Minimum_yield_stress', PETG['yield_']),
                   ('structural_Minimum_tensile_strength', PETG['tensile']), ('structural_Density', PETG['rho'])):
        for suffix in ('', '_1', '_2', '_12', '_23', '_X', '_Y', '_Z'):
            p = props.itemById(pid + suffix)
            if p is not None:
                p.value = v
    for o in d.rootComponent.occurrences:
        if (printed(o.component.name) if printed else o.component.name in PRINTED):
            o.component.material = m
    return {k: props.itemById(k).value for k in ('structural_Young_modulus', 'structural_Minimum_yield_stress')}


def add_missing(study):
    """Copies the parts of STUDIES[study] that the open study document doesn't have yet (keeps the study set up in
    the browser), sets materials and saves."""
    app = adsk.core.Application.get()
    doc_name, parts = STUDIES[study]
    src_doc = next(d for d in app.documents if d.name == ASSEMBLY)
    src = _source_bodies(adsk.fusion.Design.cast(src_doc.products.itemByProductType('DesignProductType')))
    doc = next(d for d in app.documents if d.name == doc_name)
    d = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    have = {o.component.name for o in d.rootComponent.occurrences}
    tb = adsk.fusion.TemporaryBRepManager.get()
    added = []
    for comp, rx in parts:
        if comp in have:
            continue
        hits = [b for n, b in src if re.search(rx, n)]
        if len(hits) != 1:
            raise RuntimeError('%s: %d bodies match %r' % (comp, len(hits), rx))
        occ = d.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        occ.component.name = comp
        occ.component.bRepBodies.add(tb.copy(hits[0])).name = comp
        added.append(comp)
    set_materials(d)
    ok = doc.save('Added %s (fea.add_missing)' % ', '.join(added)) if added else None
    return added, ok
