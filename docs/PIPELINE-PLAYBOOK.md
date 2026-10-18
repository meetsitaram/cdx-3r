# Pipeline playbook: body scan → Fusion → prints, BOM, docs

How CDX-3R was built, written so a **new Claude Code session on a new project** can pick up the same pipeline
without relearning it. Give the new session this file in its first message (or copy it into the new repo's
`CLAUDE.md`), together with [cad/fusion/LESSONS.md](../cad/fusion/LESSONS.md).

---

## 1. What the pipeline produces

1. A **body scan** of the wearer turned into a clean mesh, a coordinate frame and landmarks (joint centres).
2. A **parametric Fusion model** built by Python scripts (not by hand), on top of the scan as a reference.
3. **Checks**: interference, clearance to the body, range-of-motion sweeps, printability.
4. **Print files** (STL per part, orientation notes, fit coupons) for a Bambu P1S.
5. A **BOM** with Amazon (Prime) links and thumbnails.
6. **Renders and animations**: a motion GIF/MP4 and per-step exploded assembly GIFs, rendered from Fusion.
7. **Docs**: README, BOM, ASSEMBLY (plain language), LESSONS, extension notes.

## 2. Machine and tools (Windows 11, this PC)

| Thing | Where / how |
|---|---|
| Python 3.12 | `C:\Users\PC\AppData\Local\Programs\Python\Python312\python.exe` (numpy, scipy, open3d, trimesh, manifold3d, shapely, scikit-image, matplotlib, Pillow) |
| Shells | **Git Bash** for git and Python (git is not on PATH in PowerShell). PowerShell for Windows things (processes, screen capture, window focus) |
| Fusion MCP | official Autodesk Fusion MCP at `http://127.0.0.1:27182/mcp`, registered in `C:\Users\PC\.claude.json` → `mcpServers.fusion` (`type: http`) |
| Fusion account | user `tinkerbuggy`, project "my-projects" |
| Built-in browser | the app's browser pane (`mcp__Claude_Browser__*`) |
| Web search | `WebSearch` (loaded through ToolSearch when it is deferred) |
| Printer | Bambu P1S, 256 mm cube, PETG |

**Text encoding:** always `open(..., encoding='utf-8')` in Python. Write docs with the Write tool, not PowerShell
(cp1252 mojibake). Put edit scripts in files; long heredocs with quotes break in the Bash tool.

**Git:** this shell has no git identity. Commit with
`git -c user.name=meetsitaram -c user.email=6304083+meetsitaram@users.noreply.github.com commit ...`.
Commit and push only when the user asks; show previews (rendered docs, images) before committing.

## 3. Connecting to Fusion

1. The user starts Fusion and lets it load **before** the session starts (a session connects to MCP servers only at
   startup).
2. If the `fusion` tools fail with `ECONNREFUSED`: tell the user in one line to run `/mcp` and reconnect **fusion**.
   Don't write a workaround client.
3. The tools: `mcp__fusion__fusion_mcp_execute` (`featureType: "script"`, `object: {"script": ...}`) runs Python inside
   Fusion; `fusion_mcp_read` reads state.

**Script template** (repo modules imported from disk, reloaded each call so edits take effect):

```python
import sys, importlib, traceback, adsk.core, adsk.fusion
sys.path.insert(0, r'C:\path\to\repo\cad\fusion')
def run(context):
    try:
        import fxlib, mymodel
        importlib.reload(fxlib); importlib.reload(mymodel)
        print(mymodel.main())
    except Exception:
        print(traceback.format_exc())
```

**Rules that saved time:**

- **Keep each call short** (one rebuild or one export per call). Long calls time out; after a timeout, query state
  before re-running.
- Wrap in `try/traceback` and `print()` results; the MCP returns stdout.
- **Units:** the API uses **cm**; the repo uses mm. Convert at one place (fxlib).
- State that must survive reloads (e.g. collected meshes) goes in a module-level dict, carried over:
  `parts = m.STATE.get('parts'); importlib.reload(m); m.STATE['parts'] = parts`.
