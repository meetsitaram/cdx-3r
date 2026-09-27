"""Armor stages, ported from cad/armor/build_stl.py (revision B shells).

The repo samples closed skins from analytic functions (limb_point, cap_patch).
Every constant-t slice of a limb panel is planar (y = -t on the upper arm,
x = t on the forearm) and every constant-phi slice of a shoulder cap lies in a
plane through the flexion axis, so each shell is a Fusion loft through planar
sections built from the same functions: fitted splines through both skins.
"""
import math

import fxlib as fx


def Part(parent, name, layer):
    """Armor layers carry the system's ar_ prefix."""
    return fx.Part(parent, name, 'ar_' + layer)


UA, FA = fx.UA, fx.FA
WALL = 3.2
UA_ST = [[60, 69, 82], [100, 73, 85], [165, 68, 81], [230, 59, 84], [254, 57, 80]]
FA_ST = [[45, 58, 73], [70, 61, 73], [120, 56, 67], [205, 44, 52], [258, 38, 44]]


def stations(axis):
    st, scale = (UA_ST, UA / 290) if axis == 'ua' else (FA_ST, FA / 260)
    return [[s[0] * scale, s[1], s[2]] for s in st]


def limb_point(axis, t, angle, offset=0.0):
    st = stations(axis)
    xs = [s[0] for s in st]
    r = fx.interp(t, xs, [s[1] for s in st]) + offset
    z = fx.interp(t, xs, [s[2] for s in st]) + offset
    a = math.radians(angle)
    if axis == 'ua':
        return [r * math.sin(a), -t, z * math.cos(a)]
    return [t, -UA + r * math.sin(a), z * math.cos(a)]


def section_frame(axis, t):
    if axis == 'ua':
        return [0, -t, 0], [1, 0, 0], [0, 0, 1]
    return [t, 0, 0], [0, 1, 0], [0, 0, 1]


def panel_point(axis, t0, t1, a0, a1, u, v, offset):
    inset = (max(0, 1 - u / .12) + max(0, 1 - (1 - u) / .12)) * 7
    angle = (a0 + inset) * (1 - v) + (a1 - inset) * v
    ridge = 2.8 * math.sin(math.pi * v) ** 2 * math.sin(math.pi * u)
    return limb_point(axis, t0 + (t1 - t0) * u, angle, offset + ridge)


def u_samples(t0, t1, gu0=0.0, gu1=1.0, kinks=(), step=10.0):
    """Local u in [0, 1] for global u in [gu0, gu1], with a section every ~step mm and at kinks."""
    span = (t1 - t0) * (gu1 - gu0)
    n = max(3, int(math.ceil(span / step)) + 1)
    us = set(fx.linspace(0.0, 1.0, n))
    for g in kinks:
        if gu0 < g < gu1:
            us.add((g - gu0) / (gu1 - gu0))
    out = []
    for u in sorted(us):
        if not out or (u - out[-1]) * span > 0.6:
            out.append(u)
    if out[-1] != 1.0:
        out[-1] = 1.0
    return out


def limb_loft(p, axis, t0, t1, point, us, nv, name):
    """point(u, v, inner) -> 3D; sections at t0 + (t1 - t0) * u."""
    sections = []
    for u in us:
        o, ex, ey = section_frame(axis, t0 + (t1 - t0) * u)
        vs = fx.linspace(0, 1, nv)
        sections.append((o, ex, ey, [point(u, v, False) for v in vs], [point(u, v, True) for v in vs]))
    return p.loft(sections, name)


def station_kinks(axis, t0, t1):
    return [(s[0] - t0) / (t1 - t0) for s in stations(axis)]


def panel(p, axis, t0, t1, a0, a1, name):
    kinks = [.12, .88] + station_kinks(axis, t0, t1)
    return limb_loft(p, axis, t0, t1, lambda u, v, inner: panel_point(axis, t0, t1, a0, a1, u, v, 0 if inner else WALL),
                     u_samples(t0, t1, kinks=kinks), 13, name)


def sub_panel(p, axis, t0, t1, a0, a1, u0, u1, v0, v1, off_in, off_out, nv, name):
    """A patch of the exact panel surface (border strips, LED strips)."""
    kinks = [.12, .88] + station_kinks(axis, t0, t1)
    us = u_samples(t0, t1, u0, u1, kinks)

    def point(u, v, inner):
        return panel_point(axis, t0, t1, a0, a1, u0 + (u1 - u0) * u, v0 + (v1 - v0) * v, off_in if inner else off_out)
    ta, tb = t0 + (t1 - t0) * u0, t0 + (t1 - t0) * u1
    sections = []
    for u in us:
        o, ex, ey = section_frame(axis, ta + (tb - ta) * u)
        vs = fx.linspace(0, 1, nv)
        sections.append((o, ex, ey, [point(u, v, False) for v in vs], [point(u, v, True) for v in vs]))
    return p.loft(sections, name)


