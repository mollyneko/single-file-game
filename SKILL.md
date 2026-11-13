---
name: single-file-game
description: Build a complete, playable browser game as one self-contained HTML file with zero external assets, where art, audio, maps and 3D content are generated procedurally at runtime. Defaults to 3D at AAA fidelity — perspective camera, inline WebGL engine, PBR materials, shadows, height fog, reflections — and drops to 2D only when the request asks for it. Use when asked to make a game, prototype, jam entry, demo or interactive toy that must run by double-clicking a single file, work offline, or ship without build tools, CDNs or an asset pipeline.
license: MIT
---

# Single-File Game

A game you can email. One `.html`, opened from `file://`, no server, no network, no `assets/`.

The constraint is the point: no asset pipeline means no 404s; no dependency graph means the
artifact *is* the deliverable; procedural content means one file holds a large world at a small
byte cost; offline by default means it runs on a plane, in a classroom, on a USB stick.

## 0. Default target: 3D, at AAA fidelity

**Unless the request says otherwise, build a 3D game.** "Make me a game", "make an open world",
"make something like Genshin / a shooter / a driving game" are 3D briefs. A single-file 3D game
with an inline engine is the normal output of this skill, not the ambitious variant of it.

- **Inline an engine and use it.** 0.8–1.4 MB of minified WebGL library inside the `<script>` is
  expected and free of charge: it is still one file, and it buys PBR, IBL, shadow maps, skinning
  and curve geometry. Hand-writing a renderer is justified only when the asset layer is already
  complete — if the render pipeline is larger than the asset layer, the budget is inverted.
- **2D is opt-in.** Choose it only when the request names it (2D, top-down, pixel, platformer,
  card, board, text, puzzle, "like Vampire Survivors") or when the loop genuinely loses clarity in
  perspective. Then write the reason in one line before the first draw call.
- **"One file" never justifies** a fixed top-down zoom, flat ambient light, untextured boxes, a
  hand-written renderer instead of an inline engine, or 2D because 3D is harder. Those five are
  how this skill gets ignored.
- **AAA here means a frame that survives inspection plus a loop that closes**, not content
  volume. A 200 KB file can read as AAA; a 3 MB file of half-built features cannot. When time is
  short, cut breadth — never one of the six axes in §1.
- Scope still applies. 3D does not mean more mechanics: one loop, one verb, one failure state,
  one restart. Density, not breadth.

## 1. Why a frame reads as AAA: six axes

A frame is judged in ten seconds, on these six axes — not on feature count. Score the build
honestly: **fewer than five of six at the floor means it is a prototype, whatever the feature
list says.** Details and numbers live in the linked reference.

The evidence is not taste. A finished single-file 3D game was compared against a 2D canvas game of
comparable ambition, and the gap was not content volume — it was these axes: a perspective camera
against a fixed top-down zoom, a computed sun against painted shading, 130 named materials with
generated maps against flat fills, planar reflections against a gradient, container inspection
plates against unlabelled boxes, 1.4 MB of engine and assets against 190 KB of game systems. A
second teardown, this time of two 3D games, put the same gap in the asset layer: both had a
complete post chain, and only one had geometry, materials and skinning worth grading.

