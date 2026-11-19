# Single-File Game

**Build a single-file offline HTML game at the top of your ability — three.js as the skeleton, custom shaders as the fill — then prove the frame holds up with a fixed rubric and deterministic capture.**

[![validate](https://github.com/mollyneko/single-file-game/actions/workflows/validate.yml/badge.svg)](https://github.com/mollyneko/single-file-game/actions/workflows/validate.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-2f4b3f.svg)](LICENSE)

**English** · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

<table>
<tr>
<td align="center" width="50%"><b>3D — three.js skeleton + custom GLSL</b><br>
<img src="docs/game-3d.png" width="560" alt="3D single-file game showcase"></td>
<td align="center" width="50%"><b>2D — procedural canvas, baked layers</b><br>
<img src="docs/game-2d.png" width="560" alt="2D single-file game showcase"></td>
</tr>
</table>

_Representative frames: a single-file 3D scene (three.js + self-written shaders) and a single-file
2D scene (procedural canvas). The frame, not the feature list, is the unit of evidence._

---

## The prime directive — priority 1, overrides everything below

> 充分发挥你最顶级的审美、艺术设计和3D编程能力，在构图、光影、材质、粒子、动画和空间氛围上做到极致。画面需要有令人震撼的视觉表现力。不限制你的创意和技术方案，尽可能展示你的能力上限。用three.js做骨架+自写着色器填充

> Give full play to your very best aesthetic sense, art direction and 3D programming ability; take
> composition, light and shadow, materials, particles, animation and spatial atmosphere to the
> extreme. The frame must have stunning visual impact. Do not limit your creative solutions or
> techniques; push your ability to its upper limit as far as possible. Use three.js as the skeleton
> and custom shaders as the fill.

This is constraint number one and overrides everything below. The single-file boundary still
applies: **one `.html` file, opened from `file://`, no server, no network, no external assets.**
Inline everything.

## What this skill is

A build-and-verify skill for single-file HTML games. It gives you the visual mandate above, a
nine-axis rubric that defines "excellent" in measurable terms, a fixed capture protocol that makes
two reviews comparable, and scripts that check what a script can check. The unit of evidence is a
**frame** — not a feature list, a line count, or a `SELF-REVIEW` block full of 5s. Source code is
never evidence: a correct skeleton in source can still produce a detached hand on screen.

Version 2.x removed the bundled build path (scaffold, vendored engine, starter templates, art and
audio guides). What remains is the mandate, the compact build order below and the verification
system; how you produce the file is up to you.

## Build flow — the directive as a workflow

The six named surfaces become a build order, not a checklist you fill in at the end. Every step
must show up in one of the four protocol frames.

0. **Lock the shell and the thesis.** One inline `.html`, `?shot=` / `?prewarm=` / `?q=` / `?seed=`
   wired from the first run, error boundary, DPR/resize handling. Write one sentence naming the
   focal point, palette, light direction and mood.
1. **构图 / composition** — camera inside the world, three depth layers, one focal point and a value
   hierarchy; frame all four shots before adding detail.
2. **光影 / light & shadow** — one readable key light, real shadows, contact AO/SSAO, depth-aware
   fog and volumetrics, one grade. Feed the same sun/fog/shadow data into custom shaders.
3. **材质 / material** — named material families, runtime-generated maps, custom GLSL for what stock
   materials cannot express; reflections agree with the sky.
4. **粒子 / particles** — instanced or GPU-driven, motivated by light and space, never confetti.
5. **动画 / animation** — connected rig or deformer, idle / locomotion / impact, easing, hit-stop,
   camera response; inspect an animated frame and the close-up.
6. **空间氛围 / spatial atmosphere** — plates, decals, debris, density gradient, parallax and fog;
   bloom, grain and grade come last.
7. **Systems → verify loop.** Close the gameplay loop, wire input / pause / restart and resilience.
   For a 3D ship gate keep one `PIPELINE-RECEIPT` per model. Then run the six-layer loop below:
   capture → score → worst-first repair → re-shoot the same four frames. Two rounds is the minimum.

If a step cannot be seen in a protocol frame, it did not happen.

## The six layers — how the frame is verified

| # | Layer | Tool | Fails on |
| --- | --- | --- | --- |
| 1 | Format | `check_single_file.py … --strict` | external references, network calls, missing ids, missing `<title>`/viewport, no error boundary |
| 2 | Craft (3D only) | same run with `--craft` | no inline `three.js`, invalid `PIPELINE-RECEIPT`, bare primitives, RGB-only palettes, untextured surfaces, bones without skinning |
| 3 | Hard constraints (3D only) | same run, plus screen checks | missing SSAO, missing depth-aware volumetrics, drag-gated mouse look, no recorded self-review |
| 4 | Frame metrics | `score_frame.py capture` + `--craft` | manifest/fingerprint mismatch, one view pretending to be four, a score above the cap its frames set |
| 5 | Nine axes | `references/scoring-rubric.md` | any axis below floor 4, fewer than five of six ship axes at floor, a detached limb |
| 6 | Release walk | `references/release-checklist.md` | boot, input, gameplay, resilience, accessibility, content and delivery defects the scripts cannot see |

The first five are inputs to a repair loop: capture → score → fix the worst axis → re-shoot →
score again. Layer 4 is medium-agnostic: a 2D canvas frame is crushed, blown out and colourless in
exactly the same way a WebGL frame is. Layers 2–3 do not exist for 2D. The score still does.

## Quick start

```bash
# 1. Machine gates. --mode only picks the size budget; detection picks the gates.
python scripts/check_single_file.py game.html --strict --craft --mode auto

# 2. Fixed capture: four shots, 1280x720 @1, 200-frame prewarm, high, seed 0.
python scripts/score_frame.py capture game.html --out review/round-1
python scripts/score_frame.py score review/round-1/manifest.json
python scripts/score_frame.py capture game.html --out review/round-2 --marker

# 3. Score all nine axes in writing against references/scoring-rubric.md,
#    repair toward the prime directive, re-shoot the same frames, then walk release-checklist.md.
```

The build has to answer `?shot=title|play|char-closeup|hero-effect`, `?prewarm=`, `?q=` and
`?seed=`. If all four shots come back as one picture the capture is rejected and the verdict is
**not verifiable** — never guess a score from source. `score_frame.py crop shot.png out.png
--box x,y,w,h --scale 3` is an inspection aid, never a protocol frame. A headless Chrome, Edge or
`chrome-headless-shell` is required (`--chrome PATH` / `CHROME_PATH` overrides discovery).

## Scoring

Six ship axes — space, light, material, reflection, world detail, budget — decide whether the
frame reads as AAA. Three review axes — beauty, structure, UI — decide whether it is watchable.
Each axis is 1–5 with **floor 4**; fewer than five of the six at floor means **prototype**. A 2D
build reads the same nine names through the translation table in the rubric; the floor does not
move. Pixel metrics can only lower a score; an axis above its cap needs a recorded `overrides`
entry with the axis, the measured value and a stylistic reason.

The `SELF-REVIEW` HTML comment is a receipt tying the score to its frames:

```html
<!-- SELF-REVIEW {"rounds":2,
  "shots":["title","play","char-closeup","hero-effect"],
  "axes":{"space":5,"light":4,"material":5,"reflection":4,"world":4,"budget":4,
          "beauty":4,"structure":5,"ui":5},
  "fixes":["rig: parent-relative bone offsets","added depth-based SSAO"],
  "reshoot":true,
  "metrics":{"manifest":"review/round-2/manifest.json","sha256":"<manifest sha256>"}} -->
```

The auditor checks the manifest hash, the build fingerprint, ≥3 frames, more than one view and
the caps. It does not judge the numbers. The marker is a receipt, not the review.

## Files

| Path | What it owns |
| --- | --- |
| `SKILL.md` | Build mandate + verification entry point: prime directive, six-face build loop, six layers, protocol, judgment, verdict format |
| `references/scoring-rubric.md` | The only definition of the nine axes, bands, floor, 2D table and red lines |
| `references/visual-self-review.md` | capture → score → repair → re-shoot, limb checklist, symptom → cause table |
| `references/release-checklist.md` | The manual final walk |
| `scripts/score_frame.py` | Capture, pixel metrics, caps, crop |
| `scripts/check_single_file.py` | Format, craft, hard-constraint and frame-metrics gates |
| `docs/` | Hero images: `game-3d.png` (three.js + custom shaders) and `game-2d.png` (procedural canvas) |
| `tests/` | Regression tests with inline fixtures |

```bash
python -m unittest discover -s tests -v
```

## License

MIT. See [LICENSE](LICENSE).
