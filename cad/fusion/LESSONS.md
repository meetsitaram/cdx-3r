# Lessons learned: CDX-3R in Fusion + body scan

These are the issues we hit building the elbow (concept B) and the shoulder + back system on the
exoarm2 body scan, grouped by category. Each entry says what went wrong, why, and what to do instead.
Read this before starting a new part.

## 1. Environment and tooling (Windows PC)

| Issue | Cause | Do instead |
|---|---|---|
| No Python; only the Microsoft Store alias | fresh Windows install | `winget install Python.Python.3.12 --scope user`, then pip: numpy scipy open3d trimesh manifold3d shapely mapbox_earcut scikit-image matplotlib |
| matplotlib `plot_trisurf` crashed: "Application Control policy has blocked" `_qhull` | Windows Application Control blocks that DLL | render with `Poly3DCollection` (`exoarm2-scan/tools/render.py`) |
| Garbled characters (mojibake) in READMEs; a Python edit failed to match "Ø" | PowerShell 5 and Python on Windows default to cp1252 | write text with the Write tool; in Python always `open(..., encoding='utf-8')` |
| `/tmp/x.json` written in bash was not found by Python | Git-Bash `/tmp` and Windows Python resolve to different folders | use project or scratchpad paths |
| Multi-line heredoc edits broke ("here-document delimited by end-of-file") | quoting and special characters inside the Bash tool | write the edit script to a file, then run it; for exact replacements use the Edit tool |
| git not found in PowerShell; push rejected for a private email | git is not on PATH there; GitHub email privacy | use Git Bash; pass `-c user.email=<id>+<user>@users.noreply.github.com`; commit message from a file; GCM browser login |
| Fusion MCP showed `ECONNREFUSED` although Fusion was running | a session connects to MCP servers only at start; Fusion's server was not up yet | start Fusion first and let it load fully. If the connection failed, ask the user to reconnect **fusion** via `/mcp`. Do not write a workaround client |

## 2. Fusion API gotchas

