# Procedural art (2D canvas)

Every visual is a function call. The goal is not realism — it is **coherent, readable,
consistent** style across hundreds of generated objects.

## Palette first

Pick 6–10 colours with one accent. Store as CSS custom properties for UI and as a JS object
for canvas, generated from the same source so they cannot drift.

```js
const PAL = {
  ink:'#20332c', paper:'#f7f4e9', line:'#2f4b3f',
  a:'#5ba368', a2:'#3c7a4a',      // primary + shading
  b:'#efa63f', c:'#4f91c9', d:'#d85f4d', e:'#8a72c0',
  sky:'#9ed3c0', shadow:'rgba(24,48,38,.18)',
};
```

Rules that make generated art look designed rather than random:

- **Two tones per material** (base + darker). Three only for hero objects.
- **One outline colour** for everything (`PAL.line`), 2–2.6px, `lineJoin:'round'`. Mixed
  outline colours read as noise.
- **Light from one direction**, always. Highlights top-left, shadows bottom-right.
- **Saturation ceiling.** Keep generated colours under ~80% saturation; full saturation
  looks like a debug view.
- **Hue families per meaning**, not per object: green = nature/safe, red = damage, amber =
  interactable, blue = water/cool.

## Seeded randomness

Never call `Math.random()` inside a generator that runs per frame or per bake. Use a seeded
PRNG and a coordinate hash so the same tile looks the same every time.

```js
function mulberry32(seed){
  return function(){
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

// stable per-coordinate hash: identical output for identical inputs, no state
function hash3(x, y, k){
  let h = (x * 73856093 ^ y * 19349663 ^ k * 83492791) >>> 0;
  h = Math.imul(h ^ h >>> 15, 2246822519);
  return ((h ^ h >>> 13) >>> 0) / 4294967296;
}
```

`hash3` is what makes a tile field look hand-placed: grass blades, pebbles, flower positions
and colour variants all derive from their own tile coordinate.

## Shape primitives

Six helpers cover almost all 2D art. Write them once, at the top.

```js
const ell  = (g,x,y,rx,ry,fill,stroke,lw=2)=>{ g.beginPath(); g.ellipse(x,y,Math.max(.1,rx),Math.max(.1,ry),0,0,7); fill&&(g.fillStyle=fill,g.fill()); stroke&&(g.strokeStyle=stroke,g.lineWidth=lw,g.stroke()); };
const poly = (g,pts,fill,stroke,lw=2)=>{ g.beginPath(); g.moveTo(...pts[0]); pts.slice(1).forEach(p=>g.lineTo(...p)); g.closePath(); fill&&(g.fillStyle=fill,g.fill()); stroke&&(g.strokeStyle=stroke,g.lineWidth=lw,g.lineJoin='round',g.stroke()); };
const rr   = (g,x,y,w,h,r,fill)=>{ g.beginPath(); g.roundRect(x,y,w,h,r); g.fillStyle=fill; g.fill(); };
const curve= (g,pts,stroke,lw)=>{ g.beginPath(); g.moveTo(...pts[0]); for(let i=1;i<pts.length-1;i+=2) g.quadraticCurveTo(pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1]); g.strokeStyle=stroke; g.lineWidth=lw; g.lineCap='round'; g.stroke(); };
const glow = (g,x,y,r,c,a=.5)=>{ const gr=g.createRadialGradient(x,y,0,x,y,r); gr.addColorStop(0,c); gr.addColorStop(1,'transparent'); g.globalAlpha=a; g.fillStyle=gr; g.beginPath(); g.arc(x,y,r,0,7); g.fill(); g.globalAlpha=1; };
const txt  = (g,s,x,y,{size=24,fill='#fff',stroke=PAL.ink,lw=4,align='center'}={})=>{ g.font=`800 ${size}px ${FONT}`; g.textAlign=align; g.textBaseline='middle'; if(stroke){g.lineWidth=lw;g.strokeStyle=stroke;g.lineJoin='round';g.strokeText(s,x,y);} g.fillStyle=fill; g.fillText(s,x,y); };
```

## Characters: silhouette before detail

Generated creatures fail when they are built from parts without a shape. Build a
**silhouette** first, then add three details maximum (eyes, accent, one asymmetric trait).

```
body ellipse (wider than tall)  ->  limb/fin shapes  ->  accent shape (ears/leaf/fin)
->  two eyes at consistent spacing  ->  one mouth line  ->  blush or rim light
```

Consistency rules across a cast:

- Same eye radius-to-head ratio for every character.
- Same vertical eye position (roughly 35% down the head).
- Same outline width regardless of scale — scale the context, not the line width.
- Every character gets a contact shadow ellipse at the base: `ellipse(w*.9, h*.16, rgba(ink,.22))`.
- Idle motion is a sine bob of 1–2px, never zero.

## Tiles: bake once, blit forever

A 2048×2048 tile field costs seconds per frame if repainted; as one offscreen canvas it costs
one `drawImage`.

```js
const TS = 32;
function bakeMap(cols, rows, tileAt){
  const c = document.createElement('canvas');
  c.width = cols * TS; c.height = rows * TS;
  const g = c.getContext('2d');
  for (let y = 0; y < rows; y++)
    for (let x = 0; x < cols; x++)
      paintTile(g, x * TS, y * TS, tileAt(x, y));
  return c;                       // keep it; re-bake only on world change
}
```

Tile painter rules: fill base colour, add 6–12 deterministic specks, one directional
shadow, one highlight. Water gets two animated sine strokes drawn at runtime *on top of*
the baked base — cheap motion without re-baking.

## Effects layer

A flat array of short-lived records, updated and drawn after entities. Three kinds are enough:

```js
FX.push({k:'text', x, y, s:'+100', c:PAL.b, life:1.1, vy:-42});
FX.push({k:'spark', x, y, vx, vy, r:2+Math.random()*3, life:.6});
FX.push({k:'ring', x, y, r0:4, r1:46, life:.35});
```

Update with `life -= dt`, gravity for sparks, alpha = `clamp(life,0,1)` at draw. Cap the
array (drop oldest) so a chain reaction cannot tank the frame.

## Screen feel

- **Vignette:** a CSS overlay (`box-shadow: inset 0 0 140px rgba(...)`) — free, no per-frame
  cost.
- **Shake:** offset the camera by `(rand()-.5) * amp`, decaying `amp *= 0.86` per frame.
- **Hit flash:** draw the entity's silhouette again with `globalCompositeOperation='lighter'`
  and low alpha for 3 frames.
- **Damage/health feedback:** desaturate and tint the whole frame via two nested overlays;
  cheaper and more readable than per-entity effects.

## Faking depth in 2D

Y-sort entities (`entities.sort((a,b)=>a.y-b.y)`), scale with a single depth factor, and
darken distant layers by mixing toward the fog colour. Three depth layers plus a parallax
offset is enough to read as 2.5D.
