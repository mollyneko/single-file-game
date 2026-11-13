#!/usr/bin/env python3
"""Audit a single-file HTML game against the format rules and the 3D asset-craft gate.

Checks the things that actually break this format: remote resources, missing shell parts,
dangling element IDs and runaway file size. With --craft it also enforces the 3D hard gate
(bevel/curved geometry, a named material library, generated textures, continuous skinning).

    python check_single_file.py game.html
    python check_single_file.py game.html --strict
    python check_single_file.py game3d.html --strict --craft   # 3D ship gate
    python check_single_file.py assets/*.html --json

Exit codes: 0 = pass, 1 = failure (or any warning with --strict).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REMOTE_ATTR = re.compile(
    r"""\b(?:src|href|poster|data)\s*=\s*["']\s*(?:https?:)?//""", re.IGNORECASE
)
REMOTE_CSS = re.compile(r"""@import\s+(?:url\()?["']?(?:https?:)?//""", re.IGNORECASE)
CSS_URL = re.compile(r"""url\(\s*["']?(?:https?:)?//""", re.IGNORECASE)

NETWORK_CALLS = [
    (re.compile(r"\bfetch\s*\("), "fetch()"),
    (re.compile(r"\bXMLHttpRequest\b"), "XMLHttpRequest"),
    (re.compile(r"\bnew\s+WebSocket\b"), "WebSocket"),
    (re.compile(r"\bnew\s+EventSource\b"), "EventSource"),
    (re.compile(r"\bsendBeacon\s*\("), "sendBeacon"),
    (re.compile(r"\bimport\s*\(\s*['\"]"), "dynamic import()"),
    (re.compile(r"^\s*import\s+[\w{*].*from\s+['\"]", re.MULTILINE), "ES module import"),
    (re.compile(r"<script[^>]+\bsrc\s*=", re.IGNORECASE), "<script src>"),
    (re.compile(r"<link[^>]+\bhref\s*=", re.IGNORECASE), "<link href>"),
]

ID_ATTR = re.compile(r"""\bid\s*=\s*["']([^"']+)["']""")
ID_REF = [
    re.compile(r"""getElementById\s*\(\s*["']([^"']+)["']\s*\)"""),
    re.compile(r"""querySelector(?:All)?\s*\(\s*["']#([A-Za-z0-9_\-]+)["']"""),
    re.compile(r"""\$\s*\(\s*["']#([A-Za-z0-9_\-]+)["']"""),
]

INLINE_HANDLER = re.compile(r"<[^>]+\son[a-z]+\s*=\s*[\"']", re.IGNORECASE)
# Inline 3D engines ship loader classes that call fetch(). That is library code,
# not a runtime request made by the game — see references/asset-craft.md.
INLINE_LOADER_CTX = re.compile(r"THREE\.|FileLoader|ImageBitmapLoader|\bLoader\b", re.IGNORECASE)

ERROR_BOUNDARY = [
    re.compile(r"addEventListener\s*\(\s*['\"]error['\"]"),
    re.compile(r"window\.onerror"),
    re.compile(r"\bonerror\s*="),
]

REDUCED_MOTION = re.compile(r"prefers-reduced-motion")

# --- 3D asset-craft gate -------------------------------------------------
# The gate cannot judge beauty; it proves the asset work was attempted. A 3D
# deliverable must show all four groups. See references/asset-craft.md.
IS_3D = re.compile(
    r"getContext\(\s*['\"]webgl2|WebGL2RenderingContext|WebGLRenderer|"
    r"createShader|compileShader|\bTHREE\.",
    re.IGNORECASE,
)
BONE_SIGNAL = re.compile(
    r"BONE_DEFS|\bbones\b|\bSkeleton\b|computePose|poseEntity|\bskinning\b|\bboneIndex\b",
    re.IGNORECASE,
)
GEOMETRY_SIGNALS = [
    re.compile(r"\bbevel\b", re.IGNORECASE),
    re.compile(r"LatheGeometry|TubeGeometry|ExtrudeGeometry|CatmullRom|\brevolve\b", re.IGNORECASE),
    re.compile(r"computeVertexNormals", re.IGNORECASE),
    re.compile(r"\bdisplace(?:ment)?\b|\bprofilePoints\b|\blathe\b", re.IGNORECASE),
]
MATERIAL_TABLE_SIGNALS = [
    re.compile(r"mats\.get\(|\.mat\(\s*['\"]"),
    re.compile(r"\bMATERIALS\b|material(?:s|Lib|Table)\s*[:=]", re.IGNORECASE),
    re.compile(r"new\s+Mesh(?:Standard|Physical)Material"),
    re.compile(r"materialLibrary|materialTable", re.IGNORECASE),
]
TEXTURE_SIGNALS = [
    re.compile(r"DataTexture|CanvasTexture|createImageData|texImage2D", re.IGNORECASE),
    re.compile(r"createElement\(\s*['\"]canvas['\"]\s*\)", re.IGNORECASE),
    re.compile(r"getContext\(\s*['\"]2d['\"]\s*\)", re.IGNORECASE),
    re.compile(r"\bnoiseTex\b|bakeTexture|makeTexture", re.IGNORECASE),
]
SKINNING_SIGNALS = [
    re.compile(r"SkinnedMesh|new\s+Skeleton\s*\(|skinIndex|skinWeight", re.IGNORECASE),
    re.compile(r"skinning_vertex|skinnormal_vertex|boneWeights|bindMatrix", re.IGNORECASE),
]


