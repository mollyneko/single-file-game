"""Tests for the format auditor and the scaffolder.

Run: python -m unittest discover -s tests -v
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECK = ROOT / "scripts" / "check_single_file.py"
SCAFFOLD = ROOT / "scripts" / "scaffold.py"
STARTERS = sorted((ROOT / "assets").glob("starter-*.html"))

GOOD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>ok</title><style>body{margin:0}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}</style></head>
<body><canvas id="cv"></canvas><div id="fatal"></div>
<script>
addEventListener('error', () => {});
addEventListener('unhandledrejection', () => {});
document.getElementById('cv').focus();
const c = document.querySelector('#fatal');
if (c) c.textContent = '';
</script></body></html>
"""

# A 3D game built from bare primitives with bones but no skinning: the craft gate
# must reject all four groups.
BARE_3D = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>bare3d</title><style>@media (prefers-reduced-motion:reduce){*{animation:none}}</style></head>
<body><canvas id="cv"></canvas><div id="fatal"></div>
<script>
addEventListener('error', () => {});
addEventListener('unhandledrejection', () => {});
const gl = document.getElementById('cv').getContext('webgl2');
const shader = gl.createShader(gl.VERTEX_SHADER);
const BONE_DEFS = [['hips']];
function draw(){ boxGeom(); sphereGeom(); capsuleGeom(); }
</script></body></html>
"""

REVIEW = """<!-- SELF-REVIEW {"rounds":2,
  "shots":["title","play","char-closeup","hero-effect"],
  "axes":{"space":5,"light":4,"material":5,"reflection":4,"world":4,"budget":4,
          "beauty":4,"structure":5,"ui":5},
  "fixes":["rig: parent-relative bone offsets","SSAO + volumetric ray march"],
  "reshoot":true,
  "metrics":{"manifest":"review/round-1/manifest.json","sha256":"__MANIFEST_SHA__"}} -->"""

# A SELF-REVIEW that admits what its own frames measured but scores above the cap anyway.
REVIEW_OVERRIDE = REVIEW.replace(
    '"fixes":',
    '"overrides":[{"axis":"light","value":0.18,'
    '"reason":"night harbour: 18% deep shadow is the intended look, anchor frame matches"}],\n  "fixes":',
)

AXES = ("space", "light", "material", "reflection", "world", "budget",
        "beauty", "structure", "ui")


def frame_fingerprint(text: str) -> str:
    return hashlib.sha256(re.sub(r"<!--[\s\S]*?-->", "", text).encode("utf-8")).hexdigest()


def write_frame_manifest(root: Path, html_path: Path, caps: dict | None = None,
                         protocol_ok: bool = True, frames: int = 3,
                         fingerprint: str | None = None) -> str:
    """Write review/round-1/manifest.json beside the fixture and return its sha256."""
    manifest = {
        "version": 1,
        "htmlFingerprint": fingerprint or frame_fingerprint(html_path.read_text(encoding="utf-8")),
        "protocolOk": protocol_ok,
        "frames": [{"shot": name, "metrics": {}} for name
                   in ("play", "char-closeup", "hero-effect")][:frames],
        "caps": caps or {axis: 5 for axis in AXES},
        "ok": protocol_ok,
    }
    path = root / "review" / "round-1" / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()

# One receipt per model. The auditor checks the declared factory is actually
# called in the game source and that every staged pass was reviewed "continue".
PIPELINE_RECEIPT = """<!-- PIPELINE-RECEIPT {"pipeline":"img2threejs",
  "spec":"models/hero/object-sculpt-spec.json",
  "state":"models/hero/.img2threejs/state.json",
  "seed":"hero-7f3a91","factory":"createHeroModel",
  "passes":[
    {"id":"blockout","action":"continue","render":"shots/hero/blockout.png"},
    {"id":"structural-pass","action":"continue","render":"shots/hero/structural.png"},
    {"id":"form-refinement","action":"continue","render":"shots/hero/form.png"},
    {"id":"material-pass","action":"continue","render":"shots/hero/material.png"},
    {"id":"surface-pass","action":"continue","render":"shots/hero/surface.png"},
    {"id":"lighting-pass","action":"continue","render":"shots/hero/lighting.png"},
    {"id":"interaction-pass","action":"continue","render":"shots/hero/interaction.png"},
    {"id":"optimization-pass","action":"continue","render":"shots/hero/optimization.png"}],
  "references":[{"image":"refs/hero.png","generated":true,"transparent":true,
                 "styleAnchor":"refs/hero.png"}]} -->"""

# Section 2A hard-constraint signals: depth-based SSAO, depth-aware volumetrics,
# free-look mouse and the review marker above.
HARD_SNIPPET = """const FREE_LOOK = true;
const ssaoSamples = 12, aoRadius = 0.5;
const sceneDepth = new DepthTexture(2, 2);   // SSAO rebuilt from scene depth
function ssaoPass(){ /* hemisphere samples, depth-aware blur */ }
const uSigma = 0.008, uShadow = null;
function volumetricRayMarch(){ /* shadow-tested march: scatter + transmittance */ }
cv.addEventListener('pointermove', e => { look.dx += e.clientX - lastX; });
"""

CRAFT_3D = BARE_3D.replace(
    "const shader = gl.createShader(gl.VERTEX_SHADER);",
    """const shader = gl.createShader(gl.VERTEX_SHADER);