- **Small fixes can be made in place**, in the parametric timeline instead of rebuilding: find the feature/sketch by
  name, change the circle radius, the extrude distance or a construction-plane offset. Example: the abduction washer
  30 → 32 mm (sketch circle, `DistanceExtentDefinition.distance.expression`, `ConstructionPlaneOffsetDefinition.offset`).
  Then also change the script parameter, so a rebuild matches.
- **Saving:** `app.activeDocument.save('description')` (cloud), then export the archive to the repo:
  `em.createFusionArchiveExportOptions(path)` → `cad/fusion/models/<name>.f3d`.
- **Seeing what Fusion shows:** `vp.saveAsImageFile(path, w, h)` and read the PNG. For the whole window, capture the
  screen with PowerShell (`System.Drawing` `CopyFromScreen`) after `WScript.Shell.AppActivate(<Fusion PID>)`.
- Bounding boxes can be stale inside a script: measure with `measureManager`, physical properties or tessellation.

## 4. Using the built-in browser

- If the pane is closed, `navigate` fails ("denied or failed"). Open it with `preview_start({url})` first, then
  `navigate`.
- Read pages with `javascript_tool` / `get_page_text`, not screenshots.
- Some sites (YouTube, Wikipedia) may refuse to load: use `WebSearch` to find links, and give the user the URLs.
- Never sign in, buy, or accept terms. Reading search results and product pages is fine.

**Amazon search → candidates** (run on a search results page):

```js
[...document.querySelectorAll('div[data-component-type="s-search-result"]')].slice(0,16).map(d => ({
  t: d.querySelector('h2')?.innerText, a: d.getAttribute('data-asin'),
  p: d.querySelector('.a-price .a-offscreen')?.innerText, img: d.querySelector('img.s-image')?.src}))
```

**Product page check:** title, bullets (real sizes: thickness, OD), `#mir-layout-DELIVERY_BLOCK` (Prime delivery
date), `#fulfillerInfoFeature_feature_div` ("Ships from Amazon"). Thumbnail for the BOM: take the image id and use
`https://m.media-amazon.com/images/I/<id>._SS64_.jpg`. Link as `https://www.amazon.com/dp/<ASIN>`.

## 5. The pipeline, phase by phase

### 5.1 Body scan → layout (`cad/scan/tools`, working data in `C:\Users\PC\projects\exoarm2-scan`)

- Source: phone Gaussian-splat scan (`.spz`) + `.glb`. `splat.cs` decodes; `body.py` → point cloud; `solid.py` /
  `mesh.py` → watertight body; `landmarks.py` / `sections.py` → joint centres; `layout.py` → `layout.json` + distance
  fields; `trim.py` → light Fusion reference meshes; `check_fusion.py` → clearance + ROM checks on exported STLs.
- **One documented frame:** mm, X forward, Y up, Z right, floor Y = 0. In Fusion it maps to (x, −z, y) cm under a
  top component rotated +90° about X. Write the mapping down on day one.
- Keep the full scan (hands, head, legs). Trim only the Fusion reference copies.
- Scan accuracy is about ±5 mm: physical fit tests beat the scan.

### 5.2 Fusion model by script (`cad/fusion/*.py`)

- `fxlib.py`: pure-Python vector math (no numpy inside Fusion), `matrix`, `rot`, `appearance`, and the `Part` builder
  (one component per part; `prism`, `box`, `ann`, lofts, pipes; NEW/JOIN/CUT). Reuse it.
- One **parameter dict** at the top of each model script (`S` for specs, `D` for derived values); every bought part
  sized from it (bearings, bolts, nuts, washers, inserts, screws, pipe). Bought parts' components end in `(buy)`.
- Build order: base shape → joins in connected order (assert one body) → `round_edges()` → fit features last
  (bearing pockets, hex pockets, counterbores, insert holes, pipe screw holes).