| # | Axis | Floor at ship | Prototype tell | Detail |
| --- | --- | --- | --- | --- |
| 1 | **Space** | Perspective camera inside the scene, FOV 60–75, eye height 1.2–2.0 m, horizon in frame, three depth layers (foreground occluder / subject / far plane), parallax under movement | Orthographic or fixed-zoom top-down, 70% of the frame is ground, no occlusion, no parallax | `references/procedural-3d.md` |
| 2 | **Light** | One directional key at 10–20° elevation, ≥1024² shadow map with PCF, contact AO, height fog; ambient, fog and rim all derived from the same sun vector | Flat ambient plus brightness painted into albedo; object shadows are ellipses drawn under feet | `references/cinematic-look.md` |
| 3 | **Material** | ≥12 named materials, five channels (albedo, roughness, metal, height, AO), generated wear and seams, triplanar terrain | One RGB triple per object; zero roughness variance, so everything reads as plastic | `references/material-authoring.md` |
| 4 | **Reflection** | Environment/IBL sampled from `skyColor()`, planar reflection on water and wet ground, Fresnel boost at grazing angles, reflected horizon = seen horizon | No reflection at all; water is a flat gradient; specular is a white blob | `references/cinematic-look.md` |
| 5 | **World detail** | Surfaces carry information nobody will read: plate numbers, inspection dates, hazard markings, maintenance tags, decals, debris, a clutter density that rises toward the play area | Abstract symbols only — a tree is three colour blobs, a crate is a brown box, no text anywhere | `references/asset-craft.md` |
| 6 | **Budget** | Bytes go to assets, not to re-inventing the engine; bake once, instance repeats, ≤2 ms post at 1080p, 60 fps on integrated graphics | Per-frame geometry rebuild; post stack larger than the scene; multi-MB file with no stated reason | `references/performance.md` |

Axis 1 is the one you cannot recover from later: a 2.5D frame with a top-tier material system
still reads as a map, not a place. Axis 5 is the cheapest and most skipped — it is what makes a
level feel like a location. Axes 2–4 are what make objects look like matter instead of stickers.

## 2. Format rules

Non-negotiable. Violating one breaks the format.

1. **One file.** All CSS in one `<style>`, all JS in one `<script>` IIFE. No `<link href>`, no
   `<script src>`, no `fetch`, no `import`, no web fonts. An inline minified engine is intended.
2. **Zero network at runtime.** Works with the network disabled. No telemetry, no analytics.
3. **Art and audio are generated.** Canvas, SVG, CSS gradients or shader-generated textures;
   WebAudio oscillators plus one shared noise buffer. Bake expensive art once into an offscreen
   buffer, then blit.
4. **Deterministic where it matters.** Seeded PRNG for maps, palettes, spawn tables and object
   specs, so a seed reproduces a run; `Math.random()` only for cosmetic jitter.
5. **Failure is visible.** A global error handler paints a readable banner and keeps the page
   inspectable. Never ship a silent black screen.
6. **Input parity from commit one.** Keyboard, pointer, touch and gamepad resolve into one intent
   object. Mobile is not a later milestone.

## 2A. Three hard constraints (MUST)

These outrank scope, taste and time. A build missing one is not shippable, however good the
rest of it is. They are machine-checked where possible (`--craft`) and always checked on screen.

### A. Visual self-review, with a repair loop — not a score written at the end

Once the build first renders, run **at least two review rounds**. Each round is:

1. **Capture real frames.** Headless-browser screenshots of the title, a gameplay wide shot,
   a **zoomed crop of the playable character** (full-frame shots hide broken rigs), and the
   most expensive effect in the scene (water / sunset / boss). Never review from source or
   memory.
2. **Score in writing** the six axes in §1 **plus** the three review axes in
   `references/visual-self-review.md`: beauty/composition, structural plausibility, UI
   readability. Below-floor is a defect, not a taste difference.
3. **Repair every defect**, worst first, then **re-capture the same shots** and compare. A fix
   without a re-shot is an unverified claim.
4. Record rounds, scores, fixes and re-shot evidence in the handoff and in the `SELF-REVIEW`
   marker the auditor looks for.

**Structural plausibility is a hard gate.** A humanoid must read as one connected body at rest
*and through every animation*: shoulders joined to the torso, upper arm → elbow → forearm →
wrist → hand continuous, hips → thigh → knee → shin → ankle → foot continuous, head joined to
the neck. No floating hands, detached sleeves, gaps that open when a bone rotates, or limbs
clipping through cape and weapon. Verify on a zoomed idle frame **and** an animated frame
(walk / attack / jump). The classic cause in this skill's own output: bone transforms authored
as *absolute* positions in a hierarchy that expects *parent-relative* offsets — the bind pose
looks right, then the first rotation throws the arm metres away. Rig checklist and repair
recipes: `references/visual-self-review.md`.

"Looks fine" is not evidence. A screenshot, a score and a re-shot are.

### B. SSAO and volumetrics are mandatory in every 3D scene

