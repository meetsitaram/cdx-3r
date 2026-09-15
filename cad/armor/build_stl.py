#!/usr/bin/env python3
"""CDX-3R plating. Circular joint windows. Sheaves stay in the hole."""
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

# McMaster 3434T121
SHEAVE_OD = 88.9
SHEAVE_BORE = 19.05
SHEAVE_W = 17.46

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
    "bezel": "#8a9199",
    "sheave": "#c5cad3",
    "screw": "#111215",
}


def sph(r, th, ph):
    s, c = math.sin(th), math.cos(th)
    return np.array([r * s * math.cos(ph), r * s * math.sin(ph), r * c])


def window_shell(r_out, r_in, th0_deg, th1_deg, ph0_deg, ph1_deg, nt=16, nph=40) -> Mesh:
    """Spherical carbon panel with a circular hole at the +Z pole. Joint lives in the hole."""
    m = Mesh()
    ths = np.linspace(math.radians(th0_deg), math.radians(th1_deg), nt)
    phs = np.linspace(math.radians(ph0_deg), math.radians(ph1_deg), nph)

    def quad(r, i, j):
        return (
            sph(r, ths[i], phs[j]),
            sph(r, ths[i], phs[j + 1]),
            sph(r, ths[i + 1], phs[j + 1]),
            sph(r, ths[i + 1], phs[j]),
        )

    for i in range(nt - 1):
        for j in range(nph - 1):
            a, b, c, d = quad(r_out, i, j)
            m.add_tri(a, b, c)
            m.add_tri(a, c, d)
            a, b, c, d = quad(r_in, i, j)
            m.add_tri(a, d, c)
            m.add_tri(a, c, b)
    for i in range(nt - 1):
        for ph in (phs[0], phs[-1]):
            o0, o1 = sph(r_out, ths[i], ph), sph(r_out, ths[i + 1], ph)
            i0, i1 = sph(r_in, ths[i], ph), sph(r_in, ths[i + 1], ph)
            if ph == phs[0]:
                m.add_tri(o0, i0, i1)
                m.add_tri(o0, i1, o1)
            else:
                m.add_tri(o0, o1, i1)
                m.add_tri(o0, i1, i0)
    for j in range(nph - 1):
        for th in (ths[0], ths[-1]):
            o0, o1 = sph(r_out, th, phs[j]), sph(r_out, th, phs[j + 1])
            i0, i1 = sph(r_in, th, phs[j]), sph(r_in, th, phs[j + 1])
            if th == ths[0]:
                m.add_tri(o0, o1, i1)
                m.add_tri(o0, i1, i0)
            else:
                m.add_tri(o0, i0, i1)
                m.add_tri(o0, i1, o1)
    return m


def torus(R, r, n=40, m=8) -> Mesh:
    mesh = Mesh()
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        for j in range(m):
            b0, b1 = 2 * math.pi * j / m, 2 * math.pi * (j + 1) / m

            def q(a, b):
                return np.array(
                    [(R + r * math.cos(b)) * math.cos(a), (R + r * math.sin(b)), r * math.sin(a) * 0 + r * math.sin(b)]
                )

            # standard torus in XY, tube in XZ... use:
            def p(a, b):
                return np.array(
                    [
                        (R + r * math.cos(b)) * math.cos(a),
                        (R + r * math.cos(b)) * math.sin(a),
                        r * math.sin(b),
                    ]
                )

            aa, bb, cc, dd = p(a0, b0), p(a1, b0), p(a1, b1), p(a0, b1)
            mesh.add_tri(aa, bb, cc)
            mesh.add_tri(aa, cc, dd)
    return mesh


def loft_dish(r0, r1, wall, z0, z1, a0_deg, a1_deg, n=36, ns=12) -> Mesh:
    m = Mesh()
    zs = np.linspace(z0, z1, ns)
    an = np.linspace(math.radians(a0_deg), math.radians(a1_deg), n)
    rs = np.linspace(r0, r1, ns)

    def p(si, ai, r):
        a = an[ai]
        return np.array([r * math.cos(a), r * math.sin(a), zs[si]])

    for s in range(ns - 1):
        ro0, ro1 = rs[s] + wall, rs[s + 1] + wall
        ri0, ri1 = rs[s], rs[s + 1]
        for i in range(n - 1):
            m.add_tri(p(s, i, ro0), p(s, i + 1, ro0), p(s + 1, i + 1, ro1))
            m.add_tri(p(s, i, ro0), p(s + 1, i + 1, ro1), p(s + 1, i, ro1))
            m.add_tri(p(s, i, ri0), p(s + 1, i, ri1), p(s + 1, i + 1, ri1))
            m.add_tri(p(s, i, ri0), p(s + 1, i + 1, ri1), p(s, i + 1, ri0))
        for ai in (0, n - 1):
            a0, b0 = p(s, ai, ri0), p(s, ai, ro0)
            a1, b1 = p(s + 1, ai, ri1), p(s + 1, ai, ro1)
            if ai == 0:
                m.add_tri(a0, a1, b1)
                m.add_tri(a0, b1, b0)
            else:
                m.add_tri(a0, b0, b1)
                m.add_tri(a0, b1, a1)
    for s, r in ((0, rs[0]), (ns - 1, rs[-1])):
        for i in range(n - 1):
            a, b = p(s, i, r), p(s, i + 1, r)
            c, d = p(s, i + 1, r + wall), p(s, i, r + wall)
            if s == 0:
                m.add_tri(a, d, c)
                m.add_tri(a, c, b)
            else:
                m.add_tri(a, b, c)
                m.add_tri(a, c, d)
    return m


