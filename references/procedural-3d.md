# Procedural 3D (WebGL2)

3D in one file is viable, and there is exactly one route: paste a minified **three.js** build
inline and spend the bytes on assets. PBR, shadow maps, IBL, skinning and curve geometry are
solved problems; re-implementing them is how a single-file 3D game ends up with a complete post
stack and primitive art — a full composite chain grading untextured boxes. A hand-written
WebGL2 renderer is not permitted in a deliverable (`SKILL.md` §0); the bundled
`assets/starter-3d.html` survives only as a raw-WebGL2 reference slice for the post chain.

## One path: inline three.js

Every 3D deliverable pastes a **minified three.js build** (global `window.THREE`, MIT) inside
the same `<script>` and records its version and licence in a header comment. 0.6–1.4 MB is the
expected, budgeted cost — it is still one file, and it buys PBR, IBL, shadow maps, skinning,
curve geometry and instancing as working code. A `<script src>` pointing at a CDN violates the
single-file rule and turns one artifact into two with a third-party uptime dependency.

Models come from the img2threejs pipeline (`img2threejs/PIPELINE.md`): reference image →
staged, quality-gated sculpt → a `create...Model` factory that emits a rigged
`THREE.Group`. Each factory leaves a `PIPELINE-RECEIPT` in the HTML — the provenance marker
`--strict --craft` checks (`SKILL.md` Step 3). Scene assembly, lighting and post are three.js
on top of those models; writing geometry by hand here is not a modeling path.

## Boot in the right order

renderer → capability probe → materials and geometry → textures → post targets → first frame.
Every stage updates the boot bar, and every stage can fail into the 2D fallback:

```js
const renderer = new THREE.WebGLRenderer({
  canvas: cv, antialias: false, alpha: false, powerPreference: 'high-performance',
});
if (!renderer.capabilities.isWebGL2) return fallback2D();   // never a black screen
renderer.outputColorSpace = THREE.SRGBColorSpace;           // encode once, at the end
```

Keep real error reporting on shader compilation — a silent shader failure is the most common
way to end up with a black canvas:

```js
renderer.debug.checkShaderErrors = true;
renderer.debug.onShaderError = (gl, prog, vs, fs) =>
  fatal(new Error('shader: ' + gl.getShaderInfoLog(fs)));
```

## Render graph

```
sky (fullscreen, generated)  ->  shadow depth pass  ->  main pass into HDR target
  with a sampleable depth texture  ->  half-res volumetric ray march (MUST)
  ->  half-res SSAO + depth-aware blur (MUST)  ->  bloom pyramid
  ->  composite: exposure, tonemap, grade, vignette, grain, dither, FXAA  ->  present
```

The two atmosphere passes are `SKILL.md` §2A.B hard constraints. Render the HDR scene into a
target with a `DepthTexture` (and `samples = 0` — MSAA does not resolve reliably into a
sampleable depth texture); reconstruct view-space positions and normals from it in both passes.
See `references/cinematic-look.md` §5A for the contracts.

The composite pass is where the "look" lives. Render the world to an offscreen target in
linear space, then run one fullscreen shader over it. Do not tone map per-material.

## Image pipeline, in order

1. **Linear lighting.** Shade in linear; convert to sRGB exactly once, at the end.
2. **Exposure.** One scalar uniform, exposed as a settings slider.
3. **Tone map.** ACES or the AgX fit (polynomial, ~25 lines, no LUT needed). AgX holds
   highlight colour better; ACES is punchier.
4. **Grade.** Split-tone (cool shadows, warm highlights), gentle S-curve, lifted blacks.
   Fifteen lines change the entire mood.
5. **Vignette.** Also a gameplay channel: darken and desaturate as health drops.
6. **Grain + dither.** Grain kills banding in sky gradients; dither the final 8-bit write.
7. **FXAA.** Luma-based, applied last, ~30 lines. Cheaper and more robust than MSAA on
   integrated GPUs.

```glsl
vec3 col = tonemap(hdr.rgb * uExposure);
float l = dot(col, vec3(0.2126, 0.7152, 0.0722));
col *= mix(vec3(0.94, 1.00, 1.06), vec3(1.04, 1.00, 0.97), smoothstep(0.02, 0.6, l));
col = mix(col, col * col * (3.0 - 2.0 * col), 0.18);          // soft S-curve
col = col * 0.988 + vec3(0.006, 0.008, 0.011);                 // lifted blacks
col *= 1.0 - uVignette * smoothstep(0.2, 1.05, r2);
col += (hash12(gl_FragCoord.xy + uTime) - 0.5) / 255.0;        // dither
```

## Generated textures and materials

Never ship an image. Two techniques cover everything:

1. **Shader-baked texture.** Render a quad with a generator fragment shader once at boot into
   a texture, then sample it forever. Noise fields, asphalt, rock, water normals, clouds.
2. **MRT material bake.** For a ground plane, write albedo, normal+roughness and extra masks
   into three attachments in one pass:

