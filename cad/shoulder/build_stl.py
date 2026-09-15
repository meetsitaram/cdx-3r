#!/usr/bin/env python3
"""CDX-3R shoulder: 2R — flexion (lateral sheave) + abduction (posterior sheave)."""
from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "elbow"))
from build_stl import (  # noqa: E402
    SHAFT,
    SHEAVE,
    SCREW,
    IDLER,
    Mesh,
    annulus,
    box,
    cuff_c,
    cylinder,
    idler_bearing,
    idler_cup,
    polyline,
    shoulder_screw,
    strap_tabs,
    write_stl,
    arc_pts,
)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "stl"
PUB = Path("/workspace/public/cad/shoulder")
PARAMS = json.loads((ROOT.parent / "params.json").read_text())

# Origin = glenohumeral center.
# +Y up (head). +X anterior (upper arm at 90° flexion). +Z lateral (right).
PITCH = SHEAVE["pitch"] / 2
W = SHEAVE["width"]
Z_FLEX = 72.0  # flexion sheave, outboard of deltoid
X_ABD = -78.0  # abduction sheave, behind the shoulder toward the pack
CUFF_T = 8.0
DELTOID_ID = 120.0


PALETTE = {
    "arm": "#f3c6a5",
    "torso": "#e7d3c0",
    "cuff": "#5ee0ff",
    "scapula": "#f2f4f7",
    "abd_yoke": "#94a3b8",
    "flex_yoke": "#cbd5e1",
    "sheave_flex": "#ffc93c",
    "sheave_abd": "#f97316",
    "screw": "#111215",
    "bearing": "#ff6a1a",
    "anchor": "#22c55e",
    "comb": "#14b8a6",
    "housing": "#1f2937",
    "cable_flex": "#e879f9",
    "cable_abd": "#818cf8",
    "cable_elbow": "#38bdf8",
    "clamp": "#fb7185",
    "stop": "#facc15",
}


def scapula() -> Mesh:
    """Pad on top of the shoulder. Pack straps bolt here. Does not rotate."""
    m = box(-70, 20, 40, 90, -50, 40)
    m.add(box(-70, -20, 10, 90, -20, 20))
    return m


def abd_yoke() -> Mesh:
    """Rotates about AP (X). Carries the flexion sheave."""
    m = box(-20, 20, -16, 16, 8, Z_FLEX - 8)
    m.add(annulus(28, SHAFT / 2 + 0.2, 8).rx(90).move(X_ABD / 2, 0, 0))
    m.add(box(X_ABD + 8, 8, -16, 16, -12, 12))
    return m


def flex_yoke() -> Mesh:
    """Upper-arm side of the flexion hinge. Goes forward to the elbow tube."""
    m = box(12, 140, -16, 16, Z_FLEX - 6, Z_FLEX + 6)
    m.add(annulus(30, SHAFT / 2 + 0.3, 7).move(0, 0, Z_FLEX))
    m.add(box(90, 130, -14, 14, 20, Z_FLEX + 6))
    return m


def deltoid_cuff() -> Mesh:
    body = cuff_c(DELTOID_ID / 2, CUFF_T, 56, open_deg=80)
    body.add(strap_tabs(DELTOID_ID / 2 + CUFF_T, 56))
    return body.ry(90).move(70, 0, 0)


def sheave_flex() -> Mesh:
    return annulus(SHEAVE["od"] / 2, SHEAVE["bore"] / 2, W).move(0, 0, Z_FLEX)


def sheave_abd() -> Mesh:
    return annulus(SHEAVE["od"] / 2, SHEAVE["bore"] / 2, W).rx(90).move(X_ABD, 0, 0)


def screw_flex() -> Mesh:
    return shoulder_screw().move(0, 0, Z_FLEX)


def screw_abd() -> Mesh:
    return shoulder_screw().rx(90).move(X_ABD, 0, 0)


def bearings() -> Mesh:
    m = idler_bearing().move(28, 38, Z_FLEX - 4)
    m.add(idler_bearing().move(-22, 38, Z_FLEX - 4))
    m.add(idler_bearing().move(X_ABD + 6, 36, 28))
    m.add(idler_bearing().move(X_ABD + 6, -36, 28))
    return m


def cups() -> Mesh:
    m = idler_cup().move(28, 38, Z_FLEX - 4)
    m.add(idler_cup().move(-22, 38, Z_FLEX - 4))
    m.add(idler_cup().move(X_ABD + 6, 36, 28))
    m.add(idler_cup().move(X_ABD + 6, -36, 28))
    return m


def anchors() -> Mesh:
    a = box(-10, 10, -14, 14, -8, 8)
    a.add(cylinder(5.5, 14).rx(-90).move(0, 8, 0))
    m = a.move(20, 55, Z_FLEX - 8)
    m.add(a.move(-20, 55, Z_FLEX - 8))
    m.add(a.ry(90).move(X_ABD + 10, 50, 20))
    m.add(a.ry(90).move(X_ABD + 10, -50, 20))
    return m


def comb() -> Mesh:
    """Elbow Bowden pass-through on the scapula — does not wrap the shoulder."""
    m = box(-30, 10, 70, 95, -18, 18)
    for x in (-18.0, -6.0, 6.0):
        m.add(cylinder(4.0, 22).rx(90).move(x, 82, 0))
    return m


