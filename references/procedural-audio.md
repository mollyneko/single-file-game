# Procedural audio

All sound is synthesized with WebAudio at runtime. No audio files, no base64 blobs — a base64
WAV costs more bytes than the whole game and defeats the point of the format.

## The bus

One master gain, created lazily on the first real gesture (browsers block audio before that).

```js
let AC = null, master = null;

function audioInit(){
  if (AC) return;
  const C = window.AudioContext || window.webkitAudioContext;
  if (!C) return;                          // degrade silently: a silent game still plays
  try {
    AC = new C();
    master = AC.createGain();
    master.gain.value = settings.volume * 0.42;
    master.connect(AC.destination);
  } catch { AC = null; }
  if (AC && AC.state === 'suspended') AC.resume().catch(() => {});
}

['pointerdown', 'keydown', 'touchstart'].forEach(ev =>
  addEventListener(ev, audioInit, { once: true, passive: true }));
```

Every voice starts with `if (!AC) return`. That single guard makes the whole game safe in
muted tabs, headless tests and unsupported browsers.

Suspending on tab hide and resuming on return prevents a burst of queued notes:

```js
document.addEventListener('visibilitychange', () =>
  document.hidden ? AC && AC.suspend() : audioInit());
```

## A voice

Three parameters cover 90% of SFX: an oscillator sweep, an envelope, and optional noise.

```js
function tone(freq, dur, type = 'square', vol = .1, when = 0, slideTo = 0){
  if (!AC) return;
  const t = AC.currentTime + when;
  const o = AC.createOscillator(), g = AC.createGain();
  o.type = type;
  o.frequency.setValueAtTime(Math.max(20, freq), t);
  if (slideTo) o.frequency.exponentialRampToValueAtTime(Math.max(20, slideTo), t + dur);
  g.gain.setValueAtTime(.0001, t);
  g.gain.linearRampToValueAtTime(Math.max(.0002, vol), t + .012);  // fast attack
  g.gain.exponentialRampToValueAtTime(.0001, t + dur);             // no click on release
  o.connect(g); g.connect(master);
  o.start(t); o.stop(t + dur + .03);
}
```

Never ramp exponentially to exactly `0` — it throws. Use `0.0001`. Never use
`linearRampToValueAtTime` for the release — it clicks.

## Noise, created once

The buffer is the expensive part, not the source. Create one, reuse it forever.

```js
let noiseBuf = null;
function noise(dur, vol, when = 0, freq = 1200, q = .8){
  if (!AC) return;
  const t = AC.currentTime + when;
  if (!noiseBuf){
    noiseBuf = AC.createBuffer(1, AC.sampleRate * 2, AC.sampleRate);
    const d = noiseBuf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
  }
  const s = AC.createBufferSource(), g = AC.createGain(), f = AC.createBiquadFilter();
  s.buffer = noiseBuf;
  f.type = 'bandpass'; f.frequency.value = freq; f.Q.value = q;
  g.gain.setValueAtTime(Math.max(.0002, vol), t);
  g.gain.exponentialRampToValueAtTime(.0001, t + dur);
  s.connect(f); f.connect(g); g.connect(master);
  s.start(t); s.stop(t + dur + .02);
}
```

Band-passed noise is impact, explosion, footstep, water, wind and gunshot. One primitive,
a dozen sounds. Sweep the filter frequency for variation instead of building new voices.

## SFX table

Name every sound once, in one object, so mixing is reviewable in one place.

```js
const SFX = {
  click:    () => tone(660, .06, 'square', .11, 0, 880),
  cancel:   () => tone(330, .09, 'square', .08, 0, 220),
  hit:      () => { noise(.16, .16, 0, 700); tone(180, .14, 'sawtooth', .09, 0, 90); },
  pickup:   () => [523, 659, 784].forEach((f, i) => tone(f, .12, 'square', .09, i * .06)),
  error:    () => tone(220, .18, 'square', .09, 0, 140),
  levelUp:  () => [523, 587, 659, 784, 880, 1047].forEach((f, i) => tone(f, .22, 'triangle', .1, i * .08)),
};
const sfx = name => { if (!AC || !SFX[name]) return; try { SFX[name](); } catch {} };
```

Mix levels by ear, then fix them: UI ticks ~0.08–0.12, hits 0.12–0.18, fanfares 0.1 with
overlapping notes. Anything above 0.2 clips when three sounds land on the same frame — add a
short ducking gain if your game chains effects.

## Music without files

A step sequencer on a `setInterval`, reading a note table. Four bars of sixteen steps is
enough, and a scene switch simply swaps the table.

```js
const SONGS = {
  calm:  [60,0,64,67, 0,64,62,0, 60,0,55,60, 64,0,62,0],
  tense: [48,48,0,55, 48,0,58,55, 48,48,0,60, 58,55,48,0],
};

let step = 0, timer = null, current = 'calm';
const mtof = n => 440 * Math.pow(2, (n - 69) / 12);

function tick(){
  const seq = SONGS[current], n = seq[step % seq.length];
  if (n) tone(mtof(n), .16, 'triangle', .075);
  if (step % 4 === 1) tone(mtof(n - 24), .2, 'sine', .05);   // bass
  if (step % 8 === 1) noise(.05, .018, 0, 3000);             // hat
  step++;
}
function setMusic(name){
  if (current !== name) { current = name; step = 0; }
  if (!timer) timer = setInterval(tick, 190);
}
```

190 ms per step ≈ 79 BPM at 16th notes. Change the interval for tempo; never rebuild the
interval to change songs.

## Spatial cues without a 3D audio graph

Pan by screen position with a `StereoPannerNode`, attenuate by distance, and add a
low-pass as things move away. Two lines, convincing enough:

```js
function at(name, pan = 0, dist = 0){
  if (!AC) return;
  const p = AC.createStereoPanner();
  p.pan.value = clamp(pan, -1, 1);
  p.connect(master);
  // route this one voice through p, gain *= 1 / (1 + dist * .08)
}
```

## Rules

- **Never autoplay music before a gesture.** It is blocked, and the failure looks like a bug.
- **Every action gets a sound.** Silent buttons feel broken. Even a 4 ms tick helps.
- **Vary repeated sounds.** Randomise pitch ±6% and volume ±10% per hit or footsteps become
  a machine gun.
- **One `master` gain only.** Volume settings scale it; do not chase individual gains.
- **Cap concurrency.** More than ~24 simultaneous voices on mobile causes dropouts; skip
  voices when `activeVoices > cap`.
