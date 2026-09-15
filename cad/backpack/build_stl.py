#!/usr/bin/env python3
"""CDX-3R backpack: 3 winches, Hailong 48 V, ODrive S1, Bowden bulkhead."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "elbow"))
from build_stl import (  # noqa: E402
    Mesh,
    annulus,
    box,
    cylinder,
    idler_bearing,
    polyline,
    write_stl,
)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "stl"
PUB = Path("/workspace/public/cad/backpack")

# Origin: pack center on the back. +Y up, +X right, +Z out (away from the wearer).
# Hailong 48V 13Ah: 367 x 90 x 111 mm
# D6374: ~75 OD x 74 L, 10 mm shaft
# PLE60 10:1: 60 mm square, ~72 L, 14 mm out
# ODrive S1 + spreader: 105 x 75 x 22

PALETTE = {
    "torso": "#e7d3c0",
    "frame": "#f2f4f7",
    "sled": "#94a3b8",
    "battery": "#14532d",
    "motor": "#111215",
    "gear": "#64748b",
    "drum": "#ffc93c",
    "bearing": "#ff6a1a",
    "s1": "#16a34a",
    "spreader": "#cbd5e1",
    "xt90": "#f97316",
    "bullet": "#eab308",
    "bulkhead": "#22c55e",
    "housing": "#1f2937",
    "cable_el": "#38bdf8",
    "cable_flex": "#e879f9",
    "cable_abd": "#818cf8",
    "strap": "#78716c",
    "encoder": "#7c3aed",
}


def frame() -> Mesh:
    m = box(-140, 140, -200, 200, 0, 12)
    m.add(box(-140, -128, -200, 200, 0, 120))
    m.add(box(128, 140, -200, 200, 0, 120))
    m.add(box(-140, 140, 188, 200, 0, 120))
    m.add(box(-140, 140, -200, -188, 0, 80))
    return m


def sled() -> Mesh:
    """Hailong dovetail cradle. Battery slides in from +Y."""
    m = box(-50, 50, -180, 20, 16, 28)
    m.add(box(-50, -38, -180, 20, 16, 130))
    m.add(box(38, 50, -180, 20, 16, 130))
    return m


def battery() -> Mesh:
    # 367 x 90 x 111, long axis +Y
    return box(-45, 45, -175, 192, 28, 139)


def motor() -> Mesh:
    m = cylinder(37.5, 74)
    m.add(cylinder(5.0, 28, z0=37))  # 10 mm shaft
    m.add(cylinder(4.0, 16, z0=-37 - 16))  # rear 8 mm for encoder
    return m


def planetary() -> Mesh:
    m = box(-30, 30, -30, 30, -36, 36)
    m.add(cylinder(7.0, 22, z0=36))
    return m


def drum() -> Mesh:
    return annulus(22, 7.2, 18)


def encoder() -> Mesh:
    return cylinder(15, 18)


def winch() -> Mesh:
    """One axis: D6374 + 10:1 + drum + 608s. Local: motor along +Z."""
    m = motor()
    m.add(planetary().move(0, 0, 74))
    m.add(drum().move(0, 0, 74 + 36 + 16))
    m.add(idler_bearing().move(0, 0, 74 + 36 + 8))
    m.add(idler_bearing().move(0, 0, 74 + 36 + 24))
    m.add(encoder().move(0, 0, -74 / 2 - 20))
    return m


def winch_at(x: float) -> Mesh:
    # drums face +Y (up, toward shoulder cables)
    return winch().rx(-90).move(x, 70, 70)


def s1() -> Mesh:
    m = box(-52, 52, -38, 38, 0, 10)
    m.add(box(-48, 48, -34, 34, 10, 22))
    return m


def drives() -> Mesh:
    m = Mesh()
    for i, x in enumerate((-90.0, 0.0, 90.0)):
        m.add(s1().move(x, 165, 18))
    return m


def spreader() -> Mesh:
    return box(-140, 140, 120, 205, 12, 18)


def xt90() -> Mesh:
    m = box(-10, 10, -8, 8, 0, 18)
    m.add(cylinder(3.5, 10).move(-5, 0, 18))
    m.add(cylinder(3.5, 10).move(5, 0, 18))
    return m


def bullets() -> Mesh:
    m = Mesh()
    for x in (-90.0, 0.0, 90.0):
        for dy in (-8.0, 0.0, 8.0):
            m.add(cylinder(2.2, 14).ry(90).move(x + 40, 70 + dy, 70))
    return m


def bulkhead() -> Mesh:
    """6× M5 barrel adjusters — antagonist pair per axis."""
    m = box(-110, 110, 175, 198, 40, 55)
    for i, x in enumerate((-90.0, -70.0, -10.0, 10.0, 70.0, 90.0)):
        m.add(cylinder(6.0, 22).move(x, 186, 62))
        m.add(cylinder(3.0, 10).move(x, 186, 78))
    return m


def housing() -> Mesh:
    m = Mesh()
    # six Bowdens up to the shoulder
    cols = [(-90, "#"), (-70, "#"), (-10, "#"), (10, "#"), (70, "#"), (90, "#")]
    for x, _ in cols:
        m.add(polyline([np.array([x, 186.0, 78]), np.array([x * 0.4, 280.0, 40]), np.array([20.0, 360.0, 10])], 2.8))
    return m


def cables() -> dict[str, Mesh]:
    el = polyline(
        [np.array([-90.0, 130.0, 90]), np.array([-90.0, 186.0, 70]), np.array([-36.0, 280.0, 40]), np.array([20.0, 360.0, 10])],
        1.5,
    )
    el.add(
        polyline(
            [np.array([-70.0, 130.0, 90]), np.array([-70.0, 186.0, 70]), np.array([-28.0, 280.0, 40]), np.array([16.0, 360.0, 10])],
            1.5,
        )
    )
    fl = polyline(
        [np.array([-10.0, 130.0, 90]), np.array([-10.0, 186.0, 70]), np.array([0.0, 280.0, 40]), np.array([20.0, 360.0, 10])],
        1.5,
    )
    fl.add(
        polyline(
            [np.array([10.0, 130.0, 90]), np.array([10.0, 186.0, 70]), np.array([8.0, 280.0, 40]), np.array([24.0, 360.0, 10])],
            1.5,
        )
    )
    ab = polyline(
        [np.array([70.0, 130.0, 90]), np.array([70.0, 186.0, 70]), np.array([40.0, 280.0, 40]), np.array([20.0, 360.0, 10])],
        1.5,
    )
    ab.add(
        polyline(
            [np.array([90.0, 130.0, 90]), np.array([90.0, 186.0, 70]), np.array([48.0, 280.0, 40]), np.array([28.0, 360.0, 10])],
            1.5,
        )
    )
    return {"cable_el": el, "cable_flex": fl, "cable_abd": ab}


def straps() -> Mesh:
    m = box(-130, -100, -40, 160, -8, 8)
    m.add(box(100, 130, -40, 160, -8, 8))
    return m


def ghost_torso() -> Mesh:
    m = cylinder(90, 380).move(0, 0, -70)
    m.add(cylinder(55, 80).move(0, 210, -70))
    return m


def assembly_layers(with_body=True):
    layers = []
    if with_body:
        layers.append(("torso", ghost_torso(), PALETTE["torso"]))
    layers += [
        ("frame", frame(), PALETTE["frame"]),
        ("sled", sled(), PALETTE["sled"]),
        ("battery", battery(), PALETTE["battery"]),
        ("motor", winch_at(-90).add(winch_at(0)).add(winch_at(90)), PALETTE["motor"]),
        ("s1", drives(), PALETTE["s1"]),
        ("spreader", spreader(), PALETTE["spreader"]),
        ("xt90", xt90().move(0, -160, 140).add(xt90().move(40, -160, 140)), PALETTE["xt90"]),
        ("bullet", bullets(), PALETTE["bullet"]),
        ("bulkhead", bulkhead(), PALETTE["bulkhead"]),
        ("housing", housing(), PALETTE["housing"]),
        ("strap", straps(), PALETTE["strap"]),
    ]
    for k, mesh in cables().items():
        layers.append((k, mesh, PALETTE[k]))
    return layers


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PUB.mkdir(parents=True, exist_ok=True)
    parts = {
        "print_frame": frame(),
        "print_sled": sled(),
        "print_drum": drum(),
        "print_bulkhead": bulkhead(),
        "ref_battery_DO_NOT_PRINT": battery(),
        "ref_motor_DO_NOT_PRINT": motor(),
        "ref_planetary_DO_NOT_PRINT": planetary(),
        "ref_s1_DO_NOT_PRINT": s1(),
        "assembly_preview": Mesh(),
        "assembly_worn": Mesh(),
    }
    for _, mesh, _ in assembly_layers(False):
        parts["assembly_preview"].add(mesh)
    for _, mesh, _ in assembly_layers(True):
        parts["assembly_worn"].add(mesh)
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
