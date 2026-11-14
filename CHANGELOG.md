# Changelog

All notable changes to this skill are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.2] — 2026-11-14

The nine axes had two competing definitions and only two score bands between them. `SKILL.md` §1
carried a "floor / prototype tell" table while `visual-self-review.md` carried a "5 looks like /
below floor" table for the same axes — with different wording — and the promised 1–5 scale had
no description at all for 2 or 3. The standard now has exactly one home.

### Added

- `references/scoring-rubric.md` — the single definition of the nine axes. Each axis gets a
  1–5 band table with observable, screenshot-level descriptions; band 4 is the ship floor and
  bands 2 and 3 are written out for the first time. It also owns the scoring rules (fewer than
  five ship axes at floor = prototype, any axis below 4 is a defect, repair order), the nine
  `SELF-REVIEW` keys, and one implementation-handbook link per axis. It deliberately does not
  duplicate implementation detail.
- All four READMEs list the rubric in their file trees and link their scoring passages to it.

### Changed

- `SKILL.md` §1 is now an index: six ship-axis names, a one-line read and an implementation
  link, with a pointer to the rubric. The floor/prototype columns and the scoring rule are gone
  from here; §0, §2A.A, §3's Frame gate, Step 8, §6's index and §8's handoff all point to the
  rubric instead of restating a threshold.
- `references/visual-self-review.md` drops its nine-axis score table and keeps the loop, the
  checklists, the repair recipes and the evidence record. It states the division of labour up
  front and notes that `--craft` does not verify the numbers in the marker.
- `references/release-checklist.md` §0, §10 and §12 now reference the rubric; §10 reports a
  nine-axis score rather than six.
- README wording fixed in all four languages: the prototype threshold read "miss three of six",
  but the rule has always been fewer than five of six at floor — i.e. missing two.

## [1.5.1] — 2026-11-14

Generated reference images now face the same machine gate as everything else in the
pipeline. When models are produced from generated art, the intake stage refuses images
with a baked backdrop and rejects a set whose members drift apart in style.

### Added

- `check_reference_admission.py` gains a `--generated` flag: images produced by image
  generation must be transparent-background PNGs — no baked backdrop, floor, or drop
  shadow. Enforcement is a per-corner transparency audit (each 32×32 corner patch ≥90%
  transparent, overall opaque fraction ≤ a 4% floor reserve) with the reason recorded in
  the provenance JSON. Without the flag, behavior is byte-identical to upstream.
- `check_style_coherence.py` — a new stage-1 script comparing candidate reference images
  against an anchor: subject histogram cosine similarity (default ≥0.80) and mean luma
  delta (default ≤40). It is documented as a deterministic proxy for palette, lighting
  and rendering drift only; silhouette and material consistency remain human judgment.
- `SKILL.md` §0: a third hard constraint covering generated reference images (transparent
  background, no baked scenery or shadow, one coherent style across the set); Step 3 adds
  the two hard-gate commands with the reasons they exist.
- Vendored test suite grows 8 → 18: RGBA fixtures, corner-patch transparency cases, and
  coherence pass/drift scenarios. Repo suite grows 28 → 33 and still passes.

### Changed

- `THIRD_PARTY.md` now documents the three locally modified/added intake files per
  Apache-2.0 §4(b), with the rationale for each.
- `references/release-checklist.md` adds the generated-image line: transparent PNG,
  no baked backdrop, one shared style.

## [1.5.0] — 2026-11-13

The engine question is settled by mandate, and the modeling question is settled by pipeline.
Every 3D deliverable **must inline three.js**, and **every model must be produced by the
img2threejs pipeline**, now vendored in full at `img2threejs/` (Apache-2.0, upstream commit
`0c0c49b`). The raw-WebGL2 escape hatch is gone; the craft gate's "starters exempt" promise is
finally implemented in the auditor instead of only in prose.

### Added

- `img2threejs/` — the complete upstream repository (5.6 MB, 370 files), vendored unchanged
  except that its `SKILL.md` is stored as `PIPELINE.md` so skill hosts scanning this directory
  do not register a second standalone skill. Provenance and license terms in `THIRD_PARTY.md`.
