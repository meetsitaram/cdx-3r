"""Strap-driven MuJoCo test of the CDX-3R right arm exo (shoulder girdle v3b + arm + elbow).

The back frame is one rigid body fixed in the world. The wearer's arm is kinematic (a mocap body): it moves through
shrug, drop, reach, squeeze, arm raise and forward/back swing. The exo is passive and is pulled along only by the
straps: a spring between the wearer's upper arm and the exo's upper-arm pipes (half way from shoulder to elbow), and
one at the wrist cuff. We read the strap forces and the exo joints over time:
  - small strap forces -> the exo follows easily; spikes -> binding, a joint near a limit or a singular SCARA;
  - the gas strut (100 N, as bought) against the girdle + arm weight;
  - how far each exo joint lags the arm.
Geometry from the Fusion model (girdle_b.G, shoulder landmarks); scan frame mm (x fwd, y up, z right) is mapped to
MuJoCo metres with z up: (X, Y, Z) = (x, -z, y) / 1000.
Run: python exo_sim.py   (writes out/ plots, frames and a summary json)
"""
import json
import math
import os

import mujoco
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
LAY = json.load(open(r'C:\Users\PC\projects\exoarm2-scan\out\layout\layout.json'))
GH, EL, WR = (np.array(LAY['landmarks'][k], float) for k in ('GH', 'EL', 'WR'))

# girdle (girdle_b.G, mm, scan frame)
XL = LAY['derived']['xf']
LIFT_L, TILT, Z0 = 100.0, math.radians(15.0), 95.0
CARR_Y = (1545.0, 1500.0)
BASE_Y = tuple(y - LIFT_L * math.sin(-TILT) for y in CARR_Y)
ZC = Z0 + LIFT_L * math.cos(TILT)
S0, E, LS = np.array([-240.0, 200.0]), np.array([-180.5, 153.0]), 65.0
YU, YL = 1440.0, 1409.0
SPRING_LO, SPRING_HI, SPRING_F = (1475.4, 63.5), (1555.0, 175.0), 100.0
# masses (kg): PETG parts at ~60 % effective fill + their hardware (estimates; refine from Fusion)
M = dict(lift=0.03, carriage=0.20, link1=0.16, link2=0.16, end=0.22, yoke=0.18, ua_link=0.30, ua_pipes=0.06,
         elbow=0.45, forearm=0.25)
STRAP_K, STRAP_C = 3000.0, 30.0           # N/m, N s/m: a snug 25 mm webbing strap over foam
JOINT_FRICTION = 0.05                     # N m, sealed 608 / 6806 with a little preload


HARDWARE = os.path.join(HERE, '..', 'fusion', 'sim_joints.json')


def model():
    """The MuJoCo model, after checking that every hinge in it is made by real hardware listed in
    cad/fusion/sim_joints.json (fastener_check.joint_check verifies that hardware in Fusion). The sim's joints are
    ideal and can't come apart, so a joint with no bolt behind it would pass here unseen (the end plate, 25 Oct)."""
    m = mujoco.MjModel.from_xml_string(mjcf())
    hw = json.load(open(HARDWARE))
    hinges = [m.joint(i).name for i in range(m.njnt) if m.jnt_type[i] == mujoco.mjtJoint.mjJNT_HINGE]
    missing = [n for n in hinges if n not in hw]
    if missing:
        raise RuntimeError('sim joints with no hardware in sim_joints.json: %s' % ', '.join(missing))
    return m


def P(p):
    """scan mm -> MuJoCo m."""
    return np.array([p[0], -p[2], p[1]]) / 1000.0


def v(p):
    return ' '.join('%.5f' % x for x in p)


def scara_elbow(S, Et, branch=1):
    d = Et - S
    dd = np.hypot(*d)
    a = math.atan2(d[1], d[0]) + branch * math.acos(min(1.0, dd / (2 * LS)))
    return S + LS * np.array([math.cos(a), math.sin(a)])


C = scara_elbow(S0, E)


