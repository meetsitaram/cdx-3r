"""Shoulder, backpack, system and wearer stages, ported from the repo's build_stl.py files.

Coordinates are the repo's world frame (Y up, Z outboard) unless a group sets
its own frame: the backpack group carries R_PACK / T_PACK, and the deltoid
cuff and flexion yoke carry the system's rz(-90) through their own groups.
Printed parts join their primitives into one body; layers that hold several
separate pieces (bearings, anchors, collars) keep one body per piece.
"""
import math

import fxlib as fx
from fxlib import Part

SHEAVE = fx.PARAMS['cots']['sheave']
SCREW = fx.PARAMS['cots']['shoulder_screw']
IDLER = fx.PARAMS['cots']['idler_bearing']
SHAFT = SHEAVE['bore']
PACK = fx.PARAMS['packaging']
WINCH_ROWS = PACK['winch_rows_y']
WINCH_X, WINCH_Z = -35.75, float(PACK['winch_center_z'])
BATTERY_SIZE, BATTERY_CENTER = PACK['battery_envelope_xyz'], PACK['battery_center_xyz']
ZF, XA = fx.Z_FLEX, fx.X_ABD


# ---------------------------------------------------------------- shared hardware

def shoulder_screw(p, axis, c):
    """91273A274 along +axis from centre c: shoulder, head outboard, thread stub."""
    d = fx.AX[axis][2]
    L = SCREW['shoulder_len']
    at = lambda s: fx.add(c, fx.mul(d, s))
    return p.join(p.cyl(axis, c, SCREW['shoulder_dia'] / 2, L)
                  + p.cyl(axis, at(L / 2 + 6.25), SCREW['head_dia'] / 2, 12.5)
                  + p.cyl(axis, at(-L / 2 - 8), 9.4, 16))


def idler_cup(p, axis, c):
    """Printed 608 housing; the floor sits 4.9 mm below along -axis."""
    d = fx.AX[axis][2]
    w = IDLER['width'] + 0.4
    return p.join(p.ann(axis, c, 14.0, 11.15, w) + p.ann(axis, fx.add(c, fx.mul(d, -w / 2 - 1.2)), 14.0, 4.15, 2.5))


def bowden_anchor(p, center, rotated=False):
    """Block with a barrel along Y; rotated = ry(90) (block depth along X)."""
    x, y, z = center
    if rotated:
        block = p.box(x - 8, x + 8, y - 14, y + 14, z - 10, z + 10)
    else:
        block = p.box(x - 10, x + 10, y - 14, y + 14, z - 8, z + 8)
    return p.join(block + p.cyl('y', [x, y + 8, z], 5.5, 14))


# ---------------------------------------------------------------- shoulder

