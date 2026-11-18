# Release checklist

Walk this before giving a verdict. A single unchecked box is a bug report waiting to happen.
The scripts cover the first section; the rest is the manual walk they cannot perform.

## 0. Verdict inputs

- [ ] The medium is recorded: 3D or 2D. On a 2D build the six ship axes are read through the
      2D table in `references/scoring-rubric.md`; the floor and the five-of-six rule do not move.
- [ ] A 3D brief answered with a 2D canvas is reported as a **target mismatch**, not quietly
      accepted or quietly failed.
- [ ] All nine axes (six ship axes + beauty / structural plausibility / UI readability) were
      scored explicitly against `references/scoring-rubric.md` — the only definition of the 1–5
      bands and floor 4.
- [ ] The three hard constraints are checked on screen on a 3D build: SSAO and depth-aware
      volumetrics in the shipped frame, free-look mouse by default (or `DRAG_LOOK_OPT_IN` when
      the brief asked for drag), and ≥ 2 self-review rounds with re-shots. A 2D build still owes
      the two rounds and the re-shots.
- [ ] The score was written **on screenshots**, not on code, with the weakest axis named and
      every below-floor axis repaired and the same shot re-captured. Loop and evidence:
      `references/visual-self-review.md`.
- [ ] A scaffold shell (a kept `GAME (replace this block)` marker) is reported as a shell, not
      judged as a deliverable.

## 1. Machine gates

```bash
python scripts/check_single_file.py path/to/game.html --strict
python scripts/check_single_file.py path/to/game.html --strict --craft   # full ship gates
python scripts/score_frame.py capture path/to/game.html --out review/round-1
python scripts/score_frame.py capture path/to/game.html --out review/round-2 --marker
```

`--craft` is **mandatory** for a verdict above the format gate. For 3D it fails on a missing
`PIPELINE-RECEIPT` (or a receipt with unreviewed passes, an uncalled factory, or an opaque
generated reference), missing geometry craft, a missing named material library, missing generated
textures, bones without skinning, **missing SSAO, missing depth-aware volumetrics, drag-gated
mouse look, or no `SELF-REVIEW` record**. It prints an `img2threejs receipt: N model(s) verified`
line, then the craft groups and the hard constraints separately (`4/4` and `4/4`); a file needs
all three.

For 2D, `--craft` enforces **only** the evidence: a `SELF-REVIEW` marker whose manifest hash and
build fingerprint match this file, at least three frames, more than one view, and no axis scored
above the cap its own frames produced. The asset layer is 3D-specific, so it is skipped — the
`SELF-REVIEW` block is not. `--mode 2d|3d` only picks the size budget; detection decides the gate
set.

Manual confirmation of what the script cannot see:

