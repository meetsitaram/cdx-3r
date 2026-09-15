#!/usr/bin/env python3
"""CDX-3R modular carbon fairings. Screw onto the existing skeleton. Take no load."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
CAD = ROOT.parent
sys.path.insert(0, str(CAD / "elbow"))
from build_stl import (  # noqa: E402
    Mesh,
    annulus,
    box,
    cuff_c,
    cylinder,
    write_stl,
)

OUT = ROOT / "stl"
PUB = Path("/workspace/public/cad/armor")

UA_OD = 105.0 / 2 + 8.0  # 60.5
FA_OD = 95.0 / 2 + 8.0  # 55.5
DEL_OD = 120.0 / 2 + 8.0  # 68
CLEAR = 2.0
WALL = 4.5
M4 = 2.1

PALETTE = {
    "ghost_cuff": "#5ee0ff",
    "ghost_frame": "#94a3b8",
    "ua": "#1f2328",
    "fa": "#252a31",
    "deltoid": "#1c2024",
    "scapula": "#2a3038",
    "pack": "#16191d",
    "lid": "#1a1e24",
    "bezel": "#3a414c",
    "led": "#3b82f6",
    "screw": "#c5cad3",
}


def bosses_on_ring(r, h, n=4) -> Mesh:
    m = Mesh()
    for i in range(n):
        a = math.radians(-40 + i * (280 / max(n - 1, 1)))
        x, y = r * math.cos(a), r * math.sin(a)
        m.add(cylinder(5.6, 6).move(x, y, h * 0.28))
        m.add(cylinder(5.6, 6).move(x, y, -h * 0.28))
    return m


def led_strip(r, h) -> Mesh:
    return box(r - 0.4, r + 1.8, -3.2, 3.2, -h * 0.38, h * 0.38)


def fairing_ua() -> Mesh:
    """Clamshell over the upper-arm cuff. Same C-opening, taller, 2 mm slip fit."""
    body = cuff_c(UA_OD + CLEAR, WALL, 92, open_deg=70)
    body.add(bosses_on_ring(UA_OD + CLEAR + WALL, 92, 4))
    return body.rx(-90).move(0, 100, 0)


def led_ua() -> Mesh:
    return led_strip(UA_OD + CLEAR + WALL, 92).rx(-90).move(0, 100, 0)


def fairing_fa() -> Mesh:
    body = cuff_c(FA_OD + CLEAR, WALL, 82, open_deg=70)
    body.add(bosses_on_ring(FA_OD + CLEAR + WALL, 82, 4))
    return body.ry(90).move(-90, 0, 0)


def led_fa() -> Mesh:
    return led_strip(FA_OD + CLEAR + WALL, 82).ry(90).move(-90, 0, 0)


def fairing_deltoid() -> Mesh:
    """Over the deltoid cuff. Opening toward the flexion sheave so the gold pulley stays visible."""
    body = cuff_c(DEL_OD + CLEAR, 5.0, 78, open_deg=95)
    body.add(bosses_on_ring(DEL_OD + CLEAR + 5.0, 78, 3))
    # lateral cap, does not swallow the sheave
    body.add(box(DEL_OD + 2, DEL_OD + 14, -22, 22, -18, 28))
    return body.ry(90).move(70, 0, 0)


def led_deltoid() -> Mesh:
    return led_strip(DEL_OD + CLEAR + 5.0, 70).ry(90).move(70, 0, 0)


def fairing_scapula() -> Mesh:
    """Lid over the scapula plate. 3 mm wall. Strap slots stay open."""
    m = Mesh()
    m.add(box(-74, 24, 92, 96, -54, 44))  # top
    m.add(box(-74, -70, 38, 92, -54, 44))  # left
    m.add(box(20, 24, 38, 92, -54, 44))  # right
    m.add(box(-74, 24, 38, 42, -54, 44))  # bottom
    m.add(box(-74, 24, 38, 96, 40, 44))  # back
    m.add(box(-74, 24, 38, 96, -54, -50))  # front
    for x, z in ((-60, -30), (-60, 30), (10, -30), (10, 30)):
        m.add(cylinder(5.6, 6).rx(90).move(x, 94, z))
    return m


def pack_tub() -> Mesh:
    """5-sided tub around the 220×280×80 frame. Wearer side open."""
    m = Mesh()
    m.add(box(-122, 122, -154, 154, -6, -1))  # back against wearer? pack z=0 is against wearer
    # Actually pack z=0 is the back panel against the wearer. Shell wraps z=-4 (toward wearer, 4mm pad) to z=94 (out).
    m.add(box(-122, -117, -154, 154, -4, 94))
    m.add(box(117, 122, -154, 154, -4, 94))
    m.add(box(-122, 122, 149, 154, -4, 94))
    m.add(box(-122, 122, -154, -149, -4, 94))
    # wearer-side lip
    m.add(box(-122, 122, -154, 154, -6, -2))
    for x, y in ((-108, -136), (108, -136), (-108, 136), (108, 136)):
        m.add(cylinder(5.6, 8).move(x, y, 4))
    return m


def pack_lid() -> Mesh:
    """Outer lid with three drum windows. Bolts to the tub."""
    m = Mesh()
    # frame around windows
    m.add(box(-122, 122, -154, 154, 90, 96))
    for y in (-72.0, 0.0, 72.0):
        m.add(annulus(38, 27, 8).move(0, y, 93))
    # cable exit, top-right
    m.add(box(70, 110, 130, 152, 88, 100))
    for x, y in ((-100, -140), (100, -140), (-100, 140), (100, 140)):
        m.add(cylinder(5.6, 6).move(x, y, 93))
    return m


def pack_led() -> Mesh:
    m = Mesh()
    m.add(box(-90, 90, 146, 151, 70, 88))
    for y in (-72.0, 0.0, 72.0):
        m.add(cylinder(3.0, 4).move(40, y, 96))
    return m


def screws() -> Mesh:
    m = Mesh()
    for x, y, z in (
        (0, 70, 66),
        (0, 130, 66),
        (-90, 0, 60),
        (-90, 0, -60),
        (70, 0, 80),
        (70, 0, -80),
        (-60, 94, -30),
        (10, 94, 30),
    ):
        m.add(cylinder(3.5, 4).move(x, y, z))
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
    """Fairings in the worn system frame so the orbit matches the arm."""
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
    for name, mesh, _ in assembly_layers(True):
        worn.add(mesh)
    for name, mesh, _ in assembly_layers(False):
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