def mjcf():
    s0, c, e = P([S0[0], YU, S0[1]]), P([C[0], YU, C[1]]), P([E[0], YL, E[1]])
    bu, bl = P([XL, BASE_Y[0], Z0]), P([XL, BASE_Y[1], Z0])
    cu, cl = P([XL, CARR_Y[0], ZC]), P([XL, CARR_Y[1], ZC])
    gh, el, wr = P(GH), P(EL), P(WR)
    strap = gh + 0.75 * (el - gh)                        # lower upper-arm strap (75 % down)
    strap2 = gh + 0.30 * (el - gh)                       # upper upper-arm strap (30 % down)
    cuff = el + 0.8 * (wr - el)
    sp_lo, sp_hi = P([XL + 40, SPRING_LO[0], SPRING_LO[1]]), P([XL + 40, SPRING_HI[0], SPRING_HI[1]])
    ax_x, ax_lat, ax_up = '1 0 0', '0 -1 0', '0 0 1'     # scan x (fwd), scan z (lateral), scan y (up)
    fr = JOINT_FRICTION
    return f'''
<mujoco model="cdx3r_exo_strap_test">
  <option timestep="0.001" gravity="0 0 -9.81" integrator="implicitfast"/>
  <visual><headlight ambient="0.45 0.45 0.45" diffuse="0.6 0.6 0.6"/></visual>
  <default>
    <joint damping="0.02" frictionloss="{fr}" armature="0.0005"/>
    <geom contype="0" conaffinity="0" rgba="0.39 0.46 0.52 1"/>
  </default>
  <worldbody>
    <light pos="0 -1 2.5" dir="0 0.4 -1"/>
    <geom name="frame" type="box" size="0.02 0.09 0.25" pos="{v(P([XL, 1250, -40]))}" rgba="0.36 0.40 0.44 1"/>
    <site name="sp_lo" pos="{v(sp_lo)}" size="0.004"/>
    <!-- lift parallelogram: upper link carries the carriage, the lower link closes it with a connect constraint -->
    <body name="lift_u" pos="{v(bu)}">
      <joint name="lift" type="hinge" axis="{ax_x}" range="-40 75"/>
      <geom type="capsule" fromto="0 0 0 {v(cu - bu)}" size="0.012" mass="{M['lift']}"/>
      <body name="carriage" pos="{v(cu - bu)}">
        <joint name="carr" type="hinge" axis="{ax_x}"/>
        <geom type="box" size="0.02 0.02 0.04" pos="{v((s0 - cu) * 0.5)}" mass="{M['carriage']}"/>
        <site name="carr_lo" pos="{v(cl - cu)}" size="0.004"/>
        <site name="sp_hi" pos="{v(sp_hi - cu)}" size="0.004"/>
        <body name="link1" pos="{v(s0 - cu)}">
          <joint name="q1" type="hinge" axis="{ax_up}"/>
          <geom type="capsule" fromto="0 0 0 {v(c - s0)}" size="0.02" mass="{M['link1']}"/>
          <body name="spool" pos="{v(c - s0)}">
            <joint name="qs" type="hinge" axis="{ax_up}" frictionloss="0.01"/>
              <geom type="cylinder" size="0.012 0.03" mass="0.03"/>
            <body name="link2" pos="0 0 {(YL - YU) / 1000:.4f}">
              <joint name="q2" type="hinge" axis="{ax_up}"/>
              <geom type="capsule" fromto="0 0 0 {v(e - c - np.array([0, 0, (YL - YU) / 1000]))}" size="0.02" mass="{M['link2']}"/>
              <body name="end" pos="{v(e - c - np.array([0, 0, (YL - YU) / 1000]))}">
                <joint name="q3" type="hinge" axis="{ax_up}"/>
                <geom type="cylinder" fromto="{v(np.array([-0.035, 0, 0]) + (gh - e) * np.array([0, 1, 1]))} {v(np.array([0.034, 0, 0]) + (gh - e) * np.array([0, 1, 1]))}" size="0.028" mass="{M['end']}"/>
                <body name="yoke" pos="{v((gh - e) * np.array([0, 1, 1]) + np.array([gh[0] - e[0], 0, 0]))}">
                  <joint name="abd" type="hinge" axis="{ax_x}" range="-95 30"/>
                  <geom type="capsule" fromto="-0.12 0 0 0 -0.06 0" size="0.012" mass="{M['yoke']}"/>
                  <body name="ua">
                    <joint name="flex" type="hinge" axis="{ax_lat}" range="-40 125"/>
                    <geom type="capsule" fromto="0 -0.05 0 {v(el - gh + np.array([0, -0.05, 0]))}" size="0.015" mass="{M['ua_link'] + M['ua_pipes']}"/>
                    <site name="exo_strap" pos="{v(strap - gh + np.array([0, -0.045, 0]))}" size="0.006" rgba="1 0.5 0 1"/>
                    <site name="exo_strap2" pos="{v(strap2 - gh + np.array([0, -0.045, 0]))}" size="0.006" rgba="1 0.5 0 1"/>
                    <body name="fa" pos="{v(el - gh)}">
                      <joint name="elbow" type="hinge" axis="{ax_lat}" range="-5 140"/>
                      <geom type="capsule" fromto="0 -0.05 0 {v(wr - el + np.array([0, -0.04, 0]))}" size="0.015" mass="{M['elbow'] + M['forearm']}"/>
                      <site name="exo_cuff" pos="{v(cuff - el + np.array([0, -0.04, 0]))}" size="0.006" rgba="1 0.5 0 1"/>
                    </body>
                  </body>
                </body>
              </body>
            </body>
          </body>
        </body>
      </body>
    </body>
    <body name="lift_l" pos="{v(bl)}">
      <joint name="lift2" type="hinge" axis="{ax_x}"/>
      <geom type="capsule" fromto="0 0 0 {v(cl - bl)}" size="0.012" mass="{M['lift']}"/>
      <site name="lift_l_end" pos="{v(cl - bl)}" size="0.004"/>
    </body>
    <!-- the wearer's arm (kinematic): shoulder at GH, upper arm to the elbow, forearm to the wrist -->
    <body name="human" mocap="true" pos="{v(gh)}">
      <geom type="capsule" fromto="0 0 0 {v(el - gh)}" size="0.04" rgba="0.85 0.68 0.55 0.5"/>
      <site name="hum_strap" pos="{v(strap - gh + np.array([0, -0.045, 0]))}" size="0.006"/>
      <site name="hum_strap2" pos="{v(strap2 - gh + np.array([0, -0.045, 0]))}" size="0.006"/>
    </body>
    <body name="human_fa" mocap="true" pos="{v(el)}">
      <geom type="capsule" fromto="0 0 0 {v(wr - el)}" size="0.033" rgba="0.85 0.68 0.55 0.5"/>
      <site name="hum_cuff" pos="{v(cuff - el + np.array([0, -0.04, 0]))}" size="0.006"/>
    </body>
  </worldbody>
  <equality>
    <connect name="parallelogram" site1="carr_lo" site2="lift_l_end"/>
    <joint name="belt1" joint1="qs" joint2="q1" polycoef="0 -1 0 0 0"/>
    <joint name="belt2" joint1="q3" joint2="q2" polycoef="0 -1 0 0 0"/>
  </equality>
  <tendon>
    <spatial name="strut"><site site="sp_lo"/><site site="sp_hi"/></spatial>
    <spatial name="strap_ua" stiffness="{STRAP_K}" damping="{STRAP_C}" springlength="0"><site site="hum_strap"/><site site="exo_strap"/></spatial>
    <spatial name="strap_ua2" stiffness="{STRAP_K}" damping="{STRAP_C}" springlength="0"><site site="hum_strap2"/><site site="exo_strap2"/></spatial>
    <spatial name="strap_cuff" stiffness="{STRAP_K}" damping="{STRAP_C}" springlength="0"><site site="hum_cuff"/><site site="exo_cuff"/></spatial>
  </tendon>
  <actuator>
    <motor name="gas_strut" tendon="strut" gear="1" ctrlrange="-200 200"/>
  </actuator>
</mujoco>'''


