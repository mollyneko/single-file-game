#!/usr/bin/env python3
"""Capture the review frames and score the measurable half of the nine-axis rubric.

The rubric is a judgement, and judgement drifts. Two reviews of the same build can differ by a
point or two, and part of that is taste that no script should try to remove. The other part is
mechanical: the reviews were never of the same frames. A different shot, viewport, quality tier
or frame count after boot meant the score was partly measuring the capture, not the build.

This script closes both halves.

  capture   drives a headless browser through a fixed protocol -- four named shots, fixed
            viewport, fixed prewarm, fixed quality tier, fixed seed -- and writes manifest.json
            with a sha256 per frame plus the hash of the HTML that produced them. If every shot
            hashes to the same image, the build never implemented the `?shot=` protocol and the
            capture is worthless; that is reported as an error, not a warning.

  score     decodes those PNGs with the standard library alone and computes the things a human
            is bad at and a script is good at: black crush, clipped highlights, dynamic range,
            luma contrast, saturation, hue spread, edge density.

The output is deliberately not a score. It is a set of **caps**: a metric out of range caps the
affected axes at 3, and a written score of 4 or 5 for that axis then fails the audit unless the
`SELF-REVIEW` marker carries an explicit `override` for it -- the axis, the measured value and a
sentence naming the stylistic reason. That escape hatch matters: a night scene and a cel-shaded
game both trip illumination and saturation statistics on purpose, and a gate that cannot be
argued with is a gate people learn to fake. It does not weaken the red lines, because overriding
is recorded where the handoff is read, not silently applied.

A script may only lower a score, never raise one -- anything a script can reward becomes the
thing to game, and the first casualty is the part of the frame nobody measures. The 4-vs-5
judgement stays with the eye, which is why `references/scoring-rubric.md` still owns the bands.

Usage:
    python scripts/score_frame.py capture game.html --out review/round-1
    python scripts/score_frame.py score review/round-1/manifest.json
    python scripts/score_frame.py image shot.png --json

Exit codes: 0 ok (caps and warnings may be present), 1 protocol or IO failure, 2 --strict with
a cap or a warning.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import time
import zlib
from pathlib import Path
from typing import Iterable

# --- the fixed capture protocol -----------------------------------------
# Four frames, because the rubric asks for four kinds of evidence: a title card, a gameplay
# wide shot, a zoomed character crop (full-frame shots hide broken rigs) and the most expensive
# effect. Names are what the build receives as `?shot=`; they are not free text.
SHOTS = ("title", "play", "char-closeup", "hero-effect")
# The title card is UI on a possibly flat background, so its exposure statistics would trip
# every red line while telling us nothing about the frame. It is captured, measured and
# reported, but excluded from the caps.
SCORED_SHOTS = ("play", "char-closeup", "hero-effect")
DEFAULT_VIEWPORT = (1280, 720)
DEFAULT_PREWARM = 200
DEFAULT_QUALITY = "high"
DEFAULT_SEED = 0
DEFAULT_VIRTUAL_TIME_MS = 6000
DEFAULT_SAMPLE_STEP = 2

# --- red lines ----------------------------------------------------------
# Each entry: (metric, axis, test, message). A single frame out of range caps that axis at 3.
# Thresholds are set where a shipped frame stops reading as a place: 15% of pixels below luma 8
# means the shadows are gone, 8% above 250 means the sky or a light source is blown, a
# p99-p01 span under 90/255 means the frame is fogged flat, sigma under 22 means no value
# structure, saturation outside 0.06-0.75 means greyscale or candy, hue entropy under 0.45
# means one colour owns the frame.
CAP_SCORE = 3
BLACK_LUMA = 8
WHITE_LUMA = 250
RED_LINES: tuple[tuple[str, str, str, float, str], ...] = (
    ("black_crush", "light", ">", 0.15, "shadow detail is crushed ({v:.1%} of pixels below luma 8)"),
    ("overexposed", "light", ">", 0.08, "highlights are clipped ({v:.1%} of pixels above luma 250)"),
    ("dynamic_range", "light", "<", 90.0, "the frame is flat or fogged (p99-p01 span {v:.0f}/255)"),
    ("contrast", "light", "<", 22.0, "no value structure (luma sigma {v:.1f})"),
    ("contrast", "beauty", "<", 22.0, "no value structure (luma sigma {v:.1f})"),
    ("saturation_mean", "beauty", "<", 0.06, "almost greyscale (mean saturation {v:.2f})"),
    ("saturation_mean", "beauty", ">", 0.95, "paint poured straight from the tube (mean saturation {v:.2f})"),
    ("hue_families", "beauty", "<", 1.8, "one colour family owns the frame ({v:.1f} effective hues)"),
)
# Edge density is reported but never caps: a fog bank, a night sky and a desert are legitimately
# low-detail frames, and noise inflates the number for a frame that has no world detail at all.
EDGE_WARN_DENSITY = 0.012
EDGE_THRESHOLD = 10
AXES = ("space", "light", "material", "reflection", "world", "budget",
        "beauty", "structure", "ui")


# --- PNG decoding (standard library only) -------------------------------
HTML_COMMENT = re.compile(r"<!--[\s\S]*?-->")


def html_fingerprint(text: str) -> str:
    """Hash the build's code, ignoring HTML comments.

    The manifest records which build produced the frames, and the HTML records the manifest's
    hash -- a loop if both hashed the whole file. Comments are the only thing that changes when
    the marker is written, and comments never render, so stripping them leaves a fingerprint that
    identifies the code while staying stable across the write-back. Newlines are normalised so a
    CRLF checkout fingerprints the same as an LF one.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(HTML_COMMENT.sub("", normalized).encode("utf-8")).hexdigest()
