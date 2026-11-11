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

## Pointer and pointer lock (3D look)

Pointer lock gives infinite mouse travel but needs a gesture and can fail (iframes, some
browsers). Always implement the drag fallback.

```js
cv.addEventListener('click', () => {
  if (cv.requestPointerLock) cv.requestPointerLock().catch(() => {});
});

addEventListener('mousemove', e => {
  if (document.pointerLockElement === cv) {
    input.look.dx += e.movementX; input.look.dy += e.movementY;
  } else if (dragging) {                        // fallback: drag to look
    input.look.dx += e.movementX; input.look.dy += e.movementY;
  }
});
```

Show a hint ("click to capture mouse") only when lock is unavailable, and never block play
waiting for it.

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