def limb_band(p, axis, t0, t1, a0, a1, offset, wall, nv, name):
    """limb_patch(taper=False): a plain band between two angles."""
    kinks = station_kinks(axis, t0, t1)
    point = lambda u, v, inner: limb_point(axis, t0 + (t1 - t0) * u, a0 * (1 - v) + a1 * v,
                                           offset + (0 if inner else wall))
    return limb_loft(p, axis, t0, t1, point, u_samples(t0, t1, kinks=kinks, step=6.0), nv, name)


def bolt(p, point, normal):
    """bolt_at: chamfered washer-head 3.6/1.5 x 2.2 on the panel normal."""
    n = fx.unit(normal)
    ref = [0.0, 1.0, 0.0] if abs(n[1]) < .9 else [1.0, 0.0, 0.0]
    x = fx.unit(fx.cross(ref, n))
    y = fx.cross(n, x)
    return p.ann((x, y, n), point, 3.6, 1.5, 2.2, chamfer=0.7, name='bolt')


# ---------------------------------------------------------------- limbs

def limbs(parent):
    g = fx.group(parent, 'Armor - limbs')
    for axis, start, end in (('ua', 68 * UA / 290, 246 * UA / 290), ('fa', 51 * FA / 260, 252 * FA / 260)):
        pieces = [('', -39, 39), ('_front', 43, 118), ('_rear', -118, -43)]
        for suffix, a, b in pieces:
            p = Part(g, f'{axis.upper()} panel{suffix.replace("_", " ")}', axis + suffix)
            panel(p, axis, start, end, a, b, 'panel')
            p.finish(f'{axis} panel{suffix}')
        p = Part(g, f'{axis.upper()} trim', axis + '_trim')
        for _, a, b in pieces:
            for u0, u1, v0, v1 in ((.015, .985, 0, .075), (.015, .985, .925, 1), (.015, .065, .075, .925),
                                   (.935, .985, .075, .925)):
                nv = 4 if v1 - v0 < .1 else 13
                sub_panel(p, axis, start, end, a, b, u0, u1, v0, v1, 3.4, 5.2, nv, 'trim')
        p.finish('trim')
        p = Part(g, f'{axis.upper()} fasteners', axis + '_fasteners')
        for _, a0, a1 in pieces:
            for t in (start + 12, end - 12):
                for a in (a0 + 6, a1 - 6):
                    q = limb_point(axis, t, a, 6)
                    bolt(p, q, fx.sub(limb_point(axis, t, a, 7), q))
        p.finish('fastener')
        p = Part(g, f'{axis.upper()} LED strips', axis + '_led')
        for angle in (-31, 31):
            v0, v1 = (angle - 1 + 39) / 78, (angle + 1 + 39) / 78
            sub_panel(p, axis, start, end, -39, 39, .17, .84, v0, v1, 3.4, 4.4, 3, 'led')
        p.finish('LED strip')


# ---------------------------------------------------------------- shoulder cap

def cap_outer(ph):
    return 1 / math.sqrt((math.cos(ph) / 87) ** 2 + (math.sin(ph) / 99) ** 2)


def cap_loft(p, phi0, phi1, u0=0.0, u1=1.0, lift=0.0, wall=3.5, name='cap'):
    span = phi1 - phi0
    phis = fx.linspace(phi0, phi1, max(3, int(math.ceil(span / 6.0)) + 1))
    nu = max(4, int(math.ceil((u1 - u0) * 14)) + 1)
    sections = []
    for phd in phis:
        ph = math.radians(phd)
        outer_r = cap_outer(ph)
        c, s = math.cos(ph), math.sin(ph)

        def pt(u, inner):
            r = 53 + (outer_r - 53) * u
            z = 96 - 65 * u ** 2.5 + lift - (wall if inner else 0)
            return [r * c, r * s, z]
        us = fx.linspace(u0, u1, nu)
        sections.append(([0, 0, 0], [c, s, 0], [0, 0, 1], [pt(u, False) for u in us], [pt(u, True) for u in us]))
    return p.loft(sections, name)


