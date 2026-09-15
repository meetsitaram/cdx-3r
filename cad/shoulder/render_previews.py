#!/usr/bin/env python3
"""Shoulder STL stills, colored by part."""
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

STL = Path("/workspace/public/cad/shoulder")
ASM = STL / "asm"
OUT = Path("/workspace/public/cad/shoulder/preview")
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
    ax.view_init(elev=18, azim=42)
    ax.set_axis_off()
    ax.grid(False)
    ax.set_facecolor(BG)


def render_layers(names, out, title):
    fig = plt.figure(figsize=(9.6, 6.4), dpi=120, facecolor=BG)
    ax = fig.add_subplot(111, projection="3d")
    chunks = []
    legend = []
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
                linewidths=0.15,
                alpha=0.32 if name in ("arm", "torso") else 1.0,
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
    ax.add_collection3d(
        Poly3DCollection(tris, facecolors=color, edgecolors="#0a0a0c", linewidths=0.15, shade=True)
    )
    frame(ax, tris.reshape(-1, 3))
    fig.text(0.03, 0.04, title, color="#e8e8e4", fontsize=9, fontfamily="monospace")
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(out, facecolor=BG)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    worn = [
        "torso",
        "arm",
        "cuff",
        "scapula",
        "abd_yoke",
        "flex_yoke",
        "sheave_flex",
        "sheave_abd",
        "screw",
        "bearing",
        "anchor",
        "comb",
        "housing",
        "cable_flex",
        "cable_abd",
        "cable_elbow",
        "clamp",
        "stop",
    ]
    print("worn")
    render_layers(worn, OUT / "worn.png", "SHOULDER  2R  ·  gold=flexion  orange=abduction  cyan=elbow pass-through")
    print("brace")
    render_layers([n for n in worn if n not in ("arm", "torso")], OUT / "assembly.png", "SHOULDER BRACE")
    jobs = [
        ("flex.png", "ref_sheave_flex_DO_NOT_PRINT.stl", PALETTE["sheave_flex"], "BUY  3434T121  FLEXION  ·  lateral"),
        ("abd.png", "ref_sheave_abd_DO_NOT_PRINT.stl", PALETTE["sheave_abd"], "BUY  3434T121  ABDUCTION  ·  posterior"),
        ("scapula.png", "print_scapula.stl", PALETTE["scapula"], "PRINT  SCAPULA PAD"),
        ("yoke.png", "print_flex_yoke.stl", PALETTE["flex_yoke"], "PRINT  FLEXION YOKE  ·  to elbow"),
        ("cuff.png", "print_deltoid_cuff.stl", PALETTE["cuff"], "PRINT  DELTOID CUFF"),
        ("comb.png", "print_cable_comb.stl", PALETTE["comb"], "PRINT  COMB  ·  elbow cables pass, do not wrap"),
    ]
    for name, src, color, title in jobs:
        print(name)
        render(STL / src, color, OUT / name, title)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
