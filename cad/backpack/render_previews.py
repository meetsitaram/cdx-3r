#!/usr/bin/env python3
"""Backpack STL stills."""
from __future__ import annotations

import json
import struct
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import Patch

STL = Path("/workspace/public/cad/backpack")
ASM = STL / "asm"
OUT = Path("/workspace/public/cad/backpack/preview")
BG = "#121214"
PALETTE = json.loads((ASM / "colors.json").read_text())["palette"]


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


def frame(ax, pts):
    c = (pts.max(0) + pts.min(0)) / 2
    r = (pts.max(0) - pts.min(0)).max() / 2 or 1
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r, c[2] + r)
    ax.view_init(elev=16, azim=38)
    ax.set_axis_off()
    ax.grid(False)
    ax.set_facecolor(BG)


def render_layers(names, out, title):
    fig = plt.figure(figsize=(9.6, 6.4), dpi=120, facecolor=BG)
    ax = fig.add_subplot(111, projection="3d")
    chunks, legend = [], []
    for name in names:
        path = ASM / f"{name}.stl"
        if not path.exists():
            continue
        tris = read_stl(path)
        color = PALETTE.get(name, "#888")
        ax.add_collection3d(
            Poly3DCollection(
                tris,
                facecolors=color,
                edgecolors="#0a0a0c",
                linewidths=0.12,
                alpha=0.3 if name == "torso" else 1.0,
                shade=True,
            )
        )
        chunks.append(tris.reshape(-1, 3))
        legend.append(Patch(facecolor=color, edgecolor="none", label=name.replace("_", " ")))
    frame(ax, np.vstack(chunks))
    ax.legend(handles=legend, loc="upper left", fontsize=6, frameon=False, labelcolor="#e8e8e4")
    fig.text(0.03, 0.04, title, color="#e8e8e4", fontsize=9, fontfamily="monospace")
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(out, facecolor=BG)
    plt.close(fig)


def render(path, color, out, title):
    tris = read_stl(path)
    fig = plt.figure(figsize=(9.6, 6.4), dpi=120, facecolor=BG)
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(tris, facecolors=color, edgecolors="#0a0a0c", linewidths=0.15, shade=True))
    frame(ax, tris.reshape(-1, 3))
    fig.text(0.03, 0.04, title, color="#e8e8e4", fontsize=9, fontfamily="monospace")
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(out, facecolor=BG)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    worn = [
        "torso",
        "frame",
        "sled",
        "battery",
        "motor",
        "s1",
        "spreader",
        "xt90",
        "bullet",
        "bulkhead",
        "housing",
        "cable_el",
        "cable_flex",
        "cable_abd",
        "strap",
    ]
    print("worn")
    render_layers(worn, OUT / "worn.png", "PACK  ·  3× D6374 + 10:1  ·  Hailong 48 V  ·  3× S1")
    print("brace")
    render_layers([n for n in worn if n != "torso"], OUT / "assembly.png", "PACK  no torso")
    jobs = [
        ("battery.png", "ref_battery_DO_NOT_PRINT.stl", PALETTE["battery"], "BUY  HAILONG 48 V 13 Ah"),
        ("motor.png", "ref_motor_DO_NOT_PRINT.stl", PALETTE["motor"], "BUY  ODRIVE D6374 150 kV"),
        ("gear.png", "ref_planetary_DO_NOT_PRINT.stl", PALETTE["gear"], "BUY  PLE60 10:1 PLANETARY"),
        ("s1.png", "ref_s1_DO_NOT_PRINT.stl", PALETTE["s1"], "BUY  ODRIVE S1"),
        ("drum.png", "print_drum.stl", PALETTE["drum"], "PRINT  WINCH DRUM  r=20 mm"),
        ("bulkhead.png", "print_bulkhead.stl", PALETTE["bulkhead"], "PRINT  BULKHEAD  6× M5 BARRELS"),
        ("frame.png", "print_frame.stl", PALETTE["frame"], "PRINT  PACK FRAME"),
        ("sled.png", "print_sled.stl", PALETTE["sled"], "PRINT  HAILONG SLED"),
    ]
    for name, src, color, title in jobs:
        print(name)
        render(STL / src, color, OUT / name, title)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
