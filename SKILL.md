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

## 3. Ship gates

Three gates. The third is the one people skip, and it is the one being judged.

| Gate | Act | Fails on |
| --- | --- | --- |
| **Format** | `python scripts/check_single_file.py game.html --strict` | external references, network calls, missing `id`s, missing `<title>`/viewport, no error boundary |
| **Craft** (3D) | same command `--strict --craft` | bare primitives as final assets, RGB-only palettes, untextured surfaces, bones without skinning |
| **Frame** | score §1's six axes, then walk `references/release-checklist.md` | a frame that reads as a prototype |

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
**atmosphere** (height fog, then volumetrics) → **post** (HDR → bloom → ACES → grade → sRGB
encode, and check the encode before touching exposure).

Numbers and the failure each step prevents: `references/cinematic-look.md`,
`references/material-authoring.md`.

### Step 5 — Make it feel alive

Cheap, high-yield, in this order: a 2–4 px shake on impact, a short particle burst on every state
change, a 120 ms scale-pop on the thing you hit, a vignette, a two-note audio tick on every
action, idle breathing on anything alive. Two feedback channels per state change —
`references/game-feel.md` is the table.

### Step 6 — Persist and resume

Progress, best score and settings are separate versioned keys, every storage call in `try/catch`
(private mode throws), and a corrupt save never blocks boot — see
`references/state-and-persistence.md`.

### Step 7 — Audit, then hand off

Run the gates in §3, walk the release checklist, and report the six-axis score. See §8.

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

## 8. Handing off

Report the file path and size, what was verified (audit output **including the `--craft` result**,
devices and frame budget observed), the **six-axis score with the weakest axis named**, and the
one thing to build next. Say explicitly that the player only needs the single file.
