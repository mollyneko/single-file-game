# Third-party notices

## `img2threejs/`

The `img2threejs/` directory is vendored from:

- Upstream: <https://github.com/img2threejs/img2threejs>
- Vendored commit: `0c0c49bc168e648dbaf9c8c080474de0b3a941b6` (2026-11-05, v2.0.1)
- License: **Apache-2.0** — see `img2threejs/LICENSE`. The Apache-2.0 terms apply to
  that directory and everything under it; they do not relicense the rest of this
  repository, which remains MIT.

Local changes (Apache-2.0 §4(b) notice):

- `SKILL.md` is stored here as `PIPELINE.md` — a file rename only, no content altered —
  so that skill hosts scanning directories one level above (this repository is itself
  installed as an agent skill) do not register the nested directory as a second,
  standalone skill.
- `forge/stage1_intake/check_reference_admission.py`: added an opt-in
  `transparent_background_check` gate and `--generated` flag. A machine-generated
  reference is rejected at intake unless it is a transparent PNG with the subject
  isolated and the four corner patches clear. Without the flag, upstream behaviour is
  unchanged.
- `forge/stage1_intake/check_style_coherence.py`: new file. Compares a candidate
  reference against a style anchor on subject-palette histogram cosine and mean
  luminance — a deterministic proxy for style drift across a generated reference set.
- `forge/tests/test_reference_admission.py`: added coverage for both gates above.