window.THREE = { WebGLRenderer: function(){}, LatheGeometry: function(){} };
const profilePoints = [[0, .016], [.295, .022]];
const geo = new THREE.LatheGeometry(profilePoints, 22);
geo.computeVertexNormals();
const bevel = 0.03;
const MATERIALS = { steel_galv: { roughness: 0.4, metalness: 1.0 } };
const mats = new Map(); mats.get('steel_galv');
const cvs = document.createElement('canvas');
const ctx = cvs.getContext('2d');
const tex = new CanvasTexture(cvs);
const mesh = new SkinnedMesh(geo, bones);
mesh.bind(new Skeleton(bones));
const SEED = 0x5eed;
const heroGroup = createHeroModel({ seed: SEED });""",
).replace("</head>", REVIEW + "\n</head>").replace(
    "</head>", PIPELINE_RECEIPT + "\n</head>"
).replace("<script>", "<script>\n" + HARD_SNIPPET)

# Asset craft is complete, but none of the four hard constraints are present.
CRAFT_ONLY_3D = CRAFT_3D.replace(HARD_SNIPPET, "").replace(REVIEW, "")


def run(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


def audit_after(html: str, mutate=None, *flags: str) -> subprocess.CompletedProcess:
    """Audit a fixture, running `mutate(root, html_path)` after the manifest is written."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        p = root / "game.html"
        p.write_text(html.replace("__MANIFEST_SHA__", "0" * 64), encoding="utf-8")
        digest = write_frame_manifest(root, p)
        p.write_text(html.replace("__MANIFEST_SHA__", digest), encoding="utf-8")
        if mutate:
            mutate(root, p)
        return run(CHECK, str(p), *flags)