def rot(axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    x, y, z = axis
    return np.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
                     [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
                     [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]])


def quat(R):
    q = np.zeros(4)
    mujoco.mju_mat2Quat(q, R.flatten())
    return q


# The shoulder girdle moves about the sternoclavicular (SC) joint at the top of the breastbone: the collarbone swings
# up/down (shrug / drop) and forward/back (reach / squeeze), carrying the shoulder joint (GH) on an arc; arm raising
# brings ~15 % extra collarbone elevation (scapulohumeral rhythm). The arm then turns about GH.
SC = np.array([5.0, 1395.0, -20.0])          # right SC joint (scan mm), ~15 mm inside the jugular notch
RHYTHM = 0.15
# motion keys: (seconds to get there, collarbone elevation deg (+ shrug), collarbone protraction deg (+ reach),
# arm abduction deg (out/up), arm flexion deg (forward), elbow deg (bend))
KEYS = [(0.0, 0, 0, 0, 0, 0), (1.0, 0, 0, 0, 0, 0),
        (1.5, 18, 0, 0, 0, 0), (1.5, -6, 0, 0, 0, 0), (1.0, 0, 0, 0, 0, 0),
        (1.5, 0, 15, 0, 0, 0), (1.5, 0, -15, 0, 0, 0), (1.0, 0, 0, 0, 0, 0),
        (2.0, 0, 0, 60, 0, 0), (1.5, 8, 0, 90, 0, 0), (2.0, 0, 0, 0, 0, 0),
        (2.0, 0, 8, 0, 90, 60), (1.5, 0, 0, 0, 0, 90), (1.5, 0, -8, 0, -35, 20),
        (2.0, 0, 0, 0, 0, 0), (1.0, 0, 0, 0, 0, 0)]
