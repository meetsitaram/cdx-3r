#!/usr/bin/env python3
"""Render elbow STL previews to PNG (no WebGL)."""
from __future__ import annotations

import struct
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

STL = Path("/workspace/public/cad/elbow")
OUT = Path("/workspace/public/cad/elbow/preview")
BG = "#121214"


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


def render(path: Path, color: str, out: Path, title: str):
    tris = read_stl(path)
    fig = plt.figure(figsize=(9.6, 6.4), dpi=120, facecolor=BG)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor(BG)
    coll = Poly3DCollection(
        tris,
        facecolors=color,
        edgecolors="#2a2a2e",
        linewidths=0.15,
        shade=True,
    )
    ax.add_collection3d(coll)
    pts = tris.reshape(-1, 3)
    c = (pts.max(0) + pts.min(0)) / 2
    r = (pts.max(0) - pts.min(0)).max() / 2 or 1
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r, c[2] + r)
    ax.view_init(elev=22, azim=38)
    ax.set_axis_off()
    ax.grid(False)
    fig.text(0.03, 0.04, title, color="#e8e8e4", fontsize=9, fontfamily="monospace")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(out, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [
        ("worn.png", "assembly_worn.stl", "#8ab0ba", "WORN  ·  arm through cuffs, sheave outboard"),
        ("assembly.png", "assembly_preview.stl", "#8ab0ba", "ELBOW  ·  no arm  ·  joint lateral"),
        ("fork.png", "print_fork_lateral.stl", "#7eb8c9", "PRINT  LATERAL PLATE  ·  sheave mounts here"),
        ("hub.png", "print_fork_medial.stl", "#7eb8c9", "PRINT  MEDIAL PLATE"),
        ("cuff.png", "print_cuff_forearm.stl", "#7eb8c9", "PRINT  FOREARM CUFF  ·  arm goes through"),
        ("drum.png", "print_drum.stl", "#9aa3ad", "PRINT  DRUM  (not 15 kg)"),
        ("sheave.png", "ref_sheave_DO_NOT_PRINT.stl", "#c4a35a", "BUY  3434T121 SHEAVE  ·  3/4 in bore"),
        ("bearing.png", "ref_608_DO_NOT_PRINT.stl", "#c4a35a", "BUY  6455K44  608-2RS"),
        ("screw.png", "ref_shoulder_screw_DO_NOT_PRINT.stl", "#9aa3ad", "BUY  91273A274 SHOULDER SCREW"),
        ("anchor.png", "print_bowden_anchor.stl", "#7eb8c9", "PRINT  BOWDEN ANCHOR"),
        ("stop.png", "print_hard_stop.stl", "#7eb8c9", "PRINT  HARD STOP"),
        ("arm.png", "ref_arm_ghost_DO_NOT_PRINT.stl", "#c4b8a8", "GHOST ARM  ·  do not print"),
    ]
    for name, src, color, title in jobs:
        print("render", name)
        render(STL / src, color, OUT / name, title)
    # contact sheet
    fig, axes = plt.subplots(3, 4, figsize=(16, 9.6), dpi=110, facecolor=BG)
    fig.subplots_adjust(0, 0, 1, 1, 0.01, 0.01)
    for ax, (name, _, _, title) in zip(axes.ravel(), jobs):
        ax.set_axis_off()
        ax.set_facecolor(BG)
        im = plt.imread(OUT / name)
        ax.imshow(im)
    fig.savefig(OUT / "sheet.png", facecolor=BG)
    plt.close(fig)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
