"""Upper-arm unit study: mid-support ring (back/outer arc only) + pipes running up into a pipe head
on the upper-arm link.  Sweeps rest abduction, pipe angles and heights; reports the gap to the torso
(ribs, armpit fold) over shoulder flexion 0..90 deg and the gap to the arm itself at rest."""
import itertools
import numpy as np
import trimesh

__file__ = __file__.replace('study_ua.py', 'layout.py')
exec(open(__file__).read().split('# ---------------- torso-side parts')[0])   # fields, primitives, abduct()

u, fvec = _u, _f
sd_t = sdf(torso | l_arm)
sd_a0 = sdf(r_arm)                                     # scanned arm, scan pose


def flex(p, deg):
    t = np.radians(deg); c, s_ = np.cos(t), np.sin(t)
    q = p - GH
    return GH + np.c_[q[:, 0] * c - q[:, 1] * s_, q[:, 0] * s_ + q[:, 1] * c, q[:, 2]]


def unit_parts(angles, h_mid, h_head, bore=126.):
    pr = bore / 2 + L['wall'] + L['pipe_od'] / 2
    boss = L['pipe_od'] / 2 + L['wall']; h = L['ring_h']
    cm = EL + u * h_mid; ch = EL + u * h_head
    a0 = min(angles) - 20
    mid = ring(cm, u, bore / 2, h, a0, 380, angles, pr, boss)           # back + outer arc only, strap closes it
    head = ring(ch, u, bore / 2, h, a0, 365, angles, pr, boss)          # pipe head: same arc, joins the link
    c1 = EL + u * (L['ring_off'] + h / 2)
    pipes = trimesh.util.concatenate([cyl(at(c1, u, pr, a), at(ch, u, pr, a), L['pipe_od'] / 2, 20) for a in angles])
    return dict(mid=mid, head=head, pipes=pipes)


rows = []
for abd, angles, h_mid, h_head in itertools.product((16, 20), ((225, 270, 315), (255, 300, 345)),
                                                    (100.,), (155., 165., 175.)):
    P_ = {k: m.sample(3000) for k, m in unit_parts(angles, h_mid, h_head).items()}
    arm_gap = min(sample(sd_a0, p).min() for p in P_.values())         # own arm, scan pose (moves with the unit)
    rib = {}
    for k, p in P_.items():
        rib[k] = min(sample(sd_t, abduct(flex(p, fl), abd)).min() for fl in (0, 30, 60, 90))
    rows.append((abd, angles, h_mid, h_head, round(arm_gap, 1), {k: round(v, 1) for k, v in rib.items()}))

print('abd  pipes          mid  head | arm gap | torso gap over flexion 0-90: mid / head / pipes')
for r in rows:
    ok = r[4] >= 3 and min(r[5].values()) >= 10
    print('%3d  %-14s %4.0f %4.0f | %6.1f  | %6.1f %6.1f %6.1f  %s' % (r[0], r[1], r[2], r[3], r[4], r[5]['mid'],
                                                                   r[5]['head'], r[5]['pipes'], 'OK' if ok else ''))
