# Changelog

All notable changes to this skill are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
