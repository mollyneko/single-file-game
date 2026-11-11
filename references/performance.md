# Performance

A single HTML file usually means a single thread doing everything. Budget accordingly.

## The frame budget

60 fps = 16.6 ms. Plan for 12 to leave headroom for the browser and the GC.

| Stage | 2D target | 3D target |
| --- | --- | --- |
| Simulation | 1–2 ms | 1–2 ms |
| Draw calls / blits | 3–5 ms | 8–12 ms |
| Effects | 1–2 ms | 2–3 ms |
| HUD/DOM writes | <1 ms | <1 ms |

Measure, do not guess. A rolling window of the last 120 frame times, median plus p99, printed
in the debug overlay, catches the spikes that averages hide.

```js
const times = [];
function stats(dt){
  times.push(dt * 1000);
  if (times.length > 120) times.shift();
  const s = [...times].sort((a, b) => a - b);
  dbg.avg = times.reduce((a, b) => a + b, 0) / times.length;
  dbg.p99 = s[Math.floor(s.length * .99)] || 0;
}
```

## Bake, don't redraw

Anything static should be rasterised once.

- **Tiles and maps:** one offscreen canvas, one `drawImage` per frame with a source rect.
- **Repeated sprites:** pre-render each rotation/scale variant at boot into an atlas, or draw
  from a cached `Path2D`.
- **Text:** `fillText` with a stroke is expensive. Cache rendered labels into sprites when
  they repeat (damage numbers, HUD chips).
- **Gradients:** creating a gradient per frame allocates; hoist it out of the draw loop.
- **Shadows:** `shadowBlur` is the single most expensive 2D feature. Use a blurred sprite or
  a soft ellipse instead.

## Allocation discipline

Garbage collection shows up as a periodic 8–16 ms hitch. The fix is boring: stop allocating
in the loop.

```js
// bad: new array and new objects every frame
for (const e of entities) {
  const p = { x: e.x, y: e.y };
  draw(e, p);
}

// good: reuse
for (let i = 0; i < entities.length; i++) draw(entities[i]);

// pooling for short-lived objects
const pool = [];
function spawn(){ return pool.pop() || {}; }
function despawn(o){ pool.push(o); }
```

Same for vectors (`{x,y}` in a hot loop), template strings in HUD updates, and `JSON.stringify`
during play.

## Draw call reduction

- **Merge** static geometry into one buffer (3D) or one baked canvas (2D).
- **Instance** anything repeated: grass, bullets, particles, crates.
- **Sort by state** (texture/material) to avoid rebinding; bind once, draw many.
- **Cull** by screen rect / frustum before touching the GPU, and skip off-screen HUD updates.
- Target under 150 draw calls in WebGL; under 200 blits in 2D.

## Resolution

`devicePixelRatio` scaling is the largest single cost on phones. Cap it.

```js
const dpr = Math.min(window.devicePixelRatio || 1, isTouch ? 1.5 : 2) * qualityScale;
```

Offer a resolution slider (0.75 / 1.0 / 1.25) in settings. Players on weak hardware would
rather have a slightly soft image than a stuttering one.

## Adaptive quality

Detect, do not ask.

```js
function adapt(){
  if (dbg.median > 22 && tier > 0) setTier(tier - 1, 'auto');
  else if (dbg.median < 11 && tier < MAX - 1) setTier(tier + 1, 'auto');
}
```

Rules: one step at a time, at least 2 s between steps, hysteresis (upgrade threshold strictly
below downgrade threshold), and never more than one automatic downgrade per session without
telling the player.

## DOM cost

The HUD is DOM in most single-file games because it is faster to build and style. Keep it
cheap:

- Transform and opacity only for animation; never animate `width`, `top` or `box-shadow`.
- Cache node references; never `querySelector` in the loop.
- Batch text writes: only touch `textContent` when the value actually changed.
- `will-change: transform` on the handful of moving elements, nothing else.
- Hide panels with `display:none`, not by rebuilding them.

## Memory

A long session should be flat. Watch for: unbounded effect arrays, `setInterval`s created per
event, event listeners added per restart, timers never cleared, and base64 strings held in
state. Cap every growing collection (`if (arr.length > N) arr.shift()`), and clear intervals
in scene `exit()`.

## Startup

- First paint under 1 s; interactive under 2 s.
- Do heavy bakes after the first paint, with `await new Promise(requestAnimationFrame)` between
  stages so the boot bar actually moves.
- If a bake would take more than ~300 ms, show progress text, not a frozen bar.
- Never block boot on fonts, analytics or anything remote.
