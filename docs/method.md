# The method

Distilled from building and shipping browser games that are exactly one HTML file, with no
assets, no build step and no network. This document is the *why*; [SKILL.md](../SKILL.md) is
the *how*.

## The claim

A game does not need a repository, a bundler or a texture pipeline. It needs a loop, an
input, a rule, and a reason to press the button again. Everything else is a delivery
decision — and for prototypes, demos, jam entries, teaching material and small experiments,
**the best delivery decision is a single file**.

## Four constraints, and what each one buys

| Constraint | Enforced by | What it buys |
| --- | --- | --- |
| One file | no `<script src>`, no `<link href>`, no `fetch` | The artifact is the deliverable: reviewable, diffable, emailable, archivable |
| Zero assets | art drawn, audio synthesized, textures baked | No 404s, no licensing surface, no "assets not included" |
| No build | plain ES in one `<script>` | Open `file://` and it runs — on a plane, in a classroom, from a USB stick |
| No network | nothing remote at runtime | Works offline forever; no third-party uptime dependency |

The constraints are not nostalgia. They remove four whole categories of failure: missing
files, broken CDNs, build drift, and privacy questions.

## The cost

Be honest about the trade:

- **Byte budget.** Procedural content is compact but not free: a 2D arcade game lands at
  15–40 KB, and a 3D game with the mandatory inlined three.js build at 0.6–1.4 MB — of which
  almost nothing is yours. That is a feature; the models themselves come from the vendored
  img2threejs pipeline as code, not as downloaded meshes.
- **No artist pipeline.** Style must come from a system — palette, outline, one light
  direction — not from hand-painted assets. See [design-language](../references/design-language.md).
- **Single thread.** No workers by default (they need a same-origin URL, which `file://`
  usually forbids). Budget accordingly: [performance](../references/performance.md).
- **No build step, not no engine.** In 2D you write the loop, the resize and the scene machine —
  about 200 lines, once, reused forever; that is what `assets/starter-2d.html` is. In 3D you
  paste a minified engine instead: re-implementing PBR, shadows and skinning is where a
  single-file 3D game's budget goes to die.

## The pipeline

```
 1  scope ────────────► one sentence, one loop, one failure state
 2  shell ────────────► tokens · boot · title · canvas · HUD · screens · error boundary
 3  systems ──────────► loop → input → scene machine → art → entities → audio → content
 4  content ──────────► tables, seeds, waves, generated names
 5  feel ─────────────► shake, particles, pops, ticks, idle motion
 6  audit ────────────► scripts/check_single_file.py --strict  +  release checklist
```

Steps 2 and 3 are the same in every project. Steps 1, 4 and 5 are where the game actually
lives. Step 6 is what separates "it runs" from "I can hand this to someone".

## Step 1 — Scope in one sentence

> *You steer a craft, collect drifting lights, avoid shards, and the run ends on contact.*

If the sentence needs a second clause to be playable, cut a mechanic. A single file rewards
**density**, not breadth: one loop with a clear failure state and an explicit restart beats
five half-implemented systems.

Scope checks:

- Can the player lose in under 45 seconds? (If not, the loop is too slow to teach.)
- Is there exactly one primary verb? (Move, shoot, place, match.)
- Does the first death teach something? (If the player cannot say why they died, the feedback
  is missing, not the difficulty.)

## Step 2 — Shell before systems

The shell is a fixed cast of layers, back to front:

```
canvas → HUD → screens (boot / title / pause / over) → toast → fatal banner
```

Rules that keep it maintainable:

- **The canvas is always alive.** Screens are DOM cards over it; pausing does not tear
  anything down, so resume is instant and restart never reloads the page.
- **Screens own no state.** They read the game object and dispatch named actions
  (`data-act="retry"`). One delegated click handler.
- **The error boundary ships from day one.** A global handler paints a readable banner and
  keeps the page inspectable. See [resilience-and-a11y](../references/resilience-and-a11y.md).

