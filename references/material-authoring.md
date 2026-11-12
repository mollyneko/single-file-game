# Procedural material authoring

A box with one albedo value reads as a box. A box with a height field, a wear mask, a
roughness gradient and a seam grid reads as a built object. The gap is not texture memory —
it is four layers and about sixty lines of shader.

This file is the surface half of `cinematic-look.md`. Read that for lighting, this for what
the light lands on.

## The five channels

Author every surface into the same five numbers, in this order. Everything downstream
(lighting, AO, reflections) only ever needs these:

| Channel | Range | What it decides |
| --- | --- | --- |
| albedo | 0.02–0.6 linear | base colour, and how much light a surface can return |
| roughness | 0.03–0.95 | specular width; the strongest "material" cue after albedo |
| metal | 0 or 1 | whether the specular is tinted by albedo |
| height | 0–1 | normal perturbation, seams, chips, aggregate |
| AO | 0–1 | cavity darkening baked into the material itself |

Do not reach for a texture. Sample noise at three scales and combine:

```glsl
float big  = fbm3(p * 0.09);   // 10 m  — patches, repairs, damp areas
float mid  = fbm3(p * 0.70);   // 1.4 m — wear, staining, tread
float fine = vnoise(p * 34.0); // 3 cm  — aggregate, grit
```

Three octave counts are enough if each one owns a different job. The mistake is using one
noise at one scale for everything: it reads as camouflage.

## Height, then normal

Never author normals directly. Author height and differentiate it — the lighting then agrees
with the silhouette:

```glsl
float e = 0.11;
float h0 = gh(p);
vec3 N = normalize(vec3(-(gh(p + vec2(e, 0.0)) - h0) / e, 1.0,
                        -(gh(p + vec2(0.0, e)) - h0) / e));
```

Three evaluations of the height field per pixel, and a height field of two octaves, not five.

**Fade the micro-normal with distance.** Sub-pixel normals alias into glitter, which is the
single most common "cheap render" tell on large ground planes:

```glsl
N = normalize(mix(N, vec3(0.0, 1.0, 0.0), smoothstep(4.0, 45.0, dist) * 0.92));
```

## Wear is a stack, not a texture

Real painted steel fails in a fixed order: paint, then primer, then oxide, then bare metal.
Model that order and the material writes itself:

```glsl
float chip   = tri(p, w, 0.55, seed);        // large flakes
float rustN  = tri(p, w, 2.00, seed + 13.0); // rust blooms
float grime  = tri(p, w, 0.22, seed + 3.0);  // broad dirt film

float wear  = smoothstep(0.74, 0.92, chip * 0.70 + rustN * 0.40 + (1.0 - N.y) * 0.14);
alb   = mix(alb, alb * 0.55 + vec3(0.055, 0.05, 0.048), wear * 0.75);   // to primer
rough = mix(rough, 0.85, wear * 0.8);

float oxide = smoothstep(0.80, 0.96, rustN * 0.8 + wear * 0.5 + streak * 0.22);
alb   = mix(alb, mix(vec3(0.20, 0.11, 0.055), vec3(0.34, 0.18, 0.10), chip), oxide * 0.7);
rough = mix(rough, 0.95, oxide);
metal = mix(metal, 0.0, oxide);      // oxide is not metal, whatever the base was
```

Two notes. **Thresholds above ~0.7, coverage below ~30%** — most of a maintained object is
intact, and damage that covers everything reads as noise. And **`1.0 - N.y`** in the wear
term puts damage on upward faces, where water sits. That one term does more than any mask.

## Seams: the fabricated-object tell

No amount of noise makes a 12 m slab look manufactured. A grid of plate seams does it in
three lines, because it gives the eye a known size to compare against:

```glsl
float sh = abs(fract(local.y * 0.55) - 0.5);          // horizontal strakes every 1.8 m
float sv = abs(fract(local.x * 0.8 + local.z * 0.8) - 0.5);
float seam = 1.0 - smoothstep(0.43, 0.5, max(sh, sv));
alb   *= 1.0 - seam * 0.55;
rough  = mix(rough, 0.92, seam * 0.7);
```