- [ ] Opens by double-clicking from a folder with spaces in its name.
- [ ] Works with the network disabled (DevTools → Network → Offline).
- [ ] No `<script src>`, `<link href>`, `fetch`, `XMLHttpRequest`, `import`, `@font-face` URL.
      (An inline engine's own `THREE.FileLoader` / `ImageBitmapLoader` fetch text is fine.)
- [ ] A 3D deliverable carries the **inlined three.js build** (`window.THREE`, version noted in
      a header comment). A 3D file without `THREE` markers fails the audit.
- [ ] File size is justified: < 300 KB for 2D, < 2.5 MB for 3D with an inline three.js build;
      anything larger needs a stated reason in the handoff. The auditor applies the right budget
      on its own (`--mode auto`); pass `--mode 2d` when a file is ambiguous.
- [ ] `view-source` shows one `<style>` and one `<script>` (plus optional JSON blobs).

## 2. Boot and shell

- [ ] Boot screen paints within 1 s; no white flash before it.
- [ ] Boot bar advances monotonically; it never sits at 0% while work happens.
- [ ] Title screen shows the game name, one-line premise, primary action.
- [ ] `Pause` works from every gameplay state, including mid-animation.
- [ ] Restart from game over returns to play in one click, without a page reload.
- [ ] `Escape` closes the topmost panel; `Enter` activates the focused action.

## 3. Input

- [ ] Keyboard: all actions reachable, no browser shortcut collisions.
- [ ] Window blur stops movement (no "running forever" bug).
- [ ] **Mouse movement turns the camera with no button held and no drag** (`FREE_LOOK`).
      Pointer lock, if present, is an optional enhancement; play never waits for a click.
      `DRAG_LOOK_OPT_IN` is present only if the brief explicitly asked for drag controls.
- [ ] Touch look works on the right half; the left half remains the virtual stick.
- [ ] Touch targets ≥ 44 px, no overlap, thumbs do not cover critical HUD.
- [ ] Gamepad dead zone applied; no drift.
- [ ] Controls are documented in-game, not only in a README.

## 4. Gameplay

- [ ] Win and lose states both exist and both show a clear next action.
- [ ] No unwinnable state, no soft-lock (every door opens, every resource is reachable).
- [ ] Difficulty curve is monotonic for the first 60 s; the first death is understandable.
- [ ] Score / progress persists across reload where promised.
- [ ] Corrupt save does not block boot (`localStorage.setItem('save','{')` and reload).

## 5. Feel

- [ ] Every state change has audio and visual feedback within one frame.
- [ ] Impact: shake + particles + sound on the same frame.
- [ ] No input latency above ~50 ms for the primary action.
- [ ] Idle animation on anything alive; the screen is never fully static.
- [ ] Nothing pops: transitions ≤ 200 ms; no layout shift at start.

## 6. Performance

- [ ] 60 fps median on a mid-range laptop; ≥ 30 fps on a low-end phone. On software rendering
      (SwiftShader / no GPU), report **unverified** instead of quoting the number.
- [ ] p99 frame time under 33 ms (check the debug overlay, not the eye).
- [ ] No per-frame allocation growth: heap flat over a 5-minute run.
- [ ] Adaptive quality steps down once and recovers; it does not oscillate.
- [ ] Startup time to interactive < 2 s.

## 7. Resilience

- [ ] `window.onerror` and `unhandledrejection` both paint a readable banner.
- [ ] WebGL2 failure falls back to 2D (or shows a clear, styled message).
- [ ] WebAudio failure = silent play, not a crash.
- [ ] `localStorage` blocked = in-memory play plus a one-time toast.
- [ ] Resizing and rotating the device mid-game does not break layout or input.
- [ ] Tab hidden then restored: game auto-paused, no time jump, audio resumed.

## 8. Accessibility

- [ ] `prefers-reduced-motion` removes shake, bob and long transitions.
- [ ] Text contrast ≥ 4.5:1; HUD text has a shadow or scrim.
- [ ] Focus-visible ring present; panels are labelled dialogs.
- [ ] Colour is never the only signal.
- [ ] Zoom to 200% does not clip critical UI.

## 9. Content

- [ ] No placeholder text, no `TODO`, no `console.log` spam left in.
- [ ] All generated names/strings are intentional and consistent in one language.
- [ ] Credits and version string present (footer or About panel).
- [ ] No third-party trademark or asset used without a licence note.

## 10. Delivery

- [ ] File name is stable and versioned: `game-name_v1.html`.
- [ ] Open the file on a second machine, ideally another OS.
- [ ] Report back: path, size, nine-axis score with the weakest axis named, known limits,
      next step.

## 11. Asset craft and provenance (3D deliverables only)

The SSAO and volumetrics boxes belong to §12; this section judges what the asset layer proves.
Confirm each item on screen, not just in code:

- [ ] An inline minified **three.js** build is present (`window.THREE`), not a hand-written
      renderer.
- [ ] Every model carries a `PIPELINE-RECEIPT` in the HTML: a sculpt spec path, seed, a
      `create...Model` factory that is actually called in the game source, and every staged pass
      reviewed `continue` with a render screenshot. An unwitnessed receipt is a failed gate.
- [ ] If reference images were generated, each declares a transparent PNG (no baked backdrop,
      floor or drop shadow) and a style anchor shared by the set.
- [ ] No box, sphere or capsule is used directly as a finished asset.
- [ ] Hard surfaces are beveled; generated geometry recomputes normals; lathe seams are welded.
- [ ] ≥ 12 named materials with albedo + roughness + metalness, looked up by name.
- [ ] Wear, seams and decals are generated at runtime (Canvas / DataTexture / shader noise).
- [ ] Animated characters are one continuous skinned mesh, not one primitive per bone.
- [ ] Object spec tables plus a seeded builder; `Math.random()` never decides a silhouette.
- [ ] A material calibration row (roughness sweep × metalness 0/1) was inspected in frame.
- [ ] `--strict --craft` reports `3D asset-craft signals: 4/4`.

## 12. Hard constraints and visual self-review

The SSAO and volumetrics boxes below are 3D-only. The capture, marker and structural boxes apply
to both media — a 2D build owes the same two rounds, the same four shots and the same close-up.

- [ ] `check_single_file.py --strict --craft` reports no `frame metrics` failure — on 2D as well
      as 3D. On a 3D build the same run reports `3D hard constraints: 4/4`
      (SSAO, depth-aware volumetrics, free-look, `SELF-REVIEW` record with ≥ 2 rounds).
- [ ] SSAO is rebuilt from a **scene depth texture**, hemisphere-sampled, depth-blurred, and
      applied to ambient radiance only — visible at crevices and contacts on screen.
- [ ] Volumetrics ray-march to **scene depth**, are shadow-map tested, and shafts are visibly
      blocked by a pillar or tree. A radial bright-pass streak does not pass this box.
- [ ] Both passes still run (at reduced step/sample count) on the lowest quality tier.
- [ ] At least **two** review rounds were completed, each captured through the fixed protocol
      (`scripts/score_frame.py capture`: four named shots, fixed viewport, prewarm, quality and
      seed) so the two rounds photograph the same frames. A capture whose shots all came back as
      one picture is rejected — the build ignores `?shot=`.
- [ ] The `metrics` block in `SELF-REVIEW` points at a manifest whose hash matches, whose
      `htmlFingerprint` matches this build, and whose caps no axis exceeds — every exception is
      an `overrides` entry naming the axis, the measured value and the stylistic reason.
- [ ] The close-up shows a connected body: shoulder → upper arm → elbow → forearm → wrist →
      hand, hips → thigh → knee → shin → foot, head → neck, on **both** sides.
- [ ] At least one **animated** frame (walk / attack / jump) was inspected at the same zoom;
      no joint separates and no limb rotates around a distant pivot.
- [ ] Every below-floor axis (per `references/scoring-rubric.md`) was repaired and the
      **same shot re-captured**; the handoff names the fixes with before/after evidence.
- [ ] HUD stays legible over the world; no panel overlaps the character.

## Red flags that mean "not done"

- A 3D brief answered with a fixed-zoom top-down canvas scene, reported as a pass.
- A frame where nothing casts a shadow, so every object floats.
- A game that can be lost but not restarted.
- A canvas that renders only after the second resize.
- `requestAnimationFrame` started twice (double speed / double CPU).
- Panels that stay in the DOM and capture clicks after closing.
- A score that resets because the save key is different from the load key.
- A radial "god ray" blur presented as volumetrics, or vertex AO presented as SSAO.
- A camera that does nothing until the player drags or clicks to capture the pointer.
- A character whose hands float next to the sleeves — especially one that only breaks while
  animating (absolute bone positions in a parent-relative skeleton).
- A self-review with one round, no close-up, or no re-shot after the fix.
- A `SELF-REVIEW` marker claiming 5/5 while the screenshots show otherwise.
- A confident score from a build that ignored `?shot=` — that is **not verifiable**, not a 1.
