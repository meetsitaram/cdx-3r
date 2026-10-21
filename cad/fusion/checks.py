"""Model checks that must pass before prints or model code are committed.

In Fusion, on the assembly document (export_prints.export runs this first; run it alone after a change that exports
nothing, e.g. moved hardware):

    import checks
    checks.run_all('shoulder-back-v3')

It writes fastener_check.txt, collision_check.txt, motion_check.txt (moving parts swept through the poses in
collision_check.POSES) and design_rules.txt (design_rules.py on each module in RULE_MODULES, in its own open
document) into prints/<set>/, each stamped with a hash of the model
sources (the build scripts and layout files here). The pre-commit hook runs `python cad/fusion/checks.py --verify`
whenever model sources or prints are staged: every report must say "failing 0" and carry the current hash, so a
change to the model can't be committed without the checks having run on it.

The poses come from girdle_b.pose in the full shoulder document (ARCHIVE). checks.record_poses() refreshes
motion_poses.json (needs that document open; run it after changing the girdle or arm kinematics or POSES).
"""
import glob
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ASSEMBLY = 'CDX-3R assembly'
REPORTS = ('fastener_check.txt', 'collision_check.txt', 'motion_check.txt', 'design_rules.txt')
RULE_MODULES = {'gripper3': 'CDX-3R gripper 3'}         # modules with design_rules RULES, checked in their own document
ARCHIVE = 'CDX-3R shoulder + back'                       # the one document holding girdle + arm together (for poses)
POSES = os.path.join(HERE, 'motion_poses.json')         # recorded poses: each moving part's motion from rest
# offline tools that don't change the model
NOT_MODEL = {'orient_stls.py', 'print_validate.py', 'print_check.py', 'diag.py', 'export_prints.py',
             'motion_poses.json', 'fea.py', 'retrofit_backer.py'}


def source_hash():
    h = hashlib.sha1()
    for f in sorted(glob.glob(os.path.join(HERE, '*.py')) + glob.glob(os.path.join(HERE, '*.json'))):
        if os.path.basename(f) in NOT_MODEL:
            continue
        h.update(os.path.basename(f).encode())
        h.update(open(f, 'rb').read().replace(b'\r\n', b'\n'))
    return h.hexdigest()[:16]


def record_poses():
    """In Fusion: pose the full shoulder document through collision_check.POSES and save motion_poses.json."""
    import importlib

    import adsk.core
    import collision_check
    importlib.reload(collision_check)
    app = adsk.core.Application.get()
    back = app.activeDocument
    doc = next((d for d in app.documents if d.name == ARCHIVE), None)
    if doc is None:
        raise RuntimeError('open "%s" (project my-projects) to record poses' % ARCHIVE)
    doc.activate()
    try:
        if os.path.exists(POSES):
            os.remove(POSES)
        n = collision_check.record_poses(POSES)
    finally:
        back.activate()
    return '%d poses recorded' % n


def run_all(name):
    """Run every model check on the assembly; raise if any fails. Reports go to prints/<name>/."""
    import importlib

    import adsk.core
    import adsk.fusion
    import collision_check
    import fastener_check
    app = adsk.core.Application.get()
    doc = app.activeDocument
    if doc.name != ASSEMBLY:
        raise RuntimeError('checks run on the whole assembly: activate "%s" (active: %s)' % (ASSEMBLY, doc.name))
    doc.updateAllReferences()                                  # the modules' latest saved versions
    out = os.path.join(ROOT, 'prints', name)
    os.makedirs(out, exist_ok=True)
    stamp = source_hash()
    bad = []
    importlib.reload(fastener_check)
    importlib.reload(collision_check)
    if not os.path.exists(POSES):
        raise RuntimeError('no motion_poses.json: run checks.record_poses() first')
    for rep, fn in (('fastener_check.txt', fastener_check.run_check),
                    ('collision_check.txt', collision_check.run_check),
                    ('motion_check.txt', lambda p: collision_check.sweep(POSES, p))):
        path = os.path.join(out, rep)
        if fn(path):
            bad.append(path)
        with open(path, 'a') as f:
            f.write('source %s\n' % stamp)
    # design rules (floating parts, drive chains, gear meshes, strength) per mechanism module, in its own document
    import design_rules
    importlib.reload(design_rules)
    path = os.path.join(out, 'design_rules.txt')
    fails, lines = 0, []
    for mod, docname in RULE_MODULES.items():
        mdoc = next((app.documents.item(i) for i in range(app.documents.count)
                     if app.documents.item(i).name == docname), None)
        if mdoc is None:
            raise RuntimeError('open "%s" (design rules run in it)' % docname)
        m = importlib.import_module(mod)
        importlib.reload(m)
        mdoc.activate()
        try:
            fails += design_rules.run(path + '.' + mod, m)
        finally:
            doc.activate()
        lines += open(path + '.' + mod).read().splitlines()
        os.remove(path + '.' + mod)
    total = sum(1 for x in lines if x[:4] in ('ok  ', 'FAIL'))
    with open(path, 'w') as f:
        f.write('design rules %d, failing %d (modules: %s)\n' % (total, fails, ', '.join(RULE_MODULES)))
        f.write('\n'.join(x for x in lines if not x.startswith('design rules')) + '\n')
        f.write('source %s\n' % stamp)
    if fails:
        bad.append(path)
    if bad:
        raise RuntimeError('model checks failed: see ' + ', '.join(bad))
    return 'checks ok, source ' + stamp


def verify():
    """For the git hook: every report in prints/* passes and matches the current model sources."""
    stamp = source_hash()
    dirs = sorted({os.path.dirname(p) for r in REPORTS for p in glob.glob(os.path.join(ROOT, 'prints', '*', r))})
    if not dirs:
        return ['no check reports under prints/: run checks.run_all(<set>) in Fusion']
    errs = []
    for d in dirs:
        for r in REPORTS:
            p = os.path.join(d, r)
            rel = os.path.relpath(p, ROOT)
            if not os.path.exists(p):
                errs.append('%s missing' % rel)
                continue
            lines = open(p).read().splitlines()
            if not lines or 'failing 0' not in lines[0]:
                errs.append('%s: %s' % (rel, lines[0] if lines else 'empty'))
            if ('source %s' % stamp) not in lines:
                errs.append('%s is from older model code (current source %s)' % (rel, stamp))
    return errs


if __name__ == '__main__':
    if sys.argv[1:] == ['--hash']:
        print(source_hash())
    elif sys.argv[1:] == ['--verify']:
        e = verify()
        for x in e:
            print('checks: ' + x)
        if e:
            print('checks: in Fusion, activate "%s" and run checks.run_all(<set>) (or export_prints.export)' % ASSEMBLY)
        sys.exit(1 if e else 0)
    else:
        print(__doc__)
