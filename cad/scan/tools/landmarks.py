"""Slice-by-slice body measurements from body_pts.ply (mm, X fwd, Y up, Z right)."""
from pathlib import Path
import json
import numpy as np
import open3d as o3d

OUT = Path(__file__).resolve().parent.parent / 'out'
P = np.asarray(o3d.io.read_point_cloud(str(OUT / 'body_pts.ply')).points)
rows = []
print('   Y | torso Z range  | torso X back..front | R arm Zc   Xc  width(Z) depth(X) | L arm Zc')
for y in range(400, 1760, 25):
    S = P[(P[:, 1] >= y) & (P[:, 1] < y + 25)]
    if len(S) < 30: continue
    z = np.sort(S[:, 2]); gaps = np.where(np.diff(z) > 12)[0]
    blobs = np.split(z, gaps + 1)
    segs = [(b[0], b[-1], len(b)) for b in blobs if len(b) > 15]
    # torso = largest blob; arms = blobs on either side
    t = max(segs, key=lambda s: s[2])
    T = S[(S[:, 2] >= t[0]) & (S[:, 2] <= t[1])]
    r = [s for s in segs if s[0] > t[1]]; l = [s for s in segs if s[1] < t[0]]
    row = dict(y=y, tz=[t[0], t[1]], tx=[np.percentile(T[:, 0], 1), np.percentile(T[:, 0], 99)])
    txt = '%4d | %6.0f %6.0f | %6.0f %6.0f |' % (y, t[0], t[1], row['tx'][0], row['tx'][1])
    if r:
        s = r[-1]; A = S[(S[:, 2] >= s[0]) & (S[:, 2] <= s[1])]
        row['r'] = dict(zc=float((s[0] + s[1]) / 2), xc=float(np.median(A[:, 0])), w=float(s[1] - s[0]),
                        d=float(np.ptp(A[:, 0])))
        txt += ' %6.0f %5.0f %5.0f %5.0f |' % (row['r']['zc'], row['r']['xc'], row['r']['w'], row['r']['d'])
    else:
        txt += ' ' * 26 + '|'
    if l:
        s = l[0]; row['l'] = dict(zc=float((s[0] + s[1]) / 2)); txt += ' %6.0f' % row['l']['zc']
    print(txt); rows.append(row)

# back profile at the spine (|Z - mid| < 40) and at the right scapula (Z mid+60..mid+120)
mid = float(np.median(P[(P[:, 1] > 1150) & (P[:, 1] < 1350), 2]))
print('\nmidline Z %.0f' % mid)
print('   Y | spine back X | R-scap back X | chest front X')
for y in range(900, 1560, 25):
    S = P[(P[:, 1] >= y) & (P[:, 1] < y + 25)]
    sp = S[np.abs(S[:, 2] - mid) < 40]; sc = S[(S[:, 2] > mid + 60) & (S[:, 2] < mid + 120)]
    f = lambda A, q: np.percentile(A[:, 0], q) if len(A) > 10 else np.nan
    print('%4d | %8.0f | %8.0f | %8.0f' % (y, f(sp, 1), f(sc, 1), f(sp, 99)))
# top of the right shoulder: highest points with Z > mid+120, below the head
sh = P[(P[:, 2] > mid + 120) & (P[:, 1] < 1520)]
top = sh[sh[:, 1] > np.percentile(sh[:, 1], 99.5)]
print('\nright shoulder top (acromion region) ~', np.round(top.mean(0)), 'n=%d' % len(top))
json.dump(dict(rows=rows, mid_z=mid, r_shoulder_top=top.mean(0).tolist()),
          open(OUT / 'landmarks.json', 'w'), indent=1, default=float)
