"""Retrofit for shoulder towers printed before 18 Oct 2026 (no back pad: their back plate's slanted edge crosses the
rest pivot bolt line, so a through-bolt would seat on a half-moon). Instead the rest bracket clamps to the front plate
only: M6 x 30 socket head through washer, bracket, boss and front plate, into a captive nut in this printed backer
inside the tower's hollow. The nut pushes the backer onto the plate's inside face (compression only), spreading the
strap pull over a 30 mm disc of the solid 7 mm front plate. Clearance checked in the model: nothing reaches it in any
of the 22 motion poses (lower lift link >70 mm away at rest).

    python cad/fusion/retrofit_backer.py      # writes prints/shoulder-back-v3/retrofit/rest_backer_retrofit.stl
"""
import math
import os

import numpy as np
import trimesh

D, T = 30.0, 8.0            # disc: diameter, thickness (mm)
HOLE = 6.6                  # M6 clearance
AF, DEPTH = 10.3, 5.2       # hex pocket for an M6 nut (10 AF x 5): open on the face away from the plate
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'prints', 'shoulder-back-v3', 'retrofit', 'rest_backer_retrofit.stl')


def build():
    disc = trimesh.creation.cylinder(radius=D / 2, height=T, sections=96)
    disc.apply_translation([0, 0, T / 2])                    # z 0 (plate side, on the bed) .. T
    hole = trimesh.creation.cylinder(radius=HOLE / 2, height=T + 2, sections=48)
    hole.apply_translation([0, 0, T / 2])
    r = AF / 2 / math.cos(math.radians(30))
    hexa = trimesh.creation.cylinder(radius=r, height=DEPTH + 1, sections=6)
    hexa.apply_translation([0, 0, T - DEPTH + (DEPTH + 1) / 2])
    m = disc.difference(hole).difference(hexa)
    assert m.is_watertight
    return m


if __name__ == '__main__':
    m = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    m.export(OUT)
    with open(OUT, 'r+b') as f:                                 # built in print orientation (plate side on the bed)
        f.write(b'oriented for printing (cad/fusion/retrofit_backer.py)'.ljust(80, b' '))
    print(os.path.normpath(OUT), '%.0f mm3' % m.volume, np.round(m.extents, 1))
