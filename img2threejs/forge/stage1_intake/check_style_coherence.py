#!/usr/bin/env python3
"""Style-coherence gate for generated reference sets (local addition, single-file-game).

Compares a candidate reference against a style anchor on two deterministic color
facts: the coarse RGB histogram of the subject (alpha ≥ 128) and its mean
luminance. It is a machine-checkable *proxy* for "one style across the set" —
it catches palette and rendering-treatment drift between generated images, but
lighting direction, line treatment and proportions still require the staged
visual review in img2threejs/PIPELINE.md. Pure stdlib; no PIL/numpy.

    python check_style_coherence.py anchor.png candidate.png
    python check_style_coherence.py anchor.png candidate.png --min-cosine 0.7 --json

Exit codes: 0 = coherent, 1 = drift beyond thresholds, 2 = error.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_pbr_evidence import load_image  # noqa: E402

# Defaults; loosen with --min-cosine / --max-luma-delta when a set intentionally
# spans more color ground than one subject (e.g. different characters of one style).
MIN_HISTOGRAM_COSINE = 0.80
MAX_MEAN_LUMA_DELTA = 40.0
_HIST_SIDE = 16  # 4 bits per channel → 4096 bins
ALPHA_FLOOR = 128  # count only subject pixels


def subject_histogram(
    width: int,
    height: int,
    pixels: list[tuple[int, int, int, int]],
) -> list[int]:
    hist = [0] * (_HIST_SIDE**3)
    for red, green, blue, alpha in pixels:
        if alpha < ALPHA_FLOOR:
            continue
        index = (red >> 4) << 8 | (green >> 4) << 4 | (blue >> 4)
        hist[index] += 1
    return hist


def mean_luma(
    width: int,
    height: int,
    pixels: list[tuple[int, int, int, int]],
) -> float:
    values = [
        0.2126 * red + 0.7152 * green + 0.0722 * blue
        for red, green, blue, alpha in pixels
        if alpha >= ALPHA_FLOOR
    ]
    return sum(values) / max(1, len(values))


def histogram_cosine(a: list[int], b: list[int]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def check_coherence(
    anchor_path: Path,
    candidate_path: Path,
    min_cosine: float = MIN_HISTOGRAM_COSINE,
    max_luma_delta: float = MAX_MEAN_LUMA_DELTA,
) -> dict:
    try:
        aw, ah, apx, awarn = load_image(anchor_path)
    except Exception as exc:  # noqa: BLE001
        return {"coherent": False, "reasons": [f"cannot decode anchor: {type(exc).__name__}: {exc}"]}
    try:
        cw, ch, cpx, cwarn = load_image(candidate_path)
    except Exception as exc:  # noqa: BLE001
        return {"coherent": False, "reasons": [f"cannot decode candidate: {type(exc).__name__}: {exc}"]}

    anchor_hist = subject_histogram(aw, ah, apx)
    candidate_hist = subject_histogram(cw, ch, cpx)
    cosine = histogram_cosine(anchor_hist, candidate_hist)
    anchor_luma = mean_luma(aw, ah, apx)
    candidate_luma = mean_luma(cw, ch, cpx)
    luma_delta = abs(anchor_luma - candidate_luma)

    reasons: list[str] = []
    if cosine < min_cosine:
        reasons.append(
            f"color structure drift: histogram cosine {cosine:.3f} < {min_cosine:.2f} against "
            "the style anchor — palette or rendering treatment diverges; regenerate the "
            "reference from the same style anchor"
        )
    if luma_delta > max_luma_delta:
        reasons.append(
            f"luminance drift: mean luma delta {luma_delta:.1f} > {max_luma_delta:.1f} against "
            "the style anchor — the candidate reads as a different lighting/exposure regime"
        )
    return {
        "coherent": not reasons,
        "reasons": reasons,
        "metrics": {
            "histogramCosine": round(cosine, 4),
            "anchorMeanLuma": round(anchor_luma, 1),
            "candidateMeanLuma": round(candidate_luma, 1),
            "lumaDelta": round(luma_delta, 1),
        },
        "thresholds": {"minCosine": min_cosine, "maxLumaDelta": max_luma_delta},
        "anchor": str(anchor_path.resolve()),
        "candidate": str(candidate_path.resolve()),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("anchor", type=Path, help="the style anchor image (first admitted reference)")
    parser.add_argument("candidate", type=Path, help="the reference to check against the anchor")
    parser.add_argument("--min-cosine", type=float, default=MIN_HISTOGRAM_COSINE)
    parser.add_argument("--max-luma-delta", type=float, default=MAX_MEAN_LUMA_DELTA)
    parser.add_argument("--json", action="store_true", help="emit the verdict as JSON")
    parser.add_argument("--out", type=Path, help="also write the verdict JSON here")
    args = parser.parse_args(argv)

    anchor = args.anchor.expanduser().resolve()
    candidate = args.candidate.expanduser().resolve()
    for path in (anchor, candidate):
        if not path.exists():
            print(f"error: {path} does not exist", file=sys.stderr)
            return 2
    verdict = check_coherence(anchor, candidate, args.min_cosine, args.max_luma_delta)

    if args.out:
        args.out.expanduser().parent.mkdir(parents=True, exist_ok=True)
        args.out.expanduser().write_text(
            json.dumps(verdict, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    if args.json:
        print(json.dumps(verdict, indent=2, ensure_ascii=False))
    else:
        status = "COHERENT" if verdict["coherent"] else "DRIFT"
        metrics = verdict.get("metrics", {})
        print(f"{status}  cosine={metrics.get('histogramCosine')}  lumaDelta={metrics.get('lumaDelta')}")
        for reason in verdict.get("reasons", []):
            print(f"  - {reason}")
    return 0 if verdict["coherent"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
