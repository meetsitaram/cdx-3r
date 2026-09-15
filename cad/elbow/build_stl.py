#!/usr/bin/env python3
"""CDX-3R elbow STLs. Print parts + COTS envelope. Units mm."""
from __future__ import annotations

import json
import math
import struct
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "stl"
PUB = Path("/workspace/public/cad/elbow")
PARAMS = json.loads((ROOT.parent / "params.json").read_text())

N = 40
SHEAVE = PARAMS["cots"]["sheave"]
SHAFT = PARAMS["cots"]["shaft"]["dia"]
TUBE = PARAMS["cots"]["tube"]["od"]
INSERT = 4.6


def _n(a, b, c):
    n = np.cross(b - a, c - a)
    L = np.linalg.norm(n)
    return n / L if L else np.array([0.0, 0.0, 1.0])


class Mesh:
    def __init__(self):
        self.tris: list[np.ndarray] = []

    def add_tri(self, a, b, c):
        self.tris.append(np.stack([a, b, c]))

    def add(self, other: "Mesh"):
        self.tris.extend(other.tris)
        return self

    def transformed(self, R=None, t=None) -> "Mesh":
        R = np.eye(3) if R is None else R
        t = np.zeros(3) if t is None else np.asarray(t, float)
        m = Mesh()
        for tri in self.tris:
            m.tris.append(tri @ R.T + t)
        return m

    def rx(self, deg):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        return self.transformed(np.array([[1, 0, 0], [0, c, -s], [0, s, c]]))

    def ry(self, deg):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        return self.transformed(np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]]))

    def rz(self, deg):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        return self.transformed(np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]))

    def move(self, x=0, y=0, z=0):
        return self.transformed(t=np.array([x, y, z], float))


def write_stl(path: Path, mesh: Mesh, name="cdx"):
    path.parent.mkdir(parents=True, exist_ok=True)
    tris = mesh.tris
    with path.open("wb") as f:
        f.write(name.encode("ascii")[:80].ljust(80, b"\0"))
        f.write(struct.pack("<I", len(tris)))
        for tri in tris:
            n = _n(*tri)
            f.write(struct.pack("<3f", *n))
            for v in tri:
                f.write(struct.pack("<3f", *v))
            f.write(struct.pack("<H", 0))


def box(x0, x1, y0, y1, z0, z1) -> Mesh:
    p = np.array(
        [
            [x0, y0, z0],
            [x1, y0, z0],
            [x1, y1, z0],
            [x0, y1, z0],
            [x0, y0, z1],
            [x1, y0, z1],
            [x1, y1, z1],
            [x0, y1, z1],
        ],
        float,
    )
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    m = Mesh()
    for a, b, c, d in faces:
        m.add_tri(p[a], p[b], p[c])
        m.add_tri(p[a], p[c], p[d])
    return m


def cylinder(r, h, n=N, z0=None) -> Mesh:
    z0 = -h / 2 if z0 is None else z0
    z1 = z0 + h
    m = Mesh()
    an = np.linspace(0, 2 * math.pi, n, endpoint=False)
    xs, ys = r * np.cos(an), r * np.sin(an)
    top = np.array([0.0, 0.0, z1])
    bot = np.array([0.0, 0.0, z0])
    for i in range(n):
        j = (i + 1) % n
        a = np.array([xs[i], ys[i], z0])
        b = np.array([xs[j], ys[j], z0])
        c = np.array([xs[j], ys[j], z1])
        d = np.array([xs[i], ys[i], z1])
        m.add_tri(a, b, c)
        m.add_tri(a, c, d)
        m.add_tri(bot, b, a)
        m.add_tri(top, d, c)
    return m


def tube_c(r_out, r_in, h, open_deg=50, n=N) -> Mesh:
    """C-shaped cuff wall."""
    span = 360 - open_deg
    m = Mesh()
    z0, z1 = -h / 2, h / 2
    an = np.linspace(math.radians(-span / 2), math.radians(span / 2), n)
    for i in range(len(an) - 1):
        a0, a1 = an[i], an[i + 1]
        for r0, r1, flip in ((r_in, r_out, False),):
            p00 = np.array([r_in * math.cos(a0), r_in * math.sin(a0), z0])
            p10 = np.array([r_out * math.cos(a0), r_out * math.sin(a0), z0])
            p01 = np.array([r_in * math.cos(a0), r_in * math.sin(a0), z1])
            p11 = np.array([r_out * math.cos(a0), r_out * math.sin(a0), z1])
            q00 = np.array([r_in * math.cos(a1), r_in * math.sin(a1), z0])
            q10 = np.array([r_out * math.cos(a1), r_out * math.sin(a1), z0])
            q01 = np.array([r_in * math.cos(a1), r_in * math.sin(a1), z1])
            q11 = np.array([r_out * math.cos(a1), r_out * math.sin(a1), z1])
            m.add_tri(p10, q10, q11)
            m.add_tri(p10, q11, p11)
            m.add_tri(q00, p00, p01)
            m.add_tri(q00, p01, q01)
            m.add_tri(p11, q11, q01)
            m.add_tri(p11, q01, p01)
            m.add_tri(p00, q00, q10)
            m.add_tri(p00, q10, p10)
    # caps at the opening
    a0, a1 = an[0], an[-1]
    for a in (a0, a1):
        p0 = np.array([r_in * math.cos(a), r_in * math.sin(a), z0])
        p1 = np.array([r_out * math.cos(a), r_out * math.sin(a), z0])
        p2 = np.array([r_out * math.cos(a), r_out * math.sin(a), z1])
        p3 = np.array([r_in * math.cos(a), r_in * math.sin(a), z1])
        if a == a0:
            m.add_tri(p0, p1, p2)
            m.add_tri(p0, p2, p3)
        else:
            m.add_tri(p0, p2, p1)
            m.add_tri(p0, p3, p2)
    return m