def shoulder(parent):
    g = fx.group(parent, 'Shoulder')
    R = fx.rot('z', -90)

    # Deltoid cuff and flexion yoke: system applies rz(-90) (arm hangs down -Y).
    p = Part(fx.group(g, 'Deltoid cuff frame (rz -90)', R=R), 'Deltoid cuff', 'sh_cuff')
    p.cring('x', [70, 0, 0], 60, 68, 56, -90, 80)
    for x0 in (84.667, 47.333):
        p.box(x0, x0 + 8, -5, 5, -80, -66, name='strap tab')
    p.finish('deltoid cuff')

    p = Part(fx.group(g, 'Flex yoke frame (rz -90)', R=R), 'Flexion yoke', 'sh_flex_yoke')
    p.join(p.box(12, 140, -16, 16, ZF - 6, ZF + 6) + p.ann('z', [0, 0, ZF], 30, SHAFT / 2 + 0.3, 7)
           + p.box(90, 130, -14, 14, 20, ZF + 6))
    p.finish('flexion yoke')

    p = Part(g, 'Scapula', 'sh_scapula')
    p.join(p.box(-65, 15, 40, 82, -40, 18) + p.box(-65, -25, 10, 82, -18, 18))
    p.finish('scapula')

    p = Part(g, 'Abduction yoke', 'sh_abd_yoke')
    p.join(p.box(-20, 20, -16, 16, 8, ZF - 8) + p.ann('x', [XA, 0, 0], 28, SHAFT / 2 + 0.2, 8)
           + p.box(XA + 8, 8, -16, 16, -12, 12))
    p.finish('abduction yoke')

    for name, layer, axis, c in (('Flexion sheave 3434T121', 'sh_sheave_flex', 'z', [0, 0, ZF]),
                                 ('Abduction sheave 3434T121', 'sh_sheave_abd', 'x', [XA, 0, 0])):
        p = Part(g, name, layer)
        p.ann(axis, c, SHEAVE['od'] / 2, SHEAVE['bore'] / 2, SHEAVE['width'])
        p.finish(name)

    p = Part(g, 'Cable comb', 'sh_comb')
    p.join(p.box(-30, 10, 58, 70, -18, 18) + [b for x in (-18.0, -6.0, 6.0) for b in p.cyl('y', [x, 64, 0], 4.0, 22)])
    p.finish('cable comb')

    r = fx.PITCH
    flex = [[20.0, 55.0, ZF - 8], [28.0, 38.0, ZF - 4], [0.0, r + 4, ZF]]
    flex += [[r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), ZF] for a in fx.linspace(90, 10, 14)]
    abd = [[XA + 10, 50.0, 20.0], [XA + 6, 36.0, 28.0], [XA, r, 0.0], [XA, 0.0, r], [XA, -r * 0.3, r * 0.7]]
    for name, layer, pts in (('Flexion cable', 'sh_cable_flex', flex), ('Abduction cable', 'sh_cable_abd', abd)):
        p = Part(g, name, layer)
        p.polypipe(pts, 1.6)
        p.finish(name.lower())

    p = Part(g, 'Hard stop', 'sh_stop')
    p.box(-8, 8, -20, -8, ZF - 8, ZF + 8)
    p.finish('hard stop')

    p = Part(g, 'Shoulder screw 91273A274 (flex)', 'sh_screw_flex')
    shoulder_screw(p, 'z', [0, 0, ZF])
    p.finish('shoulder screw')
    p = Part(g, 'Shoulder screw 91273A274 (abd)', 'sh_screw_abd')
    shoulder_screw(p, 'x', [XA, 0, 0])
    p.finish('shoulder screw')

    flex_idlers = [[28, 38, ZF - 4], [-22, 38, ZF - 4]]
    abd_idlers = [[XA + 6, 36, 28], [XA + 6, -36, 28]]
    for tag, axis, centers in (('flex', 'z', flex_idlers), ('abd', 'x', abd_idlers)):
        p = Part(g, f'608 bearings 6455K44 ({tag})', f'sh_bearing_{tag}')
        for c in centers:
            p.ann(axis, c, IDLER['od'] / 2, IDLER['id'] / 2, IDLER['width'])
        p.finish('608-2RS')
        p = Part(g, f'Idler cups ({tag})', f'sh_cups_{tag}')
        for c in centers:
            idler_cup(p, axis, c)
        p.finish('idler cup')

    p = Part(g, 'Cable clamp (flex)', 'sh_clamp_flex')
    p.box(r - 6, r + 6, -6, 6, ZF - 6, ZF + 6)
    p.finish('cable clamp')
    p = Part(g, 'Cable clamp (abd)', 'sh_clamp_abd')
    p.box(XA - 6, XA + 6, -6, 6, r - 6, r + 6)
    p.finish('cable clamp')

    p = Part(g, 'Bowden anchors (flex)', 'sh_anchor_flex')
    for x in (20, -20):
        bowden_anchor(p, [x, 55, ZF - 8])
    p.finish('bowden anchor')
    p = Part(g, 'Bowden anchors (abd)', 'sh_anchor_abd')
    for y in (50, -50):
        bowden_anchor(p, [XA + 10, y, 20], rotated=True)
    p.finish('bowden anchor')


# ---------------------------------------------------------------- backpack (pack frame)

def winch(p, y):
    """D6374 + 10:1 + drum + two 608s + encoder; motor axis along +X after ry(90)."""
    c = lambda s: [WINCH_X + s, y, WINCH_Z]
    bodies = {'motor': p.cyl('x', c(0), 37.5, 74), 'shaft': p.cyl('x', c(51), 5.0, 28),
              'rear shaft': p.cyl('x', c(-45), 4.0, 16),
              'planetary': p.box(WINCH_X + 38, WINCH_X + 110, y - 30, y + 30, WINCH_Z - 30, WINCH_Z + 30),
              'output': p.cyl('x', c(121), 7.0, 22), 'drum': p.ann('x', c(126), 22, 7.2, 18),
              'bearing A': p.ann('x', c(118), IDLER['od'] / 2, IDLER['id'] / 2, IDLER['width']),
              'bearing B': p.ann('x', c(134), IDLER['od'] / 2, IDLER['id'] / 2, IDLER['width']),
              'encoder': p.cyl('x', c(-57), 15, 18)}
    for name, bs in bodies.items():
        for b in bs:
            b.name = f'winch y{y:g} {name}'