def read_png(path: str | Path) -> tuple[int, int, bytes, bytes]:
    """Decode an 8-bit non-interlaced PNG into (width, height, rgb, alpha).

    Screenshots are the only input this needs to handle, so the accepted subset is deliberate:
    bit depth 8, no interlacing, greyscale / RGB / grey+alpha / RGBA. Anything else raises,
    because silently mis-decoding a frame would corrupt every metric downstream.
    """
    raw = Path(path).read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")
    pos = 8
    idat: list[bytes] = []
    width = height = depth = colour_type = interlace = None
    while pos + 8 <= len(raw):
        (length,) = struct.unpack(">I", raw[pos:pos + 4])
        kind = raw[pos + 4:pos + 8]
        body = raw[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            width, height, depth, colour_type, _comp, _filt, interlace = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat.append(body)
        elif kind == b"IEND":
            break
        pos += 12 + length
    if width is None or height is None:
        raise ValueError(f"{path}: no IHDR")
    if depth != 8 or interlace != 0 or colour_type not in (0, 2, 4, 6):
        raise ValueError(f"{path}: unsupported PNG (depth {depth}, colour type {colour_type}, "
                         f"interlace {interlace})")
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[colour_type]
    stride = width * channels
    data = zlib.decompress(b"".join(idat))
    if len(data) < height * (stride + 1):
        raise ValueError(f"{path}: truncated image data")

    rgb = bytearray(width * height * 3)
    alpha = bytearray(b"\xff" * (width * height))
    previous = bytearray(stride)
    offset = 0
    for y in range(height):
        filter_type = data[offset]
        offset += 1
        line = bytearray(data[offset:offset + stride])
        offset += stride
        if filter_type == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif filter_type == 2:
            for i in range(stride):
                line[i] = (line[i] + previous[i]) & 0xFF
        elif filter_type == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + previous[i]) >> 1)) & 0xFF
        elif filter_type == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = previous[i]
                c = previous[i - channels] if i >= channels else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                predictor = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + predictor) & 0xFF
        elif filter_type != 0:
            raise ValueError(f"{path}: bad filter type {filter_type} on row {y}")
        row_start = y * width
        for x in range(width):
            src = x * channels
            dst = (row_start + x) * 3
            if channels <= 2:
                grey = line[src]
                rgb[dst] = rgb[dst + 1] = rgb[dst + 2] = grey
                if channels == 2:
                    alpha[row_start + x] = line[src + 1]
            else:
                rgb[dst] = line[src]
                rgb[dst + 1] = line[src + 1]
                rgb[dst + 2] = line[src + 2]
                if channels == 4:
                    alpha[row_start + x] = line[src + 3]
        previous = line
    return width, height, bytes(rgb), bytes(alpha)