def plate_hole(w, h, t, holes) -> Mesh:
    """Rectangle plate XY, thickness Z, holes (x,y,r). Coarse: plate minus no; ring around."""
    m = box(-w / 2, w / 2, -h / 2, h / 2, -t / 2, t / 2)
    # add hole walls as inner cylinders (slicer will treat as solid overlapping — not a real hole)
    # Real hole: rebuild faces. For garage STLs, emit a separate cutter note.
    # Better: annular plate using polar mesh if one centered hole, plus body.
    return m


def plate_with_center_hole(w, h, t, r_hole) -> Mesh:
    """Rounded-ish plate: outer box with cylindrical hole (proper)."""
    m = Mesh()
    # Use a disc-with-hole for the joint boss, plus two side wings as boxes
    # Center annulus
    n = N
    an = np.linspace(0, 2 * math.pi, n, endpoint=False)
    r_o = max(w, h) * 0.28
    z0, z1 = -t / 2, t / 2
    for i in range(n):
        j = (i + 1) % n
        a0, a1 = an[i], an[j]
        inner0 = np.array([r_hole * math.cos(a0), r_hole * math.sin(a0), z0])
        inner1 = np.array([r_hole * math.cos(a1), r_hole * math.sin(a1), z0])
        inner2 = np.array([r_hole * math.cos(a1), r_hole * math.sin(a1), z1])
        inner3 = np.array([r_hole * math.cos(a0), r_hole * math.sin(a0), z1])
        outer0 = np.array([r_o * math.cos(a0), r_o * math.sin(a0), z0])
        outer1 = np.array([r_o * math.cos(a1), r_o * math.sin(a1), z0])
        outer2 = np.array([r_o * math.cos(a1), r_o * math.sin(a1), z1])
        outer3 = np.array([r_o * math.cos(a0), r_o * math.sin(a0), z1])
        m.add_tri(inner0, inner3, inner2)
        m.add_tri(inner0, inner2, inner1)
        m.add_tri(outer0, outer1, outer2)
        m.add_tri(outer0, outer2, outer3)
        m.add_tri(outer0, inner0, inner1)
        m.add_tri(outer0, inner1, outer1)
        m.add_tri(outer3, outer2, inner2)
        m.add_tri(outer3, inner2, inner3)
    # proximal wing for tube
    m.add(box(-w / 2, -r_o + 2, -h / 2 + 6, h / 2 - 6, -t / 2, t / 2))
    return m


def fork() -> Mesh:
    r_hole = SHAFT / 2 + 0.15
    m = plate_with_center_hole(78, 52, 8, r_hole)
    # insert bosses (solid pins — heat-set drills these)
    for y in (-12.0, 12.0):
        m.add(cylinder(4.2, 8).move(-36, y, 0))
    return m


def forearm_hub() -> Mesh:
    r_hole = SHAFT / 2 + 0.15
    m = plate_with_center_hole(70, 44, 12, r_hole)
    m.add(box(12, 42, -16, 16, -6, 6))
    return m


def drum() -> Mesh:
    """Prototype printed sheave. Not for 15 kg."""
    r_o = (SHEAVE["od"] - 4) / 2
    r_i = SHAFT / 2 + 0.15
    r_g = SHEAVE["pitch"] / 2
    w = SHEAVE["width"]
    m = Mesh()
    n = N
    an = np.linspace(0, 2 * math.pi, n, endpoint=False)
    z0, z1 = -w / 2, w / 2
    # flanges
    for z_fl, sign in ((z0, 1), (z1, -1)):
        z_in = z_fl + sign * 3.5
        for i in range(n):
            j = (i + 1) % n
            a0, a1 = an[i], an[j]
            p0 = np.array([r_i * math.cos(a0), r_i * math.sin(a0), z_fl])
            p1 = np.array([r_o * math.cos(a0), r_o * math.sin(a0), z_fl])
            q0 = np.array([r_i * math.cos(a1), r_i * math.sin(a1), z_fl])
            q1 = np.array([r_o * math.cos(a1), r_o * math.sin(a1), z_fl])
            r0 = np.array([r_i * math.cos(a0), r_i * math.sin(a0), z_in])
            r1 = np.array([r_o * math.cos(a0), r_o * math.sin(a0), z_in])
            s0 = np.array([r_i * math.cos(a1), r_i * math.sin(a1), z_in])
            s1 = np.array([r_o * math.cos(a1), r_o * math.sin(a1), z_in])
            if sign == 1:
                m.add_tri(p0, q0, q1)
                m.add_tri(p0, q1, p1)
            else:
                m.add_tri(p0, p1, q1)
                m.add_tri(p0, q1, q0)
            m.add_tri(p0, r0, s0)
            m.add_tri(p0, s0, q0)
            m.add_tri(p1, q1, s1)
            m.add_tri(p1, s1, r1)
    # groove core
    r_core = r_g - 1.5
    m.add(cylinder(r_core, w - 7, z0=z0 + 3.5))
    return m