NAMES = ['rest', 'rest', 'shrug', 'drop', 'rest', 'reach', 'squeeze', 'rest', 'raise 60', 'raise 90 + shrug',
         'rest', 'swing forward 90', 'elbow 90', 'swing back 35', 'rest', 'rest']


def human_pose(t):
    """Wearer's GH position (scan mm), arm and forearm rotations (MuJoCo frame) at time t."""
    times = np.cumsum([k[0] for k in KEYS])
    i = int(np.searchsorted(times, t, side='right')) - 1
    i = min(max(i, 0), len(KEYS) - 2)
    a, b = KEYS[i], KEYS[i + 1]
    u = 0.0 if times[i + 1] == times[i] else (t - times[i]) / (times[i + 1] - times[i])
    u = min(max(u, 0.0), 1.0)
    e = 0.5 - 0.5 * math.cos(math.pi * u)
    elev, prot, abd, flex, elb = (a[j] + (b[j] - a[j]) * e for j in range(1, 6))
    elev += RHYTHM * max(abd, flex, 0.0)
    # collarbone rotation in the MuJoCo frame: elevation about the forward axis (GH goes up on the right side),
    # protraction about the vertical axis (GH goes forward)
    Rc = rot((0, 0, 1), prot) @ rot((1, 0, 0), -elev)
    sc, gh0 = P(SC), P(GH)
    gh = sc + Rc @ (gh0 - sc)
    R = Rc @ rot((1, 0, 0), -abd) @ rot((0, -1, 0), flex)
    return gh, R, rot((0, -1, 0), elb), NAMES[i + 1] if u > 0.5 else NAMES[i]


def run(record_every=40):
    os.makedirs(OUT, exist_ok=True)
    m = model()
    d = mujoco.MjData(m)
    gh, el = P(GH), P(EL)
    sid = {n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, n) for n in ('hum_strap', 'exo_strap', 'hum_strap2', 'exo_strap2', 'hum_cuff', 'exo_cuff')}
    jn = ['lift', 'q1', 'q2', 'abd', 'flex', 'elbow']
    jq = {n: m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in jn}
    T = float(np.sum([k[0] for k in KEYS]))
    hb, fb = m.body('human').mocapid[0], m.body('human_fa').mocapid[0]
    log = []
    yb = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, 'yoke')
    # settle at rest with the arm held still
    steps = int(T / m.opt.timestep)
    for k in range(steps):
        t = k * m.opt.timestep
        shoulder, R, Re, name = human_pose(t)
        dd = (shoulder - gh) * 1000.0
        d.mocap_pos[hb] = shoulder
        d.mocap_quat[hb] = quat(R)
        elbow = shoulder + R @ (el - gh)
        d.mocap_pos[fb] = elbow
        d.mocap_quat[fb] = quat(R @ Re)
        d.ctrl[0] = SPRING_F if t > 0.2 else SPRING_F * t / 0.2        # + extends the strut (pushes its ends apart)
        mujoco.mj_step(m, d)
        if k % record_every == 0:
            ua = d.site_xpos[sid['exo_strap']] - d.site_xpos[sid['hum_strap']]
            ua2 = d.site_xpos[sid['exo_strap2']] - d.site_xpos[sid['hum_strap2']]
            cf = d.site_xpos[sid['exo_cuff']] - d.site_xpos[sid['hum_cuff']]
            log.append(dict(t=t, name=name, strap_ua=STRAP_K * float(np.linalg.norm(ua) + np.linalg.norm(ua2)), strap_cuff=STRAP_K * float(np.linalg.norm(cf)),
                            gap_ua=1000 * float(np.linalg.norm(ua)), gap_cuff=1000 * float(np.linalg.norm(cf)),
                            gh_err=1000 * float(np.linalg.norm(d.xpos[yb] - shoulder)),
                            q={n: math.degrees(float(d.qpos[jq[n]])) for n in jn}, d=[float(x) for x in dd]))
    return m, log


