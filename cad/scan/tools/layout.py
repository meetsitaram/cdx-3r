"""First-pass CDX-3R layout on the scanned body (mm, X fwd, Y up, Z right; floor Y=0).

Body-hugging parts (back plate, R shoulder saddle, L strap, hip belt) are offset shells of
the torso distance field.  Arm parts are the elbow concept B envelopes (rings, 3 rear PVC
pipes, two-sided bearing hubs, wrist ring) on the scanned arm.  Shoulder: abduction hub
behind the shoulder (axis X through GH), yoke arc, flexion hub lateral (axis Z through GH),
strut down to the upper-arm far ring.

Rest pose: the scanned arm hangs against the ribs and waist, so the exo holds it at
`rest_abd` degrees of abduction.  The arm voxels are rotated about GH to pose the body, and
everything distal of the abduction joint is rotated with it.  Every part is checked against
the posed body's signed distance field.
"""
from pathlib import Path
import json
import numpy as np
import trimesh
from scipy import ndimage as ndi
from skimage import measure
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

OUT = Path(__file__).resolve().parent.parent / 'out'
LAY = OUT / 'layout'; LAY.mkdir(exist_ok=True)

# ---------------- scanned landmarks (landmarks.py / sections.py) ----------------
GH = np.array([-25., 1345., 165.])      # right glenohumeral centre
EL = np.array([-10., 1075., 215.])      # right elbow flexion centre (arm hanging)
WR = np.array([50., 830., 235.])        # right wrist centre
MID_Z = -40.                            # body midline

L = dict(
    rest_abd=20.,                                  # deg, exo rest pose: 20 keeps the upper-arm unit off the ribs (study_ua.py)
    pack_gap=30., plate_t=8., pack_depth=120., pack_y=(1030., 1390.), pack_halfw=140.,
    belt_gap=12., belt_t=10., belt_y=(985., 1045.),
    saddle_gap=15., saddle_t=10.,                 # rigid rest shell (ribbed in CAD)
    abd_hub_r=40., abd_hub_w=25., abd_gap=45.,     # gap: hub face to back of shoulder
    flex_hub_r=45., flex_hub_w=25., flex_gap=30.,  # gap: hub face to deltoid
    yoke_d=26., yoke_dy=0.,                        # yoke at GH height: near the abduction axis, clears the saddle
    abd_rom=(0., 60.),                             # hard stop (repo spec 0-60); >75 the flexion hub reaches the acromion
    # concept B (cad/fusion/concepts.py P)
    ua_d=126., fa_d=119., wrist_d=92., band_t=5., wall=3., pipe_od=21.5, ring_h=25.,  # +~5 mm over the printed 120/113/80 for easier fit
    ring_off=40., ua_far=140., fa_far=200., elbow_half=50., hub_r=44., hub_w=22.,
    fa_pipe_angles=(225., 270., 315.),
    ua_pipe_angles=(240., 285., 330.),             # rotated 15 deg lateral: clears the armpit fold
    ua_far_cover=(220., 385.),                     # far ring open medial + anterior
)

# ---------------- body: voxels, segmentation, posing ----------------
vz = np.load(OUT / 'body_vox.npz'); S, LO, VOX = vz['s'], vz['lo'], float(vz['vox'])
PAD = 30                                              # 150 mm: room for the posed arm and outboard parts
S = np.pad(S, PAD); LO = LO - PAD * VOX
I, J, K = np.indices(S.shape)
G = np.stack([LO[0] + (I + .5) * VOX, LO[1] + (J + .5) * VOX, LO[2] + (K + .5) * VOX], -1)
X, Y, Z = G[..., 0], G[..., 1], G[..., 2]


def seg_dist(p0, p1):
    d = p1 - p0; t = np.clip(((G - p0) @ d) / (d @ d), 0, 1)
    return np.linalg.norm(G - (p0 + t[..., None] * d), axis=-1)


def abduct(pts, deg):
    """Rotate about the X axis through GH; +deg swings the arm outboard (about -X)."""
    t = np.radians(deg); c, s_ = np.cos(t), np.sin(t)
    q = np.asarray(pts, float) - GH; y, z = q[..., 1], q[..., 2]
    return GH + np.stack([q[..., 0], y * c + z * s_, -y * s_ + z * c], -1)


