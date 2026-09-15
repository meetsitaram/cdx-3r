#!/usr/bin/env python3
"""Armor stills: carbon shells on the ghost skeleton."""
from __future__ import annotations

import json
import struct
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

STL = Path("/workspace/public/cad/armor")
ASM = STL / "asm"
OUT = Path("/workspace/public/cad/armor/preview")
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
    fig = plt.figure(figsize=(9.6, 6.4), dpi=120, facecolor=BG)
    ax = fig.add_subplot(111, projection="3d")
    chunks = []
    for name in names:
        path = ASM / f"{name}.stl"
        if not path.exists() or path.stat().st_size < 84:
            continue
        tris = read_stl(path)
        if len(tris) == 0:
            continue
        tris = tris[:, :, [0, 2, 1]]
        color = PALETTE.get(name, "#888")
        ghost = name.startswith("ghost")
        ax.add_collection3d(
            Poly3DCollection(
                tris,
                facecolors=color,
                edgecolors="#0a0a0c",
                linewidths=0.04,
                alpha=0.35 if ghost else 1.0,
                shade=True,
            )
        )
        chunks.append(tris.reshape(-1, 3))
    pts = np.vstack(chunks)
    lo, hi = pts.min(0) - 20, pts.max(0) + 20
    ax.set_xlim(lo[0], hi[0])
    ax.set_ylim(lo[1], hi[1])
    ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(tuple(hi - lo))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_facecolor(BG)
    fig.text(0.03, 0.04, title, color="#e8e8e4", fontsize=9, fontfamily="monospace")
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(out, facecolor=BG)
    plt.close(fig)


def render(path, color, out, title):
    tris = read_stl(path)
    tris = tris[:, :, [0, 2, 1]]
    fig = plt.figure(figsize=(7.2, 5.2), dpi=110, facecolor=BG)
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(tris, facecolors=color, edgecolors="#0a0a0c", linewidths=0.12, shade=True))
    pts = tris.reshape(-1, 3)
    lo, hi = pts.min(0) - 8, pts.max(0) + 8
    ax.set_xlim(lo[0], hi[0])
    ax.set_ylim(lo[1], hi[1])
    ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(tuple(np.maximum(hi - lo, 1)))
    ax.view_init(elev=18, azim=40)
    ax.set_axis_off()
    fig.text(0.03, 0.04, title, color="#e8e8e4", fontsize=8, fontfamily="monospace")
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(out, facecolor=BG)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    worn = [
        "ghost_ua",
        "ghost_fa",
        "ghost_deltoid",
        "ghost_frame",
        "ua",
        "fa",
        "deltoid",
        "bezel",
        "sheave",
        "scapula",
        "pack",
        "lid",
        "led",
        "screw",
    ]
    print("worn")
    render_layers(worn, OUT / "worn.png", "ARMOR  ·  circular joint windows  ·  dual sheaves in the hole")
    print("joint")
    render_layers(
        ["deltoid", "bezel", "sheave", "led"],
        OUT / "joint.png",
        "JOINT  ·  carbon window  ·  3434T121 dual stack",
        elev=8,
        azim=-70,
    )
    jobs = [
        ("ua.png", "print_fairing_ua.stl", "#1f2328", "PRINT  BICEP PLATE  ·  stops before the elbow sheave"),
        ("fa.png", "print_fairing_fa.stl", "#252a31", "PRINT  FOREARM PLATE  ·  hinge stays open"),
        ("deltoid.png", "print_fairing_deltoid.stl", "#1c2024", "PRINT  DELTOID WINDOW  ·  circular cutout for the sheave"),
        ("scapula.png", "print_fairing_scapula.stl", "#2a3038", "PRINT  YOKE DISH"),
        ("pack.png", "print_fairing_pack_tub.stl", "#16191d", "PRINT  PACK PLATE  ·  3 drum windows"),
        ("lid.png", "print_fairing_pack_lid.stl", "#1a1e24", "PRINT  DRUM BEZELS"),
    ]
    for name, src, color, title in jobs:
        render(STL / src, color, OUT / name, title)
        print(name)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