def summarize(log):
    out = {}
    for row in log:
        k = row['name']
        o = out.setdefault(k, dict(strap_ua_max=0.0, strap_cuff_max=0.0))
        o['strap_ua_max'] = round(max(o['strap_ua_max'], row['strap_ua']), 1)
        o['strap_cuff_max'] = round(max(o['strap_cuff_max'], row['strap_cuff']), 1)
    return out


if __name__ == '__main__':
    model, log = run()
    s = summarize(log)
    json.dump(dict(summary=s, log=log), open(os.path.join(OUT, 'strap_test.json'), 'w'), indent=1)
    for k, o in s.items():
        print('%-18s upper-arm strap max %6.1f N   cuff max %6.1f N' % (k, o['strap_ua_max'], o['strap_cuff_max']))


# The six numbers that describe what the straps do to the arm: the net push (3 directions) and the net twist about the
# shoulder joint (3 axes), both in the arm's own frame so they read the same in every pose.
WRENCH_ROWS = [  # (label for +, label for -, index, kind)
    ('push forward', 'push back', 0, 'F'), ('push out', 'push in', 1, 'F'), ('push up', 'pull down', 2, 'F'),
    ('lift out', 'press in', 0, 'M'), ('swing forward', 'swing back', 1, 'M'), ('twist out', 'twist in', 2, 'M')]
WRENCH_FULL = dict(F=40.0, M=8.0)          # bar end: 40 N, 8 N m


def arm_wrench(d, sid, shoulder, R):
    """Net strap force (N) on the arm and its moment about the shoulder joint (N m), in the arm frame:
    x forward, y outward (right), z up the arm."""
    F, Mo = np.zeros(3), np.zeros(3)
    for hs, es in (('hum_strap', 'exo_strap'), ('hum_strap2', 'exo_strap2'), ('hum_cuff', 'exo_cuff')):
        a0, a1 = d.site_xpos[sid[hs]], d.site_xpos[sid[es]]
        f = STRAP_K * (a1 - a0)
        F += f
        Mo += np.cross(a0 - shoulder, f)
    B = R @ np.diag([1.0, -1.0, 1.0])        # arm axes in the world: forward, outward (-y is right), up the arm
    return B.T @ F, B.T @ Mo