_u = (GH - EL) / np.linalg.norm(GH - EL); _f = (WR - EL) / np.linalg.norm(WR - EL)
# upper arm presses into the ribs: carve from Z > 95; forearm/hand hang beside the hip: only
# outboard of the hip line (Z > 165), otherwise the capsules tunnel into the hip
r_arm = S & (((Z > 95) & (seg_dist(EL, GH - _u * 45) < 56)) |
             ((Z > 165) & ((seg_dist(EL, WR) < 52) | (seg_dist(WR, WR + _f * 170) < 60))) |
             ((Y < 1330) & (Z > 172)))
l_arm = S & (Y < 1330) & (Z < -250)
torso = S & ~r_arm & ~l_arm
lab, _ = ndi.label(torso); torso = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
src = abduct(G, -L['rest_abd'])                       # pull-back: posed voxel <- scanned voxel
arm_posed = ndi.map_coordinates(r_arm.astype(np.float32), ((src - LO) / VOX - .5).transpose(3, 0, 1, 2), order=1) > .5
posed = torso | arm_posed | l_arm


def sdf(m):
    return ndi.distance_transform_edt(~m) * VOX - ndi.distance_transform_edt(m) * VOX


sd_body, sd_torso, sd_arm, sd_scan = sdf(posed), sdf(torso), sdf(arm_posed), sdf(S)
d_torso = np.maximum(sd_torso, 0)


def sample(field, pts):
    return ndi.map_coordinates(field, ((np.asarray(pts) - LO) / VOX - .5).T, order=1, mode='nearest')


def surface(mask, smooth=1.2):
    v, f, _, _ = measure.marching_cubes(ndi.gaussian_filter(mask.astype(float), smooth), 0.5)
    m = trimesh.Trimesh(v * VOX + LO, f); trimesh.smoothing.filter_taubin(m, iterations=10)
    if m.volume < 0: m.invert()
    return m


def shell(region, gap, t):
    m = surface((d_torso >= gap) & (d_torso <= gap + t) & region, 0.7)
    return trimesh.util.concatenate([p for p in m.split(only_watertight=False) if len(p.faces) > 200])


# ---------------- primitives ----------------
def frame(z_axis, origin):
    z = z_axis / np.linalg.norm(z_axis)
    a = np.array([1., 0, 0]) if abs(z[0]) < .9 else np.array([0, 1., 0])
    x = np.cross(a, z); x /= np.linalg.norm(x); y = np.cross(z, x)
    T = np.eye(4); T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = x, y, z, origin
    return T


def cyl(p0, p1, r, sections=40):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    return trimesh.creation.cylinder(r, np.linalg.norm(p1 - p0), sections=sections,
                                     transform=frame(p1 - p0, (p0 + p1) / 2))


def tube_path(pts, r):
    return trimesh.util.concatenate([cyl(a, b, r, 24) for a, b in zip(pts[:-1], pts[1:])] +
                                    [trimesh.creation.icosphere(2, r).apply_translation(p) for p in pts])


def arm_axes(axis, lat=np.array([0, 0, 1.])):
    ax = axis / np.linalg.norm(axis); e = lat - ax * (lat @ ax); e /= np.linalg.norm(e)
    n = np.cross(ax, e)
    return ax, e, (n if n[0] > 0 else -n)             # axis, lateral, anterior


def ring(centre, axis, bore_r, h, phi0, phi1, pipes, pipe_r, boss_r):
    """Band bore_r..bore_r+band_t over phi0..phi1 (deg from lateral toward anterior) + pipe bosses."""
    ax, e, n = arm_axes(axis)
    ph = np.radians(np.linspace(phi0, phi1, 64)); ro = bore_r + L['band_t']
    band = Polygon(np.r_[np.c_[ro * np.cos(ph), ro * np.sin(ph)], np.c_[bore_r * np.cos(ph[::-1]), bore_r * np.sin(ph[::-1])]])
    shp = unary_union([band] + [Point(pipe_r * np.cos(np.radians(a)), pipe_r * np.sin(np.radians(a))).buffer(boss_r, 24)
                                for a in pipes])
    T = np.eye(4); T[:3, 0], T[:3, 1], T[:3, 2] = e, n, ax; T[:3, 3] = centre - ax * h / 2
    return trimesh.creation.extrude_polygon(shp, h).apply_transform(T)