Use the box's **local** coordinate, not world space, or the grid slides as the object rotates.
Pick a plate size in metres first (1.5–2 m for industrial steel, 0.3 m for panels, 0.06 m for
sheet metal) and derive the frequency from it.

## Triplanar, or nothing

Instanced boxes have no UVs. Any 2D lookup needs a projection, and one projection stretches on
two of the three axes:

```glsl
vec3 w = abs(N); w /= (w.x + w.y + w.z);
float tri(vec3 p, vec3 w, float f, float s){
  return vnoise(p.zy * f + s) * w.x + vnoise(p.xz * f + s) * w.y + vnoise(p.xy * f + s) * w.z;
}
```

Three samples per field. Budget accordingly: two fields (wear, rust) is 6 noise lookups; add a
third only if it earns its frame time. For ground planes skip it — the plane is flat, use `p.xz`.

## Wet surfaces

Water is not a texture. It is three changes to the channels, all at once:

```glsl
alb   = base * mix(1.0, 0.30, pud);                      // wet surfaces are darker
rough = mix(0.72, 0.03, pud);                            // and far more mirror-like
N     = normalize(mix(N, vec3(0.0, 1.0, 0.0), pud * 0.9)); // and flat
```

Then add the sky, not a light: `col += skyColor(reflect(-V, N), 0.04, 0.0) * fresnel * pud`.
Because it is the same `skyColor()` the dome uses, puddles reflect the actual sunset. This is
the highest-value 20 lines in the whole renderer — a wet plane grounds an entire scene.

Pool shape matters: use a low-frequency `fbm` with a **narrow** smoothstep (0.47→0.505). Wide
edges read as fog on the floor; sharp edges plus a flat normal read as water. Add ripples only
inside the pool and keep the amplitude tiny (0.006–0.01 on the normal).

## Baking, when per-pixel is too slow

If the material is static and the camera is not looking at it from every angle, compute it
once. WebGL2 can render to multiple attachments, so one pass writes the five channels:

```js
gl.drawBuffers([gl.COLOR_ATTACHMENT0, gl.COLOR_ATTACHMENT1, gl.COLOR_ATTACHMENT2]);
// 0: rgb = albedo, a = opacity / mask
// 1: r = ao, g = roughness, b = metal, a = height
// 2: rg = packed normal xy
```

Sample two textures instead of computing 15 noise octaves per pixel, and get mip-mapping for
free (bake at 1024² or 2048² for a 40 m tile). Bake-time cost is once; per-frame cost is a
trilinear fetch. The 2D starter uses the same idea with `bakeBackground()`: expensive
per-pixel work belongs in an offscreen pass, not in the frame loop.

## Three failure modes

- **Camouflage.** One noise at 0.1 m scale on a 15 m object. Symptom: the object looks
  painted with blobs, and moving the camera makes it crawl. Fix: one field per physical scale,
  and check it at 1:1 pixels, not zoomed out.
- **Glitter.** High-frequency height with no distance fade. Symptom: the ground sparkles and
  shimmers while walking. Fix: fade normals to up past 20–40 m.
- **Plastic.** Roughness 0.4 for everything, metal 0. Symptom: every surface has the same
  broad sheen. Fix: push roughness to the ends of the range (0.05 water, 0.9 concrete) and use
  metal 0.5–0.9 on painted steel, 0 on stone.

## Checklist

1. Five channels, five numbers, one function.
2. Height differentiated, never an authored normal.
3. Micro-normal faded by distance.
4. Wear in primer → oxide → metal order, coverage under 30%.
5. Seams in local space, at a physically meaningful plate size.
6. Triplanar for boxes, planar for ground.
7. Water = darker albedo + flat normal + sky reflection.
8. Static material baked; dynamic material computed.
