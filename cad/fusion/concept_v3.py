"""Shoulder v3 concept sketch (proposal only, not for print): lift + fore-aft parallelograms behind the shoulder,
abduction housing on the moving carriage, open C-ring twist track on the upper arm, lateral upper-arm pipes.
Built as one temporary component under the top component (scan frame: mm, X fwd, Y up, Z right).
build() adds it and hides the parts it replaces; remove() deletes it and shows them again."""
import math
import adsk.core
import adsk.fusion

import fxlib as fx
from fxlib import Part, add, sub, mul, unit, cross, dot
import shoulder as sh

NAME = 'PROPOSAL v3 (concept, not for print)'
NEW_COL, SPRING_COL, PIPE_COL = '#1d9e75', '#d4a017', '#e9eef2'
HIDE = (('Abduction mount blocks', 'block R'), ('HW abd', None), ('Abduction sleeve', None),
        ('Elbow concept', 'Upper-arm unit: PVC'))


def _top():
    return next(o for o in fx.design.rootComponent.occurrences if o.component.name == sh.TOP).component


def _targets():
    root = fx.design.rootComponent
    for o in root.allOccurrences:
        for comp_pat, body_pat in HIDE:
            if comp_pat in o.component.name:
                for b in o.component.bRepBodies:
                    if body_pat is None or body_pat in b.name:
                        yield b


def remove():
    fx.init()
    top = _top()
    for o in list(top.occurrences):
        if o.component.name == NAME:
            o.deleteMe()
    for b in _targets():
        b.isLightBulbOn = True
    return 'removed'


def build():
    fx.init()
    remove()
    top = _top()
    grp = fx.group(top, NAME)
    GH = sh.GH
    out = {}

    def part(name, col):
        p = Part(grp, name, color=col)
        out[name] = p
        return p

    # ---- 1. lift parallelogram behind the upper back: links along Z, pivots about X (shrug up/down)
    p = part('1 lift parallelogram', NEW_COL)
    p.box(-216, -194, 1360, 1468, 22, 58, name='frame bracket (on top node, telescoping)')
    for y in (1450, 1385):
        p.box(-212, -198, y - 7, y + 7, 40, 152, name='lift link')
        for z in (40, 152):
            p.cyl('x', [-205, y, z], 7, 30, name='pivot')
    p.box(-216, -194, 1370, 1468, 146, 166, name='lift carriage')
    p.finish()
    s = part('spring (balances the exo weight)', SPRING_COL)
    s.polypipe([[-190, 1372, 50], [-190, 1440, 112]], 7, name='gas spring')
    s.finish()

    # ---- 2. fore-aft parallelogram: links along Y, pivots about Z (shoulder forward / back)
    q = part('2 fore-aft parallelogram', NEW_COL)
    q.box(-216, -164, 1452, 1468, 160, 180, name='carriage top arm')
    for x in (-205, -175):
        q.box(x - 6, x + 6, 1362, 1460, 166, 178, name='fore-aft link')
        for y in (1460, 1362):
            q.cyl('z', [x, y, 172], 7, 26, name='pivot')
    q.box(-214, -166, 1335, 1370, 158, 182, name='housing bracket')
    q.finish()

    # ---- 3. abduction housing on the carriage (axis X through GH), slimmer than the old block
    a = part('3 abduction housing', NEW_COL)
    a.cyl('x', [-150, GH[1], GH[2]], 30, 40, name='abduction housing (2 x 6806)')
    a.finish()

    # ---- 5. twist ring: open C-ring around the upper arm, axis along the humerus
    u = unit(sh.D['u'])
    c = sub(GH, mul(u, 80))
    ez = u
    ex = unit(cross([1, 0, 0], ez))
    ey = cross(ez, ex)
    d = unit([0, 0, -1])                                   # opening faces the ribs: nothing on the inner side
    gap = math.degrees(math.atan2(dot(d, ey), dot(d, ex)))
    r = part('5 twist ring (C-track + rollers)', NEW_COL)
    r.cring((ex, ey, ez), c, 72, 86, 22, gap, 160, name='C-track')
    for da in (-80, -30, 30, 80):
        ang = math.radians(gap + 180 + da)
        rp = add(c, add(mul(ex, 94 * math.cos(ang)), mul(ey, 94 * math.sin(ang))))
        r.cyl((ex, ey, ez), rp, 8, 14, name='roller 623VV')
    r.finish()

    # ---- upper-arm pipes on the outer / back side only (no pipe on the rib side)
    pp = part('upper-arm pipes (outer side only)', PIPE_COL)
    for da in (-35, 25):
        ang = math.radians(gap + 180 + da)
        top_pt = add(c, add(mul(ex, 79 * math.cos(ang)), mul(ey, 79 * math.sin(ang))))
        pp.polypipe([top_pt, sub(top_pt, mul(u, 150))], 10.75, name='PVC 21.5')
    pp.finish()

    for b in _targets():
        b.isLightBulbOn = False
    return 'built: ' + ', '.join(out)