def at(c, axis, r, phi):
    _, e, n = arm_axes(axis); p = np.radians(phi)
    return c + r * (np.cos(p) * e + np.sin(p) * n)


# ---------------- torso-side parts (do not move with abduction) ----------------
fixed = {}
fixed['back plate'] = shell((X < -60) & (Y > L['pack_y'][0]) & (Y < L['pack_y'][1] + 20) &
                            (np.abs(Z - MID_Z) < L['pack_halfw'] + 20), L['pack_gap'], L['plate_t'])
fixed['hip belt'] = shell((Y > L['belt_y'][0]) & (Y < L['belt_y'][1]), L['belt_gap'], L['belt_t'])
xb = float(np.percentile(fixed['back plate'].vertices[:, 0], 2))
back_x = min(x for x in np.linspace(-250, 0, 501) if sample(sd_body, [[x, GH[1], GH[2]]])[0] < 0)
ax0 = back_x - L['abd_gap']
fixed['abduction hub'] = cyl([ax0 - L['abd_hub_w'], GH[1], GH[2]], [ax0, GH[1], GH[2]], L['abd_hub_r'])

# ---- frame: PVC backbone + triangulated shoulder beam (all 21.5 mm pipe, printed nodes) ----
PR = L['pipe_od'] / 2
xf = xb - PR - 1                                   # pipe centres just behind the back plate
zb = (MID_Z - 70., MID_Z + 70.)
y_bot, y_mid, y_top = L['belt_y'][0] + 25, 1200., 1405.
xm = ax0 - L['abd_hub_w'] - 22                    # abduction mount block centre (behind the hub)
blk = np.array([xm, GH[1], GH[2]])
zin = GH[2] - 40                                   # beam pipes enter the block's medial face
fixed['frame pipes'] = trimesh.util.concatenate(
    [cyl([xf, y_bot - 20, z], [xf, y_top + 15, z], PR, 24) for z in zb] +
    [cyl([xf, y_top, zb[1]], [xm, GH[1] + 50, zin], PR, 24),        # upper beam
     cyl([xf, y_mid, zb[1]], [xm, GH[1] - 50, zin], PR, 24)])       # diagonal: mid node -> block bottom
node = lambda y, h: trimesh.creation.box((2 * PR + 12, h, 2 * 70 + 2 * PR + 12)).apply_translation([xf, y, MID_Z])
fixed['frame nodes'] = trimesh.util.concatenate([node(y_top, 36), node(y_mid, 36), node(y_bot, 50)])
fixed['abduction mount block'] = trimesh.creation.box((44, 150, 80)).apply_translation(blk)
fixed['pack'] = trimesh.creation.box((L['pack_depth'], L['pack_y'][1] - L['pack_y'][0], 2 * L['pack_halfw'])) \
    .apply_translation([xf - PR - 3 - L['pack_depth'] / 2, np.mean(L['pack_y']), MID_Z])

# ---- right shoulder rest: rigid printed shell over the trapezius, bolted to the frame ----
rest = shell((Y > 1330) & (Y < 1470) & (Z > MID_Z + 45) & (Z < GH[2] - 20) & (X > -150) & (X < 60),
             L['saddle_gap'], L['saddle_t'])
fixed['R shoulder rest'] = rest
V = rest.vertices
r_back = V[np.argmin(V[:, 0] + 0.3 * np.abs(V[:, 2] - (MID_Z + 90)))]
r_blat = V[np.argmin(V[:, 0] - 0.8 * V[:, 2])]
r_front = V[np.argmax(V[:, 0] - 0.4 * V[:, 1])]
fixed['rest struts'] = trimesh.util.concatenate([
    tube_path(np.array([r_back, [xf + 5, y_top + 12, MID_Z + 50]]), 9),
    tube_path(np.array([r_blat, blk + [8, 70, -25]]), 9)])

