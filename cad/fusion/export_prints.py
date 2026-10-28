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
        ('21_spacer_thin_x7', 'Elbow spool: bolt + pulleys PA/PB (buy)', 'link spacer Ø11 x 1 (printed)'),
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
    'gripper3-v1': [                     # prototype 3 gripper, from the 'CDX-3R gripper 3' module doc
        ('01_gripper_base', 'Gripper3 base (printed)', None),
        ('02_gripper_carrier', 'Gripper3 carrier (printed)', None),
        ('03_gripper_grip', 'Gripper3 grip (printed)', None),
        ('03b_gripper_grip_sleeve', 'Gripper3 grip sleeve (printed)', None),
        ('04_gripper_trigger', 'Gripper3 trigger (printed)', None),
        ('05_gripper_y_link', 'Gripper3 link (printed)', None),
        ('06_gripper_collar', 'Gripper3 collar (printed)', None),
        ('07_gripper_claw_TPU_x3', 'Gripper3 claw 1 (TPU)', None),
    ],
}
ELBOW = 'Elbow concept B (copy of CDX-3R elbow concepts, 12 deg)'
SETS['elbow-servo-v1'] = [                     # the XL430 on the elbow's lateral side (elbow-test-v10 parts unchanged)
    ('01_servo_case', ELBOW, 'Hardware (6806 bearings, covers): servo case (print plate down; 6 x M3 x 12 into the old cover inserts)'),
    ('02_servo_strap', ELBOW, 'Hardware (6806 bearings, covers): servo strap (print flat; 2 x M3 x 8)'),
    ('03_servo_horn_coupler', ELBOW, 'Forearm unit: servo horn coupler (print flat, pegs up; 2 x M2.5 x 6 into the horn)'),
    ('04_servo_axle_lateral', ELBOW, 'Forearm unit: servo axle, lateral (print flat, pilot up; 3 x M3 x 8 to hub)'),
]
SMOOTH = {'elbow-servo-v1'}                    # sets whose parts must have no sharp outer edge (fxlib.sharp_outer_edges)
MODULE_CHECKS = {'gripper3-v1': 'gripper3'}   # sets built in a module doc: run that module's own checks instead


def module_checks(name, out, waive=()):
    """Design rules, collisions in the working poses, a motion sweep (squeeze and fold steps) and fasteners for a
    module doc; reports into the print folder in the format checks.verify() wants (first line 'failing N', a
    'source <hash>' stamp). Raises (nothing exported) if any fail."""
    import checks, collision_check, design_rules, fastener_check
    mod = importlib.import_module(MODULE_CHECKS[name])
    for m in (checks, collision_check, design_rules, fastener_check, mod):
        importlib.reload(m)
    stamp = 'source %s' % checks.source_hash()
    nl = chr(10)
    rf = os.path.join(out, 'design_rules.txt')
    design_rules.run(rf, mod)
    fails = [l for l in open(rf) if l.startswith('FAIL') and not any(w in l for w in waive)]
    if waive:                                                     # a waived rule is recorded, never hidden
        open(rf, 'a').write(nl + 'WAIVED for this export (cosmetic, user asked to export): %s' % '; '.join(waive) + nl)
    open(rf, 'a').write(stamp + nl)
    bad = ['design rules: %d' % len(fails)]

    def sweep(poses, fname, title):
        n_bad, body = 0, []
        for f_, q in poses:
            mod.pose(f_, q)
            tmp = os.path.join(out, '_col.txt')
            n = collision_check.run_check(tmp)
            n_bad += n
            body.append('== fold %s, squeeze %s: %d failing' % (f_, q, n) + nl + open(tmp).read())
            os.remove(tmp)
        with open(os.path.join(out, fname), 'w') as f:
            f.write('%s %d poses, failing %d' % (title, len(poses), n_bad) + nl + nl.join(body) + nl + stamp + nl)
        bad.append('%s: %d' % (title, n_bad))
    stow = mod.P['hinge']['stow_deg']
    sweep([(0, 0), (0, 0.5), (0, 1), (stow, 0)], 'collision_check.txt', 'collisions in the working poses:')
    sweep([(0, k / 4) for k in range(5)] + [(stow * k / 8, 0) for k in range(1, 9)], 'motion_check.txt',
          'motion sweep (squeeze 0..1, fold 0..%d):' % stow)
    mod.pose(0, 0)
    ff = os.path.join(out, 'fastener_check.txt')
    bad.append('fasteners: %d' % fastener_check.run_check(ff, joints=False))
    open(ff, 'a').write(stamp + nl)
    if any(not b.endswith(': 0') for b in bad):
        raise RuntimeError('checks failing, nothing exported: ' + '; '.join(bad))
    return bad


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
        raise RuntimeError('orient_stls failed (an STL open in the slicer is locked: close it there):\n' + r.stderr)
    return r.stdout


def export(name, only=None, start=0, count=None, orient_after=True, waive=()):
    d = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    out = os.path.join(ROOT, 'prints', name)
    os.makedirs(out, exist_ok=True)
    # every model check (fasteners bite, nothing collides) on the whole assembly first: nothing is exported if one
    # fails. The reports go with the STLs; the git hook refuses a commit without clean, current ones
    hidden = [o.component.name + ' / ' + b.name for o in d.rootComponent.allOccurrences if o.isVisible
              for b in o.component.bRepBodies if not b.isLightBulbOn and '(buy)' not in o.component.name + b.name
              and not o.component.name.startswith('zz') and '/zz' not in o.fullPathName]
    if hidden:                                    # every check skips hidden bodies: a hidden part is never checked
        raise RuntimeError('hidden bodies (show them first, the checks would skip them): ' + '; '.join(hidden[:8]))
    if name in MODULE_CHECKS:
        module_checks(name, out, waive)
    else:
        import checks
        importlib.reload(checks)
        checks.run_all(name)
    occ = {}                                      # after the checks: they refresh the linked modules, which replaces
    for o in d.rootComponent.allOccurrences:      # every occurrence (looked up before, the export saw the old parts)
        if o.isVisible and not o.component.name.startswith('zz') and '/zz' not in o.fullPathName:
            occ.setdefault(o.component.name, o)
    parts = [p for p in SETS[name] if not only or p[0] in only]
    parts = parts[start:None if count is None else start + count]
    if name in SMOOTH:                            # no sharp outer edge on parts handled every day (user, 26 Oct)
        import fxlib
        sharp = []
        for f, cn, bn in parts:
            bodies = [x for x in occ[cn].component.bRepBodies if x.isVisible]
            b = bodies[0] if bn is None else next(x for x in bodies if x.name == bn)
            k = len(fxlib.sharp_outer_edges(b))
            if k:
                sharp.append('%s: %d' % (f, k))
        if sharp:
            raise RuntimeError('sharp outer edges, nothing exported: ' + ', '.join(sharp))
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
