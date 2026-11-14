# Release checklist

Walk this before handing the file to anyone. A single unchecked box is a bug report waiting
to happen.

## 0. Target declaration

- [ ] The build is **3D** — or, if it is 2D, the request asked for it or a one-line reason is
      written down (a perspective camera would not improve the loop).
- [ ] 2D was not chosen because 3D was hard, three.js was not rejected to keep the file small,
      and no model was hand-assembled from primitives instead of using the img2threejs
      pipeline (`SKILL.md` §0). Every model has a `PIPELINE-RECEIPT` marker in the HTML.
- [ ] All nine axes (six ship axes + beauty / structural plausibility / UI readability) were
      scored explicitly against `references/scoring-rubric.md` — the only definition of the
      1–5 bands and floor 4 — and none is below its floor.
- [ ] The three hard constraints in `SKILL.md` §2A are declared: SSAO **and** depth-aware
      volumetrics in the shipped pipeline, free-look mouse by default (or
      `DRAG_LOOK_OPT_IN` because the brief asked for drag), and ≥ 2 self-review rounds with
      re-shots.
- [ ] That score was written **on screenshots**, not on code, with the weakest axis named and
      every below-floor axis repaired and the same shot re-captured. Loop and evidence:
      `references/visual-self-review.md`.

## 1. Format audit

```bash
python scripts/check_single_file.py path/to/game.html --strict
python scripts/check_single_file.py path/to/game.html --strict --craft   # 3D deliverable
```

`--craft` is **mandatory** for a shipped 3D game: it fails on a missing `PIPELINE-RECEIPT`
(or a receipt with unreviewed passes, an uncalled factory, or an opaque generated reference),
missing geometry craft, a missing named material library, missing generated textures, bones
without skinning, **missing SSAO, missing depth-aware volumetrics, drag-gated mouse look, or no
`SELF-REVIEW` record**. It prints an `img2threejs receipt: N model(s) verified` line, then the
craft groups and the hard constraints separately (`4/4` and `4/4`); a file needs all three.
Starters and in-progress scaffolds are exempt. See `references/asset-craft.md`,
`SKILL.md` Step 3 and `references/visual-self-review.md`.

A 2D deliverable is audited with `--strict` alone; `--craft` on a non-3D file reports that the
gate was skipped. The bundled `assets/starter-3d.html` reports
`3D asset-craft signals: 2/4` and `3D hard constraints: 3/4`: it is a shell, and building its
asset layer is the first task, not a verification step.

Manual confirmation of what the script cannot see:

- [ ] Opens by double-clicking from a folder with spaces in its name.
- [ ] Works with the network disabled (DevTools → Network → Offline).
- [ ] No `<script src>`, `<link href>`, `fetch`, `XMLHttpRequest`, `import`, `@font-face` URL.
      (An inline engine's own `THREE.FileLoader` / `ImageBitmapLoader` fetch text is fine.)
- [ ] A 3D deliverable carries the **inlined three.js build** (`window.THREE`, version noted in
      a header comment). A 3D file without `THREE` markers fails the audit.
- [ ] File size is justified: < 300 KB for 2D, < 2.5 MB for 3D with an inline three.js build;
      anything larger needs a stated reason in the handoff.
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
- [ ] Controls are documented in-game, not only in the README.

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

- [ ] 60 fps median on a mid-range laptop; ≥ 30 fps on a low-end phone.
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
- [ ] Report back: path, size, nine-axis score with the weakest axis named, known limits, next
      step.

## 11. Asset craft (3D deliverables only)

Starters and in-progress scaffolds are exempt; a deliverable is not. Modeling runs through the
vendored img2threejs pipeline (`img2threejs/PIPELINE.md`) — its strict-quality spec gate and
staged reviews produce the geometry and material craft below. Confirm each item on screen,
not just in code:

- [ ] An inline minified **three.js** build is present (`window.THREE`), not a hand-written
      renderer.
- [ ] Models were produced by the img2threejs pipeline: a sculpt spec plus a
      `create...Model` factory called from the game source, with the spec seed recorded beside
      the world seed. One `PIPELINE-RECEIPT` per model is present in the HTML, with all staged
      passes reviewed `continue` and a render screenshot for each (`SKILL.md` Step 3).
- [ ] If the reference images were generated, each is a transparent PNG (no baked backdrop,
      floor or drop shadow) and the whole set shares one style — palette, lighting direction
      and rendering treatment. The transparency and palette halves were checked at intake
      (`check_reference_admission.py --generated`, `check_style_coherence.py`).
- [ ] No box, sphere or capsule is used directly as a finished asset.
- [ ] Hard surfaces are beveled; generated geometry recomputes normals; lathe seams are welded.
- [ ] ≥ 12 named materials with albedo + roughness + metalness, looked up by name.
- [ ] Wear, seams and decals are generated at runtime (Canvas / DataTexture / shader noise).
- [ ] Animated characters are one continuous skinned mesh, not one primitive per bone.
- [ ] Object spec tables plus a seeded builder; `Math.random()` never decides a silhouette.
- [ ] A material calibration row (roughness sweep × metalness 0/1) was inspected in frame.
- [ ] `--strict --craft` reports `3D asset-craft signals: 4/4`.

## 12. Hard constraints and visual self-review (3D deliverables only)

- [ ] `check_single_file.py --strict --craft` reports `3D hard constraints: 4/4`
      (SSAO, depth-aware volumetrics, free-look, `SELF-REVIEW` record with ≥ 2 rounds) and
      reports no `frame metrics` failure.
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
- [ ] HUD stays legible over the 3D world; no panel overlaps the character.

## Red flags that mean "not done"

- A 3D brief answered with a fixed-zoom top-down canvas scene.
- A frame where nothing casts a shadow, so every object floats.
- A game that can be lost but not restarted.
- A canvas that renders only after the second resize.
- Sound that works after clicking a button but not before (this one is fine — document it).
- `requestAnimationFrame` started twice (double speed / double CPU).
- Panels that stay in the DOM and capture clicks after closing.
- A score that resets because the save key is different from the load key.
- A radial "god ray" blur presented as volumetrics, or vertex AO presented as SSAO.
- A camera that does nothing until the player drags or clicks to capture the pointer.
- A character whose hands float next to the sleeves — especially one that only breaks while
  animating (absolute bone positions in a parent-relative skeleton).
- A self-review with one round, no close-up, or no re-shot after the fix.
- A `SELF-REVIEW` marker claiming 5/5 while the screenshots show otherwise.