class AuditTests(unittest.TestCase):
    def audit(self, html: str, *flags: str, caps: dict | None = None,
              protocol_ok: bool = True, frames: int = 3,
              fingerprint: str | None = None,
              write_manifest: bool = True) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p = root / "game.html"
            p.write_text(html, encoding="utf-8")
            if "__MANIFEST_SHA__" in html:
                if write_manifest:
                    digest = write_frame_manifest(root, p, caps=caps, protocol_ok=protocol_ok,
                                                  frames=frames, fingerprint=fingerprint)
                    p.write_text(html.replace("__MANIFEST_SHA__", digest), encoding="utf-8")
                else:
                    p.write_text(html.replace("__MANIFEST_SHA__", "0" * 64), encoding="utf-8")
            return run(CHECK, str(p), *flags)

    def test_starters_pass_strict(self):
        self.assertTrue(STARTERS, "no starter templates found")
        result = run(CHECK, *[str(s) for s in STARTERS], "--strict")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_good_file_passes(self):
        self.assertEqual(self.audit(GOOD).returncode, 0)

    def test_remote_script_fails(self):
        bad = GOOD.replace("<style>", '<script src="https://cdn.example/lib.js"></script><style>')
        result = self.audit(bad)
        self.assertEqual(result.returncode, 1)
        self.assertIn("script src", result.stdout.lower())

    def test_fetch_fails(self):
        bad = GOOD.replace("<script>", "<script>fetch('/x');")
        self.assertEqual(self.audit(bad).returncode, 1)

    def test_dangling_id_fails(self):
        bad = GOOD.replace("document.getElementById('cv')", "document.getElementById('missing')")
        result = self.audit(bad)
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing", result.stdout)

    def test_missing_title_fails(self):
        bad = GOOD.replace("<title>ok</title>", "")
        self.assertEqual(self.audit(bad).returncode, 1)

    def test_missing_error_boundary_fails(self):
        bad = GOOD.replace("addEventListener('error', () => {});", "")
        self.assertEqual(self.audit(bad).returncode, 1)

    def test_viewport_warning_is_strict_failure(self):
        bad = GOOD.replace("width=device-width,", "width=device-width,user-scalable=no,")
        self.assertEqual(self.audit(bad, "--strict").returncode, 0)  # still has viewport-fit
        narrow = GOOD.replace(",viewport-fit=cover", "")
        self.assertEqual(self.audit(narrow, "--strict").returncode, 1)

    def test_craft_gate_rejects_bare_primitive_3d(self):
        result = self.audit(BARE_3D, "--craft")
        self.assertEqual(result.returncode, 1)
        for group in ("geometry craft", "material library", "generated textures", "continuous skinning"):
            self.assertIn(group, result.stdout)

    # --- inlined three.js is mandatory (SKILL.md section 0) --------------
    def test_3d_deliverable_requires_inlined_three(self):
        # BARE_3D is a raw-WebGL2 file with no GAME marker: a deliverable, and
        # a deliverable without three.js now fails outright.
        result = self.audit(BARE_3D, "--craft")
        self.assertEqual(result.returncode, 1)
        self.assertIn("three.js", result.stdout)
        self.assertIn("SKILL.md section 0", result.stdout)

    def test_three_js_gate_not_enforced_without_craft(self):
        result = self.audit(BARE_3D, "--strict")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("no inlined three.js build detected", result.stdout)

    def test_shell_with_game_marker_is_exempt_from_3d_gates(self):
        # A scaffold shell (GAME markers kept) is described, not failed — even
        # with --strict --craft. This is the documented exemption, in code.
        shell = CRAFT_ONLY_3D.replace(
            "<script>",
            "<script>\n/* ====== GAME (replace this block) ====== */\n/* ====== end GAME ====== */",
        )
        result = self.audit(shell, "--strict", "--craft")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("scaffold shell", result.stdout)
        self.assertIn("craft gate not enforced until the GAME block", result.stdout)
        self.assertIn("hard constraints not enforced until the GAME block", result.stdout)

    def test_starter_3d_shell_passes_craft_flag(self):
        # The bundled raw-WebGL2 starter is a shell: --strict --craft must not
        # fail it, but it must say what a deliverable needs.
        result = run(CHECK, str(ROOT / "assets" / "starter-3d.html"), "--strict", "--craft")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("scaffold shell", result.stdout)
        self.assertIn("no inlined three.js build yet", result.stdout)

    def test_json_reports_shell_flag(self):
        result = self.audit(CRAFT_3D, "--json", "--craft")
        payload = json.loads(result.stdout)[0]
        self.assertFalse(payload["shell"])
        self.assertTrue(payload["ok"])

    def test_craft_gate_accepts_fully_crafted_3d(self):
        result = self.audit(CRAFT_3D, "--strict", "--craft")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("4/4", result.stdout)

    def test_craft_gate_skips_2d(self):
        result = self.audit(GOOD, "--strict", "--craft")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("craft gate skipped", result.stdout)

    def test_starter_3d_is_not_blocked_without_craft(self):
        result = run(CHECK, str(ROOT / "assets" / "starter-3d.html"), "--strict")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("craft gate not enforced", result.stdout)

    def test_inline_engine_loader_fetch_is_not_a_game_request(self):
        html = GOOD.replace(
            "addEventListener('error', () => {});",
            "addEventListener('error', () => {});\nTHREE.FileLoader: fetch(r).then(()=>{});",
        )
        result = self.audit(html)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("inline-engine loader", result.stdout)

    def test_game_side_fetch_still_fails(self):
        bad = GOOD.replace(
            "addEventListener('error', () => {});",
            "addEventListener('error', () => {});\nfetch(url);",
        )
        self.assertEqual(self.audit(bad).returncode, 1)

    def test_size_budget_allows_inline_engine(self):
        big = GOOD + "<!--" + "x" * (1500 * 1024) + "-->"
        result = self.audit(big, "--strict")
        self.assertEqual(result.returncode, 0, result.stdout)

    # --- section 2A hard constraints ------------------------------------
    def test_hard_constraints_reject_craft_only_3d(self):
        result = self.audit(CRAFT_ONLY_3D, "--strict", "--craft")
        self.assertEqual(result.returncode, 1, result.stdout)
        for group in ("depth-based SSAO", "depth-aware volumetrics",
                      "free-look mouse", "visual self-review"):
            self.assertIn(group, result.stdout)

    def test_both_3d_gates_pass_when_present(self):
        result = self.audit(CRAFT_3D, "--strict", "--craft")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("3D asset-craft signals: 4/4", result.stdout)
        self.assertIn("3D hard constraints: 4/4", result.stdout)

    def test_ssao_needs_a_sampled_depth_source(self):
        bad = CRAFT_3D.replace("new DepthTexture(2, 2)", "null")
        result = self.audit(bad, "--craft")
        self.assertEqual(result.returncode, 1)
        self.assertIn("depth-based SSAO", result.stdout)

    def test_free_look_marker_needs_a_move_handler(self):
        bad = CRAFT_3D.replace(
            "cv.addEventListener('pointermove', e => { look.dx += e.clientX - lastX; });", ""
        )
        result = self.audit(bad, "--craft")
        self.assertEqual(result.returncode, 1)
        self.assertIn("free-look mouse", result.stdout)

    def test_explicit_drag_opt_in_is_allowed(self):
        html = CRAFT_3D.replace("const FREE_LOOK = true;", "const DRAG_LOOK_OPT_IN = true;")
        self.assertEqual(self.audit(html, "--strict", "--craft").returncode, 0)

    def test_self_review_requires_two_rounds(self):
        bad = CRAFT_3D.replace('"rounds":2', '"rounds":1')
        result = self.audit(bad, "--craft")
        self.assertEqual(result.returncode, 1)
        self.assertIn("rounds < 2", result.stdout)

    def test_self_review_requires_character_closeup(self):
        bad = CRAFT_3D.replace('"char-closeup"', '"wide"')
        result = self.audit(bad, "--craft")
        self.assertEqual(result.returncode, 1)
        self.assertIn("character close-up", result.stdout)

    def test_self_review_requires_fixes_and_reshoot(self):
        bad = CRAFT_3D.replace('"reshoot":true', '"reshoot":false')
        self.assertEqual(self.audit(bad, "--craft").returncode, 1)
        no_fixes = REVIEW.replace(
            '"fixes":["rig: parent-relative bone offsets","SSAO + volumetric ray march"]',
            '"fixes":[]',
        )
        bad2 = CRAFT_3D.replace(REVIEW, no_fixes)
        result = self.audit(bad2, "--craft")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no recorded fixes", result.stdout)

    def test_hard_constraints_not_enforced_without_craft(self):
        result = self.audit(CRAFT_ONLY_3D, "--strict")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("not enforced", result.stdout)

    def test_inline_engine_words_do_not_satisfy_hard_gate(self):
        # A minified engine line naturally contains DepthTexture / shadowMap /
        # transmittance. Those words must not be mistaken for game-side passes.
        noise = "/* " + "DepthTexture shadowMap transmittance SSAO uSigma volumetric " * 120 + " */"
        html = CRAFT_ONLY_3D.replace(
            "<script>",
            "<script>\n" + noise
            + "\nconst FREE_LOOK = true;\n"
            + "cv.addEventListener('pointermove', e => { look.dx += e.movementX; });",
        ).replace("</head>", REVIEW + "\n</head>")
        result = self.audit(html, "--craft")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("3D hard constraints: 2/4", result.stdout)
        self.assertIn("depth-based SSAO", result.stdout)
        self.assertIn("depth-aware volumetrics", result.stdout)

    def test_json_reports_hard_gates(self):
        result = self.audit(CRAFT_3D, "--json", "--craft")
        payload = json.loads(result.stdout)[0]
        self.assertEqual(len(payload["hard_hits"]), 4)
        self.assertEqual(payload["hard_missing"], [])
        self.assertTrue(payload["ok"])

    # --- img2threejs provenance (SKILL.md section 0 / Step 3) ------------
    def test_3d_deliverable_requires_pipeline_receipt(self):
        # A fully crafted, fully constrained file still fails if its models
        # have no pipeline provenance. This is the gap that let hand-built
        # geometry ship with a passing audit.
        bad = CRAFT_3D.replace(PIPELINE_RECEIPT, "")
        result = self.audit(bad, "--strict", "--craft")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("no PIPELINE-RECEIPT marker", result.stdout)
        self.assertIn("SKILL.md Step 3", result.stdout)

    def test_receipt_factory_must_be_called_in_game_source(self):
        bad = CRAFT_3D.replace("const heroGroup = createHeroModel({ seed: SEED });", "")
        result = self.audit(bad, "--craft")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("never called", result.stdout)

    def test_receipt_requires_spec_seed_and_factory_shape(self):
        bad = (CRAFT_3D.replace('"seed":"hero-7f3a91",', "")
               .replace('"factory":"createHeroModel"', '"factory":"buildHero"'))
        result = self.audit(bad, "--craft")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("spec seed is missing", result.stdout)
        self.assertIn("factory must be a create...Model name", result.stdout)

    def test_receipt_rejects_malformed_json(self):
        bad = CRAFT_3D.replace(PIPELINE_RECEIPT, "<!-- PIPELINE-RECEIPT {broken} -->")
        result = self.audit(bad, "--craft")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("malformed PIPELINE-RECEIPT JSON", result.stdout)

    def test_receipt_requires_every_pass_reviewed_as_continue(self):
        bad = CRAFT_3D.replace('"action":"continue"', '"action":"refine-code"', 1)
        result = self.audit(bad, "--craft")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("not reviewed as continue", result.stdout)

    def test_receipt_rejects_a_one_pass_stub(self):
        stub = """<!-- PIPELINE-RECEIPT {"pipeline":"img2threejs",
          "spec":"models/hero/object-sculpt-spec.json","seed":"s",
          "factory":"createHeroModel",
          "passes":[{"id":"blockout","action":"continue","render":"a.png"}]} -->"""
        bad = CRAFT_3D.replace(PIPELINE_RECEIPT, stub)
        result = self.audit(bad, "--craft")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("at least 5 reviewed stages", result.stdout)

    def test_receipt_rejects_opaque_generated_reference(self):
        bad = CRAFT_3D.replace('"transparent":true', '"transparent":false')
        result = self.audit(bad, "--craft")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("does not declare transparent: true", result.stdout)

    def test_multiple_models_need_one_receipt_each(self):
        second = (PIPELINE_RECEIPT.replace("createHeroModel", "createPropModel")
                  .replace("hero/object-sculpt-spec.json", "prop/object-sculpt-spec.json")
                  .replace("models/hero/.img2threejs/state.json", "models/prop/.img2threejs/state.json")
                  .replace("hero-7f3a91", "prop-7f3a91"))
        html = CRAFT_3D.replace(
            "const heroGroup = createHeroModel({ seed: SEED });",
            "const heroGroup = createHeroModel({ seed: SEED });\n"
            "const propGroup = createPropModel({ seed: SEED });",
        ).replace("</head>", second + "\n</head>")
        result = self.audit(html, "--strict", "--craft")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("2 model(s) verified", result.stdout)

    def test_receipt_not_enforced_without_craft(self):
        bad = CRAFT_3D.replace(PIPELINE_RECEIPT, "")
        result = self.audit(bad, "--strict")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("img2threejs receipt not enforced", result.stdout)

    def test_shell_is_exempt_from_receipt_gate(self):
        shell = CRAFT_3D.replace(PIPELINE_RECEIPT, "").replace(
            "<script>",
            "<script>\n/* ====== GAME (replace this block) ====== */",
        )
        result = self.audit(shell, "--strict", "--craft")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("PIPELINE-RECEIPT gate not enforced", result.stdout)

    def test_2d_skips_receipt_gate(self):
        result = self.audit(GOOD, "--strict", "--craft")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("craft gate skipped", result.stdout)
        self.assertNotIn("img2threejs receipt", result.stdout)

    def test_json_reports_pipeline_receipt(self):
        result = self.audit(CRAFT_3D, "--json", "--craft")
        payload = json.loads(result.stdout)[0]
        self.assertEqual(payload["pipeline_models"], ["createHeroModel"])
        self.assertEqual(payload["pipeline_problems"], [])
        self.assertTrue(payload["ok"])