# ---- webbing + buckles (camping-pack harness) ----
GX = [np.gradient(sd_torso, VOX, axis=i) for i in range(3)]


def grad(P):
    n = np.stack([sample(g, P) for g in GX], -1)
    return n / (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9)


def onsurf(P, g):
    P = np.atleast_2d(np.array(P, float))
    for _ in range(40):
        P = P - (sample(sd_torso, P) - g)[:, None] * grad(P)
    return P


def densify(W, step=6.):
    out = [W[0]]
    for a, b in zip(W[:-1], W[1:]):
        n = max(1, int(np.linalg.norm(b - a) / step))
        out += [a + (b - a) * t for t in np.linspace(0, 1, n + 1)[1:]]
    return np.array(out)


def strap(W, width, g=None, t=2.5):
    W = np.array(W, float)
    P = densify(W)
    if g is not None:
        for _ in range(3):                             # project, smooth, re-project (ends pinned)
            P[1:-1] = (P[:-2] + P[1:-1] + P[2:]) / 3; P = onsurf(P, g)
        P[0], P[-1] = W[0], W[-1]
    tan = np.gradient(P, axis=0); tan /= np.linalg.norm(tan, axis=1, keepdims=True)
    n = grad(P); b = np.cross(tan, n); b /= np.linalg.norm(b, axis=1, keepdims=True); n = np.cross(b, tan)
    C = np.stack([P - b * width / 2, P + b * width / 2, P + b * width / 2 + n * t, P - b * width / 2 + n * t], 1)
    v = C.reshape(-1, 3); f = []
    for i in range(len(P) - 1):
        for k in range(4):
            a0, a1, b0, b1 = 4 * i + k, 4 * i + (k + 1) % 4, 4 * (i + 1) + k, 4 * (i + 1) + (k + 1) % 4
            f += [[a0, b0, b1], [a0, b1, a1]]
    last = 4 * (len(P) - 1)
    f += [[0, 2, 1], [0, 3, 2], [last, last + 1, last + 2], [last, last + 2, last + 3]]
    m = trimesh.Trimesh(v, f); m.fix_normals()
    return m, P


def buckle(p, along, size):
    n = grad(np.atleast_2d(p))[0]; a = along - n * (along @ n); a /= np.linalg.norm(a); b = np.cross(n, a)
    T = np.eye(4); T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = a, b, n, p + n * size[2] / 2
    return trimesh.creation.box(size, transform=T)


G = L['saddle_gap'] - 5
corner = lambda s_: np.array([xf + 2, y_bot + 45, MID_Z + s_ * (70 + PR + 8)])
# right: rest front anchor -> down the chest, under the arm -> frame bottom-right corner
rs, RP = strap([r_front, onsurf([90, 1260, MID_Z + 125], G)[0], onsurf([40, 1140, MID_Z + 175], G)[0],
                onsurf([-90, 1090, MID_Z + 170], G)[0], corner(1)], 25., G)
# left: frame top-left -> over the shoulder -> down the chest, under the arm -> bottom-left corner
top_l = np.array([xf + 4, y_top + 10, MID_Z - 60])
ls, LP = strap([top_l] + [onsurf(p, G)[0] for p in ([-110, 1440, MID_Z - 85], [-30, 1455, MID_Z - 100],
                                                     [60, 1395, MID_Z - 105], [90, 1260, MID_Z - 125],
                                                     [40, 1140, MID_Z - 175], [-90, 1090, MID_Z - 170])] +
               [corner(-1)], 25., G)
yst = 1275.
front_pt = lambda Pp, y: Pp[np.argmin(np.abs(Pp[:, 1] - y) + 1000 * (Pp[:, 0] < 0))]
mid_st = onsurf([120, yst, MID_Z], G + 3)[0]
st, _ = strap([front_pt(RP, yst), mid_st, front_pt(LP, yst)], 20., G + 3)
y_stay = 1495.                                     # load-lifter stays: backbone extended above the shoulders
fixed['frame pipes'] = trimesh.util.concatenate([fixed['frame pipes']] +
                                                [cyl([xf, y_top + 15, z], [xf, y_stay, z], PR, 24) for z in zb])
