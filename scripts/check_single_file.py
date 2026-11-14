#!/usr/bin/env python3
"""Audit a single-file HTML game against the format rules and the 3D ship gates.

Checks the things that actually break this format: remote resources, missing shell parts,
dangling element IDs and runaway file size. With --craft it enforces the 3D ship gates: an
inlined three.js build (mandatory, SKILL.md section 0), a PIPELINE-RECEIPT proving the models
came out of the vendored img2threejs pipeline, the asset layer (bevel/curved geometry, a named
material library, generated textures, continuous skinning) and section 2A's hard constraints
(depth-based SSAO, depth-aware volumetrics, free-look mouse, a recorded visual self-review).
A scaffold shell — a file that still carries the `GAME (replace this block)` marker — is
reported as a shell: the 3D gates describe rather than fail until the block is replaced.

    python check_single_file.py game.html
    python check_single_file.py game.html --strict
    python check_single_file.py game3d.html --strict --craft   # 3D ship gates
    python check_single_file.py assets/*.html --json

Exit codes: 0 = pass, 1 = failure (or any warning with --strict).
"""

from __future__ import annotations

import argparse
import hashlib
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
# --- inlined three.js is mandatory (SKILL.md section 0) ------------------
# The markers live inside the minified engine line, so this check runs on the
# whole text, not the game-source strip: the library's presence is the point.
THREE_SIGNAL = re.compile(
    r"window\.THREE\s*=|THREE\.WebGLRenderer|new\s+THREE\.", re.IGNORECASE
)
# A scaffold shell still carries the marker scaffold.py told the user to replace.
# Shells are described, not failed: the asset layer is the user's first task.
SHELL_SIGNAL = re.compile(r"GAME\s*\(\s*replace this block\s*\)", re.IGNORECASE)
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

# --- 3D hard constraints (SKILL.md section 2A) --------------------------
# Signals, not beauty. A shipped 3D game must prove that depth-based SSAO,
# depth-aware volumetrics, free-look mouse and a visual self-review exist.
# The screenshots and written scores remain mandatory and are judged by a human.
SSAO_SIGNAL = re.compile(
    r"\bSSAO\b|ambientOcclusion|aoSamples|uAORadius|hemisphere[A-Za-z]*[Oo]ccl", re.IGNORECASE
)
DEPTH_SAMPLE_SIGNAL = re.compile(
    r"DepthTexture|depthTexture|\buDepth\b|\btDepth\b|depthMap|gl_FragDepth|DEPTH_ATTACHMENT",
    re.IGNORECASE,
)
VOL_SIGNAL = re.compile(
    r"volumetric|raymarch|rayMarch|lightShaft|uSigma|transmittance", re.IGNORECASE
)
VOL_DEPTH_SIGNAL = re.compile(
    r"uShadow|shadowMap|sceneDepth|uDepth|tDepth|depthTexture|DepthTexture|shadowTest|uLightVP",
    re.IGNORECASE,
)
FREE_LOOK_SIGNAL = re.compile(r"\bFREE_LOOK\b|freeLook|free-look", re.IGNORECASE)
DRAG_OPT_IN_SIGNAL = re.compile(r"\bDRAG_LOOK_OPT_IN\b", re.IGNORECASE)
LOOK_HANDLER_SIGNAL = re.compile(
    r"addEventListener\(\s*['\"](?:pointermove|mousemove)['\"]", re.IGNORECASE
)
SELF_REVIEW_RE = re.compile(r"<!--\s*SELF-REVIEW\s*(\{[\s\S]*?\})\s*-->", re.IGNORECASE)

