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
    """20 L shell. 220 W × 280 H × 80 D — a pack, not a wardrobe."""
    m = box(-110, 110, -140, 140, 0, 5)
    m.add(box(-110, 110, -140, 140, 75, 80))
    m.add(box(-110, -105, -140, 140, 0, 80))
    m.add(box(105, 110, -140, 140, 0, 80))
    m.add(box(-110, 110, 135, 140, 0, 80))
    m.add(box(-110, 110, -140, -135, 0, 80))
    return m


def sled() -> Mesh:
    m = box(-42, 42, -120, 40, 8, 18)
    m.add(box(-42, -34, -120, 40, 8, 72))
    m.add(box(34, 42, -120, 40, 8, 72))
    return m


def battery() -> Mesh:
    """48 V brick that actually fits a pack. Hailong downtube is 367 mm — too tall to wear."""
    return box(-38, 38, -125, 95, 18, 70)


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
    return winch().rx(-90).move(x, 55, 42)


def s1() -> Mesh:
    m = box(-40, 40, -28, 28, 0, 8)
    m.add(box(-36, 36, -24, 24, 8, 16))
    return m


def drives() -> Mesh:
    m = Mesh()
    for x in (-65.0, 0.0, 65.0):
        m.add(s1().move(x, 105, 10))
    return m


def spreader() -> Mesh:
    return box(-100, 100, 80, 125, 6, 12)


def xt90() -> Mesh:
    m = box(-10, 10, -8, 8, 0, 18)
    m.add(cylinder(3.5, 10).move(-5, 0, 18))
    m.add(cylinder(3.5, 10).move(5, 0, 18))
    return m


def bullets() -> Mesh:
    m = Mesh()
    for x in (-65.0, 0.0, 65.0):
        for dy in (-6.0, 6.0):
            m.add(cylinder(2.2, 12).ry(90).move(x + 28, 55 + dy, 42))
    return m


def bulkhead() -> Mesh:
    m = box(-95, 95, 118, 132, 48, 58)
    for x in (-65.0, -50.0, -8.0, 8.0, 50.0, 65.0):
        m.add(cylinder(5.5, 16).move(x, 125, 64))
        m.add(cylinder(2.8, 8).move(x, 125, 74))
    return m


def housing() -> Mesh:
    m = Mesh()
    for x in (-65.0, -50.0, -8.0, 8.0, 50.0, 65.0):
        m.add(polyline([np.array([x, 125.0, 74]), np.array([x * 0.3, 200.0, 30]), np.array([18.0, 250.0, 8])], 2.6))
    return m


def cables() -> dict[str, Mesh]:
    def pair(a, b):
        m = polyline(
            [np.array([a, 70.0, 55]), np.array([a, 125.0, 64]), np.array([a * 0.3, 200.0, 30]), np.array([18.0, 250.0, 8])],
            1.4,
        )
        m.add(
            polyline(
                [np.array([b, 70.0, 55]), np.array([b, 125.0, 64]), np.array([b * 0.3, 200.0, 30]), np.array([22.0, 250.0, 8])],
                1.4,
            )
        )
        return m

    return {"cable_el": pair(-65, -50), "cable_flex": pair(-8, 8), "cable_abd": pair(50, 65)}


def straps() -> Mesh:
    m = box(-100, -78, -30, 110, -6, 6)
    m.add(box(78, 100, -30, 110, -6, 6))
    return m


def ghost_torso() -> Mesh:
    m = cylinder(140, 400).move(0, 0, -90)
    m.add(cylinder(70, 90).move(0, 220, -90))
    return m


def assembly_layers(with_body=True):
    layers = []
    if with_body:
        layers.append(("torso", ghost_torso(), PALETTE["torso"]))
    layers += [
        ("frame", frame(), PALETTE["frame"]),
        ("sled", sled(), PALETTE["sled"]),
        ("battery", battery(), PALETTE["battery"]),
        ("motor", winch_at(-65).add(winch_at(0)).add(winch_at(65)), PALETTE["motor"]),
        ("s1", drives(), PALETTE["s1"]),
        ("spreader", spreader(), PALETTE["spreader"]),
        ("xt90", xt90().move(0, -100, 40).add(xt90().move(28, -100, 40)), PALETTE["xt90"]),
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
