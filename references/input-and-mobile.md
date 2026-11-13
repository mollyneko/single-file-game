# Input and mobile

One intent object, four sources. Gameplay code never asks "was W pressed".

## The intent layer

```js
const input = {
  move:   { x: 0, y: 0 },        // -1..1, screen/world space
  look:   { dx: 0, dy: 0 },      // accumulated this frame
  fire: false, alt: false, sprint: false,
  jump: false, interact: false, pause: false,
  // edge-triggered: true only on the frame the action started
  pressed(name){ return edges.has(name); },
  endFrame(){ edges.clear(); this.look.dx = this.look.dy = 0; },
};

const edges = new Set();
const press = n => edges.add(n);
```

Keyboard, pointer, touch and gamepad all *write into the same object*. A new device is a new
writer, never a new branch in gameplay.

## Keyboard

Track a `Set` of codes, not booleans — this survives focus loss correctly.

```js
const keys = new Set();
addEventListener('keydown', e => {
  if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space'].includes(e.code)) e.preventDefault();
  if (!keys.has(e.code)) press(e.code);          // edge on first press only
  keys.add(e.code);
});
addEventListener('keyup', e => keys.delete(e.code));
addEventListener('blur', () => keys.clear());    // otherwise the player runs forever
```

Map to intent once per frame:

```js
input.move.x = (keys.has('KeyD') || keys.has('ArrowRight') ? 1 : 0) - (keys.has('KeyA') || keys.has('ArrowLeft') ? 1 : 0);
input.move.y = (keys.has('KeyS') || keys.has('ArrowDown') ? 1 : 0) - (keys.has('KeyW') || keys.has('ArrowUp') ? 1 : 0);
```

`blur` → `keys.clear()` is the single most commonly forgotten line in browser games.

## Pointer: free-look is the default (3D) — MUST

`SKILL.md` §2A.C. **Moving the mouse turns the camera immediately, with no button held and no
drag.** The very first mouse movement in the game must move the camera. Drag-to-look is
**opt-in**: use it only when the user explicitly asks for drag controls, and mark that file with
`DRAG_LOOK_OPT_IN` so the auditor knows it was requested.

Pointer lock is an *optional enhancement* for infinite travel (FPS-style, cursor hidden). It
needs a gesture, can fail in iframes, and must never be the only way to look around. Never show
a "click to capture mouse" gate that blocks play.

```js
// HARD CONSTRAINT: free-look by default; --craft looks for this marker.
const FREE_LOOK = true;
let lastX = 0, lastY = 0;

cv.addEventListener('pointermove', e => {
  if (e.pointerType === 'touch') return;        // touch look is handled below
  const locked = document.pointerLockElement === cv;
  const dx = locked ? (e.movementX || 0) : (e.clientX - lastX);
  const dy = locked ? (e.movementY || 0) : (e.clientY - lastY);
  lastX = e.clientX; lastY = e.clientY;
  input.look.dx += dx; input.look.dy += dy;      // unconditional — no dragging flag
});
cv.addEventListener('pointerdown', e => {
  if (e.pointerType === 'mouse' && e.button === 0) press('attack');   // click is an action,
  lastX = e.clientX; lastY = e.clientY;                               // never a look gate
});
// Optional: a click may capture the pointer. Failure changes nothing about play.
cv.addEventListener('dblclick', () => {
  if (cv.requestPointerLock) { try { cv.requestPointerLock(); } catch (er) {} }
});
```

Rules:

- No `dragging`, `e.buttons` or `pointerdown` guard around the mouse `look.dx/dy` write.
  A guarded mouse handler fails `--craft` unless `DRAG_LOOK_OPT_IN` is present.
- Mouse buttons are gameplay actions (attack / skill / interact), not camera gates.
- Pointer lock only changes where deltas come from (`movementX/Y` vs `clientX/Y` deltas).
- On `blur` / `pointerleave`, reset `lastX/lastY` so the first move back does not jump.
- On touch, dragging the right half of the screen still looks around; that is a different
  device and does not conflict with this rule. The left half remains the virtual stick.