lift_a = LP[np.argmax(LP[:, 1] - 3 * np.abs(LP[:, 0] - 10))]           # strap at the top of the shoulder
lift, _ = strap([lift_a, [xf + PR + 3, y_stay - 10, zb[0]]], 20.)
fixed['webbing'] = trimesh.util.concatenate([rs, ls, st, lift])
hipf = onsurf([150, np.mean(L['belt_y']), MID_Z], L['belt_gap'] + L['belt_t'])[0]
iR, iL = int(len(RP) * .72), int(len(LP) * .8)
fixed['buckles'] = trimesh.util.concatenate([
    buckle(mid_st, np.array([0, 0, 1.]), (60, 26, 12)),                 # sternum, 20 mm side-release
    buckle(hipf, np.array([0, 0, 1.]), (90, 55, 16)),                    # hip belt, 50 mm side-release
    buckle(RP[iR], RP[iR + 1] - RP[iR], (55, 32, 10)),                   # ladder-lock adjusters
    buckle(LP[iL], LP[iL + 1] - LP[iL], (55, 32, 10))])
fixed['L shoulder pad'] = shell((Y > 1350) & (Y < 1460) & (Z < 2 * MID_Z - 55) & (Z > 2 * MID_Z - 150) &
                                (X > -120) & (X < 60), L['saddle_gap'], 6.)

# ---------------- abduction-side parts: built on the scanned (hanging) arm, then posed ----------------
moving = {}
fz0 = max(z for z in np.linspace(GH[2], GH[2] + 150, 301) if sample(sd_scan, [[GH[0], GH[1], z]])[0] < 0) + L['flex_gap']
moving['flexion hub'] = cyl([GH[0], GH[1], fz0], [GH[0], GH[1], fz0 + L['flex_hub_w']], L['flex_hub_r'])
ra, rl = GH[0] - (ax0 - L['abd_hub_w'] / 2), fz0 + L['flex_hub_w'] / 2 - GH[2]
th = np.radians(np.linspace(180, 90, 12))
yk = np.c_[GH[0] + ra * np.cos(th), np.full_like(th, GH[1] + L['yoke_dy']), GH[2] + rl * np.sin(th)]
moving['yoke'] = tube_path(yk, L['yoke_d'] / 2)

u, f = _u, _f
pr = lambda d: d / 2 + L['wall'] + L['pipe_od'] / 2
boss = L['pipe_od'] / 2 + L['wall']; h = L['ring_h']
c1 = EL + u * (L['ring_off'] + h / 2); c2 = EL + u * (L['ua_far'] + h / 2)
c3 = EL + f * (L['ring_off'] + h / 2); c4 = EL + f * (L['fa_far'] + h / 2)
UA, FA = L['ua_pipe_angles'], L['fa_pipe_angles']
moving['UA near ring'] = ring(c1, u, L['ua_d'] / 2, h, 180, 360, UA, pr(L['ua_d']), boss)
moving['UA far ring'] = ring(c2, u, L['ua_d'] / 2, h, *L['ua_far_cover'], UA, pr(L['ua_d']), boss)
moving['FA near ring'] = ring(c3, f, L['fa_d'] / 2, h, 180, 360, FA, pr(L['fa_d']), boss)
moving['wrist ring + cuff'] = ring(c4, f, L['wrist_d'] / 2, h, 0, 360, FA, pr(L['wrist_d']), boss)
pp = [cyl(at(c1, u, pr(L['ua_d']), a) - u * h / 2, at(c2, u, pr(L['ua_d']), a) + u * h / 2, L['pipe_od'] / 2, 20) for a in UA]
pp += [cyl(at(c3, f, pr(L['fa_d']), a) - f * h / 2, at(c4, f, pr(L['wrist_d']), a) + f * h / 2, L['pipe_od'] / 2, 20) for a in FA]
moving['PVC pipes'] = trimesh.util.concatenate(pp)
_, eax, _ = arm_axes(u)
moving['elbow hub, lateral'] = cyl(EL + eax * L['elbow_half'], EL + eax * (L['elbow_half'] + L['hub_w']), L['hub_r'])
moving['elbow hub, medial'] = cyl(EL - eax * L['elbow_half'], EL - eax * (L['elbow_half'] + L['hub_w']), L['hub_r'])
top = at(c2, u, L['ua_d'] / 2 + L['band_t'], 0)
moving['UA strut'] = tube_path(np.array([top, [GH[0], GH[1] - 50, fz0 + 5], [GH[0], GH[1], fz0 + 5]]), 11)
for m in moving.values():
    m.vertices = abduct(m.vertices, L['rest_abd'])

