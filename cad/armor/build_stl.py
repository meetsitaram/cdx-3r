#!/usr/bin/env python3
"""CDX-3R sport dishes. Overlapping plates. Joints stay open."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
CAD = ROOT.parent
sys.path.insert(0, str(CAD / "elbow"))
from build_stl import Mesh, annulus, box, cuff_c, cylinder, write_stl  # noqa: E402

OUT = ROOT / "stl"
PUB = Path("/workspace/public/cad/armor")

PALETTE = {
    "ghost_cuff": "#5ee0ff",
    "ghost_frame": "#94a3b8",
    "ua": "#1f2328",
    "fa": "#252a31",
    "deltoid": "#1c2024",
    "scapula": "#2a3038",
    "pack": "#16191d",
    "lid": "#1a1e24",
    "led": "#3b82f6",
    "screw": "#c5cad3",
}


def _pt(r, lat, lon):
    c, s = math.cos(lat), math.sin(lat)
    return np.array([r * c * math.cos(lon), r * s, r * c * math.sin(lon)])


def sphere_shell(r_out, r_in, lat0, lat1, lon0, lon1, nlat=14, nlon=22) -> Mesh:
    """Open spherical dish. Joints live in the missing sector."""
    m = Mesh()
    lats = np.linspace(math.radians(lat0), math.radians(lat1), nlat)
    lons = np.linspace(math.radians(lon0), math.radians(lon1), nlon)

    def ring(r, i, j):
        return (
            _pt(r, lats[i], lons[j]),
            _pt(r, lats[i], lons[j + 1]),
            _pt(r, lats[i + 1], lons[j + 1]),
            _pt(r, lats[i + 1], lons[j]),
        )

    for i in range(nlat - 1):
        for j in range(nlon - 1):
            a, b, c, d = ring(r_out, i, j)
            m.add_tri(a, b, c)
            m.add_tri(a, c, d)
            a, b, c, d = ring(r_in, i, j)
            m.add_tri(a, d, c)
            m.add_tri(a, c, b)
    for i in range(nlat - 1):
        for lon in (lons[0], lons[-1]):
            o0 = _pt(r_out, lats[i], lon)
            o1 = _pt(r_out, lats[i + 1], lon)
            i0 = _pt(r_in, lats[i], lon)
            i1 = _pt(r_in, lats[i + 1], lon)
            if lon == lons[0]:
                m.add_tri(o0, i0, i1)
                m.add_tri(o0, i1, o1)
            else:
                m.add_tri(o0, o1, i1)
                m.add_tri(o0, i1, i0)
    for j in range(nlon - 1):
        for lat in (lats[0], lats[-1]):
            o0 = _pt(r_out, lat, lons[j])
            o1 = _pt(r_out, lat, lons[j + 1])
            i0 = _pt(r_in, lat, lons[j])
            i1 = _pt(r_in, lat, lons[j + 1])
            if lat == lats[0]:
                m.add_tri(o0, o1, i1)
                m.add_tri(o0, i1, i0)
            else:
                m.add_tri(o0, i0, i1)
                m.add_tri(o0, i1, o1)
    return m


def loft_dish(r0, r1, wall, z0, z1, a0_deg, a1_deg, n=22, ns=10) -> Mesh:
    """Tapered sector. Not a ring — hockey/football plate."""
    m = Mesh()
    zs = np.linspace(z0, z1, ns)
    an = np.linspace(math.radians(a0_deg), math.radians(a1_deg), n)
    rs = np.linspace(r0, r1, ns)

    def p(si, ai, r):
        a = an[ai]
        z = zs[si]
        return np.array([r * math.cos(a), r * math.sin(a), z])

    for s in range(ns - 1):
        ro0, ro1 = rs[s] + wall, rs[s + 1] + wall
        ri0, ri1 = rs[s], rs[s + 1]
        for i in range(n - 1):
            m.add_tri(p(s, i, ro0), p(s, i + 1, ro0), p(s + 1, i + 1, ro1))
            m.add_tri(p(s, i, ro0), p(s + 1, i + 1, ro1), p(s + 1, i, ro1))
            m.add_tri(p(s, i, ri0), p(s + 1, i, ri1), p(s + 1, i + 1, ri1))
            m.add_tri(p(s, i, ri0), p(s + 1, i + 1, ri1), p(s, i + 1, ri0))
        for r_a, r_b, flip in ((rs[s], rs[s] + wall, False), (rs[s + 1], rs[s + 1] + wall, True)):
            pass
        for ai in (0, n - 1):
            a0, b0 = p(s, ai, ri0), p(s, ai, ro0)
            a1, b1 = p(s + 1, ai, ri1), p(s + 1, ai, ro1)
            if ai == 0:
                m.add_tri(a0, a1, b1)
                m.add_tri(a0, b1, b0)
            else:
                m.add_tri(a0, b0, b1)
                m.add_tri(a0, b1, a1)
    for s, r, z in ((0, rs[0], zs[0]), (ns - 1, rs[-1], zs[-1])):
        for i in range(n - 1):
            a = p(s, i, r)
            b = p(s, i + 1, r)
            c = p(s, i + 1, r + wall)
            d = p(s, i, r + wall)
            if s == 0:
                m.add_tri(a, d, c)
                m.add_tri(a, c, b)
            else:
                m.add_tri(a, b, c)
                m.add_tri(a, c, d)
    return m


def heightmap_plate(ax, ay, z0, bulge, t, nx=16, ny=18, holes=()) -> Mesh:
    """Formed dish (football back plate). holes = (x, y, r)."""
    m = Mesh()
    xs = np.linspace(-ax, ax, nx)
    ys = np.linspace(-ay, ay, ny)

    def zh(x, y):
        u, v = x / ax, y / ay
        return z0 + bulge * max(0.0, 1.0 - u * u - v * v)

    def inside_hole(x, y):
        for hx, hy, hr in holes:
            if (x - hx) ** 2 + (y - hy) ** 2 < hr * hr:
                return True
        return False

    def in_plate(x, y):
        return (x / ax) ** 2 + (y / ay) ** 2 <= 1.02 and not inside_hole(x, y)

    for i in range(nx - 1):
        for j in range(ny - 1):
            quad = [(xs[i], ys[j]), (xs[i + 1], ys[j]), (xs[i + 1], ys[j + 1]), (xs[i], ys[j + 1])]
            if not all(in_plate(x, y) for x, y in quad):
                continue
            o = [np.array([x, y, zh(x, y)]) for x, y in quad]
            inn = [np.array([x, y, zh(x, y) - t]) for x, y in quad]
            m.add_tri(o[0], o[1], o[2])
            m.add_tri(o[0], o[2], o[3])
            m.add_tri(inn[0], inn[2], inn[1])
            m.add_tri(inn[0], inn[3], inn[2])
    return m


def fairing_deltoid() -> Mesh:
    """Football epaulette. Dome. Flexion sheave stays in the open sector."""
    # Open toward +Z (sheave at z=72). Pole slightly up/lateral.
    cap = sphere_shell(88, 81, 8, 78, -125, 45, nlat=12, nlon=20)
    return cap.move(48, 12, 8)


def led_deltoid() -> Mesh:
    return cylinder(2.2, 50).ry(90).move(70, 40, 18)


def fairing_ua() -> Mesh:
    """Floating bicep plate. Stops before the elbow sheave."""
    # Around Z, then rx-90 so it runs up the upper arm. Bottom of dish at y≈70, elbow at y=0.
    dish = loft_dish(66, 60, 5.0, -30, 78, 40, 195, n=20, ns=9)
    return dish.rx(-90).move(0, 108, 8)


def led_ua() -> Mesh:
    return box(68, 71, -3, 3, -20, 50).rx(-90).move(0, 108, 8)


def fairing_fa() -> Mesh:
    """Forearm dish. Starts 55 mm past the elbow axis — sheave stays clear."""
    dish = loft_dish(58, 50, 5.0, -36, 70, 50, 200, n=20, ns=9)
    return dish.ry(90).move(-118, 0, 6)


def led_fa() -> Mesh:
    return box(60, 63, -3, 3, -24, 40).ry(90).move(-118, 0, 6)


def fairing_scapula() -> Mesh:
    """Yoke dish over the scapula. Not a box lid."""
    plate = heightmap_plate(58, 52, 70, 22, 4.5, nx=14, ny=14)
    return plate.rx(-20).move(-24, 62, -6)


def pack_tub() -> Mesh:
    """Formed back plate (football kidney / moto roost). Wearer side open."""
    holes = ((0.0, -70.0, 30.0), (0.0, 0.0, 30.0), (0.0, 70.0, 30.0))
    m = heightmap_plate(118, 148, 18, 78, 6.0, nx=18, ny=22, holes=holes)
    for y in (-70.0, 0.0, 70.0):
        m.add(annulus(34, 26, 8).move(0, y, 88))
    return m


def pack_lid() -> Mesh:
    """Window bezels + cable trunk. Joints (drums) read through the holes."""
    m = Mesh()
    for y in (-70.0, 0.0, 70.0):
        m.add(annulus(36, 27, 6).move(0, y, 92))
    m.add(cylinder(16, 28).ry(90).move(70, 128, 70))
    return m


def pack_led() -> Mesh:
    m = Mesh()
    m.add(box(-80, 80, 138, 144, 55, 78))
    for y in (-70.0, 0.0, 70.0):
        m.add(cylinder(2.6, 4).move(32, y, 96))
    return m


def screws() -> Mesh:
    m = Mesh()
    for p in ((48, 40, 40), (48, -10, 40), (0, 140, 55), (0, 80, 55), (-90, 8, 40), (-150, 8, 40)):
        m.add(cylinder(3.4, 5).move(*p))
    return m


def flip_x(mesh: Mesh) -> Mesh:
    m = Mesh()
    for tri in mesh.tris:
        t = np.asarray(tri, float).copy()
        t[:, 0] *= -1
        m.tris.append(t[::-1])
    return m


def place_elbow(mesh: Mesh) -> Mesh:
    return flip_x(mesh).ry(45).move(55.0, -290.0, 8.0)


R_PACK = np.array([[0.0, 0.0, -1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]])
T_PACK = np.array([-145.0, -80.0, -200.0])


def assembly_layers(with_ghost=True):
    layers = []
    if with_ghost:
        layers.append(("ghost_ua", place_elbow(cuff_c(105 / 2, 8, 52).rx(-90).move(0, 100, 0)), PALETTE["ghost_cuff"]))
        layers.append(("ghost_fa", place_elbow(cuff_c(95 / 2, 8, 48).ry(90).move(-90, 0, 0)), PALETTE["ghost_cuff"]))
        layers.append(("ghost_deltoid", cuff_c(60, 8, 56, open_deg=80).ry(90).move(70, 0, 0).rz(-90), PALETTE["ghost_cuff"]))
        layers.append(("ghost_frame", box(-110, 110, -140, 140, 0, 12).transformed(R_PACK, T_PACK), PALETTE["ghost_frame"]))
    led = place_elbow(led_ua().add(led_fa()))
    led.add(led_deltoid().rz(-90))
    led.add(pack_led().transformed(R_PACK, T_PACK))
    layers += [
        ("ua", place_elbow(fairing_ua()), PALETTE["ua"]),
        ("fa", place_elbow(fairing_fa()), PALETTE["fa"]),
        ("deltoid", fairing_deltoid().rz(-90), PALETTE["deltoid"]),
        ("scapula", fairing_scapula(), PALETTE["scapula"]),
        ("pack", pack_tub().transformed(R_PACK, T_PACK), PALETTE["pack"]),
        ("lid", pack_lid().transformed(R_PACK, T_PACK), PALETTE["lid"]),
        ("led", led, PALETTE["led"]),
        ("screw", place_elbow(screws()), PALETTE["screw"]),
    ]
    return layers


def print_parts():
    return {
        "print_fairing_ua": fairing_ua(),
        "print_fairing_fa": fairing_fa(),
        "print_fairing_deltoid": fairing_deltoid(),
        "print_fairing_scapula": fairing_scapula(),
        "print_fairing_pack_tub": pack_tub(),
        "print_fairing_pack_lid": pack_lid(),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PUB.mkdir(parents=True, exist_ok=True)
    parts = print_parts()
    worn, preview = Mesh(), Mesh()
    for _, mesh, _ in assembly_layers(True):
        worn.add(mesh)
    for _, mesh, _ in assembly_layers(False):
        preview.add(mesh)
    parts["assembly_worn"] = worn
    parts["assembly_preview"] = preview
    for name, mesh in parts.items():
        write_stl(OUT / f"{name}.stl", mesh, name)
        write_stl(PUB / f"{name}.stl", mesh, name)
        print(f"  {name:32s} {len(mesh.tris):5d}")
    asm_pub, asm_out = PUB / "asm", OUT / "asm"
    asm_pub.mkdir(parents=True, exist_ok=True)
    asm_out.mkdir(parents=True, exist_ok=True)
    colors = {}
    for name, mesh, hex_color in assembly_layers(True):
        write_stl(asm_out / f"{name}.stl", mesh, name)
        write_stl(asm_pub / f"{name}.stl", mesh, name)
        colors[name] = hex_color
        print(f"  asm/{name:20s} {len(mesh.tris):5d}  {hex_color}")
    payload = json.dumps({"palette": PALETTE, "layers": colors}, indent=2)
    (asm_pub / "colors.json").write_text(payload)
    (asm_out / "colors.json").write_text(payload)


if __name__ == "__main__":
    main()