def shoulder(parent):
    g = fx.group(parent, 'Armor - shoulder')
    arcs = [(4, 118), (122, 238), (242, 356)]
    for (a, b), (name, layer) in zip(arcs, (('Deltoid cap', 'deltoid'), ('Deltoid cap front', 'deltoid_front'),
                                            ('Deltoid cap rear', 'deltoid_rear'))):
        p = Part(g, name, layer)
        cap_loft(p, a, b)
        p.finish(name.lower())

    p = Part(g, 'Shoulder trim', 'shoulder_trim')
    for a, b in arcs:
        cap_loft(p, a, b, .86, .99, 2, 1.6, 'rim')
        cap_loft(p, a, a + 4, .10, .86, 2, 1.6, 'rib')
        cap_loft(p, b - 4, b, .10, .86, 2, 1.6, 'rib')
    p.finish('trim')

    p = Part(g, 'Shoulder bezel', 'bezel')
    p.ann('z', [0, 0, 99], 56, 46.5, 6, chamfer=0.7)
    p.finish('bezel')

    p = Part(g, 'Scapula fairing', 'scapula')
    rx = fx.rot('x', -65)
    frame = [fx.mat_vec(rx, v) for v in ([1, 0, 0], [0, 1, 0], [0, 0, 1])]
    p.plate([[-72, -25], [-48, -42], [40, -30], [68, 0], [42, 38], [-42, 40], [-72, 20]], 0, 5, 1.5,
            origin=(-32, 62, -12), frame=frame)
    p.finish('scapula fairing')

    p = Part(g, 'Shoulder fasteners', 'shoulder_fasteners')
    for a, b in arcs:
        for phd in (a + 10, b - 10):
            ph = math.radians(phd)
            r, outer_r = 78, cap_outer(ph)
            u = (r - 53) / (outer_r - 53)
            z = 96 - 65 * u ** 2.5
            slope = 65 * 2.5 * u ** 1.5 / (outer_r - 53)
            n = fx.unit([slope * math.cos(ph), slope * math.sin(ph), 1.0])
            bolt(p, fx.add([r * math.cos(ph), r * math.sin(ph), z], fx.mul(n, 1.3)), n)
    p.finish('fastener')

    p = Part(g, 'Shoulder LED', 'shoulder_led')
    for a, b in arcs:
        p.arc_pipe([0, 0, 0], 58, 100, a + 5, b - 5, 1.1)
    p.finish('LED')


# ---------------------------------------------------------------- elbow ring and wrist

def elbow_wrist(parent):
    g = fx.group(parent, 'Armor - elbow and wrist')
    p = Part(g, 'Elbow bezel', 'elbow_bezel')
    p.ann('z', fx.add(fx.ELBOW, [0, 0, fx.Z_SHEAVE + 13]), 54, 47, 6, chamfer=0.7)
    p.finish('elbow bezel')

    p = Part(g, 'Elbow LED', 'elbow_led')
    for a, b in ((12, 162), (192, 342)):
        p.arc_pipe(fx.ELBOW, 55.5, fx.Z_SHEAVE + 16, a, b, 1.0)
    p.finish('LED')

    p = Part(g, 'Wrist collar', 'wrist')
    limb_band(p, 'fa', FA - 8, FA + 15, -120, 120, 2, 3, 25, 'wrist collar')
    p.finish('wrist collar')

    p = Part(g, 'Wrist trim', 'wrist_trim')
    for t in (FA - 3, FA + 10):
        limb_band(p, 'fa', t, t + 3, -112, 112, 5.3, 1.5, 25, 'wrist band')
    p.finish('wrist trim')

    for t in fx.linspace(FA - 62, FA - 37, 4):
        p = Part(g, f'Vent {round(t)}', f'vent_{round(t)}')
        limb_band(p, 'fa', t, t + 3, 52, 105, 4, 2, 7, 'vent')
        p.finish('vent rib')


# ---------------------------------------------------------------- pack shells (pack frame)

def pack(parent):
    g = fx.group(parent, 'Armor - pack (pack frame)', R=fx.R_PACK, t=fx.T_PACK)
    side = [[92, 146], [120, 124], [128, 70], [128, -166], [108, -234], [80, -236], [96, -180], [96, 112]]
    for name, layer, outline in (('Pack side left', 'pack', [[-x, y] for x, y in side][::-1]),
                                 ('Pack side right', 'pack_right', side)):
        p = Part(g, name, layer)
        p.plate(outline, 109, 7, 1.8)
        p.finish(name.lower())
    p = Part(g, 'Pack lid', 'lid')
    p.plate([[-94, -128], [94, -128], [104, -166], [78, -230], [-78, -230], [-104, -166]], 105, 9, 2)
    p.finish('pack lid')
    p = Part(g, 'Pack crown', 'pack_crown')
    p.plate([[-100, 126], [100, 126], [85, 148], [-85, 148]], 105, 9, 2)
    p.finish('pack crown')
    for index, y in enumerate([55, -35, -125]):
        p = Part(g, f'Pack bridge {index}', f'pack_bridge_{index}')
        p.plate([[-100, y - 5], [100, y - 5], [100, y + 5], [-100, y + 5]], 106, 7, 1.5)
        p.finish('pack bridge')
    p = Part(g, 'Pack trim', 'pack_trim')
    for s in (-1, 1):
        p.pipe(fx.curve([[s * 108, 136, 120], [s * 124, 100, 120], [s * 124, -150, 120], [s * 95, -228, 118]], 32), 2.4)
    p.finish('pack trim')
    p = Part(g, 'Pack LED', 'pack_led')
    for s in (-1, 1):
        p.pipe(fx.curve([[s * 103, 114, 119], [s * 112, 85, 119], [s * 112, -100, 119]], 24), 1.15)
    p.finish('LED')
