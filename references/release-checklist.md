# Release checklist

Walk this before handing the file to anyone. A single unchecked box is a bug report waiting
to happen.

## 1. Format audit

```bash
python scripts/check_single_file.py path/to/game.html --strict
```

Manual confirmation of what the script cannot see:

- [ ] Opens by double-clicking from a folder with spaces in its name.
- [ ] Works with the network disabled (DevTools → Network → Offline).
- [ ] No `<script src>`, `<link href>`, `fetch`, `XMLHttpRequest`, `import`, `@font-face` URL.
- [ ] File size is justified: < 300 KB for 2D, < 900 KB for 3D, larger only with a stated reason.
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
- [ ] Report back: path, size, what was verified, known limits, next step.

## Red flags that mean "not done"

- A game that can be lost but not restarted.
- A canvas that renders only after the second resize.
- Sound that works after clicking a button but not before (this one is fine — document it).
- `requestAnimationFrame` started twice (double speed / double CPU).
- Panels that stay in the DOM and capture clicks after closing.
- A score that resets because the save key is different from the load key.