class FrameMetricsTests(unittest.TestCase):
    """The measurable half of the rubric: a metric may lower a score, never raise one."""

    def test_missing_manifest_fails(self):
        result = AuditTests.audit(self, CRAFT_3D, "--strict", "--craft", write_manifest=False)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("metrics manifest not found", result.stdout)

    def test_manifest_edited_after_capture_fails(self):
        def tamper(root: Path, _html: Path) -> None:
            path = root / "review" / "round-1" / "manifest.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["caps"]["light"] = 3
            path.write_text(json.dumps(data), encoding="utf-8")

        result = audit_after(CRAFT_3D, tamper, "--strict", "--craft")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("does not match the manifest on disk", result.stdout)

    def test_frames_from_another_build_fail(self):
        result = AuditTests.audit(self, CRAFT_3D, "--strict", "--craft",
                                  fingerprint="f" * 64)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("captured from a different build", result.stdout)

    def test_axis_scored_above_its_cap_fails(self):
        # light is scored 4, the frames cap it at 3, and nothing explains the gap.
        result = AuditTests.audit(self, CRAFT_3D, "--strict", "--craft",
                                  caps={"light": 3})
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("light is scored 4 but its frames cap it at 3", result.stdout)

    def test_override_with_a_reason_is_accepted(self):
        # The escape hatch: a stylistic reason recorded in the handoff, not a silent pass.
        result = AuditTests.audit(self, CRAFT_3D.replace(REVIEW, REVIEW_OVERRIDE),
                                  "--strict", "--craft", caps={"light": 3})
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("light 4 above cap 3: overridden", result.stdout)

    def test_override_without_a_real_reason_still_fails(self):
        short = REVIEW.replace(
            '"fixes":', '"overrides":[{"axis":"light","reason":"night"}],\n  "fixes":')
        result = AuditTests.audit(self, CRAFT_3D.replace(REVIEW, short),
                                  "--strict", "--craft", caps={"light": 3})
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("light is scored 4 but its frames cap it at 3", result.stdout)

    def test_protocol_failure_blocks(self):
        result = AuditTests.audit(self, CRAFT_3D, "--strict", "--craft", protocol_ok=False)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("single view", result.stdout)

    def test_too_few_frames_fail(self):
        result = AuditTests.audit(self, CRAFT_3D, "--strict", "--craft", frames=2)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("fewer than 3 frames", result.stdout)

    def test_2d_build_is_not_asked_for_frames(self):
        result = run(CHECK, str(ROOT / "assets" / "starter-2d.html"), "--strict", "--craft")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("craft gate skipped", result.stdout)


class ScaffoldTests(unittest.TestCase):
    def test_generated_files_pass_audit(self):
        with tempfile.TemporaryDirectory() as d:
            out2 = Path(d) / "a.html"
            out3 = Path(d) / "b.html"
            self.assertEqual(run(SCAFFOLD, "--name", "Test Game", "--mode", "2d", "--out", str(out2)).returncode, 0)
            self.assertEqual(run(SCAFFOLD, "--name", "Test Game", "--mode", "3d", "--out", str(out3)).returncode, 0)
            result = run(CHECK, str(out2), str(out3), "--strict")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("Test Game", out2.read_text(encoding="utf-8"))

    def test_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "a.html"
            run(SCAFFOLD, "--name", "X", "--out", str(out))
            self.assertEqual(run(SCAFFOLD, "--name", "X", "--out", str(out)).returncode, 1)


if __name__ == "__main__":
    unittest.main()
