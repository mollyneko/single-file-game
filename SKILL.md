---
name: single-file-game
description: Build a complete, playable browser game as one self-contained HTML file with zero external assets, where art, audio, maps and 3D content are generated procedurally at runtime. Defaults to 3D at AAA fidelity: a minified three.js build is always inlined, and every 3D model is produced by the vendored img2threejs pipeline (reference image to quality-gated procedural THREE.Group factory) — never hand-assembled primitives. Perspective camera, PBR materials, shadows, SSAO, depth-aware volumetrics, height fog, free-look mouse. Drops to 2D only when the request asks for it. Use when asked to make a game, prototype, jam entry, demo or interactive toy that must run by double-clicking a single file, work offline, or ship without build tools, CDNs or an asset pipeline.
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

- **Inline three.js — mandatory, not a preference.** Every 3D file produced by this skill pastes
  a minified three.js build (global `window.THREE`, MIT) inside the `<script>`: 0.6–1.4 MB is
  expected and free of charge, and it buys PBR, IBL, shadow maps, skinning and curve geometry.
  Hand-written WebGL renderers are **not permitted in deliverables**; the bundled
  `assets/starter-3d.html` is a raw-WebGL2 shell kept only as a post-chain reference. The
  auditor fails a 3D deliverable that carries no `THREE` markers.