def backpack(parent):
    g = fx.group(parent, 'Backpack (pack frame)', R=fx.R_PACK, t=fx.T_PACK)

    p = Part(g, 'Frame', 'pk_frame')
    bodies = p.plate([[-120, -240], [120, -240], [125, -218], [125, 132], [106, 152], [-106, 152], [-125, 132],
                      [-125, -218]], 0, 6, 1)
    for x in (-122, 122):
        bodies += p.box(x - 3, x + 3, -220, 126, 6, 113)
    for y in (-132, -35, 55, 145):
        bodies += p.box(-119, 119, y - 3, y + 3, 6, 21)
    p.join(bodies)
    p.finish('frame')

    x, y, z = BATTERY_CENTER
    w, h, d = BATTERY_SIZE
    p = Part(g, 'Battery sled', 'pk_sled')
    bodies = p.box(-w / 2 - 3, w / 2 + 3, y - h / 2 - 5, y + h / 2 + 5, z - d / 2 - 5, z - d / 2 - 2)
    for s in (-1, 1):
        bodies += p.box(s * (w / 2 + 3) - 2, s * (w / 2 + 3) + 2, y - h / 2 - 5, y + h / 2 + 5, z - d / 2 - 2, z + d / 2)
    p.join(bodies)
    p.finish('battery sled')

    p = Part(g, 'Battery envelope (reference)', 'pk_battery')
    p.box(x - w / 2, x + w / 2, y - h / 2, y + h / 2, z - d / 2, z + d / 2)
    p.finish('battery envelope')

    p = Part(g, 'ODrive S1 x3', 'pk_s1')
    for wy in WINCH_ROWS:
        p.box(-40, 40, wy - 28, wy + 28, 10, 26)
    p.finish('ODrive S1')

    p = Part(g, 'Spreaders', 'pk_spreader')
    for wy in WINCH_ROWS:
        p.box(-43, 43, wy - 30, wy + 30, 6, 9)
    p.finish('spreader')

    p = Part(g, 'Bulkhead', 'pk_bulkhead')
    p.join(p.box(-65, 65, 139, 148, 30, 48)
           + [b for bx in (-50, -30, -10, 10, 30, 50) for b in p.ann('y', [bx, 153, 39], 5, 2.8, 10)])
    p.finish('bulkhead')

    p = Part(g, 'Bowden housings (pack)', 'pk_housing')
    for index, wy in enumerate(WINCH_ROWS):
        for side in (-1, 1):
            hx = -50 + index * 40 + (side + 1) * 10
            pts = [[104, wy + side * 18, 88], [112, wy + side * 22, 92], [112, 132, 92], [hx, 148, 39], [hx, 160, 39]]
            p.pipe(fx.curve(pts, 32), 2.7)
    p.finish('bowden housing')

    p = Part(g, 'Bullet connectors', 'pk_bullet')
    for wy in WINCH_ROWS:
        for dy in (-5, 5):
            p.cyl('x', [-110, wy + dy, 69], 2.2, 10)
    p.finish('bullet connector')

    p = Part(g, 'Winches x3', 'pk_motor')
    for wy in WINCH_ROWS:
        winch(p, wy)
    p.finish()

    p = Part(g, 'XT90 x2', 'pk_xt90')
    for cx in (-35, 35):
        p.box(cx - 10, cx + 10, -239, -223, 51, 69)
    p.finish('XT90')


# ---------------------------------------------------------------- system

SH_X_ABD, EL_Z_PLATE = XA, fx.Z_PLATE


def housing_paths():
    routes = []
    for i, x in enumerate([-50, -30, -10, 10, 30, 50]):
        path = [fx.pack_point([x, 160, 39]), [-157, 106, -130 + i * 9], [-103 - i * 2, 104, 2 + i * 8],
                [-78 - i * 2, 65, 64 + i * 3]]
        if i < 2:
            path += [[-62 - i * 9, -40, 88], [-52 - i * 8, -140, 87], [-37, -fx.UA + 88, 80],
                     [18 if i == 0 else -18, -fx.UA + 58, EL_Z_PLATE + 10]]
        elif i < 4:
            path += [[-52, 58, 86], [20 if i == 2 else -20, 55, ZF - 8]]
        else:
            path += [[SH_X_ABD - 24, 28 if i == 4 else -28, 50], [SH_X_ABD + 10, 50 if i == 4 else -50, 20]]
        routes.append(fx.curve(path, 70))
    return routes


