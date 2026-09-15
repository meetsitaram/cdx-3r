#!/usr/bin/env python3
"""CDX-3R wearable elbow. Arm occupies the cuffs. Joint lives outboard."""
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

N = 56
SHEAVE = PARAMS["cots"]["sheave"]
IDLER = PARAMS["cots"]["idler_bearing"]
SCREW = PARAMS["cots"]["shoulder_screw"]
SHAFT = SHEAVE["bore"]
HUMAN = PARAMS["human"]

# Anatomical: origin = elbow flexion axis, through the epicondyles.
# +X distal if extended, +Y anterior, +Z lateral (right arm).
# Work pose: 90° flexion — forearm along +Y, upper arm along -X.
ELBOW_HALF = HUMAN["elbow_width"] / 2  # 40
PAD = HUMAN["padding"]  # 8
CUFF_T = 8.0
GAP = 6.0  # air between cuff OD and lateral plate
UA_OD = HUMAN["upper_cuff_id"] / 2 + CUFF_T  # outer radius
FA_OD = HUMAN["forearm_cuff_id"] / 2 + CUFF_T
Z_PLATE = ELBOW_HALF + PAD + GAP + 4  # ~58, plate center
# Keep the sheave entirely outside the forearm cuff envelope.
Z_SHEAVE = max(Z_PLATE + 10, FA_OD + SHEAVE["width"] / 2 + 8)


def _n(a, b, c):
    n = np.cross(b - a, c - a)
    L = np.linalg.norm(n)
    return n / L if L else np.array([0.0, 0.0, 1.0])


class Mesh:
    def __init__(self):
        self.tris: list[np.ndarray] = []

    def add_tri(self, a, b, c):
        self.tris.append(np.stack([np.asarray(a, float), np.asarray(b, float), np.asarray(c, float)]))

    def add(self, other: "Mesh"):
        self.tris.extend(other.tris)
        return self

    def transformed(self, R=None, t=None) -> "Mesh":
        R = np.eye(3) if R is None else np.asarray(R, float)
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
    with path.open("wb") as f:
        f.write(name.encode("ascii")[:80].ljust(80, b"\0"))
        f.write(struct.pack("<I", len(mesh.tris)))
        for tri in mesh.tris:
            n = _n(*tri)
            f.write(struct.pack("<3f", *n))
            for v in tri:
                f.write(struct.pack("<3f", *v))
            f.write(struct.pack("<H", 0))