- `THIRD_PARTY.md` — Apache-2.0 applies to `img2threejs/`; MIT continues to cover the rest.
- `SKILL.md` §0: two hard constraints — inlined three.js (`window.THREE`) in every 3D
  deliverable, and modeling exclusively through the img2threejs pipeline (reference image →
  staged, quality-gated sculpt → `createObjectModel` factory). Workflow gains Step 3, "Build
  the models with img2threejs", including the TS→JS / module-imports→global-`THREE` adaptation.
- `check_single_file.py`: a 3D deliverable with no `THREE` markers now fails `--craft`;
  scaffold shells (a kept `GAME (replace this block)` marker) are reported as shells and the
  3D gates describe rather than fail — the documented exemption now exists in code.

### Changed

- `references/procedural-3d.md` rewritten around the single path: inline three.js; the raw
  `getContext`/program-compile boilerplate replaced by `THREE.WebGLRenderer` boot and
  `debug.onShaderError`.
- `references/asset-craft.md` and `references/material-authoring.md` repositioned as the
  rationale and theory behind the pipeline's own gates, not a parallel craft doctrine.
- The 3D starter is relabelled everywhere as a post-chain reference slice (a shell), never a
  starting point for a deliverable; all four READMEs updated accordingly.

### Removed

- The raw-WebGL2 route ("hand-writing a renderer is justified once the asset layer is
  complete") and every sentence that treated an inline engine as optional.

## [1.4.0] — 2026-11-13

Three constraints that were previously "good practice" are now hard gates. A shipped 3D game
must prove a **visual self-review with a repair loop**, real **SSAO + depth-aware volumetrics**,
and **free-look mouse by default**. Triggered by a review of a finished single-file RPG where
the hands were not attached to the body and the atmosphere passes were screen-space fakes.

### Added

- **`SKILL.md` §2A — Three hard constraints (MUST)**: (A) ≥ 2 rounds of real screenshots,
  nine-axis written score, repair and re-shot, with structural plausibility (continuous limb
  chain, animated-frame check) as a hard gate; (B) SSAO rebuilt from scene depth plus
  shadow-tested depth-aware volumetric ray marching, both present at every quality tier;
  (C) mouse movement turns the camera with no drag and no click gate, drag only via an explicit
  `DRAG_LOOK_OPT_IN`.
- `references/visual-self-review.md` — capture commands, the nine-axis score sheet, the
  limb-connection checklist, a defect → repair recipe table (including the absolute-vs-relative
  bone-offset bug), the `SELF-REVIEW` marker format and the handoff report template.
- A **second** `--craft` gate: `3D hard constraints: n/4` for SSAO, volumetrics, free-look and
  the self-review record. Both gates must report `4/4`. Signals are checked against the game's
  own source, with inline minified-engine lines stripped so `DepthTexture`/`shadowMap` inside
  three.js cannot fake a pass. `hard_hits` / `hard_missing` added to `--json`.
- Eleven new unit tests (28 total) covering both gates, drag opt-in, marker validation
  (rounds, close-up, fixes, re-shot) and the inline-engine false-positive case.
- Release checklist §12 and three new red flags; ten-second test extended to ten questions.
- Hard-constraint summaries in `README.md` and `README.zh-CN.md`.

### Changed

- `references/cinematic-look.md`: §4 volumetrics and §5 AO are now **MUST**, with a new §5A
  implementation-contract table (what counts vs. lookalikes), depth-texture wiring, the
  MSAA/depth-texture incompatibility, view-space reconstruction and the composite order.
- `references/input-and-mobile.md`: pointer section rewritten as free-look default; the old
  drag-to-look code is now an explicitly opt-in fallback.
- `references/procedural-3d.md`: render graph and quality tiers now include both atmosphere
  passes at every tier (`ao` and `volSteps` are never off); camera section states free-look.
- `assets/starter-3d.html`: the 3D starter itself now uses free-look mouse (touch still drags
  on the right half), so scaffolds inherit the default instead of drag gating.
- Workflow Step 7 is now "Self-review, repair, re-shoot, then audit"; the handoff reports nine
  axes, review rounds and both `--craft` results. Four new anti-patterns.

## [1.3.0] — 2026-11-13

2D is no longer an acceptable default answer to "make me a game", and "looks AAA" is no longer a
matter of taste: it is six named axes with numbers, scored before handoff.

### Added

- **`SKILL.md` §0 — Default target: 3D, at AAA fidelity.** Unless the request names 2D, the
  output is a perspective WebGL2 game with an inline engine. The five things "one file" never
  justifies (fixed top-down zoom, flat ambient, untextured boxes, a hand-written renderer, 2D
  because 3D is hard) are listed explicitly, along with AAA defined as *a frame that survives
  inspection plus a loop that closes* rather than content volume.
- **`SKILL.md` §1 — Six axes**: space, light, material, reflection, world detail, budget. Each
  carries a numeric floor, the prototype tell it rules out, and the reference that holds the
  detail; fewer than five of six at the floor means the build is a prototype.
- Release checklist §0 (target declaration + six-axis score) and two red flags: a 3D brief
  answered with a fixed-zoom top-down scene, and a frame where nothing casts a shadow.
- `docs/game-2d.png` — the 2D reference frame in the README hero row.

### Changed

- `SKILL.md` restructured and de-duplicated: the old **Quality bar** (8 checks) and **Asset-craft
  gate** (6 rules) are folded into §1's six axes and §3's three gates, the separate **Repo map**
  is merged into the reference index, and the anti-pattern list drops from 14 to 13 while adding
  the 2D-by-default entry. Net size 14.6 → 15.1 KB, with two whole sections merged.
- The workflow's look-development step now states the single order (composition → key light →
  materials → atmosphere → post) instead of repeating five of the old quality checks.
