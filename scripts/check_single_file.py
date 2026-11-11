#!/usr/bin/env python3
"""Audit a single-file HTML game against the format rules.

Checks the things that actually break this format: remote resources, missing shell parts,
dangling element IDs and runaway file size.

    python check_single_file.py game.html
    python check_single_file.py game.html --strict
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

ERROR_BOUNDARY = [
    re.compile(r"addEventListener\s*\(\s*['\"]error['\"]"),
    re.compile(r"window\.onerror"),
    re.compile(r"\bonerror\s*="),
]

REDUCED_MOTION = re.compile(r"prefers-reduced-motion")


@dataclass
class Report:
    path: Path
    size_kb: float = 0.0
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

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
        }


def audit(path: Path, warn_kb: float, fail_kb: float) -> Report:
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
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--warn-kb", type=float, default=500.0)
    ap.add_argument("--fail-kb", type=float, default=1200.0)
    args = ap.parse_args(argv)

    reports = []
    for p in args.paths:
        if not p.exists():
            reports.append(Report(path=p, failures=["file not found"]))
            continue
        reports.append(audit(p, args.warn_kb, args.fail_kb))

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
