# State and persistence

Two storage keys, one shape, zero crashes.

## Keys

```
<game-slug>:save:v1        progress, score, unlocks
<game-slug>:settings:v1    volume, quality, sensitivity, reduce-motion, invert
```

Separate them. Settings must survive a save wipe, and a corrupted save must not take the
volume slider with it. The version lives in the key *and* in the payload so you can migrate
either way.

## Guarded access

`localStorage` throws in private mode, in sandboxed iframes, and on quota. Wrap it once and
never touch the raw API again.

```js
const store = {
  get(key, fallback){
    try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; }
    catch { return fallback; }
  },
  set(key, value){
    try { localStorage.setItem(key, JSON.stringify(value)); return true; }
    catch { return false; }                                  // quota or blocked: play on
  },
  del(key){ try { localStorage.removeItem(key); } catch {} },
};
```

If `set` returns `false`, show a single non-blocking toast ("progress won't be saved in this
browser") and keep playing. Never throw an error into the boot path.

## Save shape

Flat, JSON-safe, human-readable, with a version and a timestamp. Everything the player would
be upset to lose, and nothing derivable.

```js
function newSave(){
  return {
    v: 1,
    t: Date.now(),
    best: 0,
    runs: 0,
    unlocked: ['default'],
    settings: undefined,        // never duplicated here
  };
}

function loadSave(){
  const s = store.get(SAVE_KEY, null);
  if (!s || typeof s !== 'object') return newSave();
  if (s.v !== 1) return migrate(s);
  return { ...newSave(), ...s };
}
```

Booleans and numbers only where possible. If you must store complex state, store IDs and
rebuild objects from the tables on load — saves built from tables survive balance changes.

## Migration

```js
function migrate(old){
  let s = { ...newSave() };
  if (!old.v || old.v < 1) { /* v0 shape → v1 */ }
  if (old.v === 1) s = { ...s, ...old, v: 2 };
  store.set(SAVE_KEY, s);
  return s;
}
```

Rules: migrate forward only, never delete unknown fields silently, and test with a
deliberately corrupted payload (`{"v":1,` truncated) plus a wrong-type payload
(`{"best":"lots"}`).

## Autosave

Save on meaningful events, not on a timer, and throttle:

```js
let dirty = false, lastWrite = 0;
function markDirty(){ dirty = true; }
function flush(force){
  if (!dirty && !force) return;
  const now = performance.now();
  if (!force && now - lastWrite < 4000) return;     // at most every 4 s
  store.set(SAVE_KEY, state); dirty = false; lastWrite = now;
}
```

Triggers: run end, level complete, purchase, unlock, settings change, `pagehide`.

```js
addEventListener('pagehide', () => flush(true));    // more reliable than beforeunload
```

Do not save every frame. Serialising a large object at 60 Hz causes visible hitches and will
eventually hit quota.

## Resume semantics

Decide explicitly and write it in the UI:

- **Arcade / run-based:** persist only `best` and unlocks; a run always starts fresh.
- **Session-based:** persist a checkpoint (position, health, inventory) and offer "Continue"
  on the title screen; disable the button when no checkpoint exists.

For session saves, store a schema version per checkpoint and rebuild entities from the tables:

```js
{ v:1, t:..., scene:{ id:'zone-3', pos:[12.5, 0, -4.0], yaw:1.57 },
  player:{ hp:72, items:{ key:1 }, flags:{ gateOpen:true } } }
```

Never serialise live objects, DOM nodes, textures or functions. If it cannot be `JSON.parse`d
into a working state, it does not belong in a save.

## Settings

`settings` is read before anything renders (so quality and volume apply to the first frame)
and written on change with debounce. Clamp every value on read — a hand-edited
`localStorage` should never produce a NaN sensitivity.

```js
const DEFAULTS = { volume:.6, quality:'auto', sens:1, invert:false, reduceMotion:false };
const settings = { ...DEFAULTS, ...store.get(SET_KEY, {}) };
for (const k in DEFAULTS)
  if (typeof settings[k] !== typeof DEFAULTS[k]) settings[k] = DEFAULTS[k];
```
