# Changelog

All notable changes to this skill are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
