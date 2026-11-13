# Release checklist

Walk this before handing the file to anyone. A single unchecked box is a bug report waiting
to happen.

## 0. Target declaration

- [ ] The build is **3D** — or, if it is 2D, the request asked for it or a one-line reason is
      written down (a perspective camera would not improve the loop).
- [ ] 2D was not chosen because 3D was hard, and an inline engine was not rejected to keep the
      file small.
- [ ] The six axes in `SKILL.md` §1 were scored explicitly, and at most one is below its floor.

## 1. Format audit

```bash
python scripts/check_single_file.py path/to/game.html --strict
python scripts/check_single_file.py path/to/game.html --strict --craft   # 3D deliverable
```

`--craft` is **mandatory** for a shipped 3D game: it fails on missing geometry craft, a
missing named material library, missing generated textures, or bones without skinning.
Starters and in-progress scaffolds are exempt. See `references/asset-craft.md`.

A 2D deliverable is audited with `--strict` alone; `--craft` on a non-3D file reports that the
gate was skipped. The bundled `assets/starter-3d.html` reports `2/4`: it is a shell, and building
its asset layer is the first task, not a verification step.

Manual confirmation of what the script cannot see:

- [ ] Opens by double-clicking from a folder with spaces in its name.
- [ ] Works with the network disabled (DevTools → Network → Offline).
- [ ] No `<script src>`, `<link href>`, `fetch`, `XMLHttpRequest`, `import`, `@font-face` URL.
      (An inline engine's own `THREE.FileLoader` / `ImageBitmapLoader` fetch text is fine.)
- [ ] File size is justified: < 300 KB for 2D, < 900 KB for hand-written 3D, < 2.5 MB with
      an inline engine; anything larger needs a stated reason in the handoff.
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
- [ ] Mouse and touch both work; pointer-lock failure falls back to drag.
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
- [ ] Report back: path, size, six-axis score with the weakest axis named, known limits, next
      step.

## 11. Asset craft (3D deliverables only)

Starters are exempt; a deliverable is not. Confirm each one on screen, not just in code:

- [ ] An inline minified 3D engine is present (PBR, IBL, shadows, skinning, curve geometry) —
      or the hand-written renderer is smaller than the asset layer.
- [ ] No box, sphere or capsule is used directly as a finished asset.
- [ ] Hard surfaces are beveled; generated geometry recomputes normals; lathe seams are welded.
- [ ] ≥ 12 named materials with albedo + roughness + metalness, looked up by name.
- [ ] Wear, seams and decals are generated at runtime (Canvas / DataTexture / shader noise).
- [ ] Animated characters are one continuous skinned mesh, not one primitive per bone.
- [ ] Object spec tables plus a seeded builder; `Math.random()` never decides a silhouette.
- [ ] A material calibration row (roughness sweep × metalness 0/1) was inspected in frame.
- [ ] `--strict --craft` reports `3D asset-craft signals: 4/4`.

## Red flags that mean "not done"

- A 3D brief answered with a fixed-zoom top-down canvas scene.
- A frame where nothing casts a shadow, so every object floats.
- A game that can be lost but not restarted.
- A canvas that renders only after the second resize.
- Sound that works after clicking a button but not before (this one is fine — document it).
- `requestAnimationFrame` started twice (double speed / double CPU).
- Panels that stay in the DOM and capture clicks after closing.
- A score that resets because the save key is different from the load key.
