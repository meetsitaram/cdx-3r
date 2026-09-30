"""Shoulder range-of-motion sweep for the layout.

Kinematics: abduction about X through GH (pack-fixed axis), then flexion about the abducted Z
axis through GH.  Yoke + flexion hub follow abduction only; the upper-arm strut and all arm
parts follow both.  Abduction angles are measured from the scanned hanging arm (the exo rest
pose is L['rest_abd']).  For every pose: min gap of each moving part to the torso (with head/
helmet, without the right arm) and to the fixed exo parts (pack, back plate, saddle, bracket,
abduction hub).
"""
import json
import numpy as np
from scipy import ndimage as ndi

src = open(__file__.replace('rom.py', 'layout.py')).read().split('ARM = (')[0]
exec(src)

ARMSIDE = ('UA near ring', 'UA far ring', 'FA near ring', 'wrist ring + cuff', 'PVC pipes',
           'elbow hub, lateral', 'elbow hub, medial', 'UA strut')
base = {k: abduct(m.sample(3000), -L['rest_abd']) for k, m in moving.items()}   # back to the scan pose

# fixed exo parts as a solid voxel field
fx = np.zeros(S.shape, bool)
for k, m in fixed.items():
    p = m.sample(200000)
    ijk = np.clip(((p - LO) / VOX).astype(int), 0, np.array(S.shape) - 1)
    fx[tuple(ijk.T)] = True
fx = ndi.binary_fill_holes(ndi.binary_closing(fx, iterations=2))
sd_fix = sdf(fx)
# the yoke and flexion hub are attached to the abduction hub: check them against the rest only
fx2 = np.zeros(S.shape, bool)
for k in [k for k in fixed if k not in ('abduction hub', 'abduction mount block')]:
    p = fixed[k].sample(200000); ijk = np.clip(((p - LO) / VOX).astype(int), 0, np.array(S.shape) - 1); fx2[tuple(ijk.T)] = True
sd_fix2 = sdf(ndi.binary_fill_holes(ndi.binary_closing(fx2, iterations=2)))
sd_t = sdf(torso | l_arm)


def flex(p, deg):
    t = np.radians(deg); c, s_ = np.cos(t), np.sin(t)
    q = p - GH
    return GH + np.c_[q[:, 0] * c - q[:, 1] * s_, q[:, 0] * s_ + q[:, 1] * c, q[:, 2]]


ABD = [12, 20, 30, 45, 60]
FLX = [-20, 0, 30, 60, 90, 120]
res = {}
print('min gap mm (to torso+head | to fixed exo parts), worst part.  rows: abduction, cols: flexion')
print('abd\\flx ' + ''.join('%22d' % f for f in FLX))
for a in ABD:
    line = '%6d  ' % a
    for fl in FLX:
        worst_t, worst_f = (1e9, ''), (1e9, '')
        for k, p in base.items():
            q = abduct(flex(p, fl) if k in ARMSIDE else p, a)
            gt, gf = sample(sd_t, q).min(), sample(sd_fix if k in ARMSIDE else sd_fix2, q).min()
            if gt < worst_t[0]: worst_t = (gt, k)
            if gf < worst_f[0]: worst_f = (gf, k)
        res['%d,%d' % (a, fl)] = dict(torso=[float(worst_t[0]), worst_t[1]], fixed=[float(worst_f[0]), worst_f[1]])
        line += '%7.0f|%-5.0f%-9s' % (worst_t[0], worst_f[0], (worst_t[1] if worst_t[0] < worst_f[0] else worst_f[1])[:9])
    print(line)
json.dump(res, open(LAY / 'rom.json', 'w'), indent=1)

print('per-part min gap to torso+head / fixed at selected poses')
for a, fl in [(12, 0), (12, 30), (45, 90), (60, 0), (60, 90)]:
    out = []
    for k, p in base.items():
        q = abduct(flex(p, fl) if k in ARMSIDE else p, a)
        out.append('%s %.0f/%.0f' % (k, sample(sd_t, q).min(), sample(sd_fix if k in ARMSIDE else sd_fix2, q).min()))
    print('abd %d flx %d: ' % (a, fl) + '; '.join(out))