## Step 3 — Systems in dependency order

Each layer must be observable before the next is written:

1. **Loop + resize + DPR** — verify with a debug readout, not by eye.
2. **Input intent** — verify by moving a rectangle with every device you support.
3. **Scene machine** — verify that pause, resume and restart never duplicate a loop.
4. **Art primitives** — verify with a static scene before anything moves.
5. **Entities and collision** — verify with a seeded spawn table.
6. **Audio and HUD** — verify every action has a sound and a visible number change.
7. **Content** — tables, waves, level data.

Skipping step 1 or 2 is the most expensive mistake in this format: every later bug becomes a
layout or input bug, and it is indistinguishable from a gameplay bug.

## Step 4 — Content as data

The reason one file can hold a large game is that content is *tables plus a generator*, not
hand-authored instances.

| Content | Representation |
| --- | --- |
| Enemies / pickups | stat table + weighted spawn table per zone |
| Levels | seeded generator (rooms, waves, terrain) + hand-tuned constraints |
| Names / flavour | small word banks combined at runtime, seeded per entity |
| Dialogue | id → line map, one speaker state machine |
| Difficulty | one curve function, sampled by elapsed time |

Determinism matters: seed the generator, store the seed, and a bug report becomes
reproducible (`?seed=1234`). Use `Math.random()` only for cosmetic jitter.

## Step 4.5 — Look development is a step, not a polish pass

The most common failure of this format is not a bug. It is a file that is technically
correct, ships, runs offline — and looks like a prototype: untextured boxes, flat ambient,
one sun behind the subject, no atmosphere.

Treat the look as a numbered step between systems and content, because it changes how content
is built (materials and light decide what a prop needs to be). Five passes, in order:
composition, key light, materials, atmosphere, post. [cinematic-look](../references/cinematic-look.md)
carries the numbers; [material-authoring](../references/material-authoring.md) carries the
surface half.

Two rules from that file are worth repeating here because they cost entire days when missed:

- **Encode to sRGB once, at the end.** Tone mapping ends in linear display values; the canvas
  does not convert them. Skip it and the whole frame reads two stops dark, which sends you
  into a false hunt for a lighting bug.
- **Do not light the subject from behind unless the frame is a deliberate silhouette.** All
  camera-facing surfaces then receive ambient only, every material flattens, and no amount of
  wear or seams will read.

## Step 5 — Feel is a checklist, not a talent

Cheap and high-yield, in order of impact per line of code:

1. Screen shake on impact (≤ 6 px, ≤ 200 ms, decaying).
2. Particle burst on every state change (collect, hit, spawn, die).
3. A 120 ms scale-pop on the thing you just touched.
4. A two-note audio tick on every action — including buttons.
5. Idle motion on anything alive (1–2 px bob).
6. A vignette and a one-colour grade over the gameplay.
7. A number that counts up rather than snapping.

All seven are ~40 lines total and do more for perceived quality than a 10× polygon budget.

## Step 6 — Audit

```bash
python scripts/check_single_file.py my-game.html --strict
```

Then walk [release-checklist](../references/release-checklist.md). The checklist exists because the
failure modes of this format are known and boring: a save key that does not match the load
key, an input that runs forever on window blur, a panel that keeps capturing clicks after it
closes, a second `requestAnimationFrame` that doubles the simulation.

## When not to use this method

Be explicit about the boundary:

- **Multiplayer with real-time sync** — needs a server; the client can still be single-file.
- **Large content games** (hundreds of art assets, voice, music) — the constraint becomes a
  tax, and a bundler plus an asset CDN is the right answer.
- **Long-lived live-service products** — you want module boundaries, tests and code review at
  file granularity.
- **Anything that must be indexed, deep-linked per level, or A/B-tested** — still possible,
  but you are fighting the format.

For everything else — prototypes, demos, jam entries, teaching, tiny products — one file is
not a compromise. It is the shortest path between an idea and a player.