def system(parent):
    g = fx.group(parent, 'System')

    p = Part(g, 'Saddle', 'saddle')
    p.plate([[-62, -58], [-38, -72], [25, -45], [30, 20], [-10, 30], [-55, 5]], 0, 12, 2,
            origin=(0, 35, 0), frame=([1, 0, 0], [0, 0, 1], [0, -1, 0]))
    p.finish('saddle')

    p = Part(g, 'Shoulder yoke', 'yoke')
    for z in (-35, 35):
        p.pipe(fx.curve([fx.pack_point([z, 145, 10]), [-122, 84, -110], [-68, 68, -45], [-26, 35, 15]], 35), 7)
    p.finish('yoke tube')

    p = Part(g, 'Upper-arm beam', 'beam')
    p.pipe([[0, 0, ZF], [0, -fx.UA + 25, EL_Z_PLATE]], 7)
    p.finish('upper-arm beam')

    p = Part(g, 'Hip belt', 'belt')

    def belt(sk, to):
        for s in (1.0, 0.89):
            sk.sketchCurves.sketchEllipses.add(to(-15, fx.MID_Z + 20), to(-15, fx.MID_Z + 20 + 161 * s),
                                               to(-15 + 104 * s, fx.MID_Z + 20))
    p.prism([0, -263, 0], fx.AX['y'], -11, 11, belt, lambda ps: [q for q in ps if q.profileLoops.count == 2],
            name='hip belt')
    p.finish('hip belt')

    p = Part(g, 'Park rest', 'park')
    mx, my = 122, -fx.UA - 36
    p.join(p.box(mx - 25, mx + 25, my - 8, my, -38, 38) + p.box(mx - 25, mx + 25, my, my + 15, -38, -32)
           + p.box(mx - 25, mx + 25, my, my + 15, 32, 38)
           + p.pipe(fx.curve([[35, -263, -65], [90, -295, -42], [122, -fx.UA - 41, 0]], 20), 6))
    p.finish('park rest')

    p = Part(g, 'Harness straps', 'strap')
    for z in (-95, 25):
        zz = fx.MID_Z + z
        p.pipe(fx.curve([[-150, 56, zz], [-40, 68, zz], [65, 6, zz], [65, -180, zz]], 40), 8)
    p.finish('strap')

    for i, path in enumerate(housing_paths()):
        p = Part(g, f'Bowden housing {i}', f'housing_{i}')
        p.pipe(path, 3.3)
        p.finish(f'housing {i}')
        p = Part(g, f'Housing collars {i}', f'collars_{i}')
        for index in range(3, len(path) - 3, 5):
            p.pipe(path[index:index + 2], 3.9)
        p.finish(f'collar {i}')
        for label, end, nb in (('base', path[0], path[1]), ('end', path[-1], path[-2])):
            p = Part(g, f'Ferrule {i} {label}', f'ferrule_{i}_{label}')
            p.pipe([end, fx.add(end, fx.mul(fx.unit(fx.sub(nb, end)), 9))], 4.8)
            p.finish('ferrule')


# ---------------------------------------------------------------- wearer (reference only)

def wearer(parent):
    g = fx.group(parent, 'Wearer (reference)')
    z = fx.MID_Z
    for name, layer, items in (
            ('Mannequin', 'human', [([96, 178, 155], [-15, -110, z + 20]), ([43, 38, 44], [-5, 80, z + 10]),
                                    ([68, 84, 70], [-5, 164, z + 10])]),
            ('Upper arm', 'ghost_upper', [([36, fx.UA / 2 - 8, 36], [0, -fx.UA / 2, 0])]),
            ('Forearm', 'ghost_forearm', [([fx.FA / 2 - 5, 31, 32], [fx.FA / 2, -fx.UA, 0])])):
        p = Part(g, name, layer)
        for radii, c in items:
            p.ellipsoid(c, radii)
        p.finish(name.lower())
        for i in range(p.comp.bRepBodies.count):
            try:
                p.comp.bRepBodies.item(i).opacity = 0.35
            except Exception:
                pass
