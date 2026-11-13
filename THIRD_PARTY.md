# Third-party notices

## `img2threejs/`

The `img2threejs/` directory is vendored, unmodified in behaviour, from:

- Upstream: <https://github.com/img2threejs/img2threejs>
- Vendored commit: `0c0c49bc168e648dbaf9c8c080474de0b3a941b6` (2026-11-05, v2.0.1)
- License: **Apache-2.0** — see `img2threejs/LICENSE`. The Apache-2.0 terms apply to
  that directory and everything under it; they do not relicense the rest of this
  repository, which remains MIT.

The only local change is the file name of the agent entry point: upstream `SKILL.md`
is stored here as `PIPELINE.md`, so that skill hosts scanning directories one level
above (this repository is itself installed as an agent skill) do not register the
nested directory as a second, standalone skill. No content was altered in the rename.