# --- img2threejs provenance (SKILL.md section 0 / Step 3) ---------------
# A 3D deliverable must prove its models came out of the vendored pipeline.
# One HTML-comment receipt per model: sculpt spec, spec seed, factory name and
# the staged pass reviews. The factory also has to be CALLED in the game's own
# source, so a receipt pasted onto a hand-built file cannot satisfy the gate.
PIPELINE_RECEIPT_RE = re.compile(
    r"<!--\s*PIPELINE-RECEIPT\s*(\{[\s\S]*?\})\s*-->", re.IGNORECASE
)
FACTORY_NAME_RE = re.compile(r"^create[A-Za-z0-9_]*Model$")
# The canonical pipeline has eight locked passes (PIPELINE.md); requiring five
# leaves room for a profile with a shorter pass order without accepting a
# one-pass stub.
MIN_REVIEWED_PASSES = 5
# An inline minified engine is one 600 KB line that already contains "DepthTexture",
# "shadowMap" and "transmittance". Counting those words as game work would make the
# gate pass a file with no SSAO and no volumetrics at all. Signals are judged on the
# game's own source only.
MINIFIED_LINE_LIMIT = 4000


def game_source(text: str) -> str:
    """Strip inline minified-engine lines before checking section 2A signals."""
    return "\n".join(line for line in text.splitlines() if len(line) <= MINIFIED_LINE_LIMIT)


def self_review_status(text: str) -> tuple[bool, str]:
    """Validate the SELF-REVIEW marker: rounds, close-up shot, fixes and re-shot."""
    m = SELF_REVIEW_RE.search(text)
    if not m:
        return False, "no SELF-REVIEW marker"
    try:
        data = json.loads(m.group(1))
    except (ValueError, TypeError):
        return False, "malformed SELF-REVIEW JSON"
    if not isinstance(data, dict):
        return False, "SELF-REVIEW is not an object"
    rounds = data.get("rounds")
    if not isinstance(rounds, int) or rounds < 2:
        return False, "rounds < 2"
    shots = data.get("shots")
    if not isinstance(shots, list) or not any(
        "close" in str(s).lower() or "char" in str(s).lower() for s in shots
    ):
        return False, "no character close-up shot"
    fixes = data.get("fixes")
    if not isinstance(fixes, list) or not fixes:
        return False, "no recorded fixes"
    if data.get("reshoot") is not True:
        return False, "no re-shot evidence"
    return True, ""


def _present(value: object) -> bool:
    """A declared scalar that is neither empty nor a placeholder boolean."""
    return isinstance(value, (str, int, float)) and not isinstance(value, bool) and str(value).strip() != ""


SCORE_AXES = ("space", "light", "material", "reflection", "world", "budget",
              "beauty", "structure", "ui")
MIN_OVERRIDE_REASON = 20
HTML_COMMENT = re.compile(r"<!--[\s\S]*?-->")