def _hue(r: int, g: int, b: int, mx: int, mn: int) -> float | None:
    delta = mx - mn
    if delta == 0:
        return None
    if mx == r:
        sector = ((g - b) / delta) % 6
    elif mx == g:
        sector = (b - r) / delta + 2
    else:
        sector = (r - g) / delta + 4
    return (sector / 6.0) % 1.0


def frame_metrics(rgb: bytes, alpha: bytes, width: int, height: int,
                  step: int = DEFAULT_SAMPLE_STEP) -> dict:
    """Exposure, contrast, colour and detail statistics over a subsampled grid."""
    step = max(1, step)
    histogram = [0] * 256
    luma_rows: list[list[float]] = []
    saturation_sum = 0.0
    hue_bins = [0] * 12
    counted = 0

    for y in range(0, height, step):
        row: list[float] = []
        for x in range(0, width, step):
            index = y * width + x
            if alpha[index] < 8:
                row.append(float("nan"))
                continue
            base = index * 3
            r, g, b = rgb[base], rgb[base + 1], rgb[base + 2]
            luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
            row.append(luma)
            histogram[min(255, int(luma))] += 1
            counted += 1
            mx, mn = max(r, g, b), min(r, g, b)
            if mx > 0:
                saturation_sum += (mx - mn) / mx
            hue = _hue(r, g, b, mx, mn)
            if hue is not None:
                hue_bins[min(11, int(hue * 12))] += 1
        luma_rows.append(row)

    if counted == 0:
        raise ValueError("frame has no opaque pixels")

    mean = sum(i * n for i, n in enumerate(histogram)) / counted
    variance = sum(n * (i - mean) ** 2 for i, n in enumerate(histogram)) / counted

    def percentile(fraction: float) -> float:
        target = fraction * counted
        running = 0
        for value, count in enumerate(histogram):
            running += count
            if running >= target:
                return float(value)
        return 255.0

    black_crush = sum(histogram[:BLACK_LUMA]) / counted
    overexposed = sum(histogram[WHITE_LUMA + 1:]) / counted

    hue_total = sum(hue_bins)
    hue_bits = 0.0
    if hue_total:
        hue_bits = -sum((n / hue_total) * math.log(n / hue_total, 2) for n in hue_bins if n)
    # Effective hue families: how many equally-weighted colours would produce the same entropy.
    # A shipped frame is normally two or three families (sky, ground, accent); one family means
    # the frame is a single wash of colour. Raw entropy in bits is more stable than a normalised
    # ratio, because the bin count is an artefact of the binning, not of the image.
    hue_families = 2.0 ** hue_bits

    strong_edges = 0
    samples = 0
    for gy in range(len(luma_rows) - 1):
        for gx in range(len(luma_rows[gy]) - 1):
            here = luma_rows[gy][gx]
            if here != here:
                continue
            right = luma_rows[gy][gx + 1]
            down = luma_rows[gy + 1][gx]
            gradient = 0.0
            for neighbour in (right, down):
                if neighbour == neighbour:
                    gradient = max(gradient, abs(here - neighbour))
            samples += 1
            if gradient > EDGE_THRESHOLD:
                strong_edges += 1

    return {
        "pixels_sampled": counted,
        "black_crush": round(black_crush, 4),
        "overexposed": round(overexposed, 4),
        "dynamic_range": round(percentile(0.99) - percentile(0.01), 1),
        "mean_luma": round(mean, 1),
        "contrast": round(variance ** 0.5, 1),
        "saturation_mean": round(saturation_sum / counted, 4),
        "hue_entropy": round(hue_bits, 3),
        "hue_families": round(hue_families, 2),
        "edge_density": round(strong_edges / samples, 4) if samples else 0.0,
    }


def _same_view(a: dict, b: dict, tolerance: float = 0.005) -> bool:
    """True when two frames carry the same picture, judged on statistics rather than bytes.

    Byte hashes are not enough: a build that ignores `?shot=` still renders fresh animation
    frames, so every screenshot differs by a few bytes while showing the same thing. Two views
    of one scene differ in mean luma, contrast or edge density by far more than this.
    """
    keys = ("black_crush", "overexposed", "dynamic_range", "mean_luma",
            "contrast", "saturation_mean", "hue_families", "edge_density")
    for key in keys:
        left, right = a.get(key, 0.0), b.get(key, 0.0)
        allowed = max(0.002, tolerance * max(abs(left), abs(right), 1.0))
        if abs(left - right) > allowed:
            return False
    return True