```glsl
layout(location=0) out vec4 oAlbedo;   // rgb + ao
layout(location=1) out vec4 oNormal;   // xy = world-space slope, z = roughness
layout(location=2) out vec4 oMask;     // puddles, wear, wetness

void main(){
  vec2 p = vUv * uWorldSize;
  float n  = fbm(p * 0.35);
  float wet = smoothstep(0.55, 0.62, fbm(p * 0.12 + 11.0));
  oAlbedo = vec4(mix(vec3(0.16,0.17,0.18), vec3(0.28,0.27,0.25), n), 1.0);
  oNormal = vec4(0.0, 0.0, mix(0.72, 0.10, wet), 1.0);   // wet = smooth = reflective
  oMask   = vec4(wet, n, 0.0, 1.0);
}
```

This is how a 200 m surface gets puddles, wear and joints without a single texture file: one
1024² bake, sampled with a repeat wrap and world-space UVs.

Rules for tileable noise: sample `fract(xz / period)`, never the raw coordinate; keep periods
integer so edges match; use 3–4 octaves, not 8.

## Geometry without assets

- **Boxes and cylinders with good materials** beat bad low-poly characters. Silhouette and
  lighting carry the scene.
- **Instancing** for everything repeated: one VBO, one draw call, per-instance matrix.
- **Extrusion / lathe** for props: a 2D profile plus a revolve is a lamp, a barrel, a bollard.
- **Vertex displacement** for terrain: two octaves on a subdivided plane, normals from finite
  differences in the shader.
- **Sky as a shader.** A gradient, a sun disc with a soft halo, one cloud layer from fbm, and
  a matching fog colour produces more atmosphere than any mesh.

## Camera

One camera object with position, yaw, pitch, fov. Movement is intent-driven
(`move.x`, `move.z`, `look.dx`, `look.dy`), never read from a keyboard inside the camera.
Mouse look is **free-look by default**: a `pointermove` handler writes `look.dx/dy`
unconditionally, with no drag gate and no click-to-capture requirement
(`SKILL.md` §2A.C, `references/input-and-mobile.md`).

```js
yaw   -= look.dx * sens;
pitch  = clamp(pitch - look.dy * sens, -1.45, 1.45);
fwd   = [Math.sin(yaw), 0, Math.cos(yaw)];
right = [fwd[2], 0, -fwd[0]];
pos  += (fwd * move.z + right * move.x) * speed * dt;
```

Head bob, landing dip and a subtle roll on strafe cost nothing and sell the weight. Cap the
bob amplitude under `prefers-reduced-motion`.

## Lighting and shadows

One directional light plus ambient/fog is enough. Shadow map: render depth from the light,
then compare with a bias that scales with slope.

```glsl
float bias = max(0.0015 * (1.0 - dot(n, L)), 0.0006);
```

Use PCF with a tap count that scales by tier (`low: 10 taps, high: 16`), cap the shadow
distance at 30–50 m, and fade the outer 20%. Re-render the shadow map only when the light or
static geometry changes — a static sun means a one-time cost.

## Quality tiers

Every expensive knob is a value in a table. No `if (tier === 'low')` scattered through the
renderer.

```js
const TIERS = {
  low:    { dpr:1.0,  shadow:1024, taps:10, aa:0, ao:true, aoSamples:8,  bloom:false, volSteps:8,  drawDist:90  },
  medium: { dpr:1.25, shadow:1024, taps:12, aa:1, ao:true, aoSamples:12, bloom:true,  volSteps:12, drawDist:140 },
  high:   { dpr:1.5,  shadow:2048, taps:16, aa:1, ao:true, aoSamples:16, bloom:true,  volSteps:20, drawDist:200 },
  ultra:  { dpr:2.0,  shadow:2048, taps:16, aa:1, ao:true, aoSamples:16, bloom:true,  volSteps:24, drawDist:260 },
};
```

`ao` and `volSteps` are **never 0/false** on a shipped build: §2A.B requires both passes at
every tier. Degrade by reducing samples/steps/resolution, not by deleting the pass.

- `dpr = Math.min(devicePixelRatio || 1, 2) * tier.dpr / 1.5` — never render a 3x phone at
  native resolution; the fill cost quadruples for no visible gain.
- Clamp `shadow` to `caps.maxTex`.
- Auto-detect: start at `medium`, measure rolling median frame time, step up after 3 s under
  12 ms, step down after 2 s over 20 ms. Tell the player in a toast; never oscillate.

## Frame budget at 60 fps

| Stage | Budget |
| --- | --- |
| Simulation | 1–2 ms |
| Shadow pass | 1–2 ms |
| Main pass | 6–9 ms |
| Post | 2–3 ms |
| HUD/DOM | <1 ms |

Keep draw calls under ~150. Batch static geometry, instance repeats, never create buffers
per frame, and never call `getUniformLocation` in the loop (cache it).

## Debug overlay

Behind a flag, print GPU string, buffer size, tier name, DPR, frame ms (avg/median/p99),
draw calls and the error count. In a single-file project this overlay *is* your profiler.

## Fallback

If WebGL2 is missing, a shader fails, or three consecutive frames throw, switch to the 2D
path with the same scene machine, the same input layer and the same save file. A degraded
game beats a broken one.