def draw_wrench(dr, x0, y0, w, F, Mo, font, font_b):
    """Six signed bars: centre line = zero, right = the first label, left = the second."""
    dr.text((x0, y0), 'Push on your arm (N)', font=font_b, fill=(255, 255, 255))
    y = y0 + 30
    for k, (pos, neg, i, kind) in enumerate(WRENCH_ROWS):
        if k == 3:
            y += 14
            dr.text((x0, y), 'Twist at your shoulder (N m)', font=font_b, fill=(255, 255, 255))
            y += 30
        val = (F if kind == 'F' else Mo)[i]
        full = WRENCH_FULL[kind]
        cx = x0 + w // 2
        dr.text((x0, y), neg, font=font, fill=(150, 160, 170))
        dr.text((x0 + w, y), pos, font=font, fill=(150, 160, 170), anchor='ra')
        by = y + 22
        dr.rectangle([x0, by, x0 + w, by + 14], fill=(45, 50, 56))
        L = max(-1.0, min(1.0, val / full)) * (w // 2)
        col = (240, 90, 70) if kind == 'F' else (90, 170, 240)
        dr.rectangle([min(cx, cx + L), by, max(cx, cx + L), by + 14], fill=col)
        dr.line([cx, by - 3, cx, by + 17], fill=(230, 230, 230), width=2)
        txt = '%+.0f' % val if kind == 'F' else '%+.1f' % val
        dr.text((cx + (8 if L <= 0 else -8), by - 1), txt, font=font, fill=(255, 255, 255), anchor='la' if L <= 0 else 'ra')
        y += 46


ARROW_M_PER_N = 0.02         # arrow length: 2 cm per newton (10 N = 20 cm), capped at 30 cm


PANEL_W = 300


def render_gif(path, fps=20, size=(600, 480), strut=20.0, azimuth=190.0, elevation=-20.0):
    """Run the sequence once with the given strut force and save an animation (front-right view)."""
    from PIL import Image, ImageDraw, ImageFont
    global SPRING_F
    try:
        FONT_B = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 20); FONT = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 17)
    except OSError:
        FONT_B = FONT = ImageFont.load_default()
    SPRING_F = strut
    m = model()
    d = mujoco.MjData(m)
    r = mujoco.Renderer(m, size[1], size[0])
    cam = mujoco.MjvCamera()
    cam.lookat[:] = P([-60, 1300, 120])
    cam.distance, cam.azimuth, cam.elevation = 0.95, azimuth, elevation
    gh, el = P(GH), P(EL)
    hb, fb = m.body('human').mocapid[0], m.body('human_fa').mocapid[0]
    sid = {n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, n) for n in ('hum_strap', 'exo_strap', 'hum_strap2', 'exo_strap2', 'hum_cuff', 'exo_cuff')}
    T = float(np.sum([k[0] for k in KEYS]))
    every = int(round(1.0 / fps / m.opt.timestep))
    frames = []
    for k in range(int(T / m.opt.timestep)):
        t = k * m.opt.timestep
        shoulder, R, Re, name = human_pose(t)
        d.mocap_pos[hb] = shoulder
        d.mocap_quat[hb] = quat(R)
        d.mocap_pos[fb] = shoulder + R @ (el - gh)
        d.mocap_quat[fb] = quat(R @ Re)
        d.ctrl[0] = SPRING_F if t > 0.2 else SPRING_F * t / 0.2
        mujoco.mj_step(m, d)
        if k % every == 0:
            r.update_scene(d, cam)
            # strap pull on the arm: an arrow at each strap from the arm toward where the exo holds it
            for hs, es, rgba in (('hum_strap', 'exo_strap', (0.9, 0.15, 0.1, 1)), ('hum_strap2', 'exo_strap2', (0.9, 0.15, 0.1, 1)),
                                 ('hum_cuff', 'exo_cuff', (1.0, 0.6, 0.0, 1))):
                a0, a1 = d.site_xpos[sid[hs]], d.site_xpos[sid[es]]
                f = STRAP_K * (a1 - a0)
                n = float(np.linalg.norm(f))
                if n < 1.0 or r.scene.ngeom >= r.scene.maxgeom:
                    continue
                u = f / n
                tail = a0 + u * 0.045                      # start at the skin, on the side the strap pulls toward
                tip = tail + u * min(0.30, ARROW_M_PER_N * n)
                g = r.scene.geoms[r.scene.ngeom]
                mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_ARROW, np.zeros(3), np.zeros(3), np.zeros(9), np.array(rgba, dtype=np.float32))
                mujoco.mjv_connector(g, mujoco.mjtGeom.mjGEOM_ARROW, 0.007, tail, tip)
                r.scene.ngeom += 1
            sim = Image.fromarray(r.render())
            im = Image.new('RGB', (size[0] + PANEL_W, size[1]), (20, 24, 28))
            im.paste(sim, (0, 0))
            Fw, Mw = arm_wrench(d, sid, shoulder, R)
            ua = STRAP_K * (np.linalg.norm(d.site_xpos[sid['exo_strap']] - d.site_xpos[sid['hum_strap']]) +
                            np.linalg.norm(d.site_xpos[sid['exo_strap2']] - d.site_xpos[sid['hum_strap2']]))
            cf = STRAP_K * np.linalg.norm(d.site_xpos[sid['exo_cuff']] - d.site_xpos[sid['hum_cuff']])
            dr = ImageDraw.Draw(im)
            dr.rectangle([0, 0, size[0] + PANEL_W, 58], fill=(20, 24, 28))
            draw_wrench(dr, size[0] + 16, 72, PANEL_W - 32, Fw, Mw, FONT, FONT_B)
            dr.text((12, 6), name, font=FONT_B, fill=(255, 255, 255))
            dr.text((12, 33), 'upper-arm straps %3.0f N' % ua, font=FONT, fill=(240, 90, 70))
            dr.text((250, 33), 'wrist cuff %3.0f N' % cf, font=FONT, fill=(255, 170, 40))
            dr.text((size[0] - 150, 33), 'strut %d N' % strut, font=FONT, fill=(200, 200, 200))
            dr.text((12, size[1] - 26), 'arrows: strap pull on your arm  (2 cm long = 1 N)', font=FONT, fill=(220, 220, 220))
            frames.append(im.convert('P', palette=Image.ADAPTIVE, colors=128))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0, optimize=True)
    return len(frames)