- Inverted Y, sensitivity and a "lock pointer" toggle belong in settings.

## Pointer lock fallback (only when the user asked for drag controls)

If — and only if — the brief explicitly asks for drag-to-look, declare
`const DRAG_LOOK_OPT_IN = true;` and gate the mouse deltas on the active drag:

```js
const DRAG_LOOK_OPT_IN = true;                 // user explicitly requested drag controls
cv.addEventListener('pointermove', e => {
  if (document.pointerLockElement === cv || dragLook.active) {
    input.look.dx += e.movementX || 0; input.look.dy += e.movementY || 0;
  }
});
```

Even then, keep pointer lock available and never block play waiting for a gesture.

## Touch

A virtual stick that spawns where the thumb lands is better than a fixed one, and it works in
both portrait and landscape.

```js
let stick = null;                              // {id, ox, oy}

cv.addEventListener('touchstart', e => {
  for (const t of e.changedTouches) {
    if (t.clientX < innerWidth * 0.5 && !stick) {
      stick = { id: t.identifier, ox: t.clientX, oy: t.clientY };
    } else { press('fire'); input.fire = true; }
  }
  e.preventDefault();
}, { passive: false });

cv.addEventListener('touchmove', e => {
  for (const t of e.changedTouches) {
    if (stick && t.identifier === stick.id) {
      const dx = t.clientX - stick.ox, dy = t.clientY - stick.oy;
      const m = Math.min(1, Math.hypot(dx, dy) / 56);
      const a = Math.atan2(dy, dx);
      input.move.x = Math.cos(a) * m; input.move.y = Math.sin(a) * m;
    } else if (t.clientX > innerWidth * 0.5) {
      input.look.dx += t.clientX - (t.lastX ?? t.clientX);
      t.lastX = t.clientX;
    }
  }
  e.preventDefault();
}, { passive: false });

cv.addEventListener('touchend', e => {
  for (const t of e.changedTouches) {
    if (stick && t.identifier === stick.id) { stick = null; input.move.x = input.move.y = 0; }
    else { input.fire = false; }
  }
});
```

Non-negotiables on touch:

- `touch-action: none` on the canvas, or the page scrolls under the game.
- `user-select: none` and `-webkit-tap-highlight-color: transparent` on the body.
- Hit targets ≥ 44×44 CSS px, spaced ≥ 8 px.
- Buttons are real `<button>`s in the DOM, not canvas hit-testing — you get focus, labels and
  accessibility for free.
- `viewport-fit=cover` plus `env(safe-area-inset-*)` padding on every HUD edge.

```css
#hud { padding: calc(10px + env(safe-area-inset-top)) calc(10px + env(safe-area-inset-right))
                 calc(10px + env(safe-area-inset-bottom)) calc(10px + env(safe-area-inset-left)); }
```

- Detect touch by capability, not user agent:

```js
const IS_TOUCH = navigator.maxTouchPoints > 0 && matchMedia('(pointer: coarse)').matches;
```

Show touch controls when `IS_TOUCH`, and also expose a toggle in settings for hybrids.

## Gamepad

Poll it in the frame loop; there is no reliable event for analog sticks.

```js
const gp = navigator.getGamepads?.()[0];
if (gp) {
  const ax = Math.abs(gp.axes[0]) > .18 ? gp.axes[0] : 0;
  const ay = Math.abs(gp.axes[1]) > .18 ? gp.axes[1] : 0;
  if (ax || ay) { input.move.x = ax; input.move.y = ay; }
  if (gp.buttons[0].pressed) input.jump = true;
  input.look.dx += gp.axes[2] * 12;
}
```

Dead zone first, always. Analog drift makes a game unplayable in a way players blame on you.

## Pause and focus

- `Escape` / `Start` toggles pause. `P` as an alias.
- On `visibilitychange` → hidden, auto-pause if playing.
- Restore focus to the canvas after closing a panel so keyboard control resumes.
- Never bind a gameplay key to a browser shortcut (`Ctrl+W`, `Cmd+Q`, `F5`).