def housing() -> Mesh:
    z = 40
    m = polyline([np.array([-40.0, 160.0, z]), np.array([20.0, 55.0, Z_FLEX - 8])], 3.0)
    m.add(polyline([np.array([-50.0, 160.0, z]), np.array([-20.0, 55.0, Z_FLEX - 8])], 3.0))
    m.add(polyline([np.array([-120.0, 80.0, 10]), np.array([X_ABD + 10, 50.0, 20])], 3.0))
    m.add(polyline([np.array([-120.0, 60.0, -10]), np.array([X_ABD + 10, -50.0, 20])], 3.0))
    # elbow pass-through up to pack
    m.add(polyline([np.array([140.0, 8.0, 30]), np.array([-10.0, 82.0, 8]), np.array([-80.0, 140.0, 20])], 2.8))
    m.add(polyline([np.array([140.0, -8.0, 30]), np.array([-10.0, 82.0, -8]), np.array([-90.0, 140.0, 10])], 2.8))
    return m


def cable_flex() -> Mesh:
    r = PITCH
    pts = [
        np.array([20.0, 55.0, Z_FLEX - 8]),
        np.array([28.0, 38.0, Z_FLEX - 4]),
        np.array([0.0, r + 4, Z_FLEX]),
        *arc_pts(r, Z_FLEX, 90, 10),
    ]
    return polyline(pts, 1.6)


def cable_abd() -> Mesh:
    r = PITCH
    # wrap in YZ around abd sheave at x=X_ABD (axis X) — approximate in YZ
    pts = [
        np.array([X_ABD + 10, 50.0, 20.0]),
        np.array([X_ABD + 6, 36.0, 28.0]),
        np.array([X_ABD, r, 0.0]),
        np.array([X_ABD, 0.0, r]),
        np.array([X_ABD, -r * 0.3, r * 0.7]),
    ]
    return polyline(pts, 1.6)


def cable_elbow() -> Mesh:
    """Elbow inners: along the upper arm, through the comb, to the pack. Do not wrap shoulder sheaves."""
    m = polyline([np.array([200.0, 8.0, 28]), np.array([140.0, 8.0, 30]), np.array([-10.0, 82.0, 8])], 1.5)
    m.add(polyline([np.array([200.0, -8.0, 28]), np.array([140.0, -8.0, 30]), np.array([-10.0, 82.0, -8])], 1.5))
    return m


def clamps() -> Mesh:
    m = box(-6, 6, -6, 6, -6, 6).move(PITCH, 0, Z_FLEX)
    m.add(box(-6, 6, -6, 6, -6, 6).move(X_ABD, 0, PITCH))
    return m


def hard_stop() -> Mesh:
    return box(-8, 8, -20, -8, Z_FLEX - 8, Z_FLEX + 8)


def ghost_arm() -> Mesh:
    return cylinder(36, 260, z0=20).ry(90).move(20, 0, 0)


def ghost_torso() -> Mesh:
    m = cylinder(90, 220).move( -30, 10, -70)
    m.add(box(-50, 30, -80, 80, -110, -40))
    return m


def assembly_layers(with_body=True):
    layers = []
    if with_body:
        layers += [
            ("torso", ghost_torso(), PALETTE["torso"]),
            ("arm", ghost_arm(), PALETTE["arm"]),
        ]
    layers += [
        ("cuff", deltoid_cuff(), PALETTE["cuff"]),
        ("scapula", scapula(), PALETTE["scapula"]),
        ("abd_yoke", abd_yoke(), PALETTE["abd_yoke"]),
        ("flex_yoke", flex_yoke(), PALETTE["flex_yoke"]),
        ("sheave_flex", sheave_flex(), PALETTE["sheave_flex"]),
        ("sheave_abd", sheave_abd(), PALETTE["sheave_abd"]),
        ("screw", screw_flex().add(screw_abd()), PALETTE["screw"]),
        ("bearing", bearings(), PALETTE["bearing"]),
        ("cups", cups(), PALETTE["scapula"]),
        ("anchor", anchors(), PALETTE["anchor"]),
        ("comb", comb(), PALETTE["comb"]),
        ("housing", housing(), PALETTE["housing"]),
        ("cable_flex", cable_flex(), PALETTE["cable_flex"]),
        ("cable_abd", cable_abd(), PALETTE["cable_abd"]),
        ("cable_elbow", cable_elbow(), PALETTE["cable_elbow"]),
        ("clamp", clamps(), PALETTE["clamp"]),
        ("stop", hard_stop(), PALETTE["stop"]),
    ]
    return layers


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PUB.mkdir(parents=True, exist_ok=True)
    parts = {
        "print_scapula": scapula(),
        "print_abd_yoke": abd_yoke(),
        "print_flex_yoke": flex_yoke(),
        "print_deltoid_cuff": deltoid_cuff(),
        "print_cable_comb": comb(),
        "print_bowden_anchor": anchors(),
        "print_hard_stop": hard_stop(),
        "ref_sheave_flex_DO_NOT_PRINT": sheave_flex().move(0, 0, -Z_FLEX),
        "ref_sheave_abd_DO_NOT_PRINT": sheave_abd().move(-X_ABD, 0, 0),
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
    payload = json.dumps({"palette": PALETTE, "layers": colors}, indent=2)
    (asm_pub / "colors.json").write_text(payload)
    (asm_out / "colors.json").write_text(payload)


if __name__ == "__main__":
    main()