def box(x0, x1, y0, y1, z0, z1) -> Mesh:
    p = np.array(
        [
            [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
            [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
        ],
        float,
    )
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
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


def annulus(r_out, r_in, h, n=N) -> Mesh:
    m = Mesh()
    z0, z1 = -h / 2, h / 2
    an = np.linspace(0, 2 * math.pi, n, endpoint=False)
    for i in range(n):
        j = (i + 1) % n
        a0, a1 = an[i], an[j]
        inner0 = np.array([r_in * math.cos(a0), r_in * math.sin(a0), z0])
        inner1 = np.array([r_in * math.cos(a1), r_in * math.sin(a1), z0])
        inner2 = np.array([r_in * math.cos(a1), r_in * math.sin(a1), z1])
        inner3 = np.array([r_in * math.cos(a0), r_in * math.sin(a0), z1])
        outer0 = np.array([r_out * math.cos(a0), r_out * math.sin(a0), z0])
        outer1 = np.array([r_out * math.cos(a1), r_out * math.sin(a1), z0])
        outer2 = np.array([r_out * math.cos(a1), r_out * math.sin(a1), z1])
        outer3 = np.array([r_out * math.cos(a0), r_out * math.sin(a0), z1])
        m.add_tri(inner0, inner3, inner2)
        m.add_tri(inner0, inner2, inner1)
        m.add_tri(outer0, outer1, outer2)
        m.add_tri(outer0, outer2, outer3)
        m.add_tri(outer0, inner0, inner1)
        m.add_tri(outer0, inner1, outer1)
        m.add_tri(outer3, outer2, inner2)
        m.add_tri(outer3, inner2, inner3)
    return m


def cuff_c(r_in, wall, h, open_deg=70, n=N) -> Mesh:
    """C-cuff around Z. Gap faces +X so we can rotate it medial after placing."""
    r_out = r_in + wall
    span = 360 - open_deg
    m = Mesh()
    z0, z1 = -h / 2, h / 2
    an = np.linspace(math.radians(-span / 2 + 180), math.radians(span / 2 + 180), n)
    for i in range(len(an) - 1):
        a0, a1 = an[i], an[i + 1]
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
    for a, flip in ((an[0], False), (an[-1], True)):
        p0 = np.array([r_in * math.cos(a), r_in * math.sin(a), z0])
        p1 = np.array([r_out * math.cos(a), r_out * math.sin(a), z0])
        p2 = np.array([r_out * math.cos(a), r_out * math.sin(a), z1])
        p3 = np.array([r_in * math.cos(a), r_in * math.sin(a), z1])
        if flip:
            m.add_tri(p0, p2, p1)
            m.add_tri(p0, p3, p2)
        else:
            m.add_tri(p0, p1, p2)
            m.add_tri(p0, p2, p3)
    return m


def strap_tabs(r_out, h=48) -> Mesh:
    m = Mesh()
    for z in (-h / 3, h / 3):
        m.add(box(r_out - 2, r_out + 12, -5, 5, z - 4, z + 4))
    return m


def cuff_upper() -> Mesh:
    # Around X (upper arm), parked 95 mm proximal. Opening medial (-Z).
    body = cuff_c(HUMAN["upper_cuff_id"] / 2, CUFF_T, 52)
    body.add(strap_tabs(UA_OD, 52))
    return body.ry(90).move(-95, 0, 0)


def cuff_forearm() -> Mesh:
    # Around Y (forearm at 90° flex), 80 mm distal of axis. Opening medial.
    body = cuff_c(HUMAN["forearm_cuff_id"] / 2, CUFF_T, 48)
    body.add(strap_tabs(FA_OD, 48))
    return body.rx(-90).move(0, 80, 0)


def lateral_plate() -> Mesh:
    """UPPER-ARM plate. Housing stops here. Does not cross the elbow."""
    t0, t1 = Z_PLATE - 4, Z_PLATE + 4
    m = Mesh()
    m.add(box(-130, 8, -16, 16, t0, t1))
    m.add(annulus(28, SHAFT / 2 + 0.2, 8).move(0, 0, Z_PLATE))
    m.add(box(-110, -80, -12, 12, FA_OD - 2, t1))
    m.add(idler_cup().move(-95, 32, Z_PLATE + 6))
    m.add(idler_cup().move(-40, -36, Z_PLATE + 6))
    return m


def distal_plate() -> Mesh:
    """FOREARM plate. Bolts to the sheave and rotates with it."""
    t0, t1 = Z_PLATE - 4, Z_PLATE + 4
    m = Mesh()
    m.add(box(-16, 16, 12, 120, t0, t1))
    m.add(annulus(32, SHAFT / 2 + 0.4, 6).move(0, 0, Z_PLATE))
    m.add(box(-12, 12, 64, 96, FA_OD - 2, t1))
    return m


def medial_plate() -> Mesh:
    """Upper-arm medial hinge only."""
    z = -Z_PLATE
    m = Mesh()
    m.add(box(-110, 8, -12, 12, z - 3, z + 3))
    m.add(annulus(22, SHAFT / 2 + 0.2, 6).move(0, 0, z))
    return m


def medial_distal() -> Mesh:
    z = -Z_PLATE
    m = Mesh()
    m.add(box(-12, 12, 12, 100, z - 3, z + 3))
    m.add(annulus(20, SHAFT / 2 + 0.4, 5).move(0, 0, z))
    return m


def idler_cup() -> Mesh:
    """Printed 608 housing. 22.3 mm ID, 8.3 mm through."""
    m = annulus(14.0, 11.15, IDLER["width"] + 0.4)
    m.add(annulus(14.0, 4.15, 2.5).move(0, 0, -(IDLER["width"] + 0.4) / 2 - 1.2))
    return m


def idler_bearing() -> Mesh:
    """COTS 608-2RS envelope. Do not print."""
    return annulus(IDLER["od"] / 2, IDLER["id"] / 2, IDLER["width"])


def shoulder_screw() -> Mesh:
    """91273A274: 3/4 in shoulder × 1.5 in, hex head outboard."""
    m = Mesh()
    # shoulder through sheave + plate
    m.add(cylinder(SCREW["shoulder_dia"] / 2, SCREW["shoulder_len"]))
    # hex approximated as cylinder
    m.add(cylinder(SCREW["head_dia"] / 2, 12.5, z0=SCREW["shoulder_len"] / 2))
    # threaded stub
    m.add(cylinder(9.4, 16, z0=-SCREW["shoulder_len"] / 2 - 16))
    return m


def nylock() -> Mesh:
    return cylinder(14.5, 10)


def drum() -> Mesh:
    w = SHEAVE["width"]
    m = annulus((SHEAVE["od"] - 4) / 2, SHAFT / 2 + 0.2, w)
    m.add(annulus(SHEAVE["od"] / 2 - 1, SHEAVE["pitch"] / 2 - 2, 4).move(0, 0, w / 2 - 2))
    m.add(annulus(SHEAVE["od"] / 2 - 1, SHEAVE["pitch"] / 2 - 2, 4).move(0, 0, -w / 2 + 2))
    return m.move(0, 0, Z_SHEAVE)


def shaft() -> Mesh:
    # Two stubs — they do NOT run through the arm.
    m = Mesh()
    m.add(cylinder(SHAFT / 2, 28).move(0, 0, Z_PLATE))
    m.add(cylinder(SHAFT / 2, 18).move(0, 0, -Z_PLATE))
    # Sheave axle, lateral only
    m.add(cylinder(SHAFT / 2, SHEAVE["width"] + 10).move(0, 0, Z_SHEAVE))
    return m


def rod(p0, p1, r=1.5) -> Mesh:
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    v = p1 - p0
    L = float(np.linalg.norm(v))
    if L < 0.8:
        return Mesh()
    z = v / L
    tmp = np.array([1.0, 0.0, 0.0]) if abs(z[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    x = np.cross(tmp, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return cylinder(r, L, n=12, z0=0).transformed(np.column_stack([x, y, z]), p0)


def polyline(pts, r=1.5) -> Mesh:
    m = Mesh()
    for a, b in zip(pts[:-1], pts[1:]):
        m.add(rod(a, b, r))
    return m


def arc_pts(radius, z, deg0, deg1, steps=14):
    an = np.linspace(math.radians(deg0), math.radians(deg1), steps)
    return [np.array([radius * math.cos(a), radius * math.sin(a), z]) for a in an]


def cable_flexor() -> Mesh:
    """Inner: ferrule on upper plate → 608 → wrap sheave → clamp on forearm sheave."""
    z_g = Z_SHEAVE
    r = SHEAVE["pitch"] / 2
    pts = [
        np.array([-160.0, 22.0, Z_PLATE + 10]),  # from backpack, still in housing
        np.array([-78.0, 26.0, Z_PLATE + 10]),  # ferrule
        np.array([-95.0, 32.0, Z_PLATE + 6]),  # 608
        np.array([-r - 4, -8.0, z_g]),
        *arc_pts(r, z_g, 185, 85),
    ]
    return polyline(pts, 1.6)


def cable_extensor() -> Mesh:
    z_g = Z_SHEAVE
    r = SHEAVE["pitch"] / 2
    pts = [
        np.array([-160.0, -22.0, Z_PLATE + 10]),
        np.array([-78.0, -26.0, Z_PLATE + 10]),
        np.array([-40.0, -36.0, Z_PLATE + 6]),
        np.array([-r - 2, 10.0, z_g]),
        *arc_pts(r, z_g, 175, 260),
    ]
    return polyline(pts, 1.6)


def cable_clamp() -> Mesh:
    """Stop on the sheave — inner is pinched here, not on the cuff."""
    r = SHEAVE["pitch"] / 2 + 4
    z = Z_SHEAVE
    m = box(-6, 6, -5, 5, -5, 5).move(0, r, z)
    m.add(box(-6, 6, -5, 5, -5, 5).move(-r * 0.2, -r * 0.95, z))
    return m


def housing() -> Mesh:
    """5 mm Bowden. Stops at the green anchors. Does not wrap the sheave."""
    m = polyline(
        [np.array([-200.0, 22.0, Z_PLATE + 10]), np.array([-78.0, 26.0, Z_PLATE + 10])],
        r=2.6,
    )
    m.add(
        polyline(
            [np.array([-200.0, -22.0, Z_PLATE + 10]), np.array([-78.0, -26.0, Z_PLATE + 10])],
            r=2.6,
        )
    )
    return m


def bowden() -> Mesh:
    a = box(-16, 16, -10, 10, -8, 8)
    a.add(cylinder(5.5, 14).ry(90).move(-8, 0, 0))
    m = a.move(-70, 28, Z_PLATE + 12)
    m.add(a.move(-70, -28, Z_PLATE + 12))
    return m


def hard_stop() -> Mesh:
    return box(-8, 22, -36, -18, Z_PLATE - 6, Z_PLATE + 6)


def ghost_arm() -> Mesh:
    """Preview only. Soft-tissue stand-in so the hole is obvious."""
    m = Mesh()
    m.add(cylinder(38, 200).ry(90).move(-100, 0, 0))  # upper arm
    m.add(cylinder(34, 180).rx(90).move(0, 90, 0))  # forearm
    return m


def sheave() -> Mesh:
    return annulus(SHEAVE["od"] / 2, SHEAVE["bore"] / 2, SHEAVE["width"]).move(0, 0, Z_SHEAVE)


PALETTE = {
    "cuff_upper": "#12b5d4",
    "cuff_forearm": "#5ee0ff",
    "lateral": "#f2f4f7",
    "distal": "#cbd5e1",
    "medial": "#4b5568",
    "sheave": "#ffc93c",
    "screw": "#111215",
    "nylock": "#ef4444",
    "bearing": "#ff6a1a",
    "anchor": "#22c55e",
    "stop": "#facc15",
    "arm": "#f3c6a5",
    "housing": "#1f2937",
    "cable_flex": "#e879f9",
    "cable_ext": "#818cf8",
    "clamp": "#fb7185",
}


def assembly_layers(with_arm=False):
    screw_z = Z_SHEAVE + SHEAVE["width"] / 2 - SCREW["shoulder_len"] / 2 + 2
    layers = [
        ("cuff_upper", cuff_upper(), PALETTE["cuff_upper"]),
        ("cuff_forearm", cuff_forearm(), PALETTE["cuff_forearm"]),
        ("lateral", lateral_plate(), PALETTE["lateral"]),
        ("distal", distal_plate(), PALETTE["distal"]),
        ("medial", medial_plate(), PALETTE["medial"]),
        ("sheave", sheave(), PALETTE["sheave"]),
        ("screw", shoulder_screw().move(0, 0, screw_z), PALETTE["screw"]),
        ("nylock", nylock().move(0, 0, Z_PLATE - 10), PALETTE["nylock"]),
        (
            "bearing",
            idler_bearing().move(-95, 32, Z_PLATE + 6).add(idler_bearing().move(-40, -36, Z_PLATE + 6)),
            PALETTE["bearing"],
        ),
        ("anchor", bowden(), PALETTE["anchor"]),
        ("housing", housing(), PALETTE["housing"]),
        ("cable_flex", cable_flexor(), PALETTE["cable_flex"]),
        ("cable_ext", cable_extensor(), PALETTE["cable_ext"]),
        ("clamp", cable_clamp(), PALETTE["clamp"]),
        ("stop", hard_stop(), PALETTE["stop"]),
    ]
    if with_arm:
        layers.insert(0, ("arm", ghost_arm(), PALETTE["arm"]))
    return layers


def assembly(with_arm=False) -> Mesh:
    m = Mesh()
    for _, mesh, _ in assembly_layers(with_arm):
        m.add(mesh)
    return m


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PUB.mkdir(parents=True, exist_ok=True)
    parts = {
        "print_cuff_upper": cuff_upper(),
        "print_cuff_forearm": cuff_forearm(),
        "print_fork_lateral": lateral_plate(),
        "print_fork_distal": distal_plate(),
        "print_fork_medial": medial_plate(),
        "print_forearm_hub": annulus(28, SHAFT / 2 + 0.2, 12),
        "print_drum": drum().move(0, 0, -Z_SHEAVE),  # print at origin
        "print_bowden_anchor": bowden().move(70, -28, -(Z_PLATE + 12)),
        "print_hard_stop": hard_stop().move(0, 36, -Z_PLATE),
        "print_idler_cup": idler_cup(),
        "ref_sheave_DO_NOT_PRINT": sheave().move(0, 0, -Z_SHEAVE),
        "ref_608_DO_NOT_PRINT": idler_bearing(),
        "ref_shoulder_screw_DO_NOT_PRINT": shoulder_screw(),
        "ref_arm_ghost_DO_NOT_PRINT": ghost_arm(),
        "assembly_preview": assembly(False),
        "assembly_worn": assembly(True),
    }
    for name, mesh in parts.items():
        write_stl(OUT / f"{name}.stl", mesh, name)
        write_stl(PUB / f"{name}.stl", mesh, name)
    asm_pub = PUB / "asm"
    asm_out = OUT / "asm"
    asm_pub.mkdir(parents=True, exist_ok=True)
    asm_out.mkdir(parents=True, exist_ok=True)
    colors = {}
    for name, mesh, hex_color in assembly_layers(True):
        write_stl(asm_out / f"{name}.stl", mesh, name)
        write_stl(asm_pub / f"{name}.stl", mesh, name)
        colors[name] = hex_color
        print(f"  asm/{name:20s} {len(mesh.tris):5d}  {hex_color}")
    (asm_pub / "colors.json").write_text(json.dumps({"palette": PALETTE, "layers": colors}, indent=2))
    (asm_out / "colors.json").write_text(json.dumps({"palette": PALETTE, "layers": colors}, indent=2))


if __name__ == "__main__":
    main()
