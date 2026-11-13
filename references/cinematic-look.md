# The cinematic look

Why one single-file game reads as "a demo" and another reads as a shipped title is rarely
polygon count. It is almost always the same eight decisions, in the same order. This file is
the stack the 3D starter implements, with the numbers it uses and the failure each number
prevents.

Read `procedural-3d.md` first for the WebGL2 plumbing. This file is about what the frame
looks like.

## The order is not negotiable

```
shadow map  ->  HDR scene  ->  volumetrics  ->  AO  ->  bloom  ->  tone map  ->  grade  ->  encode
                                  ^^^ MUST        ^^^ MUST   (SKILL.md §2A.B)
```

Both atmosphere stages are **hard constraints**, not polish. A 3D deliverable without SSAO and
depth-aware volumetrics fails `--craft`. Build the depth texture on the scene target in the
renderer step, before content.

Every stage assumes the one before it:

- Shadows before shading, or nothing is occluded.
- Linear HDR before everything, or bloom has nothing to bloom and the grade clips.
- Volumetrics and AO before tone mapping, because they multiply *radiance*, not pixels.
- **sRGB encode last.** The canvas does not encode for you. This is the single most common
  reason a hand-written pipeline looks like night. See "The two-stop bug" below.

## 1. One sun, one direction, one temperature

Pick a sun direction and keep the whole game inside it. Everything else — ambient colour,
fog colour, rim colour, the specular tint — is derived from that one vector.

```js
const SUN = { dir: norm([0.58, 0.215, -0.78]), col: [4.8, 2.30, 1.02] };  // ~12° elevation
const SKY = { zen: [0.038, 0.080, 0.185], hor: [0.98, 0.42, 0.125], away: [0.085, 0.10, 0.14] };
```

Elevation drives everything. Below ~8° the ground receives almost no light (`N·L = 0.14`)
and the frame collapses into silhouettes; at 12–18° you keep the sunset colour and still get
readable ground and long shadows. Sun intensity 3–6 in linear units, surface albedo 0.05–0.3.
If you find yourself raising exposure past ~1.2 to see the ground, the sun is too low.

**Light the faces the camera can see.** A backlit scene is beautiful and it is also the
fastest way to make every visible surface ambient-only, which flattens all your material
work. Put the key 30–50° off the view axis, behind or beside the camera, so the faces you
look at carry a gradient. Keep the sun in frame only if you also add a rim term.

## 2. A sky that is a function, not a picture

The sky is not a background. It is the light source for every shadowed surface, the colour
of the fog, and the content of every puddle reflection. Write it once:

```glsl
vec3 skyColor(vec3 d, float rough, float clouds)   // d = world direction, rough = 0..1 blur
```

Use it in the sky pass, in `skyLight()`, in `applyFog()` and in the water reflection. Four
call sites, one function, so the horizon you see and the horizon in a puddle agree.

**Do not mix horizon and zenith colours.** The horizon is roughly ten times brighter than the
zenith at sunset, so even a 20% mix weight of horizon red wins and the whole dome turns beige.
Add the glow instead:

```glsl
vec3 c = mix(uZen * 0.45, uZen, smoothstep(-0.04, 0.32, d.y));   // blue dome
float glow = exp(-max(d.y, 0.0) * 13.0);                          // ~10° thick band
c += uHor * glow * (0.28 + 0.72 * pow(azimuthToSun, 2.2));        // warm only near the sun
```

`exp(-y * 13)` is the whole trick: warm light lives in a thin band above the horizon, and the
dome stays cold. Cloud layers are two `fbm` samples projected onto `d.xz / (d.y + 0.16)`; keep
coverage under ~25% or the sky becomes a flat lid. Dither the result with interleaved gradient
noise at ~0.0025 or a 16-bit gradient bands visibly on OLED phones.

## 3. Shadows: cheap, soft, and biased correctly

A 2048² depth map, one orthographic light matrix fitted to the playable area, and a five-tap
disc in the fragment shader is enough for a scene of this size.

```glsl
vec4 sc = uLightVP * vec4(wp + N * 0.045, 1.0);   // normal offset: kills acne on grazing light
vec3 p = sc.xyz / sc.w * 0.5 + 0.5;
float s = texture(uShadow, vec3(p.xy, p.z - 0.0022));   // sampler2DShadow, hardware 2x2
```

Three rules:

- **Normal offset before the depth bias.** A grazing sun needs centimetres of offset, and
  depth bias alone cannot supply it without peter-panning.
- **Sample with `sampler2DShadow` + `COMPARE_REF_TO_TEXTURE`.** You get a free 2×2 PCF and
  correct comparison; a plain `sampler2D` needs manual unpacking.
