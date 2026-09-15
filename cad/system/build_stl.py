#!/usr/bin/env python3
"""CDX-3R worn system. Standing rest. Saddle carries the exo. Cradle is not a lock."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
CAD = ROOT.parent
sys.path.insert(0, str(CAD / "elbow"))

from build_stl import Mesh, annulus, box, cylinder, polyline, write_stl  # noqa: E402
import build_stl as elbow_mod  # noqa: E402
import importlib.util


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = spec.loader.load_module()
    return mod


sh = _load("shoulder_mod", CAD / "shoulder" / "build_stl.py")
pk = _load("backpack_mod", CAD / "backpack" / "build_stl.py")
ar = _load("armor_mod", CAD / "armor" / "build_stl.py")

OUT = ROOT / "stl"
PUB = Path("/workspace/public/cad/system")

# World: right GH. +Y up, +X forward, +Z right.
UA = 290.0
MID_Z = -200.0
# Elbow in rest: arm down, hand in front of the belt (not out to the side).
ELBOW = np.array([55.0, -UA, 8.0])
# Forearm points forward-and-in, 45° toward the belly.
FOREARM_DIR = np.array([math.cos(math.radians(45)), 0.0, -math.sin(math.radians(45))])

PALETTE = {
    "human": "#f3c6a5",
    "saddle": "#f59e0b",
    "yoke": "#e2e8f0",
    "beam": "#94a3b8",
    "belt": "#78716c",
    "park": "#f97316",
    "strap": "#a8a29e",
    "housing": "#1f2937",
    "cable_el": "#38bdf8",
    "cable_flex": "#e879f9",
    "cable_abd": "#818cf8",
    "ferrule": "#22c55e",
    "ar_ua": "#1f2328",
    "ar_fa": "#252a31",
    "ar_deltoid": "#1c2024",
    "ar_scapula": "#2a3038",
    "ar_pack": "#16191d",
    "ar_lid": "#1a1e24",
    "ar_led": "#3b82f6",
}

R_PACK = np.array([[0.0, 0.0, -1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]])
T_PACK = np.array([-145.0, -80.0, MID_Z])

ARM_SHOULDER = {"cuff", "flex_yoke", "sheave_flex"}
SKIP = {"arm", "torso", "strap"}
PACK_SKIP = SKIP | {"bullet"}


def flip_x(mesh: Mesh) -> Mesh:
    m = Mesh()
    for tri in mesh.tris:
        t = np.asarray(tri, float).copy()
        t[:, 0] *= -1
        m.tris.append(t[::-1])
    return m


def place_elbow(mesh: Mesh) -> Mesh:
    """Upper arm up to GH. Forearm forward-and-in across the belly."""
    return flip_x(mesh).ry(45).move(*ELBOW)


def human() -> Mesh:
    m = Mesh()
    m.add(cylinder(145, 420).rx(90).move(15, -50, MID_Z))
    m.add(cylinder(62, 70).rx(90).move(15, 185, MID_Z))
    m.add(cylinder(88, 120).rx(90).move(20, 255, MID_Z))
    m.add(box(-50, 40, -30, 40, MID_Z - 50, 40))
    m.add(cylinder(36, 250).rx(90).move(28, -130, 12))
    fa = cylinder(30, 200).ry(90).ry(45).move(*ELBOW)
    m.add(fa)
    return m


def saddle() -> Mesh:
    """Pad on the trap + outboard plate the beam and yoke actually bolt to."""
    m = box(-48, 28, 18, 72, -38, 52)
    m.add(box(-30, 22, 48, 82, -22, 42))
    # outboard socket — UA beam and flex axis meet here
    m.add(annulus(22, 8, 14).move(4, 20, 58))
    m.add(box(-8, 16, 8, 32, 48, 68))
    return m


def yoke() -> Mesh:
    """Tubes: pack top → saddle socket. This is the hangar."""
    pack_r = np.array([-140.0, 80.0, MID_Z - 40])
    pack_l = np.array([-140.0, 80.0, MID_Z + 20])
    sock = np.array([0.0, 28.0, 50.0])
    m = polyline([pack_r, np.array([-40.0, 55.0, 10.0]), sock], 9)
    m.add(polyline([pack_l, np.array([-50.0, 60.0, 30.0]), sock], 9))
    return m


def ua_beam() -> Mesh:
    """Saddle socket down the lateral side to the elbow plate."""
    return polyline([np.array([6.0, 22.0, 58.0]), np.array([40.0, -UA + 30, 48.0])], 10)


def hip_belt() -> Mesh:
    return annulus(168, 148, 26).rx(90).move(15, -250, MID_Z)


def park_rest() -> Mesh:
    """U-cradle, OPEN UP. Forearm sits in it. Lift out to move. Not a lock."""
    # Under the mid-forearm, along the 45° rest direction.
    mid = ELBOW + FOREARM_DIR * 110
    # local frame: along forearm (X') and vertical
    m = Mesh()
    # floor
    m.add(box(-28, 28, -10, 4, -18, 18))
    # walls — gap on +Y so the arm drops in from above
    m.add(box(-28, 28, -8, 22, -18, -10))
    m.add(box(-28, 28, -8, 22, 10, 18))
    # yaw 45° to follow the forearm, sit under it
    placed = m.ry(45).move(mid[0], mid[1] - 38, mid[2])
    # boom to belt — stays below the arm
    boom = polyline(
        [
            np.array([mid[0] - 10, -250.0, MID_Z + 100]),
            np.array([mid[0] - 10, -250.0, mid[2]]),
            np.array([mid[0], mid[1] - 40, mid[2]]),
        ],
        7,
    )
    return placed.add(boom)


def straps() -> Mesh:
    m = Mesh()
    m.add(polyline(
        [np.array([-140.0, 60.0, MID_Z - 70]), np.array([5.0, 95.0, MID_Z - 70]), np.array([10.0, 40.0, 5.0])],
        7,
    ))
    m.add(polyline(
        [np.array([-140.0, 60.0, MID_Z + 30]), np.array([8.0, 70.0, 15.0])],
        7,
    ))
    return m


def ferrules() -> Mesh:
    """M5 barrels: pack bulkhead, saddle, elbow. Green."""
    m = Mesh()
    for p in (
        np.array([-155.0, 70.0, MID_Z + 10]),
        np.array([-155.0, 70.0, MID_Z - 20]),
        np.array([-155.0, 55.0, MID_Z + 30]),
        np.array([8.0, 30.0, 62.0]),
        np.array([8.0, 18.0, 62.0]),
        np.array([42.0, -UA + 40, 52.0]),
        np.array([48.0, -UA + 25, 52.0]),
    ):
        m.add(cylinder(5.5, 16).ry(90).move(*p))
    return m


def housing() -> Mesh:
    """Bowden from pack bulkhead → saddle → joints. Housing stops at ferrules."""
    bulk = np.array([-155.0, 62.0, MID_Z])
    sad = np.array([6.0, 32.0, 60.0])
    elb = np.array([45.0, -UA + 32, 50.0])
    abd = np.array([-70.0, 10.0, 10.0])
    m = polyline([bulk + [0, 8, 20], sad + [0, 6, 0]], 3.2)
    m.add(polyline([bulk + [0, 0, 0], sad, elb], 3.2))
    m.add(polyline([bulk + [0, -6, -20], np.array([-80.0, 40.0, -20.0]), abd], 3.2))
    return m


def cables() -> dict[str, Mesh]:
    bulk = np.array([-155.0, 62.0, MID_Z])
    sad = np.array([6.0, 32.0, 60.0])
    elb = np.array([45.0, -UA + 32, 50.0])
    abd = np.array([-70.0, 10.0, 10.0])
    el = polyline([bulk + [0, 8, 16], sad, elb], 1.6)
    fl = polyline([bulk + [0, 0, 0], sad + [0, 4, 4], np.array([4.0, 8.0, 70.0])], 1.6)
    ab = polyline([bulk + [0, -8, -16], abd], 1.6)
    return {"cable_el": el, "cable_flex": fl, "cable_abd": ab}


def elbow_layers():
    out = []
    for name, mesh, color in elbow_mod.assembly_layers(False):
        if name in SKIP:
            continue
        out.append((f"el_{name}", place_elbow(mesh), color))
    return out


def shoulder_layers():
    out = []
    for name, mesh, color in sh.assembly_layers(False):
        if name in SKIP:
            continue
        if name in ARM_SHOULDER:
            mesh = mesh.rz(-90)
        out.append((f"sh_{name}", mesh, color))
    return out


def pack_layers():
    out = []
    for name, mesh, color in pk.assembly_layers(False):
        if name in PACK_SKIP:
            continue
        out.append((f"pk_{name}", mesh.transformed(R_PACK, T_PACK), color))
    return out


def armor_layers():
    led = place_elbow(ar.led_ua().add(ar.led_fa()))
    led.add(ar.led_deltoid().rz(-90))
    led.add(ar.pack_led().transformed(R_PACK, T_PACK))
    return [
        ("ar_ua", place_elbow(ar.fairing_ua()), PALETTE["ar_ua"]),
        ("ar_fa", place_elbow(ar.fairing_fa()), PALETTE["ar_fa"]),
        ("ar_deltoid", ar.fairing_deltoid().rz(-90), PALETTE["ar_deltoid"]),
        ("ar_scapula", ar.fairing_scapula(), PALETTE["ar_scapula"]),
        ("ar_pack", ar.pack_tub().transformed(R_PACK, T_PACK), PALETTE["ar_pack"]),
        ("ar_lid", ar.pack_lid().transformed(R_PACK, T_PACK), PALETTE["ar_lid"]),
        ("ar_led", led, PALETTE["ar_led"]),
    ]


def assembly_layers(with_human=True):
    layers = []
    if with_human:
        layers.append(("human", human(), PALETTE["human"]))
    layers += [
        ("saddle", saddle(), PALETTE["saddle"]),
        ("yoke", yoke(), PALETTE["yoke"]),
        ("beam", ua_beam(), PALETTE["beam"]),
        ("belt", hip_belt(), PALETTE["belt"]),
        ("park", park_rest(), PALETTE["park"]),
        ("strap", straps(), PALETTE["strap"]),
        ("ferrule", ferrules(), PALETTE["ferrule"]),
        ("housing", housing(), PALETTE["housing"]),
    ]
    for k, mesh in cables().items():
        layers.append((k, mesh, PALETTE[k]))
    layers += pack_layers()
    layers += shoulder_layers()
    layers += elbow_layers()
    layers += armor_layers()
    return layers


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PUB.mkdir(parents=True, exist_ok=True)
    worn, brace = Mesh(), Mesh()
    for _, mesh, _ in assembly_layers(True):
        worn.add(mesh)
    for _, mesh, _ in assembly_layers(False):
        brace.add(mesh)
    parts = {
        "print_saddle": saddle(),
        "print_yoke": yoke(),
        "print_ua_beam": ua_beam(),
        "print_hip_belt": hip_belt(),
        "print_park_rest": park_rest(),
        "assembly_worn": worn,
        "assembly_preview": brace,
    }
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
        print(f"  asm/{name:24s} {len(mesh.tris):5d}  {hex_color}")
    payload = json.dumps({"palette": PALETTE, "layers": colors}, indent=2)
    (asm_pub / "colors.json").write_text(payload)
    (asm_out / "colors.json").write_text(payload)


if __name__ == "__main__":
    main()