def polar_plate(ax, ay, z0, bulge, t, nrho=18, nph=36, holes=()) -> Mesh:
    m = Mesh()
    rhos = np.linspace(0.08, 1.0, nrho)
    phs = np.linspace(0, 2 * math.pi, nph, endpoint=False)

    def xyz(rho, ph, dz):
        x, y = ax * rho * math.cos(ph), ay * rho * math.sin(ph)
        z = z0 + bulge * max(0.0, 1.0 - rho * rho) + dz
        return np.array([x, y, z])

    def in_hole(rho, ph):
        x, y = ax * rho * math.cos(ph), ay * rho * math.sin(ph)
        for hx, hy, hr in holes:
            if (x - hx) ** 2 + (y - hy) ** 2 < hr * hr:
                return True
        return False

    for i in range(nrho - 1):
        for j in range(nph):
            j2 = (j + 1) % nph
            cells = [(rhos[i], phs[j]), (rhos[i], phs[j2]), (rhos[i + 1], phs[j2]), (rhos[i + 1], phs[j])]
            if any(in_hole(r, p) for r, p in cells):
                continue
            o = [xyz(r, p, 0) for r, p in cells]
            inn = [xyz(r, p, -t) for r, p in cells]
            m.add_tri(o[0], o[1], o[2])
            m.add_tri(o[0], o[2], o[3])
            m.add_tri(inn[0], inn[2], inn[1])
            m.add_tri(inn[0], inn[3], inn[2])
    return m


def fairing_deltoid() -> Mesh:
    """Carbon around a circular window. Hole faces the flexion sheave (+Z)."""
    # r=92, th0=32° → hole radius ~49 mm (sheave 44.5 + gap)
    # center pulled back so the window plane sits just inboard of z=72
    cap = window_shell(92, 85.5, 32, 108, -155, 155, nt=14, nph=42)
    return cap.move(14, 10, -6)


def bezel_deltoid() -> Mesh:
    """Machined lip around the window — the close-up ring."""
    m = annulus(52, 44, 6)
    m.add(annulus(48, 42, 4).move(0, 0, 5))
    return m.move(14, 10, 70)


def joint_sheaves() -> Mesh:
    """Dual 3434T121 stack in the window. Cables only pull."""
    m = Mesh()
    m.add(annulus(SHEAVE_OD / 2, SHEAVE_BORE / 2, SHEAVE_W).move(0, 0, 0))
    m.add(annulus(SHEAVE_OD / 2, SHEAVE_BORE / 2, SHEAVE_W).move(0, 0, SHEAVE_W + 2.0))
    m.add(cylinder(SHEAVE_BORE / 2, SHEAVE_W * 2 + 10))
    return m.move(14, 10, 58)


def led_deltoid() -> Mesh:
    return torus(49, 2.2, n=36, m=6).move(14, 10, 72)


def fairing_ua() -> Mesh:
    """Bicep plate. Stops before the elbow sheave."""
    return loft_dish(66, 60, 5.0, -28, 80, 35, 200, n=32, ns=10).rx(-90).move(0, 112, 8)


def led_ua() -> Mesh:
    return box(68, 71, -2.5, 2.5, -18, 48).rx(-90).move(0, 112, 8)


def fairing_fa() -> Mesh:
    """Forearm plate. Starts 55 mm past the elbow axis."""
    return loft_dish(58, 50, 5.0, -34, 72, 45, 205, n=32, ns=10).ry(90).move(-122, 0, 6)


def led_fa() -> Mesh:
    return box(60, 63, -2.5, 2.5, -22, 40).ry(90).move(-122, 0, 6)


def fairing_scapula() -> Mesh:
    return polar_plate(56, 50, 68, 20, 4.5, nrho=14, nph=28).rx(-18).move(-24, 62, -6)


def pack_tub() -> Mesh:
    holes = ((0.0, -70.0, 32.0), (0.0, 0.0, 32.0), (0.0, 70.0, 32.0))
    m = polar_plate(118, 148, 22, 74, 6.0, nrho=16, nph=40, holes=holes)
    for y in (-70.0, 0.0, 70.0):
        m.add(annulus(34, 26, 8).move(0, y, 86))
    return m


def pack_lid() -> Mesh:
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
    led.add(led_deltoid())
    led.add(pack_led().transformed(R_PACK, T_PACK))
    layers += [
        ("ua", place_elbow(fairing_ua()), PALETTE["ua"]),
        ("fa", place_elbow(fairing_fa()), PALETTE["fa"]),
        ("deltoid", fairing_deltoid(), PALETTE["deltoid"]),
        ("bezel", bezel_deltoid(), PALETTE["bezel"]),
        ("sheave", joint_sheaves(), PALETTE["sheave"]),
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
        "print_bezel_deltoid": bezel_deltoid(),
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