def craft_check(text: str) -> tuple[list[str], list[str], bool]:
    """Return (hit groups, missing groups, whether skinning was required)."""
    groups: dict[str, bool] = {
        "geometry craft": any(p.search(text) for p in GEOMETRY_SIGNALS),
        "material library": (
            re.search(r"roughness", text, re.IGNORECASE) is not None
            and re.search(r"metalness", text, re.IGNORECASE) is not None
            and any(p.search(text) for p in MATERIAL_TABLE_SIGNALS)
        ),
        "generated textures": any(p.search(text) for p in TEXTURE_SIGNALS),
        "continuous skinning": True,
    }
    needs_skin = BONE_SIGNAL.search(text) is not None
    if needs_skin:
        groups["continuous skinning"] = any(p.search(text) for p in SKINNING_SIGNALS)
    hits = [k for k, v in groups.items() if v]
    missing = [k for k, v in groups.items() if not v]
    return hits, missing, needs_skin


@dataclass
class Report:
    path: Path
    size_kb: float = 0.0
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    craft_hits: list[str] = field(default_factory=list)
    craft_missing: list[str] = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.failures.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)

    @property
    def ok(self) -> bool:
        return not self.failures

    def as_dict(self) -> dict:
        return {
            "path": str(self.path),
            "size_kb": round(self.size_kb, 1),
            "ok": self.ok,
            "failures": self.failures,
            "warnings": self.warnings,
            "notes": self.notes,
            "craft_hits": self.craft_hits,
            "craft_missing": self.craft_missing,
        }