A 3D deliverable MUST ship both, not one, not a lookalike:

- **SSAO** rebuilt from scene depth (normals from neighbouring depth samples is fine),
  hemisphere sampling, depth-aware blur, applied to **ambient/indirect radiance only** — never
  by multiplying the whole frame. Half resolution is fine; switching it off on the low tier
  is fine.
- **Volumetric light** as depth-aware **ray marching**, not a radial blur of the bright buffer.
  The march terminates at scene depth, integrates density along the view ray, weights by a
  phase function, and tests the sun's shadow map so geometry actually blocks shafts. Output
  scatter + transmittance, composite as `col * T + scatter`.

A radial "god ray" streak is **not** volumetrics. Vertex AO or a painted contact shadow is
**not** SSAO. Order is `shadow → HDR scene → volumetrics → AO → bloom → tone map → grade →
encode` (`references/cinematic-look.md`). `--craft` fails without both signals.

### C. Mouse look is free-look by default

Moving the mouse MUST turn the camera immediately, with no button held: the
`mousemove`/`pointermove` handler writes `look.dx/dy` unconditionally over the canvas.
**Drag-to-look is opt-in** — use it only when the user explicitly asks for drag controls, and
mark that file with `DRAG_LOOK_OPT_IN`. Pointer lock is an optional enhancement (a click may
capture the pointer for infinite travel); it must never be the only way to look around, and
play must never wait for a click before the camera responds. Touch still drags on the right
half of the screen — different device, different rule. See `references/input-and-mobile.md`.

## 3. Ship gates

Four gates. The last two are the ones people skip, and they are the ones being judged.

| Gate | Act | Fails on |
| --- | --- | --- |
| **Format** | `python scripts/check_single_file.py game.html --strict` | external references, network calls, missing `id`s, missing `<title>`/viewport, no error boundary |
| **Craft** (3D) | same command `--strict --craft` | bare primitives as final assets, RGB-only palettes, untextured surfaces, bones without skinning |
| **Hard constraints** (3D) | same `--strict --craft` run, plus screenshot evidence | missing SSAO, missing depth-aware volumetrics, drag-gated mouse look, no recorded self-review |
| **Frame** | score §1's six axes **and** §2A's three review axes, then walk `references/release-checklist.md` | a frame that reads as a prototype, a disconnected limb, or a camera that needs a drag |

The craft gate in six lines, for 3D deliverables (starters exempt; a shipped file is not). The
bundled `assets/starter-3d.html` reports `2/4` — it is a shell, and its asset layer is your first
task:

1. Inline engine, not a reimplementation.
2. No bare primitive is a finished asset — every visible object passes through a bevel, a curved
   surface (lathe / tube / extrude / spline), per-vertex displacement, or a generated texture.
3. Bevel hard edges ≥0.02 world units, recompute normals after generating geometry, weld lathe
   seam-ring normals.
4. ≥12 named materials with generated maps, looked up by name — not raw colours passed to a draw
   call. Ship a roughness × metalness calibration row and look at it before tuning exposure.
5. Animated characters are one weighted skinned mesh, never one primitive per bone.
6. Seeded, table-driven builders: object specs in a table, a builder with a named seed RNG and a
   transform stack.

`references/asset-craft.md` holds the evidence, the `--craft` signal groups and the catch-up
order.

The same `--craft` run also enforces §2A. It reports `3D hard constraints: n/4` — SSAO,
depth-aware volumetrics, free-look mouse, and a `SELF-REVIEW` record with ≥2 rounds. The
auditor checks signals, not beauty: the screenshots and the written score remain mandatory and
are what the handoff is judged on. A file that passes the auditor with a detached hand has
simply lied to it.

## 4. Workflow

### Step 1 — Scope in one sentence, then pick the mode

Write it before the code: *"You move a craft, collect drifting orbs, avoid shards, the run ends
on contact."* If it needs two sentences, cut a mechanic.

Default: **3D (WebGL2)** — space, driving, FPS/TPS, open field, atmospheric scene. **2D canvas**
only per §0, then read `references/procedural-art-2d.md`.

