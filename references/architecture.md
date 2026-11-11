# Architecture

The shell is boring on purpose. Gameplay changes every project; the shell should not.

## File layout

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
  <title>GAME TITLE</title>
  <style>
    /* 1. tokens        2. reset + shell
       3. HUD           4. screens (boot/title/pause/over)
       5. panels        6. responsive      7. reduced motion */
  </style>
</head>
<body>
  <canvas id="cv" tabindex="0"></canvas>
  <div id="hud">…</div>          <!-- pointer-events:none, children opt in -->
  <div id="title" class="screen hide">…</div>
  <div id="pause" class="screen hide">…</div>
  <div id="over"  class="screen hide">…</div>
  <div id="toast"></div>
  <div id="fatal" class="hide"></div>
  <div id="dbg" hidden></div>
  <script>(()=>{ 'use strict'; /* … */ })();</script>
</body>
</html>
```

Layers are ordered back-to-front: canvas, HUD, screens, toast, fatal. Every full-screen
layer is `position:absolute; inset:0`. Only the canvas and the visible screen receive input;
the HUD layer is `pointer-events:none` with interactive children re-enabled individually.

## Script order inside the IIFE

Ordered so nothing is referenced before it exists. Keep the section banners — they are the
map for whoever edits this next.

```
helpers      $  $$  clamp  lerp  wait  rng(seed)  pick  pad
storage      save/load settings, versioned, try/catch
audio        ctx, master bus, tone(), noise(), sfx table, music tick
input        keyboard + pointer + touch + gamepad -> intents object
art          palette, offscreen bakes, draw primitives
world        entities, spawn tables, collision
scenes       boot, title, play, paused, over  (enter/exit/update/draw)
loop         rAF, fixed-step accumulator, resize, visibility pause
bootstrap    boot() -> first frame
```

## Scene machine

A single `scene` string plus a switch in `update`/`draw`. No routing, no history, no
transition framework. Screens are DOM nodes toggled by class; the canvas is always alive
underneath, which makes pause and restart instant.

```js
const SCENES = {
  boot:   { enter(){…}, update(dt){…}, draw(g){…} },
  title:  { enter(){ show('#title'); }, exit(){ hide('#title'); } },
  play:   { enter(){ reset(); }, update: updatePlay, draw: drawPlay },
  paused: { enter(){ show('#pause'); }, exit(){ hide('#pause'); } },
  over:   { enter(){ show('#over'); } },
};

let scene = 'boot';
function go(next){
  const cur = SCENES[scene];
  if (cur && cur.exit) cur.exit();
  scene = next;
  const nxt = SCENES[next];
  if (nxt && nxt.enter) nxt.enter();
  if (window.G) G.scene = next;          // mirror for debug readout
}
```

Rules that keep this honest:

- **Pause freezes simulation, not the loop.** The loop keeps running to animate the pause
  card; `update` is skipped.
- **Restart is `go('title')` or `reset(); go('play')`** — never a page reload. A reload
  throws away the asset bakes and makes the second run visibly slower.
- **Screens never own state.** They read from the game object and dispatch named actions
  (`data-act="retry"`). One delegated click handler on `document` is enough.

## Loop contract

```js
let last = 0, acc = 0;
const STEP = 1 / 60;                       // simulate at a fixed rate

function frame(now){
  requestAnimationFrame(frame);
  const raw = (now - last) / 1000; last = now;
  const dt = Math.min(raw, 0.1);            // clamp: tab-switch spikes must not teleport
  if (scene !== 'paused' && scene !== 'title') {
    acc += dt;
    let guard = 0;
    while (acc >= STEP && guard++ < 5) { simulate(STEP); acc -= STEP; }
  }
  render(dt);                                // presentation may use variable dt
  input.endFrame();                          // clear per-frame edge flags
  stats(dt);
}
```

Why fixed step: collision and physics become reproducible, and a 144Hz monitor does not
change difficulty. Why the clamp and guard: coming back from a background tab must not
simulate 400 steps at once.

## Resize and device pixel ratio

```js
function resize(){
  const dpr = Math.min(window.devicePixelRatio || 1, QUALITY.dprCap);
  const w = cv.clientWidth, h = cv.clientHeight;
  cv.width  = Math.round(w * dpr);
  cv.height = Math.round(h * dpr);
  g.setTransform(dpr, 0, 0, dpr, 0, 0);     // draw in CSS pixels from here on
  W = w; H = h;
}
addEventListener('resize', resize, { passive: true });
```

Cap the DPR (2 on desktop, 1.5–2 on phones). A 3x phone at full resolution is four times the
fill cost of 1.5x for no visible gain on a handset.

## Boot sequence

1. Read settings and save (guarded).
2. Show boot screen with a determinate bar tied to real work: bake tiles/sprites, build the
   map texture, compile shaders. `await wait(0)` between stages so the bar paints.
3. Wire the first-gesture unlock for audio (`pointerdown`/`keydown`, once).
4. `resize()`, attach listeners, `requestAnimationFrame(frame)`.
5. Fade the boot layer out, `go('title')`.

Never gate boot on a network request. If you cannot finish a bake, degrade (flat colours
instead of textures) and keep playing.

## Visibility

```js
document.addEventListener('visibilitychange', () => {
  if (document.hidden) { if (scene === 'play') go('paused'); audioSuspend(); }
  else { last = performance.now(); audioResume(); }
});
```

Auto-pausing on hide is the single cheapest way to avoid "I came back and I was dead".
