"""Rough mass + centre-of-mass of the exo (Fusion parts + concept-B arm envelopes from the layout).

Printed parts: PETG 1.27 g/cm3 at an effective 60 % fill (walls + 40 % infill).  PVC: 21.5/15.5 tube
(1.40 g/cm3, modelled solid in CAD -> scaled by the wall-area ratio).  Bearings 6806: 25 g each.
Lateral balance = mass-weighted Z offset from the body midline (MID_Z).
"""
import numpy as np
import trimesh

__file__ = __file__.replace('com.py', 'check_fusion.py')
exec(open(__file__).read().split('# ---- static clearance')[0])

PETG, FILL, PVC = 1.27e-3, 0.60, 1.40e-3                  # g/mm3
TUBE = (21.5 ** 2 - 15.5 ** 2) / 21.5 ** 2
rows = []
for k, m in fparts.items():
    if 'PVC' in k:
        g = m.volume * TUBE * PVC
    else:
        g = m.volume * PETG * FILL
    rows.append((k, g, m.center_mass))
rows.append(('6806 bearings, abduction (2)', 50., GH + [-150, 0, 0]))
rows.append(('6806 bearings, shoulder flexion (2)', 50., abduct(np.array([[GH[0], GH[1], 236.]]), L['rest_abd'])[0]))
for k in ('UA near ring', 'UA far ring', 'FA near ring', 'wrist ring + cuff', 'elbow hub, lateral', 'elbow hub, medial'):
    rows.append(('arm: ' + k, moving[k].volume * PETG * FILL, moving[k].center_mass))
pv = moving['PVC pipes']
rows.append(('arm: PVC pipes (6)', pv.volume * TUBE * PVC, pv.center_mass))
rows.append(('arm: 6806 bearings, elbow (2)', 50., moving['elbow hub, lateral'].center_mass))
M = sum(r[1] for r in rows)
c = sum(r[1] * np.asarray(r[2]) for r in rows) / M
print('%-40s %7s %8s' % ('part', 'g', 'Z-MID'))
for k, g, cm in sorted(rows, key=lambda r: -r[1]):
    print('%-40s %7.0f %8.0f' % (k, g, cm[2] - MID_Z))
tq = sum(r[1] * (r[2][2] - MID_Z) for r in rows) / 1000.        # g*mm -> kg*mm
print('\ntotal %.2f kg, COM X %.0f Y %.0f, lateral offset %.0f mm right of midline (%.2f N*m roll)' %
      (M / 1000, c[0], c[1], c[2] - MID_Z, tq * 9.81 / 1000))
for mb, z in ((0.5, 120), (0.8, 120), (1.0, 120)):
    print('  a %.1f kg battery centred %d mm left of midline would bring it to %.0f mm' %
          (mb, z, (tq - mb * z) / (M / 1000 + mb)))