### Step 2 — Scaffold the shell

```bash
python scripts/scaffold.py --name "Night Shift" --mode 3d --out ./night-shift.html
python scripts/scaffold.py --name "Orb Runner" --mode 2d --out ./orb-runner.html
```

The scaffold already contains the shell (`references/architecture.md`): design tokens, boot
screen, title layer, canvas, HUD, pause and game-over cards, input layer, audio bus, save bus,
error boundary, adaptive quality, and a marked `GAME` block. Keep the shell, replace the rules.

### Step 3 — Systems before content, in dependency order

Loop + resize + DPR + colour pipeline → input intent → scene machine
(`boot → title → play → paused → over`) → art primitives → entities and collision → audio and
HUD feedback → content (waves, levels, tables, dialogue). Each layer must be observable before
the next is written. A one-line debug HUD (`scene`, `fps`, `entities`, `errors`) after step one
saves hours by step six (`references/resilience-and-a11y.md`).

### Step 4 — Light it like a shot, not a test scene

One pass, in this order: **composition** (one foreground object, one subject, a skyline gap where
the sun sets) → **key light** (pick the direction, derive ambient, fog and rim from it) →
**materials** (five channels, wear in primer → oxide order, seams at a plate size) →
**atmosphere** (height fog, **depth-aware volumetric ray march**, then **SSAO from scene
depth**) → **post** (HDR → bloom → ACES → grade → sRGB encode, and check the encode before
touching exposure). Both atmosphere passes are §2A hard constraints, not polish: build them
here, in the pipeline, before any content. A depth texture on the scene target is the first
thing to wire.

Numbers and the failure each step prevents: `references/cinematic-look.md`,
`references/material-authoring.md`. Wire mouse free-look (`§2A.C`) in Step 3's input layer,
not as a late fix.

### Step 5 — Make it feel alive

Cheap, high-yield, in this order: a 2–4 px shake on impact, a short particle burst on every state
change, a 120 ms scale-pop on the thing you hit, a vignette, a two-note audio tick on every
action, idle breathing on anything alive. Two feedback channels per state change —
`references/game-feel.md` is the table.

### Step 6 — Persist and resume

Progress, best score and settings are separate versioned keys, every storage call in `try/catch`
(private mode throws), and a corrupt save never blocks boot — see
`references/state-and-persistence.md`.

### Step 7 — Self-review, repair, re-shoot, then audit

Content is done, the build is not. Run §2A.A's loop **at least twice**: capture title,
gameplay, character close-up and hero-effect shots; score all nine axes in writing; repair
every below-floor item (structural plausibility first — a detached hand outranks a colour
grade); re-capture the same shots. Only then run the gates in §3
(`--strict --craft`), walk the release checklist, and report the nine-axis score, the review
rounds and the fixes with before/after evidence. See §8 and
`references/visual-self-review.md`.

## 5. What goes where

```
<style>   tokens → reset → layout → HUD → screens → panels → responsive → reduced-motion
<body>    canvas → HUD layer → screen layers → toast → fatal banner → debug node
<script>  helpers → storage → audio → input → renderer → materials → assets → entities → scenes → loop → boot
```

One IIFE, small modules as plain functions and object literals, ordered so nothing is referenced
before definition. No classes unless state is genuinely per-instance.

## 6. Index

