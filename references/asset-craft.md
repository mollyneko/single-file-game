# Asset craft — the 3D hard gate

A single file is a **format**, not a visual ceiling. Two single-file 3D games were torn apart to
find out why one reads as a shipped title and the other as a coloured prototype. The answer was
not a better shader. It was where the bytes went.

## The comparison

| | Finished 3D game | Primitive-built 3D game |
| --- | --- | --- |
| Total | 1,422,128 bytes / 6,214 lines | 160,762 bytes / 4,148 lines |
| Inline engine | minified three.js, 777 KB (two lines alone: 134 KB + 239 KB) | none — 16 hand-written GLSL programs |
| Application code | 645 KB, dominated by asset generation | ~100 KB of gameplay + world, rest is shaders |
| Materials | 130 named surfaces (`steel_galv`, `diamond_plate`, `apron_wet`, `grime_streak`, `csc_plate`, `hazard_voltage`…) | one RGB triple per part, e.g. `[0.36, 0.26, 0.17]` |
| Object specs | 36+ table rows `[w, h, d, primaryMat, secondaryMat]` | ad-hoc `push(x, y, z, ...)` calls |
| Geometry ops | bevel boxes (12 sites), lathe/tube/extrude/curve, `computeVertexNormals()` 18×, per-vertex displacement | boxes, spheres and capsules used directly as final assets |
| Texture ops | 174 Canvas 2D drawing calls, `DataTexture`, 6 `onBeforeCompile` injections across 19 shader chunks | none |
| Characters | `SkinnedMesh` + `Skeleton` + `bind()` + injected `skinning_*` chunks | one capsule per bone ("beads on a string") |
| Post chain | custom HDR pass chain | full hand-written chain (shadow → volumetrics → SSAO → bloom → ACES → FXAA) |

Both files have a complete post stack. **The gap is almost entirely in the asset layer**, not in
tone mapping. That is the point of this gate.

The winning file also contains a material calibration array — seven spheres at
`roughness: .06 + f * .15` and `metalness: 0 / 1` — and a single oil drum built from a
hand-authored 19-point profile with two reinforcing ribs, per-vertex dent displacement, a
recomputed normal buffer, and a seam-normal average so the lathe seam does not split the
highlight. That drum is worth more to the frame than any bloom tweak.

## The six hard constraints

These are non-negotiable for a **shipped 3D game**. A starter or an in-progress scaffold is
exempt; a deliverable is not. `check_single_file.py --strict --craft` is the ship gate.

### 1. Inline the engine; do not spend the budget reimplementing it

"Zero external assets" means zero runtime requests, not zero library code. A 3D build should
paste a minified engine into the `<script>` block and use its PBR materials, IBL (`PMREM`),
shadow maps, skinned meshes, lathe/tube/extrude geometry and instancing. Hand-writing a
renderer is only justified when the asset layer is *already* complete. If the render pipeline
is larger than the asset layer, the budget is inverted.

> Rule 1 of `SKILL.md` already permits an inline library. This constraint makes it the default
> for 3D, and forbids "dependency purity" as a reason to ship primitive art.

The auditor understands this build: `fetch()` calls on `THREE.FileLoader` /
`ImageBitmapLoader` lines are reported as inline-engine loader code rather than game requests,
and the size warning allows a ~1.4 MB inline build (hard limit 2.5 MB). A literal
`fetch("...")` in game code still fails. What is forbidden is the *runtime request*, not the
library text.

### 2. No bare primitive is a finished asset

A box, sphere or capsule may be an intermediate. A visible object must pass through at least
one of: **bevel, curved surface (lathe / tube / extrude / spline), per-vertex displacement,
or a generated texture**. A tree that is one box plus four boxes is a placeholder.

### 3. Bevel hard surfaces, recompute normals, weld seams

Every hard-edged box gets a bevel of at least 0.02 world units so the key light draws a rim.
Every generated geometry calls a normal recompute. Every lathe/revolved mesh averages the
first and last ring normals, or the seam shows as a dark line. The difference between a
"box" and a "steel casing" is one bevel and one normal pass.

### 4. A named material library, not a palette of RGB triples

Maintain ≥ 12 named materials, each with at least albedo + roughness + metalness (or the
equivalent shader channels). Generate maps at runtime — `CanvasTexture` / `DataTexture` /
shader noise — for wear, seams, stencils, decals and hazard markings. Surfaces are looked up
by name (`mats.get("steel_galv")`), never by passing a raw colour into a draw call. Ship a
calibration row (roughness sweep × metalness 0/1) and look at it before tuning exposure.

### 5. Continuous skinning for animated characters

If it has a skeleton, it is one continuous skinned mesh with bone weights. Attaching one
primitive per bone leaves visible gaps at every joint; widening the capsules to hide the gaps
only produces "beads on a string". Use `SkinnedMesh` + `Skeleton` + `bind()`, or an equivalent
weighted-vertex implementation in a hand-written pipeline.

### 6. Seeded, table-driven asset builders

Object definitions live in a spec table (`[w, h, d, primaryMat, secondaryMat]`), and a builder
owns a named seed RNG, a transform stack (`push` / `pop`), and material lookup by name.
`Math.random()` may jitter cosmetic particles; it must not decide silhouette, profile points
or material assignment. Otherwise the same seed cannot reproduce the same world.

## What `--craft` checks

The auditor cannot judge beauty, but it can prove the work was *attempted*. Four signal groups,
each a hard failure when missing from a 3D deliverable:

| Group | Signals (any) | Catches |
| --- | --- | --- |
| Geometry craft | `bevel`, `Lathe/Tube/Extrude/CatmullRom`, `computeVertexNormals`, per-vertex `setXYZ`/`setAttribute("position")` edits | bare primitive stacks |
| Material library | `roughness` **and** `metalness`, plus a named material table / `MeshStandardMaterial` / `get("mat")` | RGB-only palettes |
| Generated textures | `DataTexture`, `CanvasTexture`, `createElement("canvas")` + `getContext("2d")`, `createImageData`, `texImage2D` from generated buffers | untextured surfaces |
| Continuous skinning | *only required when bone/skeleton signals exist*: `SkinnedMesh`, `Skeleton`, `skinIndex`/`skinWeight`, `skinning_*` chunks | primitives hung off bones |

It also reports the four groups as a `4/4` note so a reviewer can see the craft budget at a
glance. A file that is not detected as 3D skips the gate.

## Priority when catching up

Cheapest first, all of them possible without an engine:

1. Beveled boxes + recomputed normals — smallest diff, largest perceived gain.
2. A named material table + one generated wear/seed texture pass.
3. Replace box canopies / columns with profile-driven lathes and splines.
4. Replace per-bone parts with one weighted skinned mesh.

Industrial subjects (containers, drums, railings, stencilled plates) reward this quickly:
bevel + metal + decal is almost the whole look. Organic subjects (characters, foliage,
terrain) cost more — budget for it in step 1 of the workflow, not at the end.

## Anti-patterns

- **"It is one file, so I cannot afford an engine."** A 1.4 MB inline file is still one file.
- **Untextured boxes under a flat ambient** — already an anti-pattern in `SKILL.md`; this gate
  makes it fail the audit rather than just the eye test.
- **RGB triples as the material system.** Colours are a *channel* of a material, not the material.
- **Widening capsules to hide joint gaps.** Fix the skinning.
- **Tuning bloom, exposure or grade to fix a modelling problem.** A bevel does what a bloom
  pass cannot.
