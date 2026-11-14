# Scoring rubric — the nine axes

**This file is the only definition of the axes, their 1–5 bands and the ship floor.**
`SKILL.md` §1 is a one-screen index; `references/visual-self-review.md` owns the review *loop*
(capture → score → repair → re-shoot); this file owns *what a score means*. Implementation
detail stays in the reference linked at the end of each axis. Do not restate a band anywhere
else — if a threshold changes, it changes here.

A frame is judged in ten seconds, not on feature count. Source is never evidence: score from
real screenshots of the shipped `file://` artifact, including the upscaled character close-up and
at least one animated frame (the Capture step in `references/visual-self-review.md`).

## How to score

- **1–5 per axis, floor 4.** Band 4 *is* the ship floor — it is the definition of "good enough to
  ship". Band 5 exceeds it. Bands 2 and 3 are real, describable states, not a shrug between
  "fine" and "broken".
- **Six ship axes** (1–6) decide whether the frame reads as AAA. **Fewer than five of the six at
  or above floor means it is a prototype**, whatever the feature list says.
- **Three review axes** (7–9) decide whether the frame is watchable. Structural plausibility is
  a hard gate in its own right: a detached limb fails the build even if every other axis scores 5.
- **Any axis below 4 is a defect to repair, not a stylistic difference.** Repair worst first,
  then re-capture the *same* shots and score again — at least two rounds.
- Repair order: structural plausibility → space → light / material → reflection / world detail →
  beauty / UI → budget. A detached hand outranks a colour grade.
- Score what the pixels show. A `SELF-REVIEW` marker full of 5s next to a blown-out sky is a
  failed review, not a high score.

## The nine axes

### 1. Space — `space`

| Score | What you can see |
| --- | --- |
| 5 | Perspective camera inside the scene, FOV 60–75, eye height 1.2–2.0 m, horizon in frame, three depth layers (foreground occluder / subject / far plane), parallax on movement, and a foreground object that actually occludes |
| 4 | Perspective camera, horizon, three depth layers and parallax all present; eye height or framing slightly off but the frame reads as a place |
| 3 | Perspective camera and two depth layers; horizon clipped, or parallax barely perceptible |
| 2 | Fixed zoom or a ground plane filling >70% of the frame; no occlusion |
| 1 | Orthographic / top-down map, no depth cue at all |

Implementation → `references/procedural-3d.md` (camera, generated textures, quality tiers).

### 2. Light — `light`

| Score | What you can see |
| --- | --- |
| 5 | One directional key at 10–20° elevation, ≥1024² PCF shadow map, contact AO, height fog; ambient, fog and rim all derived from the same sun vector; form still readable in shade |
| 4 | Key, shadows, AO and fog all present; one parameter rough (bias, resolution, fog density) but no principle error |
| 3 | Directional key and shadows exist, but AO or fog is missing; or shadows are soft baked ellipses rather than a shadow map |
| 2 | Flat ambient plus brightness painted into albedo; ellipses drawn under feet |
| 1 | No directional light concept; frame uniformly bright or black-crushed |

Implementation → `references/cinematic-look.md` §1–§3 (sun, sky, shadows), §4 (volumetrics)
and §5 (AO).

### 3. Material — `material`

| Score | What you can see |
| --- | --- |
| 5 | ≥12 named materials, five channels (albedo, roughness, metalness, height→normal, AO), generated wear in primer → oxide order, seams at plate scale, triplanar terrain, and a roughness × metalness calibration row inspected in frame |
| 4 | ≥12 named materials with albedo / roughness / metalness plus generated wear and seams; height or AO weaker but present |
| 3 | Named materials with some channel variance, but wear and seams are uniform or absent; several surfaces still read as plastic |
| 2 | One RGB triple per object; zero roughness variance |
| 1 | Flat fills everywhere, no material identity |

Implementation → `references/material-authoring.md`, `references/asset-craft.md`.

### 4. Reflection — `reflection`

| Score | What you can see |
| --- | --- |
| 5 | Environment/IBL sampled from `skyColor()`, planar reflection on water and wet ground, Fresnel boost at grazing angles; reflected horizon matches the seen horizon |
| 4 | IBL and planar reflection present and sky-consistent; Fresnel weak or missing |
| 3 | Some environment response, but water is a tinted gradient or the reflected sky disagrees with the real sky |
| 2 | No reflection at all; specular is a white blob painted on |
| 1 | No specular response; everything uniformly matte |