- **Fit the map to the action, not the world.** ±34 m here. A 1 km ortho box at 2048² is
  centimetres-per-texel mush.

Long shadows are the cheapest drama in the medium. A 12 m pillar at 12° casts a 56 m shadow:
one instanced box, one shadow lookup, a huge compositional element.

## 4. Volumetrics: the difference between "3D" and "atmospheric" — MUST

**Required in every 3D deliverable** (`SKILL.md` §2A.B). One half-resolution raymarch with 16–24
steps, shadow-tested, phase-weighted, terminating at scene depth. Not optional, not a tier-only
feature: the low tier may use 8 steps or quarter resolution, but the pass must exist and run.

The core loop, in linear HDR:

```glsl
float g = 0.72;                                   // forward scattering
float hg = (1.0 - g*g) / (12.566 * pow(1.0 + g*g - 2.0*g*mu, 1.5));
float dens = uSigma * (0.35 + 0.65 * exp(-max(p.y, 0.0) / 7.0));   // thicker near the ground
acc += T * (uSunCol * phase * lit * 1.9 + uHor * 0.10) * (1.0 - Ti);
T *= Ti;
```

Output `vec4(scatter.rgb, transmittance)`. Composite does `col = col * T + scatter`.

Density is where this goes wrong. `sigma = 0.03` over 70 m gives `T ≈ 0.4`, which means you
are multiplying your entire frame by 0.4 and adding orange on top: everything greys out and
you will blame the grade. **Start at 0.006–0.010**, look at the frame, and only raise it until
the shafts read. Jitter the start with interleaved gradient noise so 20 steps do not band.

Upsample with a depth-weighted 4-tap, never plain bilinear: a half-res buffer stretched over
a silhouette leaks light through geometry.

## 5. AO: contact, not dirt — MUST

**Required in every 3D deliverable** (`SKILL.md` §2A.B): screen-space ambient occlusion rebuilt
from the scene's **depth texture**, hemisphere sampling and a depth-aware blur. Vertex AO, baked
AO in the albedo, or a painted ellipse under the feet do not satisfy it. Apply to ambient /
indirect radiance only, at 0.6–0.8 strength; never multiply the whole frame. Low tier may drop
sample count or resolution.

Half-res SSAO, 12 hemisphere samples, 0.4–0.6 m radius, then a depth-aware 7-tap blur. Two
things matter more than the sampler:

- **Apply it to ambient only.** Multiplying direct sun by AO produces dirty halos on lit
  surfaces. Fade the effect where the pixel is already bright.
- **Keep the radius small.** 0.4 m reads as contact shadow; 2 m reads as dirt in the corners.

AO is subtle by design. If you can point at it, it is too strong. `0.6–0.8` strength in the
composite, never `1.0`.

## 5A. Implementation contracts (and what does not count)

Neither pass is satisfied by a lookalike. `--craft` looks for the signals, but the screenshot
is what proves it.

| Pass | Counts | Does **not** count |
| --- | --- | --- |
| SSAO | depth texture → view-space position → hemisphere samples → depth-aware blur → ambient-only multiply | vertex AO, AO baked into albedo, a radial gradient under an object, simply darkening the final image |
| Volumetrics | view-ray ray march to **scene depth**, density integrated, HG phase, **shadow-map test** per step, `col = col*T + scatter` | radial blur of the bright buffer, sun-disk streaks, a fog quad, height fog alone |

Wiring in an inlined engine (three.js r149-style):

- Attach a `DepthTexture` to the HDR scene target. **Do not combine it with MSAA `samples > 0`**
  — a multisampled framebuffer does not reliably resolve into a sampleable depth texture. Set
  `samples = 0` and add a cheap FXAA in the composite instead.
- Reconstruct view space from the non-linear depth: `ndc = vec4(uv*2-1, d*2-1, 1)`,
  `view = uProjInv * ndc; view /= view.w`. World space is `uViewInv * vec4(view,1)`.
- Reconstruct normals from neighbouring depth samples (`cross(pUp-p, pRight-p)`) — no MRT or
  derivative extension needed. Skip pixels with `d == 1.0` (sky).
- For the volumetric shadow test, project each step with the engine's shadow matrix
  (`light.shadow.matrix`), sample the packed shadow map with `unpackRGBAToDepth`, and compare.
  Blend `lit` toward an ambient floor rather than hard 0/1 so a packing mismatch degrades to
  soft haze instead of a black frame.
- Jitter the march start with interleaved gradient noise; upsample with a depth-weighted tap.
- Composite in order: `hdr = hdr * T + scatter`, then `hdr *= mix(1.0, ao, strength *
  (1.0 - smoothstep(...luma(hdr))))`, then bloom, ACES, grade, sRGB encode.

