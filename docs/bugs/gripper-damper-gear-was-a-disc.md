# Gripper damper "gear" was a plain disc

**Where:** gripper prototype 2, the rotary damper on the head and the rack on the beam
**Status:** fixed in the model (not printed yet)

| | |
|---|---|
| What | The damper's gear was drawn as a plain cylinder at the root circle beside the rack. It looked like a white puck, not a gear, and nothing meshed. |
| How found | User review: "the rack and pinion: is that supposed to be a gear wheel?" |
| Cost | A review round. |
| Root cause | I drew bought parts as placeholders and never checked that parts meant to mesh actually mesh. |
| Fix | A real 11-tooth module-1 involute gear on the damper's shaft. It is phased to the rack's tooth grid (the racks on the base and the arm share one grid) and rolls along the rack as the head slides (`poses` turns it by distance ÷ pitch radius). |
| What catches it now | `design_rules.py`, **meshes**: a gear meant to mesh must have at least 2 faces per tooth and sit within 0.3 mm of its partner. The collision check catches overlap in every pose. Proven on the old model: "3 faces < 22: no teeth modelled". |
