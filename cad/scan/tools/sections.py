"""Cross-section plots of the body points: coronal slab + transverse slices + sagittal slab."""
from pathlib import Path
import numpy as np
import open3d as o3d
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent.parent / 'out'
pc = o3d.io.read_point_cloud(str(OUT / 'body_pts.ply'))
P = np.asarray(pc.points); C = np.asarray(pc.colors)
fig = plt.figure(figsize=(20, 11))
a = fig.add_subplot(1, 4, 1)
m = (P[:, 0] > -60) & (P[:, 0] < 20) & (P[:, 1] > 900)
a.scatter(P[m, 2], P[m, 1], s=1, c=C[m]); a.set_aspect('equal'); a.grid(alpha=.4)
a.set_title('coronal slab X -60..20 (Z right ->)'); a.set_xticks(range(-360, 320, 40)); a.set_yticks(range(900, 1760, 25))
a.tick_params(labelsize=6)
a = fig.add_subplot(1, 4, 2)
m = (P[:, 2] > 120) & (P[:, 2] < 280) & (P[:, 1] > 900)
a.scatter(P[m, 0], P[m, 1], s=1, c=C[m]); a.set_aspect('equal'); a.grid(alpha=.4)
a.set_title('right-side slab Z 120..280 (X fwd ->)'); a.set_yticks(range(900, 1760, 25)); a.tick_params(labelsize=6)
a = fig.add_subplot(1, 4, 3)
m = (np.abs(P[:, 2] + 40) < 25) & (P[:, 1] > 800)
a.scatter(P[m, 0], P[m, 1], s=1, c=C[m]); a.set_aspect('equal'); a.grid(alpha=.4)
a.set_title('mid-sagittal slab Z -65..-15'); a.set_yticks(range(800, 1760, 25)); a.tick_params(labelsize=6)
a = fig.add_subplot(1, 4, 4)
for y, col in [(1000, 'tab:blue'), (1150, 'tab:green'), (1300, 'tab:orange'), (1380, 'tab:red'), (1440, 'k')]:
    m = np.abs(P[:, 1] - y) < 6
    a.scatter(P[m, 2], P[m, 0], s=2, c=col, label='Y=%d' % y)
a.set_aspect('equal'); a.grid(alpha=.4); a.legend(fontsize=7); a.set_title('transverse (Z right, X fwd up)')
plt.tight_layout(); plt.savefig(OUT / 'sections.png', dpi=75)