def count_views(frames: Iterable[dict]) -> tuple[int, list[int]]:
    """Cluster frames by picture; return (number of distinct views, group index per frame)."""
    representatives: list[dict] = []
    groups: list[int] = []
    for frame in frames:
        metrics = frame["metrics"]
        for index, representative in enumerate(representatives):
            if _same_view(metrics, representative):
                groups.append(index)
                break
        else:
            representatives.append(metrics)
            groups.append(len(representatives) - 1)
    return len(representatives), groups


def caps_for(frames: Iterable[dict]) -> tuple[dict[str, int], list[str], list[str]]:
    """Return (caps, reasons, warnings) for a set of scored frames.

    Every frame is tested, not the average: a red line crossed in the character close-up is not
    cancelled out by a clean wide shot. Untouched axes cap at 5, meaning "no mechanical limit".
    """
    caps = {axis: 5 for axis in AXES}
    reasons: list[str] = []
    warnings: list[str] = []
    for frame in frames:
        shot = frame["shot"]
        metrics = frame["metrics"]
        for metric, axis, operator, limit, message in RED_LINES:
            value = metrics.get(metric)
            if value is None:
                continue
            crossed = value > limit if operator == ">" else value < limit
            if crossed:
                caps[axis] = min(caps[axis], CAP_SCORE)
                reasons.append(f"{axis} capped at {CAP_SCORE}: {shot} {message.format(v=value)}")
        if metrics.get("edge_density", 1.0) < EDGE_WARN_DENSITY:
            warnings.append(
                f"{shot} edge density {metrics['edge_density']:.3f} < {EDGE_WARN_DENSITY}: "
                "little world detail, or a legitimately empty view (not capped)"
            )
    return caps, reasons, warnings


# --- capture ------------------------------------------------------------
def find_chrome(explicit: str | None = None) -> Path:
    """Locate a headless-capable browser: explicit path, env, puppeteer cache, system."""
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get("CHROME_PATH"):
        candidates.append(Path(os.environ["CHROME_PATH"]))
    cache = Path.home() / ".cache" / "puppeteer"
    for pattern in ("chrome-headless-shell/*/*/chrome-headless-shell*",
                    "chrome-headless-shell/*/*/*/chrome-headless-shell*",
                    "chrome/*/*/chrome.exe", "chrome/*/*/chrome"):
        candidates.extend(sorted(cache.glob(pattern)))
    if os.name == "nt":
        for root in (os.environ.get("PROGRAMFILES", "C:/Program Files"),
                     os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"),
                     os.environ.get("LOCALAPPDATA", "")):
            if root:
                candidates.append(Path(root) / "Google/Chrome/Application/chrome.exe")
                candidates.append(Path(root) / "Microsoft/Edge/Application/msedge.exe")
    else:
        candidates.append(Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))
        for name in ("google-chrome", "chromium", "chromium-browser", "chrome"):
            found = shutil.which(name)
            if found:
                candidates.append(Path(found))
    for candidate in candidates:
        if candidate and candidate.exists() and candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "no headless browser found; pass --chrome, set CHROME_PATH, or install chrome-headless-shell"
    )