def audit(path: Path, warn_kb: float, fail_kb: float, craft: bool = False) -> Report:
    r = Report(path=path)
    raw = path.read_bytes()
    r.size_kb = len(raw) / 1024
    text = raw.decode("utf-8", errors="replace")
    head = text[: text.lower().find("</head>") + 7] if "</head>" in text.lower() else text

    # --- format: no remote anything -------------------------------------
    for m in REMOTE_ATTR.finditer(text):
        line = text[: m.start()].count("\n") + 1
        r.fail(f"remote resource attribute at line {line}: {m.group(0).strip()[:60]}")
        break
    if REMOTE_CSS.search(head):
        r.fail("remote @import in CSS")
    if CSS_URL.search(head):
        r.fail("remote url(...) in CSS (fonts, images)")
    for pattern, label in NETWORK_CALLS:
        if label == "fetch()":
            hits = list(pattern.finditer(text))
            game_hits = []
            for m in hits:
                ls = text.rfind("\n", 0, m.start()) + 1
                le = text.find("\n", m.end())
                line_text = text[ls:le if le >= 0 else len(text)]
                if not INLINE_LOADER_CTX.search(line_text):
                    game_hits.append(m)
            if game_hits:
                line = text[: game_hits[0].start()].count("\n") + 1
                r.fail(f"fetch() found at line {line} — the file must work offline")
            elif hits:
                r.note(f"{len(hits)} fetch() call(s) are inline-engine loader code, not game requests")
            continue
        m = pattern.search(text)
        if m:
            line = text[: m.start()].count("\n") + 1
            r.fail(f"{label} found at line {line} — the file must work offline")

    # --- shell: required head parts -------------------------------------
    if not re.search(r"<title[^>]*>\s*\S", text, re.IGNORECASE):
        r.fail("missing or empty <title>")
    if not re.search(r"""<meta[^>]+charset""", head, re.IGNORECASE):
        r.fail("missing <meta charset>")
    if not re.search(r"""<meta[^>]+name=["']viewport["']""", head, re.IGNORECASE):
        r.fail("missing viewport meta — the game will not fit phones")
    if "viewport-fit=cover" not in head:
        r.warn("viewport meta lacks viewport-fit=cover (safe areas on notched devices)")
    if not re.search(r"<style[\s>]", text, re.IGNORECASE):
        r.fail("no inline <style> block")
    if not re.search(r"<script[\s>]", text, re.IGNORECASE):
        r.fail("no inline <script> block")

    # --- resilience ------------------------------------------------------
    if not any(p.search(text) for p in ERROR_BOUNDARY):
        r.fail("no global error handler (window 'error' / unhandledrejection)")
    if "unhandledrejection" not in text:
        r.warn("no 'unhandledrejection' handler — async failures will be silent")
    if not REDUCED_MOTION.search(text):
        r.warn("no prefers-reduced-motion handling")
    if INLINE_HANDLER.search(text):
        r.warn("inline event attributes (onclick=...) found — prefer addEventListener")

    # --- element id integrity -------------------------------------------
    declared = ID_ATTR.findall(text)
    dupes = {i for i in declared if declared.count(i) > 1}
    if dupes:
        r.warn("duplicate id attributes: " + ", ".join(sorted(dupes)[:6]))
    known = set(declared)
    missing: list[str] = []
    for pattern in ID_REF:
        for ref in pattern.findall(text):
            if ref not in known and ref not in missing:
                missing.append(ref)
    if missing:
        r.fail("referenced but missing ids: " + ", ".join(sorted(missing)[:8]))

    # --- size ------------------------------------------------------------
    if r.size_kb > fail_kb:
        r.fail(f"file is {r.size_kb:.0f} KB (hard limit {fail_kb:.0f} KB)")
    elif r.size_kb > warn_kb:
        r.warn(f"file is {r.size_kb:.0f} KB — consider a smaller visual budget")
    else:
        r.note(f"file is {r.size_kb:.0f} KB")

    # --- 3D asset craft ---------------------------------------------------
    if IS_3D.search(text):
        hits, missing, needs_skin = craft_check(text)
        r.craft_hits, r.craft_missing = hits, missing
        r.note(f"3D asset-craft signals: {len(hits)}/4" + (f" (skinning required: {needs_skin})" if needs_skin else ""))
        if craft:
            for group in missing:
                r.fail(f"3D craft gate: {group} missing — see references/asset-craft.md")
        elif missing:
            r.note("3D craft gate not enforced; ship with --strict --craft")
    elif craft:
        r.note(
            "not a 3D build: craft gate skipped. 3D is the default target (SKILL.md section 0); "
            "if this was meant to be 3D, the renderer is the problem"
        )

    # --- informational ---------------------------------------------------
    canvases = len(re.findall(r"<canvas[\s>]", text, re.IGNORECASE))
    r.note(f"{canvases} canvas element(s), {len(declared)} element ids")
    if "localStorage" in text and "try" not in text:
        r.warn("localStorage used without a try/catch guard")

    return r


def print_report(r: Report) -> None:
    status = "PASS" if r.ok else "FAIL"
    print(f"\n{status}  {r.path}  ({r.size_kb:.1f} KB)")
    for f in r.failures:
        print(f"  x  {f}")
    for w in r.warnings:
        print(f"  !  {w}")
    for n in r.notes:
        print(f"  -  {n}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Audit single-file HTML games.")
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    ap.add_argument(
        "--craft", action="store_true",
        help="enforce the 3D asset-craft hard gate (mandatory for a shipped 3D game)",
    )
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    # A minified inline 3D engine (~800 KB) plus a generated asset layer is
    # legitimately 1-2 MB; do not warn away the budget this gate requires.
    ap.add_argument("--warn-kb", type=float, default=1800.0)
    ap.add_argument("--fail-kb", type=float, default=2560.0)
    args = ap.parse_args(argv)

    reports = []
    for p in args.paths:
        if not p.exists():
            reports.append(Report(path=p, failures=["file not found"]))
            continue
        reports.append(audit(p, args.warn_kb, args.fail_kb, craft=args.craft))

    if args.json:
        print(json.dumps([r.as_dict() for r in reports], indent=2))
    else:
        for r in reports:
            print_report(r)
        bad = [r for r in reports if not r.ok or (args.strict and r.warnings)]
        print(f"\n{len(reports) - len(bad)}/{len(reports)} file(s) within the format rules")
    return 0 if all(r.ok for r in reports) and not (args.strict and any(r.warnings for r in reports)) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
