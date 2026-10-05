# Extension: shoulder-girdle degree of freedom (parked)

Status: **parked** (2026-09-30). The current exo has three joints: shoulder abduction, shoulder flexion and
elbow flexion. This note records the missing fourth one so it can be picked up later.

## Problem

Both shoulder hinges assume the shoulder joint centre (GH) is fixed relative to the back frame. The real GH
moves with the shoulder blade:

- **forward / back** (protraction / retraction): roughly ±30–40 mm;
- **up** when shrugging (elevation): about 40 mm.

With a rigid frame the exo blocks this motion, or pushes on the arm when the wearer moves the shoulder.

## What doesn't work

A slider along the **yoke arc** does nothing: the arc is centred on GH, so sliding along it only moves the flexion
hinge around the same point. The whole shoulder mechanism (mount block, abduction hinge, yoke, link, arm) has
to move relative to the frame.

A **vertical-axis swing joint behind the back** moves GH mostly sideways, not forward (15° of swing):

| Pivot location | GH forward | GH sideways |
|---|---|---|
| Behind the back, near the spine | 29 mm | 53 mm |
| Behind the shoulder blade | 6 mm | 48 mm |
| Above the trapezius, beside the neck | 38 mm | 5 mm |

## Options

**B. Linear slide at the mount block (preferred).** The mount block rides forward/back about ±40 mm on a guide,
re-centred by elastic cord or springs, with soft stops. The guide must carry the tipping moments from the arm
(about 30 N·m when assisting, twice that with bumps):

- twin 10 mm steel rods about 60 mm apart with 4 × LM10UU linear bearings (cheap, robust), or
- an MGN15 rail and carriage (compact; check its moment rating against the datasheet).

It can be motorized later with a small belt or lead screw along the slide. As a passive joint it doesn't
fight the assist, because the lifting loads act across the slide, not along it.

**A. Vertical pivot beside the neck, above the trapezius.** It gives the right motion (it's where the shoulder
blade actually pivots), but needs a boom over the shoulder from the frame, with the whole arm mechanism hanging
from it, next to the neck and the shoulder straps.

**Later: elevation (shrug).** A second passive joint for vertical motion, only if the shrug is felt to be blocked.

## Constraints when implementing

- The **flexion-hinge interface is frozen**: the upper-arm link is already printed. Keep the yoke's 6808 pockets,
  the Ø40 sleeve, the 25 mm housing width with its r44 / r31 step, the 2 mm running gaps to the fork, and the
  M8 × 55 with its captured nut.
- Only the mount block, the yoke root and the frame beams/diagonals change.
- Re-run the clearance and shoulder range-of-motion checks (`cad/scan/tools/check_fusion.py`) over the slide's
  travel.

## Related: abduction-hinge load path (to do regardless)

From the beam check (`cad/scan/tools/yoke_fea.py`):

- The yoke itself is stiff at rest (tip sag 0.4 mm with the arm resting in it). When assisting, the root
  stress reaches about 19 MPa with bumps, across the print layers.
- The abduction bearings (2 × 6806, about ±400 N when assisting) are fine. The weak link is the separate sleeve
  plus the M8: the yoke root sits in front of the front bearing and hands about 28 N·m of tipping moment through a loose sleeve fit.
- Fixes: make the sleeve part of the yoke (a Ø30 tube through both bearings); widen the bearing spacing
  (69 → about 90 mm; optionally 6808s); taper the yoke root 36 → 56 mm tall; print the yoke flat.