def capture(html: Path, out_dir: Path, chrome: Path, viewport: tuple[int, int],
            prewarm: int, quality: str, seed: int, virtual_time_ms: int,
            shots: Iterable[str] = SHOTS, timeout: int = 120) -> dict:
    """Drive the browser through the fixed protocol and write the manifest."""
    out_dir.mkdir(parents=True, exist_ok=True)
    html = html.resolve()
    uri = html.as_uri()
    frames: list[dict] = []
    headless_shell = "headless-shell" in chrome.name.lower()
    for shot in shots:
        target = out_dir / f"{shot}.png"
        if target.exists():
            target.unlink()
        url = (f"{uri}?shot={shot}&prewarm={prewarm}"
               f"&q={quality}&seed={seed}&review=1")
        command = [str(chrome)]
        if not headless_shell:
            command.append("--headless=new")
        command += [
            "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
            "--hide-scrollbars", "--force-device-scale-factor=1",
            f"--window-size={viewport[0]},{viewport[1]}",
            f"--virtual-time-budget={virtual_time_ms}",
            f"--screenshot={target}", url,
        ]
        started = time.time()
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"{shot}: browser timed out after {timeout}s") from exc
        if not target.exists() or target.stat().st_size == 0:
            detail = (result.stderr or result.stdout or "").strip().splitlines()
            raise RuntimeError(f"{shot}: no screenshot produced ({detail[-1] if detail else 'no output'})")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        width, height, rgb, alpha = read_png(target)
        frames.append({
            "shot": shot,
            "file": target.name,
            "sha256": digest,
            "bytes": target.stat().st_size,
            "width": width,
            "height": height,
            "seconds": round(time.time() - started, 2),
            "metrics": frame_metrics(rgb, alpha, width, height),
        })

    manifest = {
        "version": 1,
        "capturedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "html": str(html),
        "htmlFingerprint": html_fingerprint(html.read_text(encoding="utf-8", errors="replace")),
        "protocol": {
            "shots": list(shots),
            "viewport": list(viewport),
            "prewarm": prewarm,
            "quality": quality,
            "seed": seed,
            "virtualTimeMs": virtual_time_ms,
            "browser": chrome.name,
        },
        "frames": frames,
    }
    scored = [f for f in frames if f["shot"] in SCORED_SHOTS]
    caps, reasons, warnings = caps_for(scored)
    manifest["caps"] = caps
    manifest["reasons"] = reasons
    manifest["warnings"] = warnings

    distinct_hashes = len({f["sha256"] for f in frames})
    unique_views, groups = count_views(frames)
    for frame, group in zip(frames, groups):
        frame["view"] = group
    # One shot cannot prove anything about the protocol; a single-image check is a legitimate
    # use, so it is reported as "not judged" instead of failed.
    protocol_ok = None if len(frames) < 2 else unique_views >= 2
    manifest["distinctFrames"] = distinct_hashes
    manifest["uniqueViews"] = unique_views
    manifest["protocolOk"] = protocol_ok
    if protocol_ok is False:
        manifest["reasons"].append(
            f"only {unique_views} distinct view(s) across {len(frames)} shots: the build ignores "
            "?shot=, so these frames are not separate views of the build"
        )
    manifest["ok"] = protocol_ok is not False

    path = out_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["manifestPath"] = str(path)
    manifest["manifestSha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return manifest


# --- reporting ----------------------------------------------------------
def print_manifest(manifest: dict) -> None:
    print(f"html: {manifest['html']}")
    protocol = manifest["protocol"]
    print(f"protocol: {len(protocol['shots'])} shots, {protocol['viewport'][0]}x{protocol['viewport'][1]}, "
          f"prewarm {protocol['prewarm']}, quality {protocol['quality']}, seed {protocol['seed']}")
    for frame in manifest["frames"]:
        m = frame["metrics"]
        print(f"  {frame['shot']:<14} {frame['width']}x{frame['height']}  "
              f"crush {m['black_crush']:.1%}  clip {m['overexposed']:.1%}  "
              f"range {m['dynamic_range']:.0f}  sigma {m['contrast']:.1f}  "
              f"sat {m['saturation_mean']:.2f}  hues {m['hue_families']:.1f}  "
              f"edge {m['edge_density']:.3f}")
    print(f"distinct frames: {manifest['uniqueViews']} view(s) / {len(manifest['frames'])} shots "
          f"({manifest['distinctFrames']} distinct byte hashes)")
    for reason in manifest["reasons"]:
        print(f"  x {reason}")
    for warning in manifest["warnings"]:
        print(f"  ! {warning}")
    limited = {axis: cap for axis, cap in manifest["caps"].items() if cap < 5}
    print("caps: " + (", ".join(f"{axis}<={cap}" for axis, cap in sorted(limited.items()))
                      if limited else "none — no mechanical limit on any axis"))
    protocol = manifest.get("protocolOk")
    print("protocol: " + ("ok" if protocol else ("not judged (single shot)" if protocol is None else "failed")))


def marker_fragment(manifest: dict, manifest_path: Path, html: Path) -> str:
    """The `metrics` block to paste into SELF-REVIEW, with a path relative to the HTML."""
    relative = os.path.relpath(manifest_path.resolve(), html.resolve().parent).replace("\\", "/")
    payload = {
        "manifest": relative,
        "sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "htmlFingerprint": manifest["htmlFingerprint"],
        "caps": manifest["caps"],
    }
    return json.dumps({"metrics": payload}, indent=2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="action", required=True)

    cap = sub.add_parser("capture", help="drive the fixed protocol and write manifest.json")
    cap.add_argument("html", type=Path)
    cap.add_argument("--out", type=Path, default=Path("review/round-1"))
    cap.add_argument("--chrome")
    cap.add_argument("--viewport", default=f"{DEFAULT_VIEWPORT[0]}x{DEFAULT_VIEWPORT[1]}")
    cap.add_argument("--prewarm", type=int, default=DEFAULT_PREWARM)
    cap.add_argument("--quality", default=DEFAULT_QUALITY)
    cap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    cap.add_argument("--virtual-time", type=int, default=DEFAULT_VIRTUAL_TIME_MS)
    cap.add_argument("--shots", nargs="+", default=list(SHOTS))
    cap.add_argument("--timeout", type=int, default=180,
                     help="per-shot browser timeout in seconds (raise it for heavy builds)")
    cap.add_argument("--marker", action="store_true", help="print the SELF-REVIEW metrics block")

    sco = sub.add_parser("score", help="score an existing manifest")
    sco.add_argument("manifest", type=Path)
    sco.add_argument("--json", action="store_true")
    sco.add_argument("--strict", action="store_true")

    img = sub.add_parser("image", help="score one PNG")
    img.add_argument("image", type=Path)
    img.add_argument("--step", type=int, default=DEFAULT_SAMPLE_STEP)
    img.add_argument("--json", action="store_true")
    img.add_argument("--strict", action="store_true")

    args = parser.parse_args(argv)

    if args.action == "capture":
        try:
            width, height = (int(part) for part in args.viewport.lower().split("x"))
        except ValueError:
            parser.error(f"--viewport must be WxH, got {args.viewport!r}")
        try:
            chrome = find_chrome(args.chrome)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        try:
            manifest = capture(args.html, args.out, chrome, (width, height), args.prewarm,
                               args.quality, args.seed, args.virtual_time, args.shots,
                               args.timeout)
        except (RuntimeError, ValueError, OSError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print_manifest(manifest)
        if args.marker:
            print()
            print(marker_fragment(manifest, Path(manifest["manifestPath"]), args.html))
        return 0 if manifest["ok"] else 1

    if args.action == "score":
        if not args.manifest.exists():
            print(f"error: no manifest at {args.manifest}", file=sys.stderr)
            return 1
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if args.json:
            manifest["manifestPath"] = str(args.manifest)
            manifest["manifestSha256"] = hashlib.sha256(args.manifest.read_bytes()).hexdigest()
            print(json.dumps(manifest, indent=2))
        else:
            print_manifest(manifest)
        if not manifest.get("ok", True):
            return 1
        if args.strict and (manifest.get("reasons") or manifest.get("warnings")):
            return 2
        return 0
    width, height, rgb, alpha = read_png(args.image)
    metrics = frame_metrics(rgb, alpha, width, height, args.step)
    manifest = {"frames": [{"shot": args.image.stem, "metrics": metrics}]}
    caps, reasons, warnings = caps_for(manifest["frames"])
    if args.json:
        print(json.dumps({"image": str(args.image), "metrics": metrics,
                          "caps": caps, "reasons": reasons, "warnings": warnings}, indent=2))
    else:
        for key, value in metrics.items():
            print(f"{key}: {value}")
        for reason in reasons:
            print(f"  x {reason}")
        for warning in warnings:
            print(f"  ! {warning}")
        limited = {axis: cap for axis, cap in caps.items() if cap < 5}
        print("caps: " + (", ".join(f"{axis}<={cap}" for axis, cap in sorted(limited.items()))
                          if limited else "none"))
    if args.strict and (reasons or warnings):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
