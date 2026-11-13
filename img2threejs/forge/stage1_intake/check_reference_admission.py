#!/usr/bin/env python3
"""Reference-admission gate (Plan 1.3 §4.5.2) — no meaningless references.

Before an image/crop is admitted as ground truth for a component or the whole
object, it must pass deterministic checks so the Divine Eye never compares a
render against junk (empty mask, fragmented subject, too-small crop, a duplicate
angle that adds no information). A reference that fails is rejected WITH A REASON
at intake, before any tokens are spent — never silently used.

Pure Python stdlib (reuses extract_pbr_evidence's mask primitives + the shared
pHash). No PIL/numpy.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_pbr_evidence import build_foreground_mask, load_image  # noqa: E402
from probe_image import probe  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from image_hash import hamming, phash_from_image  # noqa: E402


# Thresholds (calibratable in Plan 1.3 §5; conservative defaults here).
MIN_FOREGROUND_COVERAGE = 0.05
MAX_FOREGROUND_COVERAGE = 0.97
MIN_SHORT_SIDE_PX = 64
MIN_LARGEST_COMPONENT_FRACTION = 0.60  # largest blob must be ≥60% of all foreground
DUPLICATE_HAMMING_THRESHOLD = 6  # pHash distance ≤ this vs an admitted ref ⇒ duplicate
COHERENCE_GRID = 96  # downsample mask to this side for connected-component analysis

# Generated-reference gate (local addition, single-file-game skill): a machine-generated
# reference must be a transparent PNG — the subject isolated on real alpha, no baked
# backdrop, floor or drop shadow — and the leftover background must sit at the corners
# while the subject stays centered. Enforced only with --generated; hand-picked photos
# legitimately have no alpha channel.
MIN_TRANSPARENT_FRACTION = 0.04  # ≥4% of all pixels visibly transparent
MIN_CORNER_TRANSPARENCY = 0.90  # ≥90% of each corner patch fully transparent
CORNER_PATCH_FRACTION = 0.06  # corner patch side = 6% of the image short side


def transparent_background_check(
    width: int,
    height: int,
    pixels: list[tuple[int, int, int, int]],
) -> tuple[bool, list[str], dict[str, Any]]:
    """Transparency gate for machine-generated references.

    Two deterministic facts must hold: a real fraction of the image is transparent
    (the subject is cut out, not composited onto a backdrop), and the transparency
    is where a background lives — the four corner patches are essentially clear
    while the subject occupies the middle. Returns (ok, reasons, detail)."""
    total = max(1, width * height)
    transparent = sum(1 for _r, _g, _b, alpha in pixels if alpha < 245)
    transparent_fraction = transparent / total
    patch = max(2, int(min(width, height) * CORNER_PATCH_FRACTION))
    clear_corners = 0
    for x0, x1, y0, y1 in (
        (0, patch, 0, patch),
        (width - patch, width, 0, patch),
        (0, patch, height - patch, height),
        (width - patch, width, height - patch, height),
    ):
        area = 0
        clear = 0
        for y in range(max(0, y0), min(height, y1)):
            for x in range(max(0, x0), min(width, x1)):
                area += 1
                if pixels[y * width + x][3] < 245:
                    clear += 1
        if area and clear / area >= MIN_CORNER_TRANSPARENCY:
            clear_corners += 1
    reasons: list[str] = []
    if transparent_fraction < MIN_TRANSPARENT_FRACTION:
        reasons.append(
            f"transparent background: only {transparent_fraction:.3f} of pixels are "
            f"transparent < {MIN_TRANSPARENT_FRACTION} — a generated reference must be a "
            "transparent PNG with the subject isolated (no baked backdrop, floor or drop shadow)"
        )
    elif clear_corners < 4:
        reasons.append(
            f"transparent background: only {clear_corners}/4 corner patches are clear "
            f"(≥{MIN_CORNER_TRANSPARENCY:.0%} transparent each) — the backdrop is not fully "
            "cut out; re-export with the background removed"
        )
    detail = {
        "transparentFraction": round(transparent_fraction, 4),
        "clearCorners": f"{clear_corners}/4",
    }
    return not reasons, reasons, detail


def largest_component_fraction(
    mask: list[bool], width: int, height: int, grid: int = COHERENCE_GRID
) -> float:
    """Fraction of foreground occupied by its single largest 4-connected blob,
    computed on a downsampled grid. ~1.0 = one coherent subject; low = scattered
    fragments (a meaningless silhouette for IoU/DCD)."""
    if width <= 0 or height <= 0 or not mask:
        return 0.0
    g = min(grid, max(1, width), max(1, height))
    cell = [[False] * g for _ in range(g)]
    for idx, on in enumerate(mask):
        if not on:
            continue
        x = idx % width
        y = idx // width
        if y >= height:
            break
        cell[min(g - 1, y * g // height)][min(g - 1, x * g // width)] = True
    total = sum(1 for row in cell for c in row if c)
    if total == 0:
        return 0.0
    seen = [[False] * g for _ in range(g)]
    best = 0
    for sy in range(g):
        for sx in range(g):
            if not cell[sy][sx] or seen[sy][sx]:
                continue
            size = 0
            stack = [(sy, sx)]
            seen[sy][sx] = True
            while stack:
                cy, cx = stack.pop()
                size += 1
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < g and 0 <= nx < g and cell[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            best = max(best, size)
    return best / total


def check_admission(
    crop_path: Path,
    viewpoint: str = "reference",
    against_hashes: list[int] | None = None,
    generated: bool = False,
) -> dict[str, Any]:
    """Return an admission verdict dict with reasons + a provenance tag.

    `against_hashes` are pHashes of already-admitted references; a near-duplicate
    (Hamming ≤ threshold) is rejected as adding no information. With `generated=True`
    the reference is machine-generated and must additionally pass the transparent-
    background gate (see transparent_background_check)."""
    reasons: list[str] = []
    try:
        width, height, pixels, _load_warnings = load_image(crop_path)
    except Exception as exc:  # noqa: BLE001
        # A reference that cannot even be decoded is a clean rejection, not a crash —
        # an undecodable image is the most meaningless "reference" of all.
        return {
            "admitted": False,
            "reasons": [f"cannot decode image as a usable reference: {type(exc).__name__}: {exc}"],
            "provenance": {
                "viewpoint": viewpoint,
                "sourcePath": str(crop_path.resolve()),
                "width": 0,
                "height": 0,
                "foregroundCoverage": 0.0,
                "largestComponentFraction": 0.0,
                "pHash": None,
                "duplicateOfHash": None,
            },
        }

    short_side = min(width, height)
    if short_side < MIN_SHORT_SIDE_PX:
        reasons.append(
            f"resolution floor: short side {short_side}px < {MIN_SHORT_SIDE_PX}px "
            "(too few pixels to derive geometry/color reliably)"
        )

    mask, diag, _mask_warnings = build_foreground_mask(width, height, pixels)
    coverage = float(diag.get("foregroundCoverage", 0.0))
    if coverage < MIN_FOREGROUND_COVERAGE:
        reasons.append(
            f"foreground coverage {coverage:.3f} < {MIN_FOREGROUND_COVERAGE} "
            "(empty/near-empty — meaningless silhouette)"
        )
    elif coverage > MAX_FOREGROUND_COVERAGE:
        reasons.append(
            f"foreground coverage {coverage:.3f} > {MAX_FOREGROUND_COVERAGE} "
            "(no background to segment against — silhouette not isolable)"
        )

    transparency_detail: dict[str, Any] | None = None
    if generated:
        transparency_ok, transparency_reasons, transparency_detail = transparent_background_check(
            width, height, pixels
        )
        reasons.extend(transparency_reasons)

    coherence = largest_component_fraction(mask, width, height)
    if coverage >= MIN_FOREGROUND_COVERAGE and coherence < MIN_LARGEST_COMPONENT_FRACTION:
        reasons.append(
            f"mask coherence: largest connected blob is {coherence:.2f} of foreground "
            f"< {MIN_LARGEST_COMPONENT_FRACTION} (fragmented/scattered subject — ambiguous)"
        )

    ref_hash = phash_from_image(width, height, pixels)
    duplicate_of: int | None = None
    for other in against_hashes or []:
        if hamming(ref_hash, other) <= DUPLICATE_HAMMING_THRESHOLD:
            duplicate_of = other
            reasons.append(
                f"duplicate/near-duplicate: pHash within {DUPLICATE_HAMMING_THRESHOLD} of an "
                "already-admitted reference (adds no information)"
            )
            break

    admitted = not reasons
    provenance = {
        "viewpoint": viewpoint,
        "sourcePath": str(crop_path.resolve()),
        "width": width,
        "height": height,
        "foregroundCoverage": round(coverage, 4),
        "largestComponentFraction": round(coherence, 4),
        "pHash": ref_hash,
        "duplicateOfHash": duplicate_of,
    }
    if transparency_detail is not None:
        provenance["transparency"] = transparency_detail
    return {
        "admitted": admitted,
        "reasons": reasons,
        "provenance": provenance,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--viewpoint", default="reference", help="viewpoint tag this ref is ground truth for")
    parser.add_argument(
        "--against",
        default="",
        help="comma-separated pHashes (ints) of already-admitted references, for duplicate detection",
    )
    parser.add_argument("--json", action="store_true", help="emit the verdict as JSON")
    parser.add_argument(
        "--generated",
        action="store_true",
        help="the reference was machine-generated: enforce the transparent-background gate",
    )
    # --out publishes the verdict as a workspace artifact so a later step -- including one
    # contributed by a domain plugin -- can consume it instead of recomputing admission.
    parser.add_argument("--out", type=Path, help="also write the verdict JSON here")
    # This step is where the base pipeline establishes the technical facts about a reference, so it
    # publishes the probe alongside its verdict. A later step -- including one contributed by a
    # domain plugin, which may not import forge.* -- consumes these instead of re-deriving them.
    parser.add_argument("--probe-out", type=Path, help="also write the image probe JSON here")
    args = parser.parse_args(argv)

    against: list[int] = []
    for token in args.against.split(","):
        token = token.strip()
        if token:
            try:
                against.append(int(token))
            except ValueError:
                print(f"warning: ignoring non-integer --against token {token!r}", file=sys.stderr)

    try:
        verdict = check_admission(
            args.image.expanduser().resolve(), args.viewpoint, against, generated=args.generated
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for target, payload in ((args.out, verdict), (args.probe_out, probe(args.image.expanduser().resolve()) if args.probe_out else None)):
        if target is None:
            continue
        target.expanduser().parent.mkdir(parents=True, exist_ok=True)
        target.expanduser().write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(verdict, indent=2, ensure_ascii=False))
    else:
        status = "ADMITTED" if verdict["admitted"] else "REJECTED"
        print(f"{status}  ({verdict['provenance']['viewpoint']})  pHash={verdict['provenance']['pHash']}")
        for reason in verdict["reasons"]:
            print(f"  - {reason}")
    return 0 if verdict["admitted"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