- README hero row (all four languages) shows two finished games — 2D as an opt-in route, 3D as
  the default — instead of a generator starter next to a finished 3D game, plus a six-axis
  summary linking into `SKILL.md`.
- `docs/method.md` no longer claims "no engine": it now separates *no build step* from *no
  engine*, and states the 0.8–1.4 MB inline-engine byte range.
- `references/procedural-3d.md` no longer opens with "3D in one file is viable without any
  library" — the inlined engine is now the default row in its path table, and the asset layer,
  not the grading pass, is named as where perceived quality comes from.
- `--craft` on a non-3D file now explains the skip and names the default target (a note, not a
  failure, so a deliberate 2D build still audits clean).

## [1.2.0] — 2026-11-13

The 3D asset layer is now a hard, machine-checked gate. Comparing two single-file 3D games
showed the visual gap was not in the post stack (both had a complete one) but in generated
geometry, a named material library, runtime textures and continuous skinning.

### Added

- `references/asset-craft.md` — the comparison evidence, six non-negotiable constraints
  (inline engine, no bare primitives, bevel/normals/seams, named materials with generated
  maps, continuous skinning, seeded table-driven builders), the catch-up order, and the
  four signal groups `--craft` checks.
- An **Asset-craft gate (3D, non-negotiable)** section in `SKILL.md`, four new anti-patterns,
  and `--strict --craft` as the 3D ship gate in the workflow, release checklist and handoff.
- `--craft` in `scripts/check_single_file.py`: hard failures for missing geometry craft,
  a missing material library, missing generated textures, or bones without skinning;
  `craft_hits` / `craft_missing` in `--json`; a `4/4` note for 3D files.
- Eight new unit tests covering the craft gate, inline-engine loader handling and the size
  budget. The ship gate is documented in all four READMEs.

### Changed

- Core rule 1 now makes an inline minified 3D engine the **default** for 3D, not a last
  resort: "zero external assets" means zero runtime requests, not zero library code.
- Size budget: warning 500 KB → 1800 KB, hard limit 1200 KB → 2560 KB, so a ~1.4 MB inline
  engine plus a generated asset layer is not penalised.
- `fetch()` on inline-engine loader lines (`THREE.FileLoader` / `ImageBitmapLoader`) is
  reported as library code; a `fetch()` in game code still fails the offline rule.