def html_fingerprint(text: str) -> str:
    """Hash the code, ignoring comments: the marker cannot hash the file that contains it.

    Comments are stripped because writing the marker's own hash into it must not change the
    fingerprint. Newlines are normalised because the auditor decodes raw bytes while the capture
    script reads text, and a CRLF checkout must fingerprint the same as an LF one.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(HTML_COMMENT.sub("", normalized).encode("utf-8")).hexdigest()


def frame_metrics_status(text: str, base_dir: Path | None, fingerprint: str | None) -> tuple[list[str], list[str]]:
    """Return (notes, problems) for the frame-metrics block inside SELF-REVIEW.

    The block points at a manifest written by `scripts/score_frame.py`. Three things are
    checked that a hand-written score cannot fake: the manifest is the one that was hashed, the
    frames were captured from *this* file (not an earlier build), and no axis is scored above
    the cap its own frames produced -- unless the marker carries an explicit override naming the
    axis and the stylistic reason. A metric is not a judgement: it can only lower a score.
    """
    m = SELF_REVIEW_RE.search(text)
    if not m:
        return [], ["no SELF-REVIEW marker, so there is no frame-metrics block"]
    try:
        data = json.loads(m.group(1))
    except (ValueError, TypeError):
        return [], ["malformed SELF-REVIEW JSON"]
    if not isinstance(data, dict):
        return [], ["SELF-REVIEW is not an object"]

    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        return [], ["no metrics block — capture the frames with scripts/score_frame.py"]
    relative = metrics.get("manifest")
    if not isinstance(relative, str) or not relative.strip().lower().endswith(".json"):
        return [], ["metrics.manifest must be the path to a score_frame manifest.json"]
    digest = metrics.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        return [], ["metrics.sha256 is missing or not a sha256"]
    if base_dir is None:
        return [], ["cannot resolve metrics.manifest without the HTML's directory"]

    path = (base_dir / relative).resolve()
    if not path.is_file():
        return [], [f"metrics manifest not found: {relative}"]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != digest.lower():
        return [], ["metrics.sha256 does not match the manifest on disk (it was edited after capture)"]
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return [], [f"metrics manifest is not readable JSON: {relative}"]

    problems: list[str] = []
    notes: list[str] = []
    if fingerprint and manifest.get("htmlFingerprint") != fingerprint:
        problems.append("the frames were captured from a different build (fingerprint mismatch) — re-capture")

    frames = manifest.get("frames")
    if not isinstance(frames, list) or len(frames) < 3:
        problems.append("the manifest has fewer than 3 frames; the protocol asks for play, "
                        "char-closeup and hero-effect")
    elif manifest.get("protocolOk") is False:
        problems.append("the shots produced a single view: the build ignores ?shot=, so the "
                        "frames are not separate views of it")
    else:
        notes.append(f"frame metrics: {len(frames)} frames from this build")

    caps = manifest.get("caps") if isinstance(manifest.get("caps"), dict) else {}
    axes = data.get("axes") if isinstance(data.get("axes"), dict) else {}
    overrides = data.get("overrides") if isinstance(data.get("overrides"), list) else []
    waived: dict[str, str] = {}
    for entry in overrides:
        if isinstance(entry, dict) and isinstance(entry.get("axis"), str):
            reason = entry.get("reason")
            if isinstance(reason, str) and len(reason.strip()) >= MIN_OVERRIDE_REASON:
                waived[entry["axis"]] = reason.strip()

    for axis in SCORE_AXES:
        score = axes.get(axis)
        cap = caps.get(axis)
        if not isinstance(score, int) or not isinstance(cap, int):
            continue
        if score > cap and axis not in waived:
            problems.append(
                f"{axis} is scored {score} but its frames cap it at {cap} — repair the frame, or "
                f"add an override naming the axis and the stylistic reason"
            )
        elif score > cap:
            notes.append(f"{axis} {score} above cap {cap}: overridden ({waived[axis][:60]})")
    if problems:
        return notes, problems
    return notes, []


def pipeline_receipt_status(text: str, source: str) -> tuple[list[str], list[str]]:
    """Return (verified factory names, problems) for all PIPELINE-RECEIPT markers.

    A receipt is a declaration, so the gate checks the parts a hand-built file
    cannot honestly fill in: a `create...Model` factory that is actually called
    in the game source, and every staged pass recorded as reviewed `continue`
    with a render screenshot. Generated reference images must also declare the
    transparent-background and style-anchor gates from SKILL.md section 0.
    """
    markers = list(PIPELINE_RECEIPT_RE.finditer(text))
    if not markers:
        return [], ["no PIPELINE-RECEIPT marker"]

    models: list[str] = []
    problems: list[str] = []
    for index, marker in enumerate(markers, 1):
        tag = f"receipt {index}"
        try:
            data = json.loads(marker.group(1))
        except (ValueError, TypeError):
            problems.append(f"{tag}: malformed PIPELINE-RECEIPT JSON")
            continue
        if not isinstance(data, dict):
            problems.append(f"{tag}: not a JSON object")
            continue

        bad: list[str] = []
        if str(data.get("pipeline", "")).lower() != "img2threejs":
            bad.append("pipeline is not img2threejs")
        spec = data.get("spec")
        if not isinstance(spec, str) or not spec.strip().lower().endswith(".json"):
            bad.append("spec must be the path to the sculpt spec .json")
        if not _present(data.get("seed")):
            bad.append("spec seed is missing")

        factory = data.get("factory")
        if not isinstance(factory, str) or not FACTORY_NAME_RE.match(factory):
            bad.append("factory must be a create...Model name")
        elif not re.search(re.escape(factory) + r"\s*\(", source):
            bad.append(f"factory {factory} is declared but never called in the game source")

        passes = data.get("passes")
        if not isinstance(passes, list) or len(passes) < MIN_REVIEWED_PASSES:
            bad.append(f"passes must list at least {MIN_REVIEWED_PASSES} reviewed stages")
        else:
            ids: list[str] = []
            for entry in passes:
                if not isinstance(entry, dict):
                    bad.append("a pass entry is not an object")
                    break
                pid = entry.get("id")
                if not isinstance(pid, str) or not pid.strip():
                    bad.append("a pass has no id")
                    break
                ids.append(pid)
                if entry.get("action") != "continue":
                    bad.append(f"pass {pid} is not reviewed as continue")
                evidence = entry.get("renderScreenshot") or entry.get("render")
                if not isinstance(evidence, str) or not evidence.strip():
                    bad.append(f"pass {pid} has no render screenshot evidence")
            if len(ids) != len(set(ids)):
                bad.append("pass ids are duplicated")
            if ids and ids[0] != "blockout":
                bad.append("the first reviewed pass is not blockout")

        refs = data.get("references")
        if isinstance(refs, list):
            for ref in refs:
                if isinstance(ref, dict) and ref.get("generated") is True:
                    if ref.get("transparent") is not True:
                        bad.append("a generated reference does not declare transparent: true")
                    if not _present(ref.get("styleAnchor")):
                        bad.append("a generated reference has no style anchor")
        elif refs is not None:
            bad.append("references must be an array")

        state_path = data.get("state")
        if state_path is not None and (
            not isinstance(state_path, str) or not state_path.endswith("state.json")
        ):
            bad.append("state must point at the pipeline state.json")

        if bad:
            problems.extend(f"{tag}: {msg}" for msg in bad)
        elif factory in models:
            problems.append(f"{tag}: duplicate factory {factory}")
        else:
            models.append(factory)
    return models, problems


def hard_check(text: str) -> tuple[list[str], list[str], list[str]]:
    """Return (hit groups, missing groups, diagnostic details) for section 2A."""
    detail: list[str] = []
    groups: dict[str, bool] = {}

    ssao = SSAO_SIGNAL.search(text) is not None and DEPTH_SAMPLE_SIGNAL.search(text) is not None
    groups["depth-based SSAO"] = ssao
    if not ssao:
        detail.append("SSAO needs both an AO pass and a sampled scene-depth source")

    vol = VOL_SIGNAL.search(text) is not None and VOL_DEPTH_SIGNAL.search(text) is not None
    groups["depth-aware volumetrics"] = vol
    if not vol:
        detail.append("volumetrics needs a ray march plus depth/shadow termination")

    opt_in = DRAG_OPT_IN_SIGNAL.search(text) is not None
    free = (opt_in or FREE_LOOK_SIGNAL.search(text) is not None) and LOOK_HANDLER_SIGNAL.search(text) is not None
    groups["free-look mouse"] = free
    if not free:
        detail.append("mouse look needs FREE_LOOK (or an explicit DRAG_LOOK_OPT_IN) and a move handler")

    review, why = self_review_status(text)
    groups["visual self-review"] = review
    if not review:
        detail.append(f"self-review: {why}")

    hits = [k for k, v in groups.items() if v]
    missing = [k for k, v in groups.items() if not v]
    return hits, missing, detail


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
    shell: bool = False
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    craft_hits: list[str] = field(default_factory=list)
    craft_missing: list[str] = field(default_factory=list)
    hard_hits: list[str] = field(default_factory=list)
    hard_missing: list[str] = field(default_factory=list)
    pipeline_models: list[str] = field(default_factory=list)
    pipeline_problems: list[str] = field(default_factory=list)

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
            "shell": self.shell,
            "failures": self.failures,
            "warnings": self.warnings,
            "notes": self.notes,
            "craft_hits": self.craft_hits,
            "craft_missing": self.craft_missing,
            "hard_hits": self.hard_hits,
            "hard_missing": self.hard_missing,
            "pipeline_models": self.pipeline_models,
            "pipeline_problems": self.pipeline_problems,
        }


def audit(path: Path, warn_kb: float, fail_kb: float, craft: bool = False) -> Report:
    r = Report(path=path)
    raw = path.read_bytes()
    r.size_kb = len(raw) / 1024
    text = raw.decode("utf-8", errors="replace")
    game_src = game_source(text)
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

    # --- 3D gates: three.js inline, asset craft, section 2A constraints ---
    if IS_3D.search(text):
        is_shell = SHELL_SIGNAL.search(text) is not None
        r.shell = is_shell
        if is_shell:
            r.note("scaffold shell: replace the GAME block to make it a deliverable")

        if not THREE_SIGNAL.search(text):
            if is_shell:
                r.note("shell has no inlined three.js build yet — a deliverable must (SKILL.md section 0)")
            elif craft:
                r.fail("3D deliverable without an inlined three.js build — see SKILL.md section 0")
            else:
                r.note("no inlined three.js build detected; a 3D deliverable must inline it (SKILL.md section 0)")

        p_models, p_problems = pipeline_receipt_status(text, game_src)
        r.pipeline_models, r.pipeline_problems = p_models, p_problems
        if p_problems:
            r.note(
                f"img2threejs receipt: {len(p_models)} model(s) verified, "
                f"{len(p_problems)} problem(s)"
            )
        else:
            r.note(f"img2threejs receipt: {len(p_models)} model(s) verified — {', '.join(p_models)}")
        if craft:
            if is_shell:
                r.note("shell: PIPELINE-RECEIPT gate not enforced until the GAME block is replaced")
            else:
                for problem in p_problems:
                    r.fail(f"img2threejs receipt: {problem} — see SKILL.md Step 3")
        elif p_problems:
            r.note("img2threejs receipt not enforced; ship with --strict --craft")

        f_notes, f_problems = frame_metrics_status(text, path.parent, html_fingerprint(text))
        for note in f_notes:
            r.note(note)
        if craft:
            if is_shell:
                r.note("shell: frame-metrics gate not enforced until the GAME block is replaced")
            else:
                for problem in f_problems:
                    r.fail(f"frame metrics: {problem} — see references/scoring-rubric.md")
        elif f_problems:
            r.note("frame metrics not enforced; ship with --strict --craft")

        hits, missing, needs_skin = craft_check(text)
        r.craft_hits, r.craft_missing = hits, missing
        r.note(f"3D asset-craft signals: {len(hits)}/4" + (f" (skinning required: {needs_skin})" if needs_skin else ""))
        if craft:
            if is_shell:
                r.note("shell: craft gate not enforced until the GAME block is replaced")
            else:
                for group in missing:
                    r.fail(f"3D craft gate: {group} missing — see references/asset-craft.md")
        elif missing:
            r.note("3D craft gate not enforced; ship with --strict --craft")

        h_hits, h_missing, h_detail = hard_check(game_src)
        r.hard_hits, r.hard_missing = h_hits, h_missing
        r.note(f"3D hard constraints: {len(h_hits)}/4")
        for line in h_detail:
            r.note(f"  {line}")
        if craft:
            if is_shell:
                r.note("shell: hard constraints not enforced until the GAME block is replaced")
            else:
                for group in h_missing:
                    r.fail(f"3D hard constraint: {group} missing — see SKILL.md section 2A")
        elif h_missing:
            r.note("3D hard constraints not enforced; ship with --strict --craft")
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
        help="enforce the 3D ship gates: img2threejs receipt, asset craft and section 2A hard constraints",
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
