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
| Again in the v3 girdle (carriage 9 bodies, elbow plate 12): `Part.join` took pieces in list order, so a fork's lower cheek (touching only via the posts listed after it) stayed loose, and the inner-ring bosses on it became 0.07 cm³ bodies. Fusion **does not raise** for a combine of non-touching bodies | `fxlib.Part.join` now joins in passes and only joins a piece once `measureMinimumDistance` says it touches; `measureMinimumDistance` raises 'invalid argument' on a nested component's native bodies, so measure **proxies** (`createForAssemblyContext` with the occurrence from `rootComponent.allOccurrences`) |
| Feature names get " (1)" appended | match with `startswith` |
| Component names are unique per design: building v3b while the old v3 group was still in the model renamed the new parts "Lift link upper (1)" and broke name matching | delete (or rename) a superseded group before building its replacement; match component names with `startswith` |
| Posing parts of a sub-group by setting `transform2` on `group.occurrences` failed: "transform overrides can only be set on Occurrence proxy from root component" | pose through `rootComponent.allOccurrences` (full-path proxies), filtered by `fullPathName` |
| Circular pattern of cut features fails when a copy cuts nothing | drill once at the end; pattern only what intersects |
| Fillet sets fail as a whole | tangent chain off; try the set, then edge-by-edge with a smaller radius, then skip (`concepts._fillet`) |
| Rounding the rim of a Ø51 flange pocket nicked the mating flange (1 mm³) | never round hole/socket/pocket edges; the skip test covers concave cylinders up to r 30 mm |
| Reference meshes drew every triangle edge (no per-body API switch; "Smooth Shaded" doesn't help) | hide the mesh bodies and draw them as **custom graphics** (`shoulder.show_reference_smooth()`); not saved with the document, so re-run it after reopening |
| Rebuilding the frame (`main()`) recreates the top component and wipes the arm side | after `main()` always run `main2()` and `place_elbow()` |
| Five different small screws (M3 × 8/10, M4 × 12, #4 self-tappers) made ordering and assembly painful | pick **one** small screw (M3 × 8) and one insert; counterbore the head wherever a wall is thicker, so the screw always reaches; but into PVC use **#4 × 3/8" pan-head self-tapping screws** (pointed, the common kind): they cut their own thread, and the printed hole centres them |
| A trim cut split a wall into a sliver + the wall; the join grabbed the stale reference (the sliver), leaving the wall loose and uncut by later sockets | after any cut that can split a body, re-collect bodies by volume, drop slivers, join everything; step the timeline (markerPosition) to find which feature changes the body count |
| Plate and gusset of different widths, or a gusset starting mid-disc, left pinch corners | give a disc-plus-plate a D profile: circle on top, a same-width rectangle below (tangent sides); start the slope where the circle ends; keep it thin next to the skin (a flat layer running further down pressed into the deltoid) |
| Insert holes sized for 4 mm inserts; the inserts actually bought were ruthex 5.7 mm | size insert holes from the actual part bought (ruthex RX-M3 × 5.7: Ø4.0 × ~7 mm); model the insert at its real length |
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
| The abduction hinge's 30 mm fender washer pulled into the rear 6806 (bore 30): it only sat on the sleeve end and clamped nothing | a washer or boss that clamps a bearing inner ring must be **larger than the bore and no larger than the ring land** (6806: 30 < OD ≤ 33, so a 32 mm washer); check bought washers against both, not only the bolt size |
| v3 girdle: hand-placed SCARA root/elbow swung into the fixed lift base (1–2 mm in shrug and squeeze); found only after building every part in Fusion | lay out mechanisms first with a fast offline search (`cad/fusion/girdle_layout.py`: plan circles/capsules + height bands, every pose, part-to-part, base, body and size limits), then build once in Fusion |
| A parallelogram used to keep a SCARA's end from turning needs its two bars ~2 × bar width apart, or they hit each other when the link swings ~35° from square; with 608 pivots that spacing pushed parts past the arm or 7 cm behind the frame (no layout fit) | keep the orientation with a **timing belt inside each link** (like real SCARA robots) — one bar per link; the layout then fits with 17 mm clearance |
| Rest-level lift links make the carriage drift toward the mast on every shrug (18 mm at +60) | tilt the links ~15° at rest so a shrug passes through level: drift drops to a few mm |
| A combined elbow rebuild + shoulder rebuild in one MCP call timed out | split long runs into separate calls (elbow rebuild / shoulder rebuild / place + check / export); after a timeout, query the state before re-running |
| Building a whole new mechanism (8 printed parts, 12 pivots of hardware) in one call froze Fusion for minutes: the call timed out and every follow-up query timed out too (Fusion "not responding" while it kept working) | **one part per MCP call** for new parts; time each; wait for Fusion to respond again (poll `Get-Process Fusion360` `.Responding`) instead of firing more calls; keep `round_edges` to plain outlines (round before adding bosses and pockets, which the lessons already require) |
| Motion review renders: posing the girdle + 3 camera views costs ~1.8 s per frame | `render/girdle_anim.py`: 20 frames per MCP call (~36 s), PNG → JPEG q72 (~26 kB), publish as a frame-player page; 79 frames × 3 views fits the 255-file publish limit |
| Splitting a mirrored node so only the left keeps a socket: the socket boss, added after the bore, filled part of the backbone bore (4270 mm³ into the pipe) | a boss that starts inside a bore must be **joined before the bore is cut** (or cut the bore again after it); run interference after every rebuilt frame part |
| A sleeve laid over the outside of a node looked bolted on, and its cheeks stuck up 8 mm | make the node end a **tenon** (cut down by the sleeve thickness + 0.3 mm fit) so the sleeve is flush with its faces; cut the tenon after `round_edges`; leave the seam edges sharp (`round_edges(seam_z=...)`); re-cut the sleeve cavity square after rounding (its concave fillets hit the tenon's sharp corners); sink bolt heads (sex bolts) |
| Connection audit of the v3b girdle: lift pivots had bearings but no bolts; the gas spring passed through solid ears; the S0 head was buried 2 mm in the carriage with no way in; the E nut was buried in the end plate's drop column; the SCARA link boxes sealed the belt and pulleys inside, with bearings in through-holes and no lip | run interference with every bought part modelled, in every pose; follow the connection and print rules in sections 5a and 5b |
| Hinges with two bolts + nuts per joint stuck out and added weight; a lockable hinge also fights a chain that should drape | a shoulder rest chain uses **one clevis pin per joint** (ISO 2341-B: head + R-clip, it can't walk out) through end knuckles on one piece and a middle knuckle on the other; the strap's tension holds it on the body |
| Nuts deep in a hex tunnel or a side slot under a housing were legal but fiddly to fit | prefer: head locked in a hex pocket that's open before assembly (the next part slides over it) and the nut on an open face; or bolt in from the buried side through a round tunnel a hex key reaches, nut on the open side |
| Deleting an early component "succeeded" but came back: removing it made later fragile fillets fail on recompute, so Fusion rolled the delete back | `fx.retire()`: hide and rename 'zz old ...' first (that sticks), then delete; to get a clean document, rebuild into a fresh one |
| A round plate under a square block left a ring | loft the round foot into the square (`girdle_b._loft`) |
| New hardware piled up (4 clevis pin lengths, M5 sex bolts, M5 nuts, M8 hex heads, washers) | **check every new part against BOM.md before adding it**: reuse the sizes already bought (one M8 length + cut spares; M3 × 8/12 + ruthex; one pin size by making every hinge the same width); put hard-to-reach nyloc nuts in printed hex pockets instead of buying hex-head bolts |
| Honeycomb pockets on a part printed on edge | orient the hexagons corner-up for the print direction (60° roofs); pockets open on the top face only, the pad side stays flat |
| A hand-drawn line on a screenshot ("slide to that place") meant *cut along this line*; I read it as "add a gusset" and added material where the user wanted it removed | a line drawn across a part is a cut line; if unsure, say back "cut along this line?" before building |
| A timed-out MCP call that rebuilt the pipes left the old component next to the new one ("... (1)") | after any timeout, list components and delete duplicates before the next check |
| The static scan never moves the shoulder blade, so a girdle placed at blade height looked clear (48 mm) | move torso points near the shoulder with it (`girdle_follow.py`: weight fades toward the spine and down the back) and **swing the arm back** about GH before trusting any part behind the upper arm; under the housing the arm hit the SCARA elbow at 35° (24° squeezed) |

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
- **Keep the girdle above GH.** The space behind the upper arm, below GH, is swept by a normal 0–60° backswing. A shoulder-girdle SCARA placed there (between the top and mid nodes) stops the arm at 24–47°, even moved 20 mm back. Above GH, the arm reaches the girdle's height only past 75°.
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
7. Interference **including every bought part** (bolts, nuts, bearings, spacers) in every pose: a buried nut or a
   head sunk into a block only shows up this way. Skip only parts meant to overlap (a gas spring's rod in its body).

## 5. (cont.) Physics test before printing: `cad/sim/exo_sim.py` (MuJoCo)

- **Test the exo the way it's driven: by the straps.** The back frame is one rigid body fixed in the world; the
  wearer's arm is a kinematic (mocap) body; the exo is passive and pulled only by strap springs (3000 N/m). Read the
  strap forces and how far the exo's shoulder centre is from the wearer's.
- **Move the shoulder about the sternoclavicular joint** (top of the breastbone), not in straight lines: shrug/drop
  = collarbone elevation, reach/squeeze = protraction, + ~15 % elevation with an arm raise. GH then rides on an arc.
- **Two straps on the upper arm (≈30 % and 75 % of shoulder → elbow) + the wrist cuff.** With one upper-arm strap the
  exo pivots around it and its shoulder drifts ~5 cm off the wearer's.
- **Size the lift's gas strut in the sim:** 15–25 N gave the lowest strap forces (rest ~6 N, mean ~19 N, shoulder
  centre within 4 mm mean / 15 mm max); a 100 N strut doubled the strap forces and pushed the girdle to its stops.
- Peak strap loads (65–95 N) come only at the ends of travel (arm raise 90° + shrug: abduction stop at 95°, lift at
  ~68 mm): expected stops, not binding.

## 5a. Connection rules (bolts, nuts, bearings): check each joint

- **Every hole has its hardware, every bolt its hole.** Model the bolt, nut, washers and spacers for each pivot; a
  pivot with bearings but no bolt is unfinished (the v3b lift pivots were).
- **Bolt length = stack + nut + 1.5 mm.** A nyloc only locks when the thread passes all the way through it (M8
  nyloc 8 mm, M5 5 mm). Round up to the next 5 mm. A helper that used "stack + 2" made every M8 one size short.
- **Two bolts entering one part from opposite ends must not meet:** width ≥ 2 × (grip + nut + 1.5) + gap. Two
  M5 × 30 hinge bolts need a 64 mm joint.
- **Every nut and bolt head needs a way in and a way to hold it.** If it sits inside a block, give it a hex
  tunnel or a side-loaded hex slot (it slides in and can't turn), or a hex pocket for a hex-head bolt plus an
  access bore to drop it in. No buried nuts.
- **Hex pockets use the same sketch frame as the modelled nut/head**, or the hex is rotated 30° and corners clash.
  For a side-loaded slot, the flats must face the slot walls.
- **Nut traps over a tool:** a captive nut (hex pocket, 0.3 mm over across-flats, 0.2 mm deeper) where a spanner
  can't reach (inside the tower between its plates).
- **608 stacks:** pocket from the outer face + a Ø19 lip on the cavity side (1.5 mm), so the bearing carries the
  part both ways. Clamp only the inner rings: Ø11 bosses / spacers (the 608 inner-ring land) between bearings,
  pulleys, heads and nuts; nothing larger than Ø11 may touch a 608 face (a Ø13 head or a nut rubs the outer ring).
- **Single-shear pins** for small loads (gas spring eyes): hex head locked in the ear, eye outside, washer, nyloc.
- **Closed belts need exact centres:** GT2 loop length = 2C + π·PD. 40-tooth pulleys (PD 25.46) + a 210 mm loop
  fit C = 65 mm exactly; size the cavity ≥ pulley + belt + 0.7 mm.
- **Pipe screws** into PVC through more than ~7 mm of plastic: counterbore (use `shoulder.pipe_screws`), or the
  #4 × 3/8" never reaches the pipe.
- **Sizing moving parts that have to fit inside each other** (a gas spring): compute the length range over the
  poses first (v3b spring: 112–169 mm, so 170 mm extended with 60 mm stroke).

## 5b. Print rules (Bambu P1S, PETG, 0.2 mm, 4–5 walls, 40 % gyroid)

- **Decide each part's print orientation while designing it**, and put it in the part's docstring.
- **Flat underside + no overhang over 45°.** Hinge knuckles sit on the bed: make the plate's underside flush
  with the knuckle's bottom (axis one knuckle radius up) and carry the knuckle on a gusset that slopes into the
  plate (D-profile). A knuckle centred on a thin plate needs supports and snaps at the neck.
- **Horizontal holes:** ≤ Ø14 print fine; hex holes print best with a corner up; Ø22 bearing pockets lying
  sideways need supports or a teardrop.
- **Bridges** up to ~30 mm are fine (the tower's saddle top over its cavity).
- **No sealed cavities.** Anything with parts inside (belt, pulleys) is a tray + screwed lid; split it at the lid
  line after rounding, so the seam stays sharp and both pieces print flat.
- **Minimum walls:** 1.5 mm around a ruthex Ø4 insert hole, about 3 mm around a bolt hole, a 6 mm plate for
  knuckled blades. Ribs on parts that span air (the shoulder rest's root arm: 2 ribs 6 × 8 mm).
- **Gussets under round ends that overhang when printed upright** (the tower's lift cheeks: 63° wedge).
- **Load across layers is weakest:** keep thin sections (tabs, knuckle necks) in the layer plane, and give
  anything loaded across layers a thick section.

| Part | Print orientation | Supports |
|---|---|---|
| Shoulder tower | upright (node end on the bed) | none expected; check the spring ear |
| Lift carriage | root disc down, box up (brim: it stands on the 0.6 mm inner-ring boss); NOT on its side (Bambu auto-orient's pick: supports in the tunnels) | tree, build plate only |
| SCARA link trays and lids | outer face down | none |
| End plate + housing | on the housing's front face (the E nut slot then opens upward) | none |
| Lift links | flat on a cheek face | none |
| Shoulder rest root arm, blades | flat, pad side down (honeycomb holes vertical, open upward; Ø6.3 pin holes horizontal bridge fine). On edge they have no flat face on the bed | none |
| Shoulder rest bracket | flat, tower side down | none |
| Pulleys, spacers | flat | none |

## 5c. Assembly guide and animations (`cad/fusion/render/asm.py`, `mkgif.py`, `docs/ASSEMBLY.md`)

What went wrong in the first v3 guide (user review, Oct 2026), and the rule each one produced:

| Mistake | Rule |
|---|---|
| Bolts flew in from the nut side, heads through holes they can't pass | Fasteners use the `'head'` rule (they enter head-last from the head side); nuts use `'nut'` (from the far end of the bolt they meet, `mate_bolt`); hidden-pocket nuts use the direction the pocket really opens. Never fly hardware with the generic `'axis'` sign. |
| Parts flew horizontally *through* fork plates (lift links, carriage) | A part entering a fork slides in the plane of the fork's gap (here from above/below), never along the pivot axis. Check every direction against the mating part's walls. |
| Stacks of bearings/spacers/pulleys floated in thin air | Build order: the part that **holds** something appears first. Sub-assemblies (SCARA links, carriage with its nuts, end plate) are built at a staging spot (`{'at': offset}`), then carried in with a `'move'` group. |
| Hidden nuts invisible during their step | Make the receiving part see-through for that group (`{'ghost': parts}`), and for bolts that pass through closed parts. |
| Shoulder-rest pins all added at the end | Every piece is pinned the moment it goes on (piece, pin, clip, next piece); otherwise it would fall off. Animate the order a person can actually hold. |
| Flat parts (nuts, bearings, washers, pulleys) got an in-plane "axis" | The axis of a disc is its **thinnest** principal direction (`principal_axis`); only rods use the longest. Print the computed directions per group and sanity-check them before rendering. |
| Regex `R-clip` also matched "Clevis pin … + R-clip" | Select hardware by an unambiguous name fragment (`R-clip / split`) and print the selection counts. |
| Framing: content clipped or tiny | Render wide (`ZOOM_OUT`), let `mkgif` crop to the pixels that change plus 12 %. Don't "correct" the camera from `modelToViewSpace`: it reports scaled pixels (×1.5 on this PC) while saved images are already centred. Staging distances small (≈5–6 cm) so the crop stays tight. |
| Old pictures left in the docs (README, guide hero) after a redesign | After any design change, re-render every image that shows it (`render('all')` for the hero) and grep the docs for image names. |
| Guide was a wall of text | Animation first; one parts line; ⚠ lines only for order-dependent actions; everything else inside `<details markdown="1">`. Captions in the GIF carry the step-by-step. |
| Modelled the gas strut with ball-socket ends; the listing we picked has flat **eyelet** ends | Before modelling a bought part's interface, open the listing photos (dimension drawing) and model *that* end fitting; note hole size / thickness in the BOM. If the listing doesn't give a dimension, design the mount to tolerate the likely range (e.g. a fork + bush for a 6 or 8 mm eyelet). |
| Carriage printed on its side: tree supports grew into the pivot tunnels and the S0 bore; the README orientation was a guess | Choose each part's print orientation with `orient_stls.py` on the exported STLs (their frame is the design frame, y up; never assume) and ship the STLs pre-rotated so the slicer's auto-orient isn't needed. Horizontal round tunnels get 45° teardrop points (both ways if the part might print either way up); frame nodes stand on their bottom face so pipe sockets are vertical. |
| Carriage: a clearance cut started 0.05 mm off the cheek face (left a 0.05 mm film that can't print), and in the build code it started at the cheek's *inner* face (cut away the nut's seat). A round well into the strut ear left a crescent wall thinning to zero | Cuts start **exactly** on the face they clear, never at a small offset; check which face (inner/outer) a range variable means. Never leave a crescent where a cut cylinder overlaps another round boss: cut flat (tangent chord) instead. `print_validate.py` (rays inward from 12,000 surface points; FAIL on a thin *film*: points under 0.8 mm sideways / 0.6 mm vertically spread over > 1 mm in two directions; thin points along a line are knife edges or acute tips and only warn; plus one shell per part) runs after every export and in the pre-commit hook. Proven on the old carriage: its 0.05 mm film fails, real edges spread ≤ 0.53 mm. |
| Rebuilds in the one big document took ~10 min each (2,900 timeline steps; deleted parts can't be deleted, only retired, and still recompute) | **Done 2026-10-18:** one document per module + a linked assembly (`split.py`, PIPELINE-PLAYBOOK 5.2). A carriage rebuild now takes ~20 s in a fresh document (~80 s with the switch). The split rebuilt every part from the scripts and matched all 30 print volumes exactly: the scripts are the source of truth, never hand-edit a document. |
| Claimed a fix was "already in the code" without making it (carriage boss lip) | Before reporting a fix, check the diff contains it. |
| Docs kept a stale cut length (right backbone 583 vs 568 mm in the model) | Cut lengths in docs come from the build's own cut list (`split.build('frame')` returns it); re-check after any frame change. |
| Carriage disc sat on a 0.6 mm boss: the whole disc underside needed support | A part's print base must be truly flat: functional bosses on the base face become separate printed spacers. Overhanging lugs get a 45° web down to the base. |
| `bracket_bolts()` put the rest's thumb screw at 90° while the slot was cut at `phi` = 50°: screw, tower hole and nut trap sat on top of the strut ear, unnoticed | Any position derived from a parameter (slot angle, radius) comes from **one** function used by the cut, the hardware and the mating part. Interference sweeps include **all** hardware (thumb screws, pins), pair by pair with names printed. |
| Rest bracket held against strap pull by one M6 into a nut behind a 1.7 mm wall; found only after a 9 h tower print (docs/bugs/rest-bracket-attachment.md). Then I misdiagnosed it as "screw in thin air" from a probe along the hole axis and an uncalibrated test (docs/bugs/false-thin-air-diagnosis.md) | For every joint ask: which load, which direction, what carries it? `fastener_check.py` gates exports (screws must bite). Run any new test on a known-good and a known-bad case before believing it; show a section picture before declaring a geometry bug. Each bug gets a file in `docs/bugs/`. |
| A fix (rest pivot bolt) was checked for grip and printability but not collisions: its head sat inside the rest's hinge knuckle and clevis pin (docs/bugs/pivot-bolt-hits-rest-hinge.md) | `collision_check.py` runs on the whole assembly before every export (hook requires `failing 0`). Moving parts: also sweep them through their range (rotate a temporary copy with `TemporaryBRepManager` and intersect). |
| Checks only ran when someone exported; moving parts were never checked against fixed ones (raised arm into the shoulder rest, docs/bugs/raised-arm-hits-shoulder-rest.md) | `checks.run_all` (fasteners, static collisions, motion sweep through `collision_check.POSES`) writes reports stamped with a hash of the model code; the pre-commit hook refuses commits of model code or prints without passing, current reports. Every new check is run on a known-bad case first: the first versions of the collision test and of the sweep both reported nonsense (part names with '+', results without assembly paths). |
| Questions the guide didn't answer ("how is the strut attached?") | Every bought part gets its attachment shown and named, even if it's "snaps on, no screw". |
| Sim animation didn't show forces | Draw the strap pull as arrows from the skin outward (2 cm per N), from a view where they aren't foreshortened; label forces and units in the frame. |

Render loop: `recollect` (close temp doc, `restore`, `collect`, `migrate`), then `render(step)` in batches of
steps that fit the 60 s MCP limit, contact-sheet the frames, then `python mkgif.py`.

## 6. Working agreements with the user

- Physical fit tests beat the scan. Ask what fit well or tight after each print.
- Print on a Bambu P1S (256 mm cube). Rounded skin-side edges. Robust over minimal.
- Left/right symmetry through Fusion mirror features, so edits on the right carry over.
- When a request is ambiguous (e.g. "rotate the yoke higher"), state the interpretation explicitly and offer the alternative.
- When something needs the user's hand (credentials, a Submit button), prepare it so it's one tap, rather than building workarounds.
- **Keep pushing until it works.** When blocked, try the next legitimate route instead of stopping or lecturing (see
  docs/PIPELINE-PLAYBOOK.md section 7). A dead Fusion MCP is fixed by restarting the session, not by a homemade client;
  Claude app gaps go upstream with the `file-claude-bug` skill.