Implementation → `references/cinematic-look.md` §2 (sky) and §8 (two-stop bug); the water case in
`references/material-authoring.md`.

### 5. World detail — `world`

| Score | What you can see |
| --- | --- |
| 5 | Plate numbers, inspection dates, hazard markings, maintenance tags, decals and debris; clutter density rises toward the play area; repeated instances share a seeded transform table |
| 4 | Several families of labels / decals / debris with a seeded distribution and a visible density gradient |
| 3 | Decals or debris exist but are abstract symbols; no text anywhere; density flat |
| 2 | A tree is three colour blobs, a crate is a brown box |
| 1 | Empty ground, unlabelled primitives |

Implementation → `references/asset-craft.md`; for 2D builds `references/procedural-art-2d.md`.

### 6. Budget — `budget`

| Score | What you can see |
| --- | --- |
| 5 | Bake once and instance repeats; ≤2 ms post at 1080p; 60 fps median on integrated graphics; heap flat over a 5-minute run |
| 4 | 60 fps median, p99 < 33 ms, no per-frame geometry rebuild; post stack smaller than the scene |
| 3 | Occasional stutter, one per-frame allocation or rebuild, but still ≥30 fps |
| 2 | Post stack larger than the scene; visible frame-time spikes |
| 1 | Per-frame geometry rebuild; multi-MB file with no stated reason |

Implementation → `references/performance.md`.

### 7. Beauty / composition — `beauty`

| Score | What you can see |
| --- | --- |
| 5 | Intentional palette, one focal point, value hierarchy, warm/cool balance, highlights roll off, sky has a gradient, no global grey cast |
| 4 | Clear subject and readable value range; one minor issue (slight overexposure, weak warm/cool separation) |
| 3 | Muddy or randomly saturated, focal point ambiguous, but the sRGB encode is correct |
| 2 | Overexposed or black-crushed, no focal point, or a global grey cast from a transfer-function bug |
| 1 | Unreadable frame |

Implementation → `references/cinematic-look.md` §7–§8 and the composition checklist in
`references/visual-self-review.md`.

### 8. Structural plausibility — `structure`

Hard gate. Judge on an **upscaled close-up at rest and through an animation** (walk / attack /
jump), never on the bind pose alone. A 40 px character hides every defect.

| Score | What you can see |
| --- | --- |
| 5 | One connected body at rest and through every animation; believable proportions; props attached to hand bones; cape, hair and weapon never cut through limbs |
| 4 | Connected in idle and at least one animated frame; a tight fit at one joint but no separation |
| 3 | Bind pose looks right, first animation opens a small gap or detaches a sleeve |
| 2 | Floating hands, gap at the shoulder, weapon in mid-air, cape cutting an arm |
| 1 | Beads-on-a-string, or limbs metres from the torso on the first bone rotation |

Implementation → `references/visual-self-review.md` (the structural plausibility checklist and
the defect → repair recipes).

### 9. UI readability — `ui`

| Score | What you can see |
| --- | --- |
| 5 | Legible on the 3D background, scrim or shadow under text, ≥4.5:1 contrast, no overlap, state clear at a glance |
| 4 | Legible everywhere with one minor overlap in a transient panel |
| 3 | Readable, but thin light text on a bright sky, or a panel briefly covers the character |
| 2 | Overlapping panels, hidden HUD, clipped title text |
| 1 | HUD unreadable or missing state entirely |

Implementation → `references/design-language.md`, `references/resilience-and-a11y.md` and the
HUD checks in `references/visual-self-review.md`.

## `SELF-REVIEW` marker

The artifact carries the score as an HTML comment (zero runtime bytes). The nine keys are fixed —
they are the `axes` names above, not free text:

```html
<!-- SELF-REVIEW {"rounds":2,
  "shots":["title","play","char-closeup","hero-effect"],
  "axes":{"space":5,"light":4,"material":5,"reflection":4,"world":4,"budget":4,
          "beauty":4,"structure":5,"ui":5},
  "fixes":["rig: parent-relative bone offsets; arms reconnect at shoulder",
           "added depth-texture SSAO and shadow-tested volumetric ray march"],
  "reshoot":true} -->
```

`scripts/check_single_file.py --craft` checks `rounds ≥ 2`, a close-up shot, non-empty `fixes`
and `reshoot: true`. **It does not verify the numbers.** The score is an assertion, the
screenshots are the evidence, and the marker is a receipt — never the review itself. See
`references/visual-self-review.md` for the loop that produces it (its Evidence and record
section).