Both passes run at half (or quarter) resolution into their own targets; on a low tier reduce
steps and samples, never delete the passes. Budget from the starter still applies:
volumetrics 20 steps ≈ 1.2 ms, SSAO half res ≈ 0.5 ms at 1280×800 on integrated graphics.

## 6. Bloom: a pyramid, not a blur

Five mips. Downsample with a 13-tap filter, Karis-average the first mip (that is what stops
fireflies), then upsample with a 9-tap tent and **add** into the higher mip.

```glsl
col = max(col - uThresh, 0.0);   // threshold in HDR units, ~2.4 when the sun is 5
```

- Upsample must be additive blending into the destination, not a read of the destination.
  Sampling the texture you are writing is a feedback loop and drivers will hand you garbage.
- Threshold only means something in HDR. On an RGBA8 fallback everything clips at 1.0, so
  switch the threshold to the display range (`~0.7`) or you get no bloom at all.
- Strength 0.03–0.06. Bloom is an artefact of lenses, not a glow effect.

## 7. Tone map, then grade

ACES-fitted is 4 lines and behaves well with a 5:1 sun-to-sky ratio:

```glsl
col = (col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14);
```

Then, in display space, a grade that does one thing per line:

```glsl
float l = luma(col);
col = mix(col, vec3(l), -0.07);                    // +7% saturation
col *= vec3(1.05, 1.0, 0.95);                      // warm highlights
col += vec3(-0.006, 0.002, 0.011) * (1.0 - l);     // cool shadows
col = clamp((col - 0.5) * 1.12 + 0.5, 0.0, 1.0);   // contrast
```

Complementary split toning — warm light, cold shadow — does more for perceived quality than
another light. Vignette 0.4–0.6, radial, `length(uv - 0.5) ^ 2.4`. Film grain 0.01–0.02,
strongest in the midtones, absent in blacks: it dithers gradient banding and hides the
resampling seams of upscaled buffers.

## 8. The two-stop bug

```glsl
// After tone mapping the values are linear display values.
// The canvas expects sRGB-encoded bytes and will NOT convert for you.
col = mix(col * 12.92, 1.055 * pow(col, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, col));
```

Symptom: a scene that looks correct in a debug raw pass, then turns into night after the
composite; you compensate with exposure 2.0, highlights clip, and the image still feels flat.
Fix the transfer, then set exposure back to ~0.8–1.0. Every hand-written pipeline hits this
once. Check it first.

## Camera

- **Never a static camera.** Even 0.03 rad/s of drift on the title screen separates "menu" from
  "engine". Add a two-octave sine bob while walking (amplitude ~4 cm) and a 1.5 s shake decay
  on impact.
- **FOV 60–70°.** Wider distorts, narrower feels like a scope. Add +3° while sprinting.
- **Start on a composition, not on coordinates.** Put a foreground object at 3–5 m, the subject
  at 10–20 m, and a skyline gap where the sun goes down. `buildWorld()` here lowers monoliths
  within ±0.75 rad of the sun azimuth for exactly this reason.

## Budget

Measured on the starter at 1280×800, 60 fps target, integrated GPU:

| Pass | Cost | Dial it down by |
| --- | --- | --- |
| Shadow 2048² | 0.6 ms | 1024², tighter ortho |
| Scene (PBR + sky) | 2.5 ms | resolution scale, cheaper noise octaves |
| Volumetrics 20 steps | 1.2 ms | 12 steps, quarter res, lower sigma |
| SSAO half res | 0.5 ms | 8 samples, or off |
| Bloom 5 mips | 0.6 ms | 4 mips |
| Composite + FXAA + grain | 0.5 ms | FXAA off above DPR 1.5 |

Degrade in that order: resolution → volumetrics → AO → bloom. Never degrade the shadow map
first; a scene without contact shadows reads as broken before it reads as slow.

## The ten-second test

Open the file and look for ten seconds. Then answer:

1. Is there one clear light direction?
2. Do the shadowed sides still show form, or are they flat fill?
3. Is there anything within 5 m of the camera?
4. Does the horizon have a value gradient, or one flat band?
5. Do surfaces have scale — seams, wear, aggregate — or one albedo per object?
6. Is there atmosphere between you and the far plane?
7. Does anything move that is not gameplay?
8. Do the highlights roll off instead of clipping?
9. Do crevices and contact points darken (SSAO), and do shafts stop at a pillar instead of
   shining through it (depth-aware volumetrics)?
10. Does the camera turn when the mouse simply moves — no drag, no click to capture?

Two "no"s is a prototype. Fix those two, look again. A "no" on 9 or 10 is a §2A failure and
blocks the ship gate regardless of the other eight. Then review the character close-up per
`references/visual-self-review.md`: a good frame with a detached hand is still not done.
