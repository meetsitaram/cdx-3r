#!/usr/bin/env python3
"""Render elbow STL previews to PNG (no WebGL). Colored by part."""
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

STL = Path("/workspace/public/cad/elbow")
ASM = STL / "asm"
OUT = Path("/workspace/public/cad/elbow/preview")
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


def frame(ax, pts, title):
    c = (pts.max(0) + pts.min(0)) / 2
    r = (pts.max(0) - pts.min(0)).max() / 2 or 1
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r, c[2] + r)
    ax.view_init(elev=22, azim=38)
    ax.set_axis_off()
    ax.grid(False)
    ax.set_facecolor(BG)


def render(path: Path, color: str, out: Path, title: str):
    tris = read_stl(path)
    fig = plt.figure(figsize=(9.6, 6.4), dpi=120, facecolor=BG)
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(
        Poly3DCollection(tris, facecolors=color, edgecolors="#1a1a1c", linewidths=0.12, shade=True)
    )
    frame(ax, tris.reshape(-1, 3), title)
    fig.text(0.03, 0.04, title, color="#e8e8e4", fontsize=9, fontfamily="monospace")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(out, facecolor=fig.get_facecolor())
    plt.close(fig)


def render_layers(names: list[str], out: Path, title: str):
    fig = plt.figure(figsize=(9.6, 6.4), dpi=120, facecolor=BG)
    ax = fig.add_subplot(111, projection="3d")
    chunks = []
    legend = []
    for name in names:
        path = ASM / f"{name}.stl"
        if not path.exists():
            continue
        tris = read_stl(path)
        color = PALETTE[name]
        ax.add_collection3d(
            Poly3DCollection(
                tris,
                facecolors=color,
                edgecolors="#0a0a0c",
                linewidths=0.2,
                alpha=1.0,
                shade=True,
            )
        )
        chunks.append(tris.reshape(-1, 3))
        legend.append(Patch(facecolor=color, edgecolor="none", label=name.replace("_", " ")))
    pts = np.vstack(chunks)
    frame(ax, pts, title)
    ax.legend(
        handles=legend,
        loc="upper left",
        fontsize=7,
        frameon=False,
        labelcolor="#e8e8e4",
        bbox_to_anchor=(0.0, 1.0),
    )
    fig.text(0.03, 0.04, title, color="#e8e8e4", fontsize=9, fontfamily="monospace")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(out, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    worn = [
        "arm",
        "cuff_upper",
        "cuff_forearm",
        "lateral",
        "distal",
        "medial",
        "sheave",
        "screw",
        "nylock",
        "bearing",
        "anchor",
        "housing",
        "cable_flex",
        "cable_ext",
        "clamp",
        "stop",
    ]
    brace = [n for n in worn if n != "arm"]
    print("render worn (colored)")
    render_layers(worn, OUT / "worn.png", "WORN  ·  color by part")
    print("render assembly (colored)")
    render_layers(brace, OUT / "assembly.png", "BRACE  ·  color by part")

    jobs = [
        ("fork.png", "print_fork_lateral.stl", PALETTE["lateral"], "PRINT  LATERAL PLATE  ·  titanium"),
        ("hub.png", "print_fork_medial.stl", PALETTE["medial"], "PRINT  MEDIAL PLATE  ·  slate"),
        ("cuff.png", "print_cuff_forearm.stl", PALETTE["cuff_forearm"], "PRINT  FOREARM CUFF  ·  ice"),
        ("drum.png", "print_drum.stl", "#9aa3ad", "PRINT  DRUM  (not 15 kg)"),
        ("sheave.png", "ref_sheave_DO_NOT_PRINT.stl", PALETTE["sheave"], "BUY  3434T121 SHEAVE  ·  gold"),
        ("bearing.png", "ref_608_DO_NOT_PRINT.stl", PALETTE["bearing"], "BUY  6455K44  608-2RS  ·  orange"),
        ("screw.png", "ref_shoulder_screw_DO_NOT_PRINT.stl", PALETTE["screw"], "BUY  91273A274  ·  carbon"),
        ("anchor.png", "print_bowden_anchor.stl", PALETTE["anchor"], "PRINT  BOWDEN ANCHOR  ·  green"),
        ("stop.png", "print_hard_stop.stl", PALETTE["stop"], "PRINT  HARD STOP  ·  yellow"),
        ("arm.png", "ref_arm_ghost_DO_NOT_PRINT.stl", PALETTE["arm"], "GHOST ARM  ·  skin  ·  do not print"),
    ]
    for name, src, color, title in jobs:
        print("render", name)
        render(STL / src, color, OUT / name, title)
    fig, axes = plt.subplots(3, 4, figsize=(16, 9.6), dpi=110, facecolor=BG)
    fig.subplots_adjust(0, 0, 1, 1, 0.01, 0.01)
    thumbs = [("worn.png",), ("assembly.png",)] + [(j[0],) for j in jobs]
    for ax, (name,) in zip(axes.ravel(), thumbs):
        ax.set_axis_off()
        ax.set_facecolor(BG)
        ax.imshow(plt.imread(OUT / name))
    fig.savefig(OUT / "sheet.png", facecolor=BG)
    plt.close(fig)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
