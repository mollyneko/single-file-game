# Game feel

A game can be lit perfectly and still feel dead. Feel is the set of signals that tell the
player their input mattered, and it is cheaper to add than a single new asset.

The rule: **every state change gets at least two channels.** One channel reads as a bug; two
channels read as an event.

## The feedback table

For each event in your game, fill this in before writing the code. If a row has one entry, it
is not finished.

| Event | Visual | Audio | Camera | HUD |
| --- | --- | --- | --- | --- |
| Pick up | scale-pop + burst + light pulse | two-note rise | 4 px shake | counter counts up |
| Take damage | 120 ms red edge + freeze 60 ms | filtered noise hit | 8 px shake | bar drains with easing |
| Fail | desaturate + slow-mo 200 ms | descending third | pull back | card slides in |
| Start | 300 ms fade from black | rising swell | FOV +3° | HUD fades in last |
| Move | footstep bob | bandpassed noise per step | 4 cm sine | — |
| Idle | breathing / bobbing | room tone | 0.03 rad/s drift | — |

## Impact: hitstop, shake, pop

Three primitives, each three lines, each used everywhere.

**Hitstop** — freeze the simulation for 40–80 ms on a heavy hit. Not the render: keep drawing,
skip `update()`:

```js
if (hitstop > 0) { hitstop -= dt; return; }
```

**Shake** — one decaying scalar, consumed by the camera, never by gameplay:

```js
cam.shake = Math.max(0, cam.shake - dt * 2.4);
cam.y += cam.shake * 0.05 * Math.sin(time * 61.0);
```

**Pop** — scale up 12% over 80 ms, back over 160 ms, eased. Apply to the thing that was hit,
not to the whole screen.

Damage numbers, dust puffs and screen flashes are all the same three primitives with different
parameters. Build them once.

## Easing

Linear motion is the loudest amateur tell. Four curves cover everything:

```js
const easeOut  = t => 1 - Math.pow(1 - t, 3);       // things arriving
const easeIn   = t => t * t * t;                     // things leaving
const easeInOut= t => t < .5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3)/2;
const overshoot= t => 1 + 2.2*Math.pow(t-1,3) + 1.2*Math.pow(t-1,2);  // buttons, pickups
```

Anything that moves toward the player uses `easeOut`. Anything the player pushes uses
`easeOut` with a shorter duration. Nothing in a game moves linearly except a bullet.

## Camera

The camera is a character. Give it:

- **Idle drift.** 0.03 rad/s of yaw plus a two-octave sine. It costs nothing and removes the
  "static render" feel entirely.
- **Walk bob.** `sin(bob) * 0.038` on Y, phase-locked to footsteps, and *stopped* by
  `prefers-reduced-motion`.
- **Look-ahead.** Offset the target by 8% of velocity so the player sees where they are going.
- **Impact kick.** 1.5° of pitch on a heavy event, decaying in 200 ms.
- **No roll.** Except 0.5° on strafe, and only if the game is a vehicle.

## Particles: the 3-layer rule

A burst reads as an effect when it has three layers with different physics:

1. **Core** — 4–8 bright, fast, short-lived (0.15 s), additive.
2. **Body** — 12–20 medium, gravity-affected, tinted by the surface (0.4 s).
3. **Dust** — 6–10 large, slow, low alpha, expanding (0.8 s).

One layer is a sprite. Three layers is an explosion. Pool them: allocate a fixed array at boot,
never `new` in the loop.

## Audio: three voices per action

WebAudio gives you three cheap layers that, stacked, sound expensive:

```js
tone(520, 0.50, 'triangle', 0.14, 780);   // body: pitch sweep
tone(1040, 0.70, 'sine', 0.06, 1560);     // air: octave above, quieter, longer
noise(0.12, 0.08, 0, 2400);               // transient: bandpassed noise
```

Rules that matter more than the synthesis:

- **Init on the first gesture**, never on load. Browsers block audio before interaction.
- **Never the same pitch twice.** ±3% random detune on every repeated SFX; identical repeats
  become machine-gun artifacts within seconds.
- **Duck, don't mute.** On pause, ramp the master gain to 0 over 120 ms before suspending.
- **One ambient bed.** Two detuned sines at 54/81 Hz through a lowpass is a room. It makes
  silence audible.

## HUD motion

- Numbers **count** to their new value over 200 ms; never snap.
- Bars ease out over 180 ms and overshoot 2% when they refill.
- The HUD fades in 400 ms *after* the world appears, so the first frame is the world.
- Anything that can be a diegetic element (a light on the object, a glow on the ground) is
  better in the world than in a corner.
- Tabular numerals (`font-variant-numeric: tabular-nums`) or the score jitters as it counts.

## The one-second test

Play for one second and count the distinct feedback events. A game with movement, a pickup and
a footstep should produce four or five. Zero means the simulation is running and nobody told
the player.

## What not to do

- **Shake on everything.** If every event shakes, none of them do. Reserve it for damage and
  pickups.
- **Screen flash as the only channel.** Photosensitivity risk and it hides the frame you just
  spent hours lighting.
- **Long animations that block input.** An 800 ms pickup animation that locks movement will be
  hated by the third pickup.
- **Sound on load.** Autoplay policy will silently drop it and you will spend an hour debugging
  a mixer that was never running.
- **Feel added at the end.** It is 30 lines per event. Add it when the event is written, or it
  never happens.

## Checklist

1. Every event has ≥2 channels.
2. Hitstop, shake and pop are shared primitives, not one-offs.
3. All motion is eased.
4. Camera drifts, bobs, and respects reduced motion.
5. Bursts have three layers and are pooled.
6. SFX are detuned, layered, and gated behind a gesture.
7. HUD counts, bars ease, numerals are tabular.