- Plugin and marketplace versions bumped to 1.2.0.

## [1.1.0] — 2026-11-12

The 3D path was rebuilt around a real render pipeline. The previous shell was correct and
looked like a prototype; "single file" was never meant to be an excuse for that.

### Added

- `references/cinematic-look.md` — the full stack with numbers: sun placement, the additive
  horizon-glow sky model, PCSS-style shadow bias, volumetric ray marching with height density
  and Henyey-Greenstein phase, SSAO placement, bloom pyramid construction, ACES + split-tone
  grade, camera language, a per-pass frame budget and a ten-second look test.
- `references/material-authoring.md` — the five-channel material model (albedo, roughness,
  metal, height, AO), wear in primer → oxide order, object-space plate seams, triplanar
  sampling, water as a channel change, MRT baking, and the three classic failure modes
  (camouflage, glitter, plastic).
- `references/game-feel.md` — the feedback table, hitstop/shake/pop primitives, easing curves,
  camera behaviour, the three-layer particle rule, layered SFX and HUD motion.
- A **Quality bar** section in `SKILL.md`: eight checks a render has to pass before the skill is
  considered followed, plus four new anti-patterns (untextured boxes under flat ambient,
  missing sRGB encode, exposure used to hide a lighting bug, bloom as a glow effect).
- A look-development step in the workflow, between systems and content.

### Changed

- `assets/starter-3d.html` rewritten (27 KB → 75 KB) as a cinematic slice, still zero
  dependencies: HDR RGBA16F pipeline with an RGBA8 fallback, 2048² shadow map with a 5-tap
  PCF disc, analytic sky shared by dome/ambient/fog/reflections, PBR ground with wet pools and
  sun mirror, instanced props with paint wear and plate seams, half-resolution volumetric sun
  shafts, half-resolution SSAO with a bilateral blur, five-mip bloom with Karis averaging,
  ACES tone mapping, split-tone grade, chromatic aberration, vignette, grain, FXAA, adaptive
  resolution and a touch stick.
- The 3D starter is now a playable slice: four signal cores, a 120-second light window, pause,
  restart, and a win/lose card.
- READMEs (all four languages) document the pipeline and the quality bar; the screenshots are
  re-captured from the new render.
- The README hero row now shows what the skill actually produces: a 2D starter next to a
  finished single-file 3D game (`docs/game-3d.png`), with the bare 3D template moved inline as
  the "before you write a line" proof.

### Fixed

- Missing linear → sRGB encode in the composite, which made a correct HDR scene read as night
  and invited "fixes" to exposure and lighting that were never the problem.
- Shadow attributes bound to the wrong attribute slots in the depth pass, which silently
  produced an empty shadow map.
- Sky built by mixing horizon and zenith colours, which turns a sunset into a beige wall; it is
  now a blue dome with an additive horizon glow.
- Bloom upsample sampling the texture it was writing (a feedback loop).
- Title card clipped on viewports shorter than its content.

## [1.0.0] — 2026-11-11

### Added

- `SKILL.md` with the single-file, zero-asset method: rules, workflow, reference index and
  anti-patterns.
- Ten references covering architecture, procedural 2D art, procedural 3D (WebGL2), procedural
  audio, input and mobile, state and persistence, performance, resilience and accessibility,
  design language, and the release checklist.
- Two runnable starter templates in `assets/`: a 2D canvas arcade shell and a raw WebGL2
  courtyard with instanced geometry and a post-processing grade. Both boot, play, pause,
  restart and save without a single external request.
- `scripts/scaffold.py` — generate a named game from either template, with its own storage
  namespace and accent colour.
- `scripts/check_single_file.py` — audit a candidate file for remote resources, network calls,
  missing shell parts, dangling element IDs and size budget. `--strict` turns warnings into
  failures.
- Unit tests for both tools, and a GitHub Actions workflow that validates the skill
  frontmatter, runs the tests, audits the templates and syntax-checks every inline script.
- `docs/method.md` — the reasoning behind the constraints, the six-step pipeline, and when
  not to use the method.
- README in English, Simplified Chinese, Japanese and Korean.
