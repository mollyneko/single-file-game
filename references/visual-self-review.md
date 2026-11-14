# Visual self-review, with a repair loop

**MUST.** `SKILL.md` §2A.A. This is the gate that catches the defects a format auditor cannot
see: a hand floating 40 cm from its sleeve, a sky that clips, a cape that eats an arm, a whole
frame that is technically complete and reads as a grey prototype.

The auditor checks that work was *attempted*. It cannot tell a good frame from a bad one. This
document is how the model judges its own output — and proves the judgement with pixels.

**Division of labour:** `references/scoring-rubric.md` defines the nine axes, their 1–5 bands
and the ship floor. This file owns the *loop* — capture, score, repair, re-shoot, record — plus
the checklists and repair recipes. Score against the rubric; never restate a band here.

## Why this file exists

A finished single-file 3D RPG was reviewed from its source and declared good: it had a weighted
skinned mesh, 22 named materials, a full HDR post chain, four heroes and a quest. The first
zoomed screenshot showed **hands detached from the body**. Cause: `BONE_DEF` stored each bone's
world-space position, while `THREE.Bone` positions are **offsets from the parent bone**. The
bind pose renders correctly (bone matrices cancel), so source inspection and a static frame both
pass. The moment `poseHero()` sets `rotation.z` on an arm bone, its pivot is ~6 m above the
shoulder and the limb sweeps half a metre away from the torso.

Three lessons, now rules:

1. Review **pixels**, never code.
2. Review the **character close-up**, never just the wide shot.
3. Review **at least one animated frame**, never just the bind/idle pose.

## The loop (≥ 2 rounds, mandatory)

```
capture → score → repair → re-capture → compare → (repeat) → record
```

### 1. Capture

Use a headless browser against the `file://` artifact (no server, no network). Four shots
minimum, from the *same* build:

| Shot | Why |
| --- | --- |
| Title | Composition, type over 3D, sky, first impression |
| Gameplay wide | Space, light, world detail, HUD in context |
| **Character close-up** | The structural gate. Crop and upscale the character region ~3× |
| Hero effect | Water / sunset / boss / particles — the most expensive, most likely to be broken |

```bash
EDGE="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
"$EDGE" --headless=new --no-sandbox --disable-dev-shm-usage \
  --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader \
  --enable-logging=stderr --v=0 --window-size=1280,800 \
  --virtual-time-budget=16000 --screenshot="shots/play.png" \
  --user-data-dir="shots/profile" "file:///path/game.html#play"
```

Add a `#play` (or equivalent) entry that skips the title so gameplay is reachable. Capture
console errors in the same run: an `Uncaught`/`TypeError` is a defect of the highest severity,
even if the frame looks fine. Crop with Pillow (`Image.crop(...).resize(...)`) — do not "zoom" by
squinting at a 1280 px screenshot.

### 2. Score in writing

Score **all nine axes in writing against `references/scoring-rubric.md`** — six ship axes
(space, light, material, reflection, world detail, budget) plus three review axes (beauty /
composition, structural plausibility, UI readability). The rubric is the only definition of the
1–5 bands, the floor and the prototype rule; this file does not restate them.

Write one integer per axis, name the weakest, and rank the defects worst-first. Structural
plausibility is a hard gate: a detached limb fails the build regardless of the other eight.

Also confirm the three hard constraints from §2A on screen: SSAO contact darkening at
junctions, shafts that stop at geometry, and a camera that turns when the mouse simply moves.

### 3. Structural plausibility checklist

Hard gate. Check **every** humanoid/creature, at rest and animated:

- [ ] Head → neck → collar → torso is continuous; no floating head or gap at the jaw.
- [ ] Shoulder → upper arm → elbow → forearm → wrist → hand is one unbroken chain on both
      sides; sleeves meet the torso; the shoulder pad overlaps the torso surface.
- [ ] Hip → thigh → knee → shin → ankle → boot is continuous; feet touch the ground plane.
- [ ] Proportions are believable: head ≈ 1/6–1/8 of body height, arms reach mid-thigh,
      no limb longer than the torso.
- [ ] **Animated frames** (walk, attack, jump, glide): no joint separates, no limb teleports,
      no bone rotates around a distant pivot. This is the frame that catches parent-relative
      offsets.
