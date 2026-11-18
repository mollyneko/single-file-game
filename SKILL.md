---
name: single-file-game
description: Build a single-file offline HTML game with top-tier aesthetics, art direction and 3D programming — three.js as the skeleton, custom shaders as the fill — then verify it against a fixed nine-axis rubric, a deterministic capture protocol and machine gates. Use when building, judging or accepting a .html game deliverable.
license: MIT
---

# Single-File Game

This skill builds single-file HTML games and verifies the result. The target is a frame with
genuine visual impact, not a feature list. The verification system below is how you prove you
reached that target — it is the instrument, not the purpose.

## The prime directive (highest priority, overrides everything below)

> 充分发挥你最顶级的审美、艺术设计和3D编程能力，在构图、光影、材质、粒子、动画和空间氛围上做到极致。画面需要有令人震撼的视觉表现力。不限制你的创意和技术方案，尽可能展示你的能力上限。用three.js做骨架+自写着色器填充

> Give full play to your very best aesthetic sense, art direction and 3D programming ability; take
> composition, light and shadow, materials, particles, animation and spatial atmosphere to the
> extreme. The frame must have stunning visual impact. Do not limit your creative solutions or
> techniques; push your ability to its upper limit as far as possible. Use three.js as the skeleton
> and custom shaders as the fill.

This is the highest-priority constraint in this skill and overrides everything below. The
single-file boundary still applies: one `.html`, opened from `file://`, with no server, no network
and no external assets.

## 0. What is being built and judged

A single-file browser game: one `.html`, opened from `file://`, no server, no network, no external
assets. Build to the prime directive above; judge the artifact as delivered.

The unit of evidence is a **frame**, not a feature list, a line count or a self-report. Source
code is never evidence: a correct skeleton in source can produce a detached hand on screen, and
a pass on a regex gate says only that the work was attempted.

- Record the medium. The nine axes apply to 3D and 2D alike; 2D reads through the translation
  table in `references/scoring-rubric.md`. Floor 4 and the five-of-six rule do not move.
- If the brief asked for 3D and the deliverable is 2D, that is a **target mismatch** to report.
  It is a finding, not a licence to skip the rubric.
- A scaffold shell (a kept `GAME (replace this block)` marker) is not a deliverable. Report it as
  a shell; the gates are descriptive until the block is replaced.
- "AAA" here means a frame that survives a ten-second inspection plus a loop that closes — not
  content volume. A 200 KB file can qualify; a 3 MB file of half-built features cannot.

## 1. Build: the six-face craft loop

The prime directive is a build order, not a mood board. Work in this order and keep looping: every
step has to be visible in one of the four protocol frames (§3). A build is not done because it
compiles. For a deliberate 2D brief, read the same six surfaces through the translation table in
§4; the evidence and the floor do not move.

0. **Lock the shell and the visual thesis.** One `.html`, `file://`, inline `three.js` and custom
   GLSL; wire `?shot=` / `?prewarm=` / `?q=` / `?seed=` from the first run; add the error boundary,
   resize and DPR handling. Write one sentence naming the focal point, palette, light direction and
   mood. Every later choice serves it. A 3D brief answered with 2D is a mismatch to report, not a
   shortcut.
1. **构图 / composition.** Put a perspective camera inside the world, not above a flat board.
   Build three depth layers (foreground, subject, background), one focal point, leading lines and a
   value hierarchy. Frame `title`, `play`, `char-closeup` and `hero-effect` before adding detail —
   particles cannot rescue a shot with no composition.
2. **光影 / light & shadow.** One key light with a readable direction; real shadows, contact AO and
   SSAO from scene depth; depth-aware fog and volumetrics; one tone-mapping and grade. Feed the same
   sun, fog and shadow data into custom shaders so surfaces respond to the world instead of being
   painted on.
3. **材质 / material.** Name material families and generate their maps at runtime — albedo,
   roughness, metal, height, AO, seams and wear. Custom GLSL carries what stock materials cannot:
   procedural surface variation, anisotropic or wet response, IBL and reflections that agree with
   the sky. Bare primitives, one flat colour per object and stock-only PBR are not a finish.
4. **粒子 / particles.** Use instanced or GPU-driven particles as spatial information — dust in a
   light shaft, impact spray, wind, embers — not confetti. Their motion, density and colour answer
   to the light and atmosphere from steps 2–3. Cap the count and bake what can be baked.
5. **动画 / animation.** Drive idle, locomotion and impact through a connected rig or deformer;
   procedural motion is fine, detached limbs are not. Add easing, hit-stop, shake and camera
   response so the frame feels physical. Inspect the close-up and an animated frame, not only a
   resting pose.
6. **空间氛围 / spatial atmosphere.** Add plates, decals, debris and a density gradient toward the
   play space; parallax and fog make the world continue past the frame. Bloom, grain, vignette and
   colour grade come last and serve the thesis from step 0 — they do not repair a flat scene.
