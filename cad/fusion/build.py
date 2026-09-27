"""Build the CDX-3R design in Fusion from the repo's CAD sources.

Run from the Fusion MCP (or Scripts and Add-Ins) with a small runner:

    import sys, importlib
    sys.path.insert(0, r'C:\\Users\\PC\\projects\\cdx-3r\\cad\\fusion')
    import fxlib, elbow, mech, armor, build
    for m in (fxlib, elbow, mech, armor, build): importlib.reload(m)
    def run(context): build.main(['all'])

Stages rebuild independently; each replaces its own group under
"CDX-3R (Fusion)". 'check' compares every tagged part with the imported
reference mesh of the same layer (bounding boxes, mm).
"""
import time
import traceback

import fxlib as fx
import elbow
import mech
import armor

STAGES = {
    'elbow': elbow.build,
    'shoulder': mech.shoulder,
    'backpack': mech.backpack,
    'system': mech.system,
    'wearer': mech.wearer,
    'armor_limbs': armor.limbs,
    'armor_shoulder': armor.shoulder,
    'armor_elbow_wrist': armor.elbow_wrist,
    'armor_pack': armor.pack,
}


def main(stages, tolerance=1.0):
    fx.init()
    top = fx.top_occurrence().component
    names = list(STAGES) if stages == ['all'] else stages
    for name in names:
        if name == 'check':
            continue
        t0 = time.time()
        try:
            report = STAGES[name](top)
            print(f'{name}: ok in {time.time() - t0:.1f} s')
            for line in report or []:
                print('  ' + line)
        except Exception:
            print(f'{name}: FAILED after {time.time() - t0:.1f} s\n{traceback.format_exc()}')
    if 'check' in stages or stages == ['all']:
        rows, missing = fx.check(tolerance)
        bad = [r for r in rows if r[0] > tolerance]
        print(f'check: {len(rows)} parts, {len(bad)} over {tolerance} mm, {len(missing)} reference layers not built')
        for dev, layer, note in bad:
            print(f'  {dev:8.2f} mm  {layer}  ({note})')
        if missing:
            print('  missing: ' + ', '.join(missing))