def cuff(id_mm: float) -> Mesh:
    m = tube_c(id_mm / 2 + 8, id_mm / 2, 48, open_deg=48)
    r = id_mm / 2 + 8 + 8
    for z in (-16.0, 16.0):
        for s in (-1, 1):
            tab = box(-7, 7, -5, 5, -4, 4).move(s * r, 0, z)
            m.add(tab)
    return m


def bowden() -> Mesh:
    m = box(-14, 14, -9, 9, -8, 8)
    # ferrule boss
    m.add(cylinder(5, 10).ry(90).move(-10, 0, 0))
    return m


def hard_stop() -> Mesh:
    return box(-15, 15, -9, 9, -7, 7)


def ref_sheave() -> Mesh:
    """COTS envelope — do not print."""
    r_o = SHEAVE["od"] / 2
    r_i = SHEAVE["bore"] / 2
    w = SHEAVE["width"]
    m = Mesh()
    n = N
    an = np.linspace(0, 2 * math.pi, n, endpoint=False)
    z0, z1 = -w / 2, w / 2
    for i in range(n):
        j = (i + 1) % n
        a0, a1 = an[i], an[j]
        inner0 = np.array([r_i * math.cos(a0), r_i * math.sin(a0), z0])
        inner1 = np.array([r_i * math.cos(a1), r_i * math.sin(a1), z0])
        inner2 = np.array([r_i * math.cos(a1), r_i * math.sin(a1), z1])
        inner3 = np.array([r_i * math.cos(a0), r_i * math.sin(a0), z1])
        outer0 = np.array([r_o * math.cos(a0), r_o * math.sin(a0), z0])
        outer1 = np.array([r_o * math.cos(a1), r_o * math.sin(a1), z0])
        outer2 = np.array([r_o * math.cos(a1), r_o * math.sin(a1), z1])
        outer3 = np.array([r_o * math.cos(a0), r_o * math.sin(a0), z1])
        m.add_tri(inner0, inner3, inner2)
        m.add_tri(inner0, inner2, inner1)
        m.add_tri(outer0, outer1, outer2)
        m.add_tri(outer0, outer2, outer3)
        m.add_tri(outer0, inner0, inner1)
        m.add_tri(outer0, inner1, outer1)
        m.add_tri(outer3, outer2, inner2)
        m.add_tri(outer3, inner2, inner3)
    return m


def assembly() -> Mesh:
    span = SHEAVE["width"] + 14
    m = Mesh()
    m.add(fork().move(0, 0, span / 2))
    m.add(fork().move(0, 0, -span / 2))
    m.add(ref_sheave())
    m.add(cylinder(SHAFT / 2, 100))
    m.add(forearm_hub().move(0, 8, 0))
    m.add(cuff(PARAMS["human"]["forearm_cuff_id"]).rx(90).move(0, 70, 0))
    m.add(cuff(PARAMS["human"]["upper_cuff_id"]).ry(90).move(-90, 0, 0))
    m.add(bowden().move(-42, 30, 18))
    m.add(bowden().move(-42, 30, -18))
    m.add(hard_stop().move(20, -30, 0))
    return m


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PUB.mkdir(parents=True, exist_ok=True)
    parts = {
        "print_fork_lateral": fork(),
        "print_fork_medial": fork(),
        "print_forearm_hub": forearm_hub(),
        "print_drum": drum(),
        "print_cuff_forearm": cuff(PARAMS["human"]["forearm_cuff_id"]),
        "print_cuff_upper": cuff(PARAMS["human"]["upper_cuff_id"]),
        "print_bowden_anchor": bowden(),
        "print_hard_stop": hard_stop(),
        "ref_sheave_DO_NOT_PRINT": ref_sheave(),
        "assembly_preview": assembly(),
    }
    for name, mesh in parts.items():
        write_stl(OUT / f"{name}.stl", mesh, name)
        write_stl(PUB / f"{name}.stl", mesh, name)
        print(f"  {name}.stl  {len(mesh.tris)} tris")


if __name__ == "__main__":
    main()
