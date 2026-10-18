"""Split CDX-3R into module documents (run inside Fusion via MCP, one step per call).

Each module is rebuilt from the scripts into its own clean document (no retired parts, short timeline), saved in the
project folder FOLDER; an assembly document inserts them all as linked components. Every module document keeps the
same top component (shoulder.TOP, rotated x 90 so the design frame's y is up), so the build functions work unchanged
and the modules land in place in the assembly with an identity transform.

    import split
    split.new('frame')        # new document, top component
    split.build('frame')      # build that module (may need several calls for the girdle: see STEPS)
    split.save('frame')       # save into FOLDER as DOCS['frame']
    ... then split.assembly() and split.save_assembly()
"""
import adsk.core
import adsk.fusion

import fxlib as fx
import shoulder as sh

FOLDER = 'CDX-3R v3'
DOCS = {'frame': 'CDX-3R frame', 'girdle': 'CDX-3R shoulder girdle', 'rest': 'CDX-3R shoulder rest',
        'arm': 'CDX-3R shoulder hinges + arm', 'assembly': 'CDX-3R assembly'}
STEPS = {'girdle': ('start', 'tower', 'lift0', 'lift1', 'carriage', 'link1', 'link2', 'spool', 'end', 'spring', 'finish'),
         'rest': ('start', 'bracket', 'root', 'blade1', 'blade2', 'blade3', 'soft', 'hw')}


def app():
    return adsk.core.Application.get()


def folder():
    """The FOLDER inside the project that holds the current shoulder document (created if missing)."""
    a = app()
    proj = next(p for p in a.data.dataProjects if p.name == 'my-projects')
    root = proj.rootFolder
    for i in range(root.dataFolders.count):
        f = root.dataFolders.item(i)
        if f.name == FOLDER:
            return f
    return root.dataFolders.add(FOLDER)


def new(module):
    """A fresh design document with the shared top component."""
    doc = app().documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    d = adsk.fusion.Design.cast(app().activeProduct)
    d.designType = adsk.fusion.DesignTypes.ParametricDesignType
    fx.init()
    sh.top_component()
    return doc.name


def build(module, step=None):
    fx.init()
    top = next(o.component for o in fx.design.rootComponent.occurrences if o.component.name == sh.TOP)
    if module == 'frame':
        parts, cut, g = sh.build_frame(top)
        import shoulder_rest as sr
        fr = next(o.component for o in top.occurrences if o.component.name == 'Frame')
        sr.build_back_pads(fr)
        return dict(cut_list_mm=[(k, round(v, 1)) for k, v in cut])
    if module == 'girdle':
        import girdle_b as gb
        return gb.build_step(step)
    if module == 'rest':
        import shoulder_rest as sr
        return sr.build_step(step)
    if module == 'arm':
        out, cp = sh.build_moving(top, sh.derived())
        return sh.place_elbow()
    raise ValueError(module)


def save(module):
    doc = app().activeDocument
    ok = doc.saveAs(DOCS[module], folder(), 'Built from cad/fusion scripts (split from CDX-3R shoulder + back v54)', '')
    return DOCS[module], ok


def _file(name):
    f = folder()
    for i in range(f.dataFiles.count):
        df = f.dataFiles.item(i)
        if df.name == name:
            return df
    raise KeyError(name)


def assembly():
    """New document: the four modules inserted as linked components (identity: they share the world frame), plus
    the scan reference and the harness illustration."""
    app().documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    d = adsk.fusion.Design.cast(app().activeProduct)
    d.designType = adsk.fusion.DesignTypes.ParametricDesignType
    fx.init()
    root = d.rootComponent
    out = []
    for m in ('frame', 'girdle', 'rest', 'arm'):
        occ = root.occurrences.addByInsert(_file(DOCS[m]), adsk.core.Matrix3D.create(), True)
        occ.isGroundToParent = True
        out.append(occ.component.name)
    top = sh.top_component()                              # scan reference + harness live in the assembly itself
    sh.reference(top)
    return out


def save_assembly():
    return save('assembly')