| Path | Read it when |
| --- | --- |
| `references/architecture.md` | You need the shell, the scene machine or the loop contract |
| `references/procedural-3d.md` | WebGL2 setup, camera, generated textures, quality tiers, fallback |
| `references/cinematic-look.md` | Sun, sky, shadows, volumetrics, AO, bloom, tone map, grade, the ten-second test |
| `references/material-authoring.md` | PBR channels, height → normal, wear, seams, triplanar, water, baking |
| `references/asset-craft.md` | The craft gate: teardown evidence, six constraints, `--craft` signals, catch-up order |
| `references/procedural-art-2d.md` | 2D only: seeded palettes, shape primitives, tile baking, effects |
| `references/game-feel.md` | Hitstop, shake, easing, particles, audio layering, HUD motion |
| `references/procedural-audio.md` | Any sound: SFX table, noise, step-sequenced music, mixing |
| `references/input-and-mobile.md` | Touch, pointer lock fallback, gamepad, safe areas |
| `references/state-and-persistence.md` | Saves, settings, migration, autosave |
| `references/performance.md` | Frame budget, baking, pooling, instancing, adaptive quality |
| `references/resilience-and-a11y.md` | Error boundary, degradation ladder, reduced motion, contrast |
| `references/design-language.md` | Tokens, HUD composition, buttons, type scale |
| `references/visual-self-review.md` | The mandatory shot → score → repair → re-shoot loop, the limb-connection checklist, defect recipes, report template |
| `references/release-checklist.md` | The final pass; the ship gate, not a suggestion |
| `assets/starter-3d.html` | Runnable WebGL2 slice: HDR, shadows, volumetrics, SSAO, bloom, ACES, playable |
| `assets/starter-2d.html` | Runnable canvas shell, playable, juice included |
| `scripts/scaffold.py` | Generate a named game from either shell |
| `scripts/check_single_file.py` | Format audit; `--strict` and `--craft` are the gates |
| `docs/method.md` | Why the constraints exist, and when not to use this method |

## 7. Anti-patterns

- **Shipping 2D because 3D is harder.** The unstated default is 3D. 2D has to be asked for or
  argued for, never fallen into.
- **Loading a CDN "just for the prototype."** The prototype is the deliverable; a CDN turns a
  one-file game into a two-file game with a dependency on someone else's uptime.
- **Writing a renderer to avoid an inline engine.** Zero runtime requests is the rule; a 1.4 MB
  inline library is still one file.
- **Untextured boxes under a flat ambient.** The fastest way to look like a placeholder — and
  with `--craft`, a failing audit rather than just a bad eye test.
- **An RGB triple as a material.** Albedo is one channel; no roughness, wear or seam means no
  scale.
- **One primitive per bone.** Widening the parts to hide joint gaps produces beads on a string.
- **Writing gameplay before the loop and the resize handler.** Every later bug becomes a layout
  bug.
- **One giant `draw()` with gameplay inside it.** Separate simulation from presentation, or
  pausing, restarting and testing become impossible.
- **Random palettes at draw time.** Derive colours once from a seed and store them.
- **`localStorage` without `try/catch`.** Private mode and quota errors throw, and an unguarded
  call kills boot.
- **Shipping without a restart path.** A game that ends in a dead screen is a demo.
- **Writing linear radiance into the canvas.** Two lines of transfer function stand between
  "night" and "dusk".
- **Tuning exposure or bloom to fix a lighting or modelling problem.** If the ground needs
  exposure 2.0, the sun is too low or the albedo is too dark; a bevel does what a bloom pass
  cannot.
- **Grading a frame that has no SSAO and no volumetrics.** A radial bright-pass streak is a
  lens effect; it does not put air between the camera and the far plane, and it cannot be
  occluded by a pillar. This is a §2A failure, not a missing nice-to-have.
- **Requiring a drag (or a click to capture the pointer) before the camera moves.** The
  player moves the mouse and nothing happens until they discover an undocumented gesture.
  Free-look is the default; drag is opt-in.
- **Writing a self-review score without screenshots, or claiming a fix without a re-shot.**
  Code is not evidence. The rig that looks connected in the bind pose can throw a hand three
  metres away on the first attack animation.
- **Absolute bone positions in a parent-relative hierarchy.** Skeleton nodes store offsets
  from their parent; authoring them as world coordinates produces a correct-looking bind pose
  and a disintegrating character as soon as anything animates.

## 8. Handing off

Report the file path and size, what was verified (audit output **including the `--craft` result
and the `3D hard constraints: 4/4` line**, devices and frame budget observed), the **six-axis
score plus the three review axes with the weakest axis named**, the **self-review rounds and
the before/after fixes** (including the character close-up), confirmation that SSAO and
depth-aware volumetrics are in the shipped pipeline and that mouse look needs no drag, and the
one thing to build next. Say explicitly that the player only needs the single file.