7. **Systems, then the loop.** Close the gameplay loop, wire input / pause / restart, resilience and
   the performance budget. For a 3D ship gate, inline every emitted model factory and keep one
   `PIPELINE-RECEIPT` per model; this skill verifies the receipt, it does not bundle the pipeline.
   Then run §5, rank defects worst-first (structure → space → light/material → reflection/world →
   beauty/UI → budget), repair, re-shoot the same four frames and write the receipt. Two rounds is
   the minimum; the loop ends only when the directive and the rubric agree.

If a step cannot be seen in a protocol frame, it did not happen as far as this skill is concerned.

## 2. The six layers

Four layers run as scripts, the fifth is a written judgement, and the sixth is a manual walk.
All six are part of the verdict; none substitutes for another.

| # | Layer | Tool | Fails on |
| --- | --- | --- | --- |
| 1 | Format | `check_single_file.py … --strict` | external references, network calls, missing ids, missing `<title>`/viewport, no error boundary |
| 2 | Craft (3D only) | same run with `--craft` | no inline `three.js`, no `PIPELINE-RECEIPT` (unreviewed passes / uncalled factory / opaque generated reference), bare primitives, RGB-only palettes, untextured surfaces, bones without skinning |
| 3 | Hard constraints (3D only) | same run, plus the screen checks | missing SSAO, missing depth-aware volumetrics, drag-gated mouse look, no recorded self-review |
| 4 | Frame metrics | `score_frame.py capture` + `check_single_file.py --craft` | manifest hash or build fingerprint mismatch, one view pretending to be four, an axis scored above the cap its own frames set without an override |
| 5 | Nine axes | `references/scoring-rubric.md` + captured frames | any axis below floor 4; fewer than five of six ship axes at floor; a detached limb; an unexplained score above a cap |
| 6 | Release walk | `references/release-checklist.md` | boot, input, gameplay, resilience, accessibility, content and delivery defects the scripts cannot see |

Layer 4 is medium-agnostic: a 2D canvas frame is crushed, blown out and colourless in exactly the
same way a WebGL frame is. Layers 2 and 3 do not exist for 2D. The score still does.

## 3. The fixed capture protocol

Every score comes from the same four frames, at the same settings. Two judgments that photographed
different frames are not comparable, and the difference silently becomes "taste".

```bash
python scripts/score_frame.py capture game.html --out review/round-1
python scripts/score_frame.py score review/round-1/manifest.json
python scripts/score_frame.py capture game.html --out review/round-1 --marker   # SELF-REVIEW block
```

| | Value | Why |
| --- | --- | --- |
| Shots | `title`, `play`, `char-closeup`, `hero-effect` | title, gameplay, the structural gate, the most expensive effect |
| Viewport | 1280×720, device scale 1 | A frame scored at another size is another frame |
| Prewarm | 200 frames | Boot, shader compiles and LOD settling are not the game |
| Quality | `high` | Judge the tier that would be shown |
| Seed | 0 | Same world across rounds; a new seed is a new build |

The build must answer `?shot=`, `?prewarm=`, `?q=` and `?seed=`. 3D builds do this with a camera
preset; 2D builds with a zoom preset. If all four shots come back as the same picture, the capture
is rejected and **there is no verdict** — do not substitute a hand-cropped screenshot and do not
invent a score from source. `score_frame.py crop shot.png closeup.png --box x,y,w,h --scale 3` is
an inspection aid only; a crop is never a protocol frame.

A headless Chrome, Edge or `chrome-headless-shell` is required; the script discovers one or takes
`--chrome PATH` / `CHROME_PATH`. No browser means no evidence, which means no verdict above the
format gate. Capture console errors in the same run — an uncaught exception is the highest-severity
defect even when the frame looks fine.

## 4. The nine axes

`references/scoring-rubric.md` is the **only** definition of the axes, their 1–5 bands and the
ship floor. Do not restate a band here or in a report; quote the file.

- Six **ship** axes — space, light, material, reflection, world detail, budget — decide whether
  the frame reads as AAA. **Fewer than five at or above floor 4 means prototype**, whatever the
  feature list says.
- Three **review** axes — beauty/composition, structural plausibility, UI readability — decide
  whether the frame is watchable. Structural plausibility is a hard gate in its own right.
- Any axis below 4 is a defect to repair, not a taste difference. Repair worst first:
  structure → space → light/material → reflection/world → beauty/UI → budget.
- A metric may only **lower** a score. Capped axes top out at 3; writing 4 or 5 above a cap needs
  an `overrides` entry naming the axis, the measured value and the stylistic reason.
- Score the pixels: a `SELF-REVIEW` full of 5s next to a blown-out sky is a failed review.

