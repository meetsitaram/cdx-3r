# Wrist ring v2: plunger latch, rounded edges

Replaces `05_wrist_ring` and `06_wrist_cuff` of elbow test print v10. Built by `wrist_cuff()` and `ring()` in
`cad/fusion/concepts.py`.

## Changes

- **Latch (outer side):** the cuff no longer needs a loose pin. The ring's elbow-side knuckle is thicker (Ø16) and
  takes the **M8 index plunger** with the pull ring, the same one as the gripper's fold latch (3 spare in the Bitray
  4-pack). Its 5 mm pin drops into the cuff's knuckle. Pull the ring to open the cuff; let go and it springs back in.
- **Edges:** the band's circular edges are rounded nearly full (2 mm on the skin side, 2.5 mm outside, on a 5 mm
  band), like a donut. Every other outer edge is rounded too; the export fails if one is sharp.
- The hinge side is unchanged: Ø4 × 25 dowel.

## Parts

| File | Qty | Print | Notes |
|---|---|---|---|
| `01_wrist_ring.stl` | 1 | flat, as exported | the thick knuckle's Ø6.8 hole is for the plunger's thread (it cuts its own) |
| `02_wrist_cuff.stl` | 1 | flat, as exported | |

Hardware: M8 index plunger with its lock nut (from the gripper's 4-pack), the Ø4 × 25 dowel (unchanged).

## Fitting

1. Cuff onto the ring's hinge side with the 4 mm dowel (drop of glue at one end).
2. Screw the plunger into the thick knuckle from the elbow side until its end is flush with the knuckle's underside,
   then lock it with its nut.
3. Pull the ring, swing the cuff shut, let go: the pin drops into the cuff's knuckle.
