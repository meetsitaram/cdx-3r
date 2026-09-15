#!/usr/bin/env python3
"""CDX-3R full system: pack + shoulder + elbow. Weight in the saddle and hip belt."""
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

OUT = ROOT / "stl"
PUB = Path("/workspace/public/cad/system")

# World: GH origin. +Y up. +X anterior. +Z right/lateral.
UA = 290.0  # GH to elbow

PALETTE = {
    "human": "#f3c6a5",
    "saddle": "#f59e0b",
    "yoke": "#e2e8f0",
    "beam": "#94a3b8",
    "belt": "#78716c",
    "park": "#ef4444",
    "strap": "#a8a29e",
}

# Pack: packX→world Z, packY→world Y, packZ→world −X (posterior)
R_PACK = np.array([[0.0, 0.0, -1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]])
T_PACK = np.array([-150.0, -80.0, -30.0])


def xf(mesh: Mesh, R=None, t=None) -> Mesh:
    return mesh.transformed(R, t)


def human() -> Mesh:
    """Torso + head + right arm. Arm occupies cuffs. Does not carry the exo."""
    m = Mesh()
    m.add(cylinder(95, 420).move(-25, -40, -95))  # torso
    m.add(cylinder(58, 90).move(-15, 210, -90))  # neck/head
    m.add(cylinder(36, UA, z0=20).ry(90).move(20, -15, 0))  # upper arm +X
    m.add(cylinder(32, 200, z0=0).move(UA, -100, 0))  # forearm down −Y
    return m


def saddle() -> Mesh:
    """Rests ON the trapezius / acromion. This is where the exo sits."""
    m = box(-55, 35, 42, 92, -50, 58)
    m.add(box(-40, 25, 70, 98, -30, 48))
    # axillary hook — does not crush the armpit; load is on top of the shoulder
    m.add(box(-20, 20, 8, 48, 28, 52))
    return m


def yoke() -> Mesh:
    """Pack → saddle. Gravity of the arm structure goes this way, not into the biceps."""
    m = box(-150, -40, 70, 92, -20, -6)
    m.add(box(-150, -40, 70, 92, 10, 24))
    m.add(box(-55, -35, 50, 95, -20, 24))
    return m


def ua_beam() -> Mesh:
    """Lateral structural tube. GH to elbow. Outside the arm."""
    return cylinder(12, 240, z0=30).ry(90).move(30, 8, 52)


def hip_belt() -> Mesh:
    m = annulus(115, 95, 28).move(-25, -250, -95)
    m.add(box(-40, 40, -268, -232, -20, 20))
    return m


def park_rest() -> Mesh:
    """Shelf the forearm beam sits on in rest. Biceps do nothing."""
    m = box(240, 340, -130, -95, 20, 70)
    m.add(box(150, 250, -250, -230, -10, 20))  # from belt
    m.add(box(240, 260, -250, -95, 20, 40))  # riser
    return m


def straps() -> Mesh:
    m = box(-130, -100, -40, 160, -8, 8).transformed(R_PACK, T_PACK)
    m.add(box(100, 130, -40, 160, -8, 8).transformed(R_PACK, T_PACK))
    # left shoulder strap over the other trap
    m.add(box(-40, 20, 40, 90, -160, -140))
    return m


def skip(name: str) -> bool:
    return name in {"arm", "torso", "strap"}


def elbow_layers():
    out = []
    for name, mesh, color in elbow_mod.assembly_layers(False):
        if skip(name):
            continue
        out.append((f"el_{name}", mesh.rz(90).move(UA, 0, 0), color))
    return out


def shoulder_layers():
    out = []
    for name, mesh, color in sh.assembly_layers(False):
        if skip(name):
            continue
        out.append((f"sh_{name}", mesh, color))
    return out


def pack_layers():
    out = []
    for name, mesh, color in pk.assembly_layers(False):
        if skip(name):
            continue
        out.append((f"pk_{name}", xf(mesh, R_PACK, T_PACK), color))
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
    worn = Mesh()
    brace = Mesh()
    for name, mesh, _ in assembly_layers(True):
        worn.add(mesh)
    for name, mesh, _ in assembly_layers(False):
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
    payload = json.dumps({"palette": {**PALETTE}, "layers": colors}, indent=2)
    (asm_pub / "colors.json").write_text(payload)
    (asm_out / "colors.json").write_text(payload)


if __name__ == "__main__":
    main()