| Axis | One-line read (3D) | 2D reads as |
| --- | --- | --- |
| `space` | perspective camera inside the scene, three depth layers, parallax | constructed depth: y-sorting, occlusion, scale falloff, parallax |
| `light` | one sun, real shadows, contact AO, height fog | shading discipline: one direction, two tones, contact shadows |
| `material` | named PBR channels, generated wear and seams | stroke consistency: palette, two tones per material, one outline |
| `reflection` | IBL and planar water agreeing with the sky | environmental response: wet ground, halos, highlights that agree |
| `world` | plates, decals, debris, density rising toward play | set dressing: seeded decals, families of debris, density gradient |
| `budget` | bake once, instance repeats, 60 fps on integrated graphics | bake discipline: static art baked once, under 200 blits |
| `beauty` | intentional palette, one focal point, value hierarchy | unchanged |
| `structure` | one connected body at rest and through animation | silhouette integrity at rest and in animation |
| `ui` | legible over the world, ≥4.5:1 contrast, no overlap | unchanged |

## 5. Running a judgment (the verify half of the build → verify loop)

Build with §1 first; then run this loop and feed every finding back into the frame. One judgment is
one rung, not the finish line.

1. **Identify the build.** Path, size, medium, whether it is a shell. If it cannot be opened from
   `file://`, stop there and report that.
2. **Run the format gate.** `python scripts/check_single_file.py <file> --strict --craft --mode auto`.
   `--mode {auto,2d,3d}` only selects the size budget (2D 300/600 KB, 3D 1800/2560 KB); the gate
   set follows the build. Read the notes as well as the failures — `--craft` off leaves the
   evidence gate unenforced.
3. **Capture two rounds.** Round 1 establishes the frames and the caps; repair what is broken;
   round 2 re-photographs the same shots. One round is not a review.
4. **Score all nine axes in writing** against the rubric, on the frames, starting from the caps.
   Name the weakest axis and rank the defects worst-first. Inspect the upscaled character close-up
   and at least one animated frame before scoring `structure`.
5. **Verify the evidence chain.** A `SELF-REVIEW` marker is a receipt: its manifest must hash to
   the file on disk, its fingerprint to this build, and no axis may exceed its caps without an
   override. Only then does the written score mean anything.
6. **Walk the release checklist**, then report the verdict. A passing auditor with no screenshot
   ever opened is a failed review, not a pass.

If the build ignores the protocol, say so plainly and report the judgment as **not verifiable**.
Never convert a missing capture into a guessed number.

## 6. What the scripts can and cannot say

`scripts/check_single_file.py` checks signals: remote resources, shell parts, element ids, size,
and — under `--craft` — the 3D asset layer, the three hard constraints and the frame-metrics
chain. It cannot judge beauty, composition, whether a reflection agrees with the sky, or whether
a hand is attached to an arm. `scripts/score_frame.py` measures exposure, contrast, colour and
detail from a fixed capture; those numbers can hold an axis down, never lift it up, and they do
not see composition or structural plausibility.

The audit reports a `SELF-REVIEW` record and a frame-metrics chain; it does not validate the
numbers in the record beyond what the frames cap. That is intentional: the score is an assertion,
the frames and their metrics are the evidence, and the marker is the receipt. A file that passes
the auditor with a detached hand has simply lied to it.

## 7. Verdict format

Report, in this order:

- path, size, medium, and whether it is a deliverable or a shell;
- the audit output, including every `--craft` failure and the `3D hard constraints: n/4` line
  when applicable;
- the four protocol shots with their metrics and caps, plus the number of rounds;
- the **nine-axis score** with the weakest axis named, the 2D table used where relevant, and any
  overridden cap with its reason;
- the defects found on screen, worst first, with before/after evidence from the re-shoot;
- the verdict: **pass** (all nine at floor, ≥5 of 6 ship axes, no hard-gate failure), **prototype**
  (floor rule missed), or **not verifiable** (protocol or evidence missing).

## 8. Index

| Path | Read it when |
| --- | --- |
| `references/scoring-rubric.md` | **The nine axes, their 1–5 bands, the floor, the 2D translation table and the pixel red lines** — the only definition of a score |
| `references/visual-self-review.md` | The capture → score → repair → re-shoot loop, the limb-connection checklist, defect symptoms and the report record |
| `references/release-checklist.md` | The final manual walk: boot, input, gameplay, feel, performance, resilience, accessibility, content, delivery |
| `scripts/score_frame.py` | Capture the four shots through the fixed protocol, measure them, print the caps and the `SELF-REVIEW` metrics block; `crop` inspects a close-up when a build has no preset |
| `scripts/check_single_file.py` | Format, craft, hard-constraint and frame-metrics gates; `--strict`, `--craft`, `--mode {auto,2d,3d}` |
| `tests/` | Regression fixtures for both scripts |