- **Every model comes from the img2threejs pipeline.** This skill vendors
  [img2threejs](https://github.com/img2threejs/img2threejs) (Apache-2.0) at `img2threejs/`,
  entry `img2threejs/PIPELINE.md`. Modeling is: reference image → staged sculpt
  (blockout → structural → form → material → surface → lighting → interaction → optimization),
  each stage visually reviewed before the next unlocks → a quality-gated `createObjectModel`
  factory emitting a rigged, animation-ready `THREE.Group` with named materials. Hand-assembling
  boxes and capsules into characters, or any ad-hoc primitive stack, is not modeling and fails
  the audit. The pipeline's own gates (strict-quality spec, per-pass review) are this skill's
  geometry and material craft gate. Each model must also leave a `PIPELINE-RECEIPT` marker in
  the shipped HTML (spec, seed, factory, reviewed passes); `--craft` fails a 3D deliverable
  without one, and fails a receipt whose factory is never called in the game source.
- **Generated reference images: transparent background, one style.** When the image fed to
  img2threejs is generated rather than hand-picked, it MUST be a transparent PNG — no baked
  backdrop, no floor, no drop shadow — and the whole reference set MUST share one style: same
  palette, lighting direction and rendering treatment, produced in one session from one style
  anchor. A baked background corrupts the silhouette trace; a mixed-style set fails review
  even when each image alone looks fine. Both rules are machine-checked at intake
  (`check_reference_admission.py --generated`, `check_style_coherence.py`).
- **2D is opt-in.** Choose it only when the request names it (2D, top-down, pixel, platformer,
  card, board, text, puzzle, "like Vampire Survivors") or when the loop genuinely loses clarity in
  perspective. Then write the reason in one line before the first draw call.
- **"One file" never justifies** a fixed top-down zoom, flat ambient light, untextured boxes, a
  hand-written renderer (§0: three.js is mandatory), or 2D because 3D is harder. Those five are
  how this skill gets ignored.
- **AAA here means a frame that survives inspection plus a loop that closes**, not content
  volume. A 200 KB file can read as AAA; a 3 MB file of half-built features cannot. When time is
  short, cut breadth — never one of the six ship axes in §1.
- Scope still applies. 3D does not mean more mechanics: one loop, one verb, one failure state,
  one restart. Density, not breadth.

## 1. Why a frame reads as AAA: six axes

A frame is judged in ten seconds, on six ship axes — not on feature count.

**This section is an index.** `references/scoring-rubric.md` is the only definition of the nine
axes, their 1–5 bands, the ship floor and the scoring rules — including the three review axes
added during self-review. Score against that file; do not invent a second set of thresholds here.
Implementation detail stays in the references linked below.

The evidence is not taste. A finished single-file 3D game was compared against a 2D canvas game of
comparable ambition, and the gap was not content volume — it was these axes: a perspective camera
against a fixed top-down zoom, a computed sun against painted shading, 130 named materials with
generated maps against flat fills, planar reflections against a gradient, container inspection
plates against unlabelled boxes, 1.4 MB of engine and assets against 190 KB of game systems. A
second teardown, this time of two 3D games, put the same gap in the asset layer: both had a
complete post chain, and only one had geometry, materials and skinning worth grading.

| # | Ship axis | One-line read | Implementation |
| --- | --- | --- | --- |
| 1 | **Space** | Perspective camera inside the scene, three depth layers, parallax | `references/procedural-3d.md` |
| 2 | **Light** | One sun, real shadows, contact AO, height fog | `references/cinematic-look.md` |
| 3 | **Material** | Named PBR channels, generated wear and seams | `references/material-authoring.md` |
| 4 | **Reflection** | IBL and planar water agree with the sky | `references/cinematic-look.md` |
| 5 | **World detail** | Plates, decals, debris, density rising toward play | `references/asset-craft.md` |
| 6 | **Budget** | Bake once, instance repeats, 60 fps on integrated graphics | `references/performance.md` |

Axis 1 is the one you cannot recover from later: a 2.5D frame with a top-tier material system
still reads as a map, not a place. Axis 5 is the cheapest and most skipped — it is what makes a
level feel like a location. Axes 2–4 are what make objects look like matter instead of stickers.
Three further axes — beauty / composition, structural plausibility, UI readability — are scored
on screenshots during self-review, not here. All nine, with their 1–5 bands, live in
`references/scoring-rubric.md`.

## 2. Format rules

Non-negotiable. Violating one breaks the format.

1. **One file.** All CSS in one `<style>`, all JS in one `<script>` IIFE. No `<link href>`, no
   `<script src>`, no `fetch`, no `import`, no web fonts. An inline minified three.js build is
   intended — and mandatory in every 3D deliverable (§0).
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
2. **Score in writing** all nine axes against `references/scoring-rubric.md` — the six ship
   axes in §1 plus beauty/composition, structural plausibility and UI readability. That file
   owns the 1–5 bands and the floor; below-floor is a defect, not a taste difference.
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
| **Craft** (3D) | same command `--strict --craft` | no `PIPELINE-RECEIPT` (or a receipt with unreviewed passes / an uncalled factory), bare primitives as final assets, RGB-only palettes, untextured surfaces, bones without skinning |
| **Hard constraints** (3D) | same `--strict --craft` run, plus screenshot evidence | missing SSAO, missing depth-aware volumetrics, drag-gated mouse look, no recorded self-review |
| **Frame** | score all nine axes in `references/scoring-rubric.md`, then walk `references/release-checklist.md` | a frame that reads as a prototype, a disconnected limb, or a camera that needs a drag |

The craft gate for a 3D deliverable is two sentences:

1. **three.js is inlined and the models are not hand-made.** A deliverable carries a minified
   three.js build (`window.THREE`) and one `PIPELINE-RECEIPT` per model: sculpt spec path, spec
   seed, factory name and the staged pass reviews recorded with `append_review.py` (Step 3).
   The auditor fails a 3D deliverable with no `THREE` markers or no valid receipt; scaffold
   shells (a kept `GAME (replace this block)` marker) are reported as shells rather than failed.
2. **The pipeline's own quality gates were run.** Strict-quality spec validation before any
   code, plus the staged visual review passes, are what "geometry craft" and "material
   library" mean here. `references/asset-craft.md` keeps the teardown evidence behind the
   auditor's four signal groups; those signals describe the resulting asset layer, they are
   not an alternative modeling route — a hand-built file can reach `4/4` there and still fail
   the receipt gate.

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

**The 3D scaffold is a shell, not a modeling path.** It ships a raw-WebGL2 post chain for
reference; it is not the renderer and not where models are written. Do **not** start filling the
`GAME` block until Step 3 has produced the factories and Step 4 has inlined three.js. Writing
gameplay into that block first is exactly how a build ends up hand-assembled.

### Step 3 — Build the models with img2threejs

3D modeling in this skill is the vendored pipeline, never hand-authored geometry
(`img2threejs/PIPELINE.md`; Apache-2.0, vendored at `img2threejs/`). Run the commands from the
repository root; keep one working directory per model. `PIPELINE.md` is the authority for the
full gate list — the chain below is its executable spine, verified against the vendored scripts.

**A reference image is required, one per model.** If the brief supplies none, ask for one or
generate them before anything else; "no image, so I'll just build primitives" is not a fallback,
it is a failed run. Generated images are hard-gated at intake:

- **Transparent background.** PNG with a real alpha channel; no baked backdrop, no floor, no
  drop shadow. Stage 1 traces silhouettes to build the sculpt — a background becomes phantom
  geometry that every later stage has to fight. `check_reference_admission.py --generated`
  rejects an opaque or partly cut-out image and prints why (α ≥ 4%, each corner ≥ 90% transparent).
- **One style for the whole set.** Every reference in the game shares one palette, lighting
  direction and rendering treatment: generate them in one session from one style anchor (a fixed
  prompt suffix, a seed family, or an explicit style sheet). The palette and luminance half is
  machine-checked against the anchor — the first admitted reference — by
  `check_style_coherence.py` (histogram cosine ≥ 0.80, mean luma delta ≤ 40); lighting direction
  and line treatment stay with the staged visual review.

```bash
REF=refs/hero.png
OUT=models/hero
SPEC="$OUT/object-sculpt-spec.json"
STATE="$OUT/.img2threejs/state.json"

# 0. Intake gates (generated references only). Run once per image; the second
#    command compares every other reference against the style anchor.
python img2threejs/forge/stage1_intake/check_reference_admission.py "$REF" --generated
python img2threejs/forge/stage1_intake/check_style_coherence.py "$REF" refs/prop.png

# 1. Local state is the checklist authority. `next.py` prints the current step
#    and the exact next command at every start, resume and correction iteration.
python img2threejs/forge/state.py init --state "$STATE" --reference "$REF" \
  --profile character --spec "$SPEC"          # use generic for props
python img2threejs/forge/next.py --state "$STATE"

# 2. Analyze the image with agent vision first (`PIPELINE.md` step 1), then probe
#    its technical metadata and author the pre-spec assessment.
python img2threejs/forge/stage1_intake/probe_image.py "$REF"
python img2threejs/forge/stage2_spec/new_pre_spec_assessment.py "Hero" \
  --image "$REF" --complexity complex --out "$OUT/assessment.json"

# 3. THIS is where spec.json comes from. The generator writes the starter spec;
#    fill in the real component hierarchy, detail inventory, PBR evidence,
#    lighting entries and identity-defining feature targets before validating.
python img2threejs/forge/stage2_spec/new_sculpt_spec.py "Hero" --image "$REF" \
  --assessment "$OUT/assessment.json" --domain character --out "$SPEC"
python img2threejs/forge/stage2_spec/validate_sculpt_spec.py "$SPEC"
python img2threejs/forge/stage2_spec/validate_sculpt_spec.py "$SPEC" --strict-quality  # must PASS
```

`--strict-quality` is the gate that stops a shallow spec. A stub spec fails with a numbered list
of concrete quality errors; fix those in the spec, do not patch code around them. The factory
generator is fail-closed — it writes nothing until strict quality passes.

```bash
# 4. Locked build passes. Generate only the currently unlocked pass; the default
#    order is blockout → structural-pass → form-refinement → material-pass →
#    surface-pass → lighting-pass → interaction-pass → optimization-pass.
python img2threejs/forge/stage3_build/orchestrate_passes.py status "$SPEC"
python img2threejs/forge/stage3_build/generate_threejs_factory.py "$SPEC" \
  --out "$OUT/createHeroModel.ts"

# 5. For EACH pass: browser render → deterministic gates (`PIPELINE.md` steps 7–9)
#    → comparison sheet → agent-vision decision → record the review → sync →
#    re-check the state machine. Example for the first pass:
python img2threejs/forge/stage4_review/make_comparison_sheet.py --reference "$REF" \
  --render shots/hero/blockout.png --out shots/hero/cmp.png --json
python img2threejs/forge/stage4_review/append_review.py "$SPEC" --pass-id blockout \
  --fidelity 0.88 --action continue --summary "silhouette matches" \
  --render-screenshot shots/hero/blockout.png \
  --map-stripped-render shots/hero/blockout-unlit.png \
  --comparison-image shots/hero/cmp.png --ai-vision-score 0.88 \
  --review-viewpoints-json '["thickness-axis","long-axis"]' --in-place
python img2threejs/forge/stage3_build/orchestrate_passes.py sync "$SPEC" --in-place
python img2threejs/forge/state.py mark render-capture --state "$STATE" \
  --evidence shots/hero/blockout.png
python img2threejs/forge/next.py --state "$STATE" "$SPEC"
```

`append_review.py` refuses `continue` without the evidence its pass requires (a render
screenshot, an unlit map-stripped render for blockout, and an AI-vision score at or above the
threshold). Exit code 3 or `status=stopped` from `next.py` is a hard stop: report the reason and
request input, never reconstruct progress from chat history.

**Adapt each factory for the single file:**

1. Strip the type annotations — the generated code is structurally plain JS.
2. Replace `import * as THREE from 'three'` and any `three/examples/jsm/*` imports with the
   inlined global `window.THREE` build; paste in the few jsm helpers the model actually uses.
   OrbitControls is rarely one of them — the game owns its camera.
3. Paste the factory into the `<script>` IIFE as a `models` module and **call it** from a spec
   table row. The factory is deterministic: record the spec seed beside the world seed.

**Write a `PIPELINE-RECEIPT` marker for every model, in the shipped HTML.** This is the audit
trail for §0's "models come from the pipeline" rule — `--craft` fails a 3D deliverable without
one. One HTML comment per model, with the sculpt spec path, state file, spec seed, the factory
name (which must actually be called in the game source), every reviewed pass with its render
screenshot, and the reference declarations:

```html
<!-- PIPELINE-RECEIPT {"pipeline":"img2threejs",
  "spec":"models/hero/object-sculpt-spec.json",
  "state":"models/hero/.img2threejs/state.json",
  "seed":"hero-7f3a91","factory":"createHeroModel",
  "passes":[
    {"id":"blockout","action":"continue","render":"shots/hero/blockout.png"},
    {"id":"structural-pass","action":"continue","render":"shots/hero/structural.png"},
    {"id":"form-refinement","action":"continue","render":"shots/hero/form.png"},
    {"id":"material-pass","action":"continue","render":"shots/hero/material.png"},
    {"id":"surface-pass","action":"continue","render":"shots/hero/surface.png"},
    {"id":"lighting-pass","action":"continue","render":"shots/hero/lighting.png"},
    {"id":"interaction-pass","action":"continue","render":"shots/hero/interaction.png"},
    {"id":"optimization-pass","action":"continue","render":"shots/hero/optimization.png"}],
  "references":[{"image":"refs/hero.png","generated":true,"transparent":true,
                 "styleAnchor":"refs/hero.png"}]} -->
```

The auditor requires ≥ 5 distinct passes, all `action: "continue"`, each with render evidence,
and `blockout` first. It also rejects a declared factory that never appears as a call in the
game's own source, and a generated reference that does not declare `transparent: true` plus a
style anchor. A scaffold shell (the `GAME` marker still present) is exempt; a deliverable is not.

The factory is code — its textures are generated inside it and its output is a rigged
`THREE.Group` with named materials and joints the game can pose. The screenshots, spec and
state file are **review evidence outside the HTML**, never runtime assets; the shipped file must
not reference them.

### Step 4 — Systems before content, in dependency order

Loop + resize + DPR + colour pipeline → input intent → scene machine
(`boot → title → play → paused → over`) → art primitives → entities and collision → audio and
HUD feedback → content (waves, levels, tables, dialogue). Each layer must be observable before
the next is written. A one-line debug HUD (`scene`, `fps`, `entities`, `errors`) after step one
saves hours by step six (`references/resilience-and-a11y.md`).

### Step 5 — Light it like a shot, not a test scene

One pass, in this order: **composition** (one foreground object, one subject, a skyline gap where
the sun sets) → **key light** (pick the direction, derive ambient, fog and rim from it) →
**materials** (five channels, wear in primer → oxide order, seams at a plate size) →
**atmosphere** (height fog, **depth-aware volumetric ray march**, then **SSAO from scene
depth**) → **post** (HDR → bloom → ACES → grade → sRGB encode, and check the encode before
touching exposure). Both atmosphere passes are §2A hard constraints, not polish: build them
here, in the pipeline, before any content. A depth texture on the scene target is the first
thing to wire.

Numbers and the failure each step prevents: `references/cinematic-look.md`,
`references/material-authoring.md`. Wire mouse free-look (`§2A.C`) in Step 4's input layer,
not as a late fix.

### Step 6 — Make it feel alive

Cheap, high-yield, in this order: a 2–4 px shake on impact, a short particle burst on every state
change, a 120 ms scale-pop on the thing you hit, a vignette, a two-note audio tick on every
action, idle breathing on anything alive. Two feedback channels per state change —
`references/game-feel.md` is the table.

### Step 7 — Persist and resume

Progress, best score and settings are separate versioned keys, every storage call in `try/catch`
(private mode throws), and a corrupt save never blocks boot — see
`references/state-and-persistence.md`.

### Step 8 — Self-review, repair, re-shoot, then audit

Content is done, the build is not. Run §2A.A's loop **at least twice**: capture title,
gameplay, character close-up and hero-effect shots; score all nine axes in writing against
`references/scoring-rubric.md`; repair every below-floor item (structural plausibility first —
a detached hand outranks a colour grade); re-capture the same shots. Only then run the gates in
§3 (`--strict --craft`), walk the release checklist, and report the nine-axis score, the review
rounds and the fixes with before/after evidence. See §8,
`references/scoring-rubric.md` and `references/visual-self-review.md`.

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
| `references/scoring-rubric.md` | **The nine axes and their 1–5 bands** — the only definition of the score and the ship floor; read before every self-review |
| `references/architecture.md` | You need the shell, the scene machine or the loop contract |
| `references/procedural-3d.md` | Inline three.js integration, camera, generated textures, quality tiers, fallback |
| `references/cinematic-look.md` | Sun, sky, shadows, volumetrics, AO, bloom, tone map, grade, the ten-second test |
| `references/material-authoring.md` | PBR channels, height → normal, wear, seams, triplanar, water, baking |
| `references/asset-craft.md` | Craft-gate rationale: teardown evidence behind the four `--craft` signal groups |
| `img2threejs/PIPELINE.md` | **The modeling pipeline**: stages, quality gates, review contracts, script reference (vendored, Apache-2.0) |
| `img2threejs/forge/` | The pipeline scripts: intake, spec validation, factory generation, staged review, rig |
| `THIRD_PARTY.md` | Provenance and license of the vendored img2threejs copy |
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
| `assets/starter-3d.html` | Raw-WebGL2 reference slice for the post chain (HDR, shadows, volumetrics, SSAO, bloom, ACES) — a shell, not the modeling path; 3D deliverables inline three.js and build models with img2threejs |
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
  inline three.js is still one file — and a 3D deliverable without `THREE` markers now fails
  the audit outright.
- **Hand-assembling characters from boxes and capsules.** Modeling is the img2threejs pipeline;
  an ad-hoc primitive stack is how rigs detach, materials collapse to RGB triples, and the
  receipt gate fails. `--craft` 4/4 on the four asset signals is not a modelling exemption.
- **Filling the scaffold's `GAME` block before Step 3 produced the factories.** The shell is
  raw-WebGL2 post-chain reference code; writing models into it is the shortcut that skips the
  pipeline entirely.
- **A reference image being missing, or the first pipeline command failing.** Ask for an image
  or generate a transparent one; read the error and fix the spec. Neither is a reason to fall
  back to hand-built geometry.
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
and the `3D hard constraints: 4/4` line**, devices and frame budget observed), confirmation that
three.js is inlined (version noted) and that every model carries a `PIPELINE-RECEIPT` from the
img2threejs pipeline (spec path, seed, factory and reviewed passes), the **nine-axis score** (`references/scoring-rubric.md`) with the weakest
axis named, the **self-review rounds and the before/after fixes** (including the character
close-up), confirmation that SSAO and depth-aware volumetrics are in the shipped pipeline and
that mouse look needs no drag, and the one thing to build next. Say explicitly that the player
only needs the single file.