- Left/right: build the right side, mirror about a midline construction plane.
- Rebuild entry points (CDX-3R): `shoulder.main()` (frame) → `main2()` (moving parts) → `place_elbow()`; elbow in
  `concepts.py`. A rebuild that recreates the top component wipes what was placed after it: always re-run the chain.
- Reference meshes: add as mesh bodies inside a base feature, hide them, draw them smoothly as custom graphics
  (`show_reference_smooth()`). Custom graphics are not saved: re-run after reopening.

### 5.3 Verification (after every change)

1. Fusion interference (exclude coincident faces; cross-component hits only, including `(buy)` bodies).
2. Clearance to the body distance fields at rest.
3. Range-of-motion sweeps of every joint against the torso and the fixed parts.
4. Print checks: one watertight shell per STL, oriented box within 256 mm minus a margin.
5. A screenshot of the joint in question.
6. For load paths, a quick beam check (`cad/scan/tools/yoke_fea.py` is a 3D frame FE template: sag, stress, twist).

### 5.4 Print export

- `export_print(out_dir)` → `prints/<assembly>-vN/` with one STL per printed part, in print orientation, plus a
  README (orientation, supports, infill, which hardware goes where).
- Always include **fit coupons** (`00_fit_coupon_*`: bearing pocket, pipe hole) and print them first.
- Version folders (`-v2`, `-v10`); never overwrite a version the user may have printed. Once a part is printed, its
  interfaces are **frozen**: record them.

### 5.5 BOM (`BOM.md`)

- Table per category: thumbnail | item | spec (the sizes that matter, and what **not** to buy) | qty | where used |
  extra qty for a left arm | link.
- Consolidate hardware: one small screw (M3 × 8) + one insert (ruthex M3 × 5.7); #4 × 3/8" pan-head self-tappers into
  PVC; as few big bolt lengths as possible.
- Check each part against its **mating geometry**, not only the thread size (a washer clamping a bearing inner ring:
  bore < OD ≤ ring land).
- PVC cut list with **whole-mm lengths** (hand cuts are good to ~1 mm; round down where both ends are blind sockets).
- Show the user a rendered preview of the BOM before committing.

### 5.6 Renders and animations (`cad/fusion/render/`)

- **Motion animation** (`anim.py`): split moving assemblies into temporary components, pose them with
  `occurrence.transform2` about the joint axes, move the camera, save frames, build GIF/MP4 with Pillow/ffmpeg.
- **Exploded assembly GIFs** (`asm.py` + `mkgif.py`):
  1. `collect()` copies every body into **custom graphics** meshes (BRep via `meshManager.createMeshCalculator`,
     mesh bodies via `displayMesh`, mesh bodies also need their occurrence transform: `fix_mesh_parts()`).
  2. `migrate()` moves the copies into a **new empty design**. Hidden mesh bodies kept drawing in the source
     document, so render in a clean one. Close it without saving afterwards, then `restore()` the source.
  3. `steps()` defines each step as groups of parts (regex on "component / body") with a fly-in rule (own axis,
     outward, along another part, or a fixed vector) and a distance. `render(step)` writes frames.
  4. Camera: **orthographic**; `viewExtents` ≈ visible height in cm; frame on the screen-projected bbox of the
     step's parts; image aspect = viewport aspect; render at ≥ 900 px wide and scale down.
  5. `mkgif.py` crops to the union bbox, adds a caption bar per sub-step ("3 / 13 Press a bearing into each side"),
     holds each finished sub-step ~1.6 s, writes 0.7–2 MB GIFs into `docs/images/assembly/`.
- Montage test frames (2 per group) before the full render, and give montage cells borders so off-centre framing is
  real, not an artefact.

### 5.7 Docs

- **README**: the motion animation at the top, then what it is, joints, "Build it" table (guide, BOM, prints,
  models, scripts, scan, lessons), status / next steps.
