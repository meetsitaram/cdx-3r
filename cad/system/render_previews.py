#!/usr/bin/env python3
"""System stills from behind-right: pack + full right arm."""
from __future__ import annotations

import json
import struct
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

STL = Path("/workspace/public/cad/system")
ASM = STL / "asm"
OUT = Path("/workspace/public/cad/system/preview")
BG = "#121214"
PALETTE = json.loads((ASM / "colors.json").read_text())["layers"]


def read_stl(path: Path):
    data = path.read_bytes()
    n = struct.unpack_from("<I", data, 80)[0]
    tris = np.empty((n, 3, 3), np.float32)
    off = 84
    for i in range(n):
        chunk = struct.unpack_from("<12fH", data, off)
        off += 50
        tris[i] = np.array(chunk[3:12], np.float32).reshape(3, 3)
    return tris


def render_layers(names, out, title, elev=8, azim=110):
    fig = plt.figure(figsize=(9.6, 6.4), dpi=130, facecolor=BG)
    ax = fig.add_subplot(111, projection="3d")
    chunks = []
    for name in names:
        path = ASM / f"{name}.stl"
        if not path.exists():
            continue
        tris = read_stl(path)
        tris = tris[:, :, [0, 2, 1]]  # CAD Y-up → plot Z-up
        color = PALETTE.get(name, "#888")
        ghost = name == "human"
        ax.add_collection3d(
            Poly3DCollection(
                tris,
                facecolors=color,
                edgecolors="#121214",
                linewidths=0.02 if ghost else 0.06,
                alpha=0.12 if ghost else 1.0,
                shade=True,
            )
        )
        chunks.append(tris.reshape(-1, 3))
    pts = np.vstack(chunks)
    lo, hi = pts.min(0) - 30, pts.max(0) + 30
    ax.set_xlim(lo[0], hi[0])
    ax.set_ylim(lo[1], hi[1])
    ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(tuple(hi - lo))
    ax.view_init(elev=8, azim=130)
    ax.set_axis_off()
    ax.set_facecolor(BG)
    fig.text(0.03, 0.04, title, color="#e8e8e4", fontsize=9, fontfamily="monospace")
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(out, facecolor=BG)
    plt.close(fig)


def render(path, color, out, title):
    tris = read_stl(path)
    tris = tris[:, :, [0, 2, 1]]
    fig = plt.figure(figsize=(9.6, 6.4), dpi=120, facecolor=BG)
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(tris, facecolors=color, edgecolors="#0a0a0c", linewidths=0.15, shade=True))
    pts = tris.reshape(-1, 3)
    c = (pts.max(0) + pts.min(0)) / 2
    r = (pts.max(0) - pts.min(0)).max() / 2 or 1
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r, c[2] + r)
    ax.view_init(elev=14, azim=215)
    ax.set_axis_off()
    fig.text(0.03, 0.04, title, color="#e8e8e4", fontsize=9, fontfamily="monospace")
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(out, facecolor=BG)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    load = ["human", "saddle", "yoke", "beam", "belt", "park", "strap", "pk_frame"]
    worn = [
        "human",
        "saddle",
        "yoke",
        "beam",
        "belt",
        "park",
        "strap",
        "pk_frame",
        "pk_battery",
        "pk_motor",
        "pk_bulkhead",
        "sh_cuff",
        "sh_sheave_flex",
        "sh_sheave_abd",
        "el_cuff_upper",
        "el_cuff_forearm",
        "el_sheave",
        "el_lateral",
        "housing",
        "cable_el",
        "cable_flex",
        "cable_abd",
        "ferrule",
    ]
    print("load path")
    render_layers(load, OUT / "loadpath.png", "LOAD PATH  ·  behind-right  ·  pack + saddle + arm")
    print("worn")
    render_layers(worn, OUT / "worn.png", "SYSTEM  ·  behind right shoulder  ·  pack and full right arm")
    # human last so it doesn't paint over the exo; also a no-body crop
    print("worn no body")
    render_layers([n for n in worn if n != "human"], OUT / "worn_gear.png", "SYSTEM  ·  behind-right  ·  pack and right arm")
    print("load path")
    render_layers(load, OUT / "loadpath.png", "LOAD PATH  ·  behind-right  ·  pack + saddle + arm")
    print("worn")
    render_layers(worn, OUT / "worn.png", "SYSTEM  ·  behind right shoulder  ·  pack and full right arm")
    print("parts")
    jobs = [
        ("saddle.png", "print_saddle.stl", "#f59e0b", "PRINT  SHOULDER SADDLE  ·  exo sits here"),
        ("yoke.png", "print_yoke.stl", "#e2e8f0", "PRINT  YOKE  ·  pack to saddle"),
        ("beam.png", "print_ua_beam.stl", "#94a3b8", "PRINT  UPPER-ARM BEAM  ·  lateral, not through flesh"),
        ("belt.png", "print_hip_belt.stl", "#78716c", "PRINT  HIP BELT  ·  pack weight"),
        ("park.png", "print_park_rest.stl", "#f97316", "PRINT  PARK CRADLE  ·  forearm sits here"),
    ]
    for name, src, color, title in jobs:
        render(STL / src, color, OUT / name, title)
        print(name)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
