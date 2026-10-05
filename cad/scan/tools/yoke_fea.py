"""Yoke strength / sag check: 3D Euler-Bernoulli frame FE along the yoke's real arc.

The yoke is a flat band (24 mm radial x 36 mm tall) on a quarter-ellipse (ra 108 behind, rl 71 lateral) in
the horizontal plane at GH height, clamped at its root on the abduction hinge (sleeve + 2 x 6806) and loaded
at its tip (flexion housing). Loads are applied at the tip: a vertical force, and optionally the flexion
torque (about scan Z) when the arm is assisted. Scan frame: mm, X fwd, Y up, Z right.
"""
import numpy as np

RA, RL = 108.0, 71.0
T, H = 24.0, 36.0                     # band: radial thickness (in plane), height (vertical)
E, G = 2000.0, 700.0                  # PETG, printed (MPa)
N = 40

th = np.radians(np.linspace(180, 90, N + 1))
P = np.c_[RA * np.cos(th), np.zeros_like(th), RL * np.sin(th)]      # relative to GH

A = T * H
Iv = T * H ** 3 / 12                  # vertical bending (load up/down): 36 mm is the depth
Ip = H * T ** 3 / 12                  # in-plane bending
a, b = max(T, H) / 2, min(T, H) / 2
J = a * b ** 3 * (16 / 3 - 3.36 * b / a * (1 - b ** 4 / (12 * a ** 4)))    # rectangle torsion constant


def k_local(L):
    k = np.zeros((12, 12))
    def put(i, j, v):
        k[i, j] += v
    EA, GJ = E * A / L, G * J / L
    for i, j, v in ((0, 0, EA), (6, 6, EA), (0, 6, -EA), (6, 0, -EA),
                    (3, 3, GJ), (9, 9, GJ), (3, 9, -GJ), (9, 3, -GJ)):
        put(i, j, v)
    for (Ii, w, r, s) in ((Iv, 1, 5, 1), (Ip, 2, 4, -1)):     # bending in local y (vertical) about z; local z about y
        c = E * Ii / L ** 3
        m = np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                      [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]]) * c
        idx = [w, r, w + 6, r + 6]
        sg = np.array([1, s, 1, s])
        k[np.ix_(idx, idx)] += m * np.outer(sg, sg)
    return k


def frame(p0, p1):
    x = (p1 - p0) / np.linalg.norm(p1 - p0)
    y = np.array([0, 1.0, 0])                  # local y = vertical
    z = np.cross(x, y)
    R = np.vstack([x, y, z])
    Tm = np.zeros((12, 12))
    for i in range(4):
        Tm[3 * i:3 * i + 3, 3 * i:3 * i + 3] = R
    return Tm


def solve(F_tip, M_tip):
    nd = 6 * (N + 1)
    K = np.zeros((nd, nd))
    for e in range(N):
        L = np.linalg.norm(P[e + 1] - P[e]); Tm = frame(P[e], P[e + 1])
        ke = Tm.T @ k_local(L) @ Tm
        idx = list(range(6 * e, 6 * e + 12))
        K[np.ix_(idx, idx)] += ke
    f = np.zeros(nd); f[-6:-3] = F_tip; f[-3:] = M_tip
    free = np.arange(6, nd)                    # root clamped
    u = np.zeros(nd); u[free] = np.linalg.solve(K[np.ix_(free, free)], f[free])
    # section forces -> max stress
    smax, where = 0, 0
    for e in range(N):
        L = np.linalg.norm(P[e + 1] - P[e]); Tm = frame(P[e], P[e + 1])
        fl = k_local(L) @ (Tm @ u[6 * e:6 * e + 12])
        for s in (0, 6):
            Nx, Vy, Vz, Mx, My, Mz = fl[s:s + 6]
            sig = abs(Nx) / A + abs(Mz) * (H / 2) / Iv + abs(My) * (T / 2) / Ip
            tau = abs(Mx) / (0.246 * H * T * T)          # max torsion shear, rectangle 1.5:1
            vm = np.sqrt(sig ** 2 + 3 * tau ** 2)
            if vm > smax:
                smax, where = vm, e
    return u[-6:], smax, where


g = 9.81
exo = 1.4 * g                          # link + flexion hardware + elbow unit + pipes (~1.4 kg)
arm = 3.8 * g                          # wearer's arm (~5 % of body mass) resting in the exo
crate = 5 * g
cases = [
    ('exo hanging (rest)', exo, 0),
    ('arm resting in the exo', exo + arm, 0),
    ('assist, 5 kg in hand (17 N*m flexion)', exo + arm + crate, 17e3),
    ('same, x2 dynamic (walking, bumps)', 2 * (exo + arm + crate), 2 * 17e3),
]
root_len = np.sum(np.linalg.norm(np.diff(P, axis=0), axis=1))
print('yoke arc length %.0f mm, band %g x %g mm, Iv %.0f mm4, J %.0f mm4' % (root_len, T, H, Iv, J))
print('%-40s %9s %9s %9s %11s' % ('load case', 'F (N)', 'sag (mm)', 'twist deg', 'max MPa'))
for name, F, Mz in cases:
    d, s, w = solve(np.array([0, -F, 0]), np.array([0, 0, -Mz]))
    print('%-40s %9.0f %9.2f %9.2f %11.1f  (at %2d%% from root)' % (name, F, -d[1], np.degrees(np.hypot(d[3], d[5])), s, 100 * w / N))
