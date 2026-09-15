#!/usr/bin/env python3
"""CDX-3R worn system. Standing rest pose. Load on saddle + hip belt."""
from __future__ import annotations

import json
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

OUT = ROOT / "stl"
PUB = Path("/workspace/public/cad/system")

# World: right GH. +Y up, +X forward, +Z right.
# Person standing. Arm down. Elbow 90°. Forearm forward. Pack on the back.
UA = 290.0
MID_Z = -180.0  # spine
BACK_X = -110.0

PALETTE = {
    "human": "#f3c6a5",
    "saddle": "#f59e0b",
    "yoke": "#e2e8f0",
    "beam": "#94a3b8",
    "belt": "#78716c",
    "park": "#ef4444",
    "strap": "#a8a29e",
}

# Pack local: +X right, +Y up, +Z out the back.
# World: packX → +Z, packY → +Y, packZ → −X.
R_PACK = np.array([[0.0, 0.0, -1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]])
T_PACK = np.array([-200.0, -100.0, MID_Z])

ARM_SHOULDER = {"cuff", "flex_yoke", "sheave_flex"}
SKIP = {"arm", "torso", "strap"}


def flip_x(mesh: Mesh) -> Mesh:
    """Mirror in X and reverse winding. Elbow wrist −X becomes +X (forward)."""
    m = Mesh()
    for tri in mesh.tris:
        t = np.asarray(tri, float).copy()
        t[:, 0] *= -1
        m.tris.append(t[::-1])
    return m


def human() -> Mesh:
    """Vertical person. Torso along +Y. Right arm down, forearm forward."""
    m = Mesh()
    m.add(cylinder(92, 380).rx(90).move(0, -40, MID_Z))  # torso
    m.add(cylinder(55, 70).rx(90).move(0, 180, MID_Z))  # neck
    m.add(cylinder(62, 110).rx(90).move(10, 250, MID_Z))  # head
    m.add(box(-40, 30, -25, 35, MID_Z - 40, 35))  # shoulder girdle
    m.add(cylinder(34, 250).rx(90).move(15, -130, 22))  # upper arm down
    m.add(cylinder(30, 220).ry(90).move(20, -UA, 22))  # forearm forward
    return m


def saddle() -> Mesh:
    """Pad ON the right trapezius / acromion. Exo sits here."""
    m = box(-50, 35, 28, 78, -40, 58)
    m.add(box(-35, 25, 55, 88, -25, 48))
    return m


def yoke() -> Mesh:
    """Two beams: pack top → saddle. This is the hangar, not the biceps."""
    # pack top ~ (-140, 80, -180)
    m = box(-180, -20, 55, 78, MID_Z - 20, MID_Z + 20)
    m.add(box(-40, 10, 48, 78, -20, 40))
    m.add(box(-180, -140, 55, 90, MID_Z - 30, 20))
    return m


def ua_beam() -> Mesh:
    """Lateral tube, GH down to elbow. Outside the arm."""
    return cylinder(11, 250).rx(90).move(8, -130, 58)


def hip_belt() -> Mesh:
    """Around the waist. Ring in the XZ plane."""
    return annulus(118, 96, 26).rx(90).move(0, -250, MID_Z)


def park_rest() -> Mesh:
    """Forearm shelf at the right hip, tied back to the belt."""
    m = box(40, 200, -UA - 28, -UA - 6, 0, 48)
    m.add(box(40, 58, -260, -UA - 6, 8, 36))  # riser
    m.add(box(-20, 58, -262, -238, MID_Z + 90, 20))  # boom from belt
    return m


def straps() -> Mesh:
    """Over both shoulders into the pack."""
    m = Mesh()
    m.add(polyline(
        [np.array([-140.0, 70.0, MID_Z - 80]), np.array([0.0, 90.0, MID_Z - 80]), np.array([20.0, 40.0, 10.0])],
        8,
    ))
    m.add(polyline(
        [np.array([-140.0, 70.0, MID_Z + 40]), np.array([10.0, 80.0, 10.0]), np.array([5.0, 40.0, 20.0])],
        8,
    ))
    return m


def elbow_layers():
    out = []
    for name, mesh, color in elbow_mod.assembly_layers(False):
        if name in SKIP:
            continue
        out.append((f"el_{name}", flip_x(mesh).move(15, -UA, 22), color))
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
        if name in SKIP or name in {"bullet", "housing"}:
            continue
        out.append((f"pk_{name}", mesh.transformed(R_PACK, T_PACK), color))
    return out


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
    ]
    layers += pack_layers()
    layers += shoulder_layers()
    layers += elbow_layers()
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
