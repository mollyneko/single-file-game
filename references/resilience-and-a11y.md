# Resilience and accessibility

The file will be opened in a browser you have never seen, on hardware you do not own. Assume
the worst and degrade instead of dying.

## Error boundary

Three layers, in order of severity.

```js
const ERRS = [];
function fatal(e){
  const msg = (e && (e.message || e.reason && e.reason.message)) || String(e);
  if (!ERRS.includes(msg)) ERRS.push(msg);
  const el = document.getElementById('fatal');
  if (el) {
    el.classList.remove('hide');
    el.textContent = 'Something went wrong: ' + msg;
  }
  document.body.dataset.error = msg;          // machine-readable, survives to a bug report
  if (window.G) G.errs = ERRS.length;
}
addEventListener('error', ev => fatal((ev.message || 'error') + ' @' + (ev.lineno || 0)));
addEventListener('unhandledrejection', ev => fatal(ev.reason));
```

The banner must be readable, dismissible, and must not cover the whole screen — the player
should still see that the page works and be able to copy the message.

Wrap risky subsystems so one failure does not take the game down:

```js
function safe(name, fn, fallback){
  try { return fn(); }
  catch (e) { console.warn('[safe]', name, e); return fallback; }
}
// const audio = safe('audio', initAudio, null);
// const gl    = safe('webgl', initGL, null);   -> if null, run the 2D path
```

Do not wrap the whole game in one `try`. You will lose the frame loop and the error will look
like a freeze.

## Debug overlay

Behind `?debug=1` or a key chord, show: scene name, fps, frame ms (avg/p99), entity count,
error count, quality tier, DPR. This is what turns "it's slow" into "it's the shadow pass".

```html
<div id="dbg" hidden></div>
```

```js
if (new URLSearchParams(location.search).has('debug')) dbgEl.hidden = false;
```

## Reduced motion

Honour it. It is an accessibility requirement and it also happens to help weak hardware.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
  }
}
```

```js
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches || settings.reduceMotion;
if (reduceMotion) { shakeAmp = 0; bob = 0; screenFlash = 0; }
```

Keep gameplay information that motion carried (hit direction, damage) in a static form: a
tint, an arrow, a number. Reduced motion must not mean reduced feedback.

## Contrast and readability

- Body text ≥ 4.5:1 against its background; large display text ≥ 3:1.
- Never rely on hue alone — damage/health/success also need shape, icon or position.
- Put a text shadow or a scrim behind HUD text over gameplay. A dark stroke on a light chip
  reads at any background (the classic `strokeText` + `fillText` pair).
- Minimum HUD font 12 px, minimum touch label 14 px.
- Respect `color-scheme` and do not fight the OS.

## Keyboard and focus

- Every interactive element is a `<button>` or has `tabindex="0"` and a key handler.
- Visible focus ring (`:focus-visible`) with a 2 px outline — do not `outline:none` without a
  replacement.
- `Escape` closes the topmost panel; `Enter` activates the focused action.
- When a panel opens, move focus into it; when it closes, return focus to where it was.
- Screens use `role="dialog"` with `aria-modal="true"` and a label.

## Semantics

```html
<section class="screen" role="dialog" aria-modal="true" aria-label="Paused">
  <h2>Paused</h2>
  <div class="actions">
    <button data-act="resume">Resume</button>
  </div>
</section>
```

Screen-reader users will not play a fast action game, but they will hit the title screen,
read the controls, and judge the work. Label the canvas (`aria-label`) and the HUD regions.

## Graceful degradation ladder

| Missing | Degrade to |
| --- | --- |
| WebGL2 | 2D canvas path, same scene machine |
| WebAudio | silent play, all calls no-op |
| `localStorage` | in-memory save, toast once |
| Pointer lock | drag-to-look |
| Touch | mouse/keyboard |
| Gamepad | ignore |
| Reduced motion | static feedback |
| Small viewport | compact HUD, landscape hint |

Each row is a `try/catch` or a capability check plus one fallback path — an hour of work that
turns a fragile demo into something you can hand to a stranger.

## Never do

- `throw` inside `requestAnimationFrame` without catching — you lose the loop permanently.
- `alert()` for errors: it blocks the loop and looks broken.
- A full-screen "unsupported browser" wall: degrade, do not gate.
- `document.write`, `eval` of remote content, or inline event attributes (`onclick="…"`).
- Autoplay audio or video on load.