ARM = ('UA near ring', 'UA far ring', 'FA near ring', 'wrist ring + cuff', 'PVC pipes',
       'elbow hub, lateral', 'elbow hub, medial', 'UA strut')
parts = {**fixed, **moving}
rep = {}
print('rest abduction %.0f deg' % L['rest_abd'])
print('%-22s %9s %9s   (arm parts: gap to own arm | gap to torso)' % ('part', 'min gap', 'p5 gap'))
for k, m in parts.items():
    pts = m.sample(8000)
    if k in ARM:
        ga, gt = sample(sd_arm, pts), sample(sd_torso, pts)
        rep[k] = dict(arm_min=float(ga.min()), arm_p5=float(np.percentile(ga, 5)), torso_min=float(gt.min()))
        print('%-22s %9.1f %9.1f   | torso %6.1f' % (k, ga.min(), np.percentile(ga, 5), gt.min()))
    else:
        g = sample(sd_body, pts)
        rep[k] = dict(min=float(g.min()), p5=float(np.percentile(g, 5)))
        print('%-22s %9.1f %9.1f' % (k, g.min(), np.percentile(g, 5)))
    m.export(LAY / (k.replace(' + ', '_').replace(', ', '_').replace(' ', '_') + '.stl'))

surface(torso | l_arm).simplify_quadric_decimation(face_count=40000).export(LAY / 'body_torso.stl')
surface(arm_posed).simplify_quadric_decimation(face_count=12000).export(LAY / 'body_arm.stl')
body_mesh = surface(posed)
body_mesh.export(OUT / 'body_posed_full.stl')
body_light = body_mesh.simplify_quadric_decimation(face_count=40000)
body_light.export(OUT / 'body_posed.stl')
json.dump(dict(landmarks=dict(GH=GH.tolist(), EL=EL.tolist(), WR=WR.tolist(), MID_Z=MID_Z), params=L,
               derived=dict(back_x_at_GH=back_x, abd_hub_face_x=ax0, flex_hub_face_z=fz0, xb=xb, xf=xf, zb=list(zb),
                            y_bot=y_bot, y_mid=y_mid, y_top=y_top, y_stay=y_stay, block=blk.tolist(), zin=zin,
                            yoke_ra=float(ra), yoke_rl=float(rl), ua_far_top=top.tolist(), u=u.tolist(), f=f.tolist()), clearance=rep),
          open(LAY / 'layout.json', 'w'), indent=1)

COL = {'back plate': '#5b6770', 'hip belt': '#3a3f44', 'R shoulder rest': '#d4a017', 'L shoulder pad': '#8a7a4a',
       'pack': '#4a5560', 'webbing': '#26292c', 'buckles': '#0d0d0d', 'frame pipes': '#e9eef2', 'PVC pipes': '#e9eef2', 'UA strut': '#647684', 'yoke': '#647684'}
import render
items = [(body_light, '#e8c9a8')] + [(m, COL.get(k, '#647684' if k in fixed or 'UA' in k or 'hub' in k else '#8fa3b3'))
                                     for k, m in parts.items()]
render.render(LAY / 'layout.png', items, crop=(np.array([-450, 650, -450]), np.array([400, 1800, 450])))
render.render(LAY / 'layout_shoulder.png', items, views=[(5, 0, 'front'), (5, -90, 'right'), (5, 180, 'back'), (70, 0, 'top')],
              crop=(np.array([-360, 1150, -80]), np.array([200, 1560, 400])), size=5)
