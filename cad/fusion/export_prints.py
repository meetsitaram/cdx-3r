"""Export a print set from the open Fusion document, then orient it for printing. Run inside Fusion (fusion_mcp).

    import export_prints as ep
    ep.export('shoulder-back-v3')            # all parts (two MCP calls if it times out: start=0/15, count=15)
    ep.export('shoulder-back-v3', only=['10_lift_carriage'])

Each STL is exported in the design frame, then `orient_stls.py` (system Python, numpy) rotates it into its print
orientation in place and writes orientation.json. That second step is not optional: the STLs in prints/ are always
pre-rotated so the slicer's auto-orient is never needed (it sends supports into holes). The git pre-commit hook in
.githooks/ orients any STL that reaches a commit unoriented, as a backstop.
"""
import importlib
import os
import shutil
import subprocess

import adsk.core
import adsk.fusion

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SETS = {
    # file name -> (component, body or None for the component's only visible body)
    'shoulder-back-v3': [
        ('01_bottom_node_R', 'Bottom node', 'Bottom node R'),
        ('02_bottom_node_L', 'Bottom node', 'Bottom node L'),
        ('03_bottom_node_splice_plate', 'Bottom node splice plate', None),
        ('04_mid_node', 'Mid node', None),
        ('05_top_node', 'Top node', None),
        ('06_shoulder_block_L', 'Abduction mount blocks', 'Abduction mount block L'),
        ('07_shoulder_tower', 'Shoulder tower', None),
        ('08_lift_link_upper', 'Lift link upper', None),
        ('09_lift_link_lower', 'Lift link lower', None),
        ('10_lift_carriage', 'Lift carriage + SCARA root', None),
        ('11_scara_link1_tray', 'SCARA link 1', 'SCARA link 1 tray'),
        ('12_scara_link1_lid', 'SCARA link 1', 'SCARA link 1 lid'),
        ('13_scara_link2_tray', 'SCARA link 2', 'SCARA link 2 tray'),
        ('14_scara_link2_lid', 'SCARA link 2', 'SCARA link 2 lid'),
        ('15_end_plate_housing', 'SCARA end plate + abduction housing', None),
        ('16_pulley_P0', 'Carriage HW + pulley P0 (buy)', 'pulley P0 (fixed, printed)'),
        ('17_pulley_PA', 'Elbow spool: bolt + pulleys PA/PB (buy)', 'pulley PA (printed)'),
        ('18_pulley_PB', 'Elbow spool: bolt + pulleys PA/PB (buy)', 'pulley PB (printed)'),
        ('19_pulley_P2', 'End plate HW + pulley P2 (buy)', 'pulley P2 (fixed, printed)'),
        ('20_spacer_thick_x8', 'Elbow spool: bolt + pulleys PA/PB (buy)', 'inner-ring spacer (printed)'),
        ('21_spacer_thin_x6', 'Elbow spool: bolt + pulleys PA/PB (buy)', 'link spacer Ø11 x 1 (printed)'),
        ('22_abduction_sleeve', 'Abduction sleeve', None),
        ('23_yoke', 'Yoke', None),
        ('24_flexion_sleeve', 'Flexion axle sleeve', None),
        ('25_upper_arm_link', 'Upper-arm link', None),
        ('26_rest_bracket', 'Rest bracket (on the tower)', None),
        ('27_rest_root_arm', 'Rest root arm', None),
        ('28_rest_blade_1', 'Rest blade 1', None),
        ('29_rest_blade_2', 'Rest blade 2', None),
        ('30_rest_blade_3', 'Rest blade 3', None),
        ('31_rest_washer_x2', 'Rest washers (printed)', 'rest washer, front'),
        ('32_rest_pivot_spacer', 'Rest pivot spacer (printed)', None),
    ],
}


def system_python():
    """The user's Python (with numpy); Fusion's own interpreter has no numpy."""
    for c in (os.path.expandvars(r'%LOCALAPPDATA%\Programs\Python\Python312\python.exe'), shutil.which('python')):
        if c and os.path.exists(c) and 'WindowsApps' not in c:
            return c
    raise RuntimeError('no system Python found for orient_stls.py')


def orient(folder):
    r = subprocess.run([system_python(), os.path.join(HERE, 'orient_stls.py'), folder], capture_output=True, text=True,
                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if r.returncode:
        raise RuntimeError('orient_stls failed:\n' + r.stderr)
    return r.stdout


def export(name, only=None, start=0, count=None, orient_after=True):
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    out = os.path.join(ROOT, 'prints', name)
    os.makedirs(out, exist_ok=True)
    occ = {}
    for o in d.rootComponent.allOccurrences:
        if o.isVisible and not o.component.name.startswith('zz') and '/zz' not in o.fullPathName:
            occ.setdefault(o.component.name, o)
    # every model check (fasteners bite, nothing collides) on the whole assembly first: nothing is exported if one
    # fails. The reports go with the STLs; the git hook refuses a commit without clean, current ones
    import checks
    importlib.reload(checks)
    checks.run_all(name)
    parts = [p for p in SETS[name] if not only or p[0] in only]
    parts = parts[start:None if count is None else start + count]
    em = d.exportManager
    for f, cn, bn in parts:
        o = occ[cn]
        bodies = [x for x in o.component.bRepBodies if x.isVisible]
        body = bodies[0] if bn is None else next(x for x in bodies if x.name == bn)
        opt = em.createSTLExportOptions(body.createForAssemblyContext(o), os.path.join(out, f + '.stl'))
        opt.isBinaryFormat = True
        opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        em.execute(opt)
    done = [p[0] for p in parts]
    # record every part's current volume, so orient_stls.py can flag STLs that no longer match the model
    import json
    vols = {}
    for f, cn, bn in SETS[name]:
        bodies = [x for x in occ[cn].component.bRepBodies if x.isVisible]
        b = bodies[0] if bn is None else next(x for x in bodies if x.name == bn)
        vols[f] = round(b.volume * 1000, 1)                      # mm3
    json.dump(vols, open(os.path.join(out, 'model_volumes.json'), 'w'), indent=1)
    return (done, orient(out)) if orient_after else (done, 'not oriented yet: run orient(%r)' % out)