| Issue | Do instead |
|---|---|
| Bounding boxes stale or wrong inside a script (built an elbow backwards; "moved" parts that had not moved) | measure with `measureManager.measureMinimumDistance`, `physicalProperties.centerOfMass` on assembly proxies, or tessellation extents; confirm with a screenshot |
| New occurrences come in grounded, so joints do not move them | set `occ.isGroundToParent = False` on moving parts |
| Joint pose lost after save / in references | after setting `rotationValue`, capture the position with `design.snapshots.add()` before `doc.save()` |
| STL export of an occurrence is in the component's **own** coordinates (parent transforms ignored) | account for it in checks: moving parts arrive un-posed; concept-frame parts need mapping; never guess units from magnitude (a "<400 → cm" rule broke small parts) |
| Inserting a Z-up document into a Y-up one re-orients it; an xref of a design with two **ungrounded** jointed units re-solves unpredictably (arm units lay sideways) | copy the posed bodies with `TemporaryBRepManager.copy(proxy)` into a component with a known transform (`shoulder.place_elbow`); re-run after elbow edits |
| Body names/appearances set inside a base-feature edit were lost | set them after `bf.finishEdit()` |
| A JOIN whose target it doesn't touch silently makes a **new body** (the link came out as 4–6 bodies; loose bosses overlapped pipes) | build outward in connected order (hub → strip → web → head → bosses → fork); assert body count is 1 |
| Feature names get " (1)" appended | match with `startswith` |
| Circular pattern of cut features fails when a copy cuts nothing | drill once at the end; pattern only what intersects |
| Fillet sets fail as a whole | tangent chain off; try the set, then edge-by-edge with a smaller radius, then skip (`concepts._fillet`) |
| Rounding the rim of a Ø51 flange pocket nicked the mating flange (1 mm³) | never round hole/socket/pocket edges; the skip test covers concave cylinders up to r 30 mm |
| Reference meshes drew every triangle edge (no per-body API switch; "Smooth Shaded" doesn't help) | hide the mesh bodies and draw them as **custom graphics** (`shoulder.show_reference_smooth()`); not saved with the document, so re-run it after reopening |
| Rebuilding the frame (`main()`) recreates the top component and wipes the arm side | after `main()` always run `main2()` and `place_elbow()` |
| Five different small screws (M3 × 8/10, M4 × 12, #4 self-tappers) made ordering and assembly painful | pick **one** small screw (M3 × 8) and one insert; counterbore the head wherever a wall is thicker, so the screw always reaches; but into PVC use **self-drilling (Tek) screws** (2.9 × 9.5, DIN 7504 N): no pilot, and they grip better than machine screws |
| A trim cut split a wall into a sliver + the wall; the join grabbed the stale reference (the sliver), leaving the wall loose and uncut by later sockets | after any cut that can split a body, re-collect bodies by volume, drop slivers, join everything; step the timeline (markerPosition) to find which feature changes the body count |
| Plate and gusset of different widths, or a gusset starting mid-disc, left pinch corners | give a disc-plus-plate a D profile: circle on top, a same-width rectangle below (tangent sides); start the slope where the circle ends; keep it thin next to the skin (a flat layer running further down pressed into the deltoid) |
| Mesh bodies in a parametric design | add them inside a base feature (`baseFeatures.add(); startEdit(); meshBodies.add(...); finishEdit()`) |
| Left/right copies drifted when edited separately | build the right half and add a **Mirror feature** about a midline construction plane (associative); for split prints use `isCombine=False` |

## 3. Geometry and modelling mistakes

| Issue | Do instead |
|---|---|
| Renders showed the arm on the wrong side | plotting (X, Z, Y) swaps handedness; plot (X, −Z, Y) and label views from the viewer's side |
| Scan frame vs CAD frame confusion | one documented frame (scan: mm, X fwd, Y up, Z right, floor Y = 0); concept frame X lateral, Y anterior, Z up the upper arm; convert explicitly (`elbow_matrix`) |
| A variable reused (`out`) wiped the parts dict | distinct names for geometry temporaries |
| Zero-length tube segment gave NaN meshes | drop duplicate path points |
| An angled pipe hit the backbone pipe inside the node | socket bottom at `clear_start()` = (OD + gap) / sin(angle) along the pipe |
| An angled pipe's rim dug into the block before its socket began | start the socket cut in the air (−15 mm before the face) |
| A blunt "arm bore" cut through composite parts left fins and knife edges | shape features to stop short (web ends inside the band, bosses stop 0.5 mm short of the bore); no trim cut needed |
| Enclosed voids: an insert hole buried under the yoke band; tunnels in the scan torso | check each STL is one watertight shell with positive volume; count shells |
| A part longer than the P1S bed (376 mm) | check each printed body's oriented box against 256 mm minus a margin; split symmetric parts at the mirror plane plus a bolted splice plate |
| Sharp edges everywhere looked unfinished | `round_edges()` on every printed body (2 mm), skipping fits and the mirror seam |
| Stacked hub + strip + web prisms of different widths left visible steps | derive a part from **one outline** (e.g. hub disc + end disc + tangent lines) and cut every feature from it (extrude, or intersect with a region) so all sides are flush |
| Concentric hinge parts all different radii (r 28 / 34 / 36) looked random | make stacked circles on one axis the same radius; pick the smallest that keeps the wall (r 30 = 9 mm around a 6806) |
| Merged pieces came out separate **again** (the fork's inner plate joined before the Y wedge that connects it) | order every JOIN/combine so each piece touches what is already there; check the body count after each rebuild |
| A straight full-length Y slope came within 1.9 mm of the deltoid; a half-length Y left a ledge | run the gusset the full length and make its inner edge an **arc bowed away from the body** (6 mm sag); end neighbouring slabs exactly where the slope starts |
| A sketch arc + lines made a bow-tie profile (thin strut instead of a solid gusset) | Fusion orders arc ends counter-clockwise, not as given: connect lines to whichever arc end is nearest each point |
| Hardware helper hard-coded an M8 shank, so the M4 screws modelled 4x too big and "collided" | size every bought part from parameters; run interference including '(buy)' bodies |
| Edge rounding also rounded the hex nut pocket's inside corners, so the nut would not fit | cut fit features (hex pockets, counterbores, bearing pockets) **after** `round_edges`, or skip them |
| A final `finish(name)` renamed all hardware bodies to "HW ... 1..n" | never rename '(buy)' components' bodies |
| A 4.4 mm button head on the arm side became the tightest part in the shoulder sweep | sink bolt heads that face the body: low-head DIN 7984 in a counterbore, with the material behind it counted (plate + boss) |
| A combined elbow rebuild + shoulder rebuild in one MCP call timed out | split long runs into separate calls (elbow rebuild / shoulder rebuild / place + check / export); after a timeout, query the state before re-running |

## 4. Design and ergonomics (from the body scan and fitting)

- **Scan accuracy is about ±5 mm.** The printed elbow fits although the scan says it is 5–7 mm tight. Treat small negative gaps to the arm as noise; torso gaps below 10 mm are real.
- **The hanging arm rests on the ribs.** Rings that wrap the medial side press into the ribs and armpit. Wrap only the back and outer side, close with a strap, and rest the exo at 20° abduction.
- **No band across the back of the upper arm mid-length:** it pinches the triceps. With the pipes fixed at both ends (near ring + rigid pipe head, ~100 mm apart) a mid support adds nothing.
- **Armpit fold zone:** no hard parts about 170–205 mm above the elbow on the back-medial side. The pipe head is at 155 mm.
- **Load path:** frame → hip belt carries the load. Backpack straps hold the frame to the back. A rigid shoulder saddle was redundant once there was a frame, straps and a belt.
- **Joints that carry the arm:** no small bolted lugs on thin bands and no single-sided cantilevers. Use one-piece parts, a two-sided fork (double shear) with a through-bolt, Y-joins instead of square corners, and deep blind pipe sockets with screws.
- **Bearings:** a 6806 at ~1.1 kN is far from its limit. Stiffness comes from bearing spacing and the printed structure around it, not bearing size.
- **Kinematics:** both shoulder axes pass through the glenohumeral joint (GH). Parts that turn with the arm keep a constant gap to it; check them against the **torso** across the range. Fixed parts are checked at rest.
- **Yoke routing:** above GH it swings into the neck and saddle under abduction; near the abduction axis it barely moves. A link inside the hinge collides with the deltoid bulge.
- **Balance:** a one-arm exo sits about 96 mm right of the spine. Use a symmetric frame and put the battery at the left mount block.
- **Earlier elbow lessons:**
  - no hard parts on the front of the forearm near the elbow (biceps pinch at full flexion);
  - parts must pass through the bearing bore;
  - delicate lips break;
  - fillet before drilling, and drill pipe holes last.
- Keep the full scan (hands, head, legs). Trim only the Fusion reference copies.

## 5. Verification routine (run after every change)

1. Fusion interference across all bodies, **excluding** coincident faces. Report cross-component hits only.
2. Body clearance against the scan distance fields at rest (`exoarm2-scan/tools/check_fusion.py`).
3. Shoulder range-of-motion sweep: abduction 20–60° × flexion −20–120°, against the torso and the fixed exo parts.
4. The elbow's own 0–135° sweep and door sweeps (`concepts.main`).
5. Print checks: one watertight shell per STL; oriented box within the bed.
6. A screenshot at the joint in question. Numbers can hide ugly geometry.

## 6. Working agreements with the user

- Physical fit tests beat the scan. Ask what fit well or tight after each print.
- Print on a Bambu P1S (256 mm cube). Rounded skin-side edges. Robust over minimal.
- Left/right symmetry through Fusion mirror features, so edits on the right carry over.
- When a request is ambiguous (e.g. "rotate the yoke higher"), state the interpretation explicitly and offer the alternative.
- When something needs the user's hand (MCP reconnect, credentials), say so in one line rather than building workarounds.