- [ ] Held props are attached to a hand bone, not floating; capes/hair do not cut through arms.
- [ ] No giant foreground slab from a misplaced mesh, no geometry clipped by the near plane.
- [ ] Close-up is **upscaled** and inspected at ≥3× — a 40 px character hides every defect.

For buildings, vehicles and props: parts meet, nothing hovers above the terrain, contact
shadows land under feet/wheels, and repeated instances share a seeded transform table.

### 4. Beauty / composition checklist

- [ ] One focal point, one foreground object at 3–5 m, a skyline gap for the sun.
- [ ] Value range: readable shadows (not black), highlights that roll off (not clipped).
- [ ] Hue discipline: one warm key against a cool ambient; no global grey cast (check the
      colour-management / sRGB encode first — a grey frame is usually a transfer-function bug,
      not a palette problem).
- [ ] Sky has a gradient, not a flat band; horizon in the water reflection matches the sky.
- [ ] No speckle/aliasing that reads as noise; normal-map strength and texture repeat are sane.
- [ ] HUD has a scrim or shadow; text ≥ 4.5:1 contrast; nothing overlaps the character.
- [ ] Title text is legible over the world; no clipped floating islands in a corner.

### 5. Defect → repair recipes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Hand/forearm detached on first animation | Bone positions authored as **absolute** world coords in a parent-relative hierarchy | Convert each bone to `abs(child) - abs(parent)`; keep the root at origin. Re-check bind pose, then re-check an animated pose |
| Limb swings wildly around a distant pivot | Same, or a bone attached to the wrong parent | Check the parent index table and joint chain |
| Gap opens at a joint when bent | Adjacent segments weighted to different bones with a hard step | Blend weights across the joint (`smoothstep` over ~15% of segment length), overlap the segment ends by ~2% of radius |
| "Beads on a string" | One primitive per bone, widened to hide gaps | One weighted continuous skinned mesh; no per-bone spheres as joints |
| Whole frame grey / flat | Colour management, missing sRGB encode, or ambient-only lighting | Fix the transfer function and colour space **before** exposure; re-derive ambient/fog/rim from the sun |
| Ground looks like TV static | Normal strength or texture repeat too high | Lower `normalScale`, raise texel density, reduce speckle in the baked albedo |
| No contact shadows | No SSAO; painted ellipse under feet | Depth-texture SSAO, half-res, ambient-only (§2A.B) |
| "God rays" shine through pillars | Radial bright-pass blur, not volumetrics | Depth-aware ray march with shadow-map test (§2A.B) |
| Camera does nothing until a drag | Drag-gated `pointermove` | Unconditional mouse look; pointer lock optional (§2A.C) |
| Character hidden behind a slab | Misplaced mesh / near-plane clip | Check world positions and camera collision; re-shoot |

### 6. Evidence and record

The artifact must carry a machine-readable marker (an HTML comment costs zero bytes at
runtime). The nine `axes` keys and their bands are defined in `references/scoring-rubric.md`.
`--craft` parses the marker and fails if rounds < 2, shots are missing the close-up, fixes are
empty, or no re-shot is claimed — it does not verify the numbers:

```html
<!-- SELF-REVIEW {"rounds":2,
  "shots":["title","play","char-closeup","hero-effect"],
  "axes":{"space":5,"light":4,"material":5,"reflection":4,"world":4,"budget":4,
           "beauty":4,"structure":5,"ui":5},
  "fixes":["rig: parent-relative bone offsets; arms reconnect at shoulder",
           "added depth-texture SSAO and shadow-tested volumetric ray march",
           "mouse look now free-look by default"],
  "reshoot":true} -->
```

Keep the actual screenshots beside the build during review; the handoff must state the rounds,
the weakest axis and the before/after fixes. **The marker is a receipt, not the review.** A file
with a perfect marker and a detached hand is a failed review.

## Red flags

- "The code has a skinned mesh, so the character is fine."
- One round, no re-shot.
- Only wide shots; the character occupies 40 px.
- Scoring every axis 5 while the screenshot shows a blown-out sky.
- Fixing a structural defect by widening the limb to cover the gap.
- Handing off with the audits passing but no screenshot ever opened.
