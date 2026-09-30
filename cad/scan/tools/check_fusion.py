"""Clearance + shoulder ROM check of the Fusion-built parts against the scanned body.

Fusion STLs (out/fusion/*.stl) are in Fusion world coordinates: the top component is the scan
frame rotated +90 deg about X, so scan (x, y, z) = (X, Z, -Y).  Moving parts come out in the
rest pose (abducted rest_abd); they are un-posed, then swept like rom.py.
"""
import numpy as np
import trimesh
from pathlib import Path

src = open(__file__.replace('check_fusion.py', 'layout.py')).read().split('ARM = (')[0]
exec(src)                                                  # body fields, layout parts, abduct(), sample()

FU = OUT / 'fusion'
ABD_SIDE = {'Yoke', 'Abduction_sleeve', 'HW_abd_(buy)'}
FLEX_SIDE = {'Upper-arm_link', 'Flexion_axle_sleeve', 'HW_flex_(buy)'}


def load(f):
    m = trimesh.load(f, force='mesh')
    v = m.vertices.copy()
    m.vertices = v                                         # occurrence STL export is already in the scan frame
    return m


fparts = {f.stem: load(f) for f in sorted(FU.glob('*.stl'))}
# the pipe head and the elbow copy are exported in the elbow concept frame: map them to the scan frame
_e = np.array([0, 0, 1.]) - _u * _u[2]; _e /= np.linalg.norm(_e); _n = np.cross(_u, _e); _n = _n if _n[0] > 0 else -_n
CONCEPT = [k for k in fparts if k.startswith(('Upper-arm_pipe_head', 'Elbow_concept_B'))]
for k in CONCEPT:
    v = fparts[k].vertices
    fparts[k].vertices = EL + v[:, :1] * _e + v[:, 1:2] * _n + v[:, 2:3] * _u
FLEX_SIDE = FLEX_SIDE | set(CONCEPT)
# occurrence export ignores parent transforms: moving parts arrive in the scan (0 deg) pose
scan_pose = {k: m.copy() for k, m in fparts.items() if k in ABD_SIDE | FLEX_SIDE}
for k in scan_pose:
    fparts[k].vertices = abduct(fparts[k].vertices, L['rest_abd'])
print('Fusion parts:', {k: np.round(m.bounds.mean(0)).tolist() for k, m in fparts.items()})

# ---- static clearance, rest pose ----
print('\nrest pose, gap to body (mm): min / p5')
for k, m in fparts.items():
    g = sample(sd_body, m.sample(8000))
    print('  %-28s %7.1f %7.1f' % (k, g.min(), np.percentile(g, 5)))

# ---- self-interference at rest: printed parts vs each other (voxel overlap, 2 mm) ----
def vox(m, pitch=2.0):
    return set(map(tuple, np.floor(m.sample(60000) / pitch).astype(int)))

# ---- ROM: fixed = frame + rest + layout torso-side parts; moving = yoke/axle (abd), link + arm parts (abd+flex)
base = {k: m.sample(4000) for k, m in scan_pose.items()}
arm_layout = ('UA near ring', 'UA far ring', 'FA near ring', 'wrist ring + cuff', 'PVC pipes',
              'elbow hub, lateral', 'elbow hub, medial')
# (the real elbow parts are in the Fusion export now; the layout stand-ins are not used)
fx_ = np.zeros(S.shape, bool)
fixed_meshes = [m for k, m in fparts.items() if k not in ABD_SIDE | FLEX_SIDE]
# (shoulder rest dropped: the backpack straps + hip belt carry the frame)
fixed_meshes += [fixed[k] for k in ('back plate', 'pack', 'webbing', 'buckles', 'L shoulder pad', 'hip belt')]
for m in fixed_meshes:
    p = m.sample(150000)
    ijk = np.clip(((p - LO) / VOX).astype(int), 0, np.array(S.shape) - 1)
    fx_[tuple(ijk.T)] = True
fx_ = ndi.binary_fill_holes(ndi.binary_closing(fx_, iterations=1))
# the yoke/axle sit in the mount block's bearings by design: exclude the block for them
fx_nb = np.zeros(S.shape, bool)
for m in [fparts[k] for k in fparts if k not in ABD_SIDE | FLEX_SIDE and not k.startswith('Abduction_mount_block')] + fixed_meshes[-6:]:
    p = m.sample(150000)
    ijk = np.clip(((p - LO) / VOX).astype(int), 0, np.array(S.shape) - 1)
    fx_nb[tuple(ijk.T)] = True
fx_nb = ndi.binary_fill_holes(ndi.binary_closing(fx_nb, iterations=1))
sd_f, sd_fnb, sd_t = sdf(fx_), sdf(fx_nb), sdf(torso | l_arm)


def flex(p, deg):
    t = np.radians(deg); c, s_ = np.cos(t), np.sin(t)
    q = p - GH
    return GH + np.c_[q[:, 0] * c - q[:, 1] * s_, q[:, 0] * s_ + q[:, 1] * c, q[:, 2]]


ABD, FLX = [20, 30, 45, 60], [-20, 0, 45, 90, 120]
print('\nROM min gap (torso+head | exo fixed parts), worst part')
print('abd\\flx' + ''.join('%26d' % f for f in FLX))
for a in ABD:
    row = '%5d  ' % a
    for fl in FLX:
        wt, wf = (1e9, ''), (1e9, '')
        for k, p in base.items():
            q = abduct(p if k in ABD_SIDE else flex(p, fl), a)
            gt = sample(sd_t, q).min()
            gf = sample(sd_fnb if k in ABD_SIDE else sd_f, q).min()
            if gt < wt[0]: wt = (gt, k)
            if gf < wf[0]: wf = (gf, k)
        w = wt[1] if wt[0] < wf[0] else wf[1]
        row += '%7.0f|%-5.0f%-13s' % (wt[0], wf[0], w[:13])
    print(row)
