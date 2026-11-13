"""Tests for the format auditor and the scaffolder.

Run: python -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
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
  "reshoot":true} -->"""

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
mesh.bind(new Skeleton(bones));""",
).replace("</head>", REVIEW + "\n</head>").replace("<script>", "<script>\n" + HARD_SNIPPET)

# Asset craft is complete, but none of the four hard constraints are present.
CRAFT_ONLY_3D = CRAFT_3D.replace(HARD_SNIPPET, "").replace(REVIEW, "")


def run(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


class AuditTests(unittest.TestCase):
    def audit(self, html: str, *flags: str) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "game.html"
            p.write_text(html, encoding="utf-8")
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