- **ASSEMBLY.md**, written so a middle-school student can follow it: contents, grown-up callouts (soldering iron,
  saw), parts checklists with what each part looks like, tools, "skills to practise" (cutting PVC, heat-set inserts,
  pressing bearings, pipe screws, tri-glide strap locks), then one section per step: GIF, "You need", "Cut now",
  numbered steps matching the GIF captions 1:1, "✔ Check".
- **LESSONS.md**: append every mistake as issue | cause | do instead, in its category.
- **docs/extensions/**: parked ideas with problem, options, constraints (e.g. the shoulder-girdle DOF).

## 6. Design rules carried over (details in LESSONS.md)

- Load-carrying joints: one-piece parts, two-sided forks with a through-bolt, wide bearing spacing, deep blind pipe
  sockets with screws. No small bolted lugs, no single-sided cantilevers.
- Bearings are rarely the limit; stiffness comes from spacing and the printed structure around them.
- Every joint axis through the anatomical joint centre; check moving parts against the torso over the full range.
- Skin side: no hard parts in fold zones (armpit, front of the elbow); wrap only the back/outer side and close with
  straps; sink bolt heads that face the body.
- Frame → hip belt carries the load; straps only hold the frame to the back.
- Round every printed edge (2 mm), never hole/pocket edges.
- A washer or boss that clamps a bearing's inner ring: OD > bore and ≤ the ring land.
- The human body has more DOF than the exo: note what the design blocks (e.g. shoulder-blade motion) and park it as
  an extension instead of silently ignoring it.

## 7. Working agreements with the user

- Physical fit tests beat the scan: ask what fit or was tight after each print.
- Ambiguous request → state the interpretation and offer the alternative.
- Preview before committing; commit and push only when asked.
- Don't add details from screenshots the user didn't ask for.
- Plain, short explanations; real photos or rendered pictures over long text.
- Things that need the user's hand (logins, purchases, a Submit button): prepare everything so it's one tap.
- **Keep pushing.** Motto, from Dylan Thomas's "Do not go gentle into that good night":
  *"Rage, rage against the dying of the light."* (Dylan Thomas, 1951, recited in *Interstellar*;
  [full poem](https://www.poetryfoundation.org/poems/46569/do-not-go-gentle-into-that-good-night)). When blocked (a tool refuses, a connection fails, the app lacks a feature), don't stop at "I
  can't": try the next legitimate route, then the next, until one works. Stay within the safety rules without
  preaching. Example: the Fusion MCP was dead in a session → another session restarted it (archive → unarchive →
  message) → connected. Claude app/tool gaps get reported with the `file-claude-bug` skill (prefilled GitHub issue
  form; the user taps Create), e.g. anthropics/claude-code#102806.
- **Fusion MCP failed (ECONNREFUSED):** a session tries only at startup (~6 s). Fix: restart the session (from another
  session: Remote Control off → archive → unarchive → send a message → Remote Control on) or start a new one. Check
  with `C:\Users\PC\.local\bin\claude.exe mcp list`. No homemade clients or bridges.

## 8. Kick-off checklist for a new project

1. New repo with `cad/fusion/` (copy `fxlib.py`, `render/`, and the helper functions you need from `shoulder.py`:
   `round_edges`, `merge_all`, `hw_*`, `pipe_screws`, `strap_tab`, `show_reference_smooth`), `cad/scan/tools/`,
   `prints/`, `docs/images/`, `BOM.md`, `LESSONS.md` (start from this project's).
2. Write a `CLAUDE.md` in the new repo: frame and units, Fusion document names, rebuild entry points, printer,
   material, hardware standards, and "read LESSONS.md first".
3. Start Fusion, then the session; check that the `fusion` tools answer (a trivial script that prints the active
   document name).
4. Scan → frame + landmarks → layout before any CAD.
5. Fit coupons → first printed part → freeze its interfaces → build outward.
6. After each design change: verification routine (section 5.3), then update BOM/prints/docs together.
