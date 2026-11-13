"""Tests for the format auditor and the scaffolder.

Run: python -m unittest discover -s tests -v
"""

from __future__ import annotations

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

CRAFT_3D = BARE_3D.replace(
    "const shader = gl.createShader(gl.VERTEX_SHADER);",
    """const shader = gl.createShader(gl.VERTEX_SHADER);
const profilePoints = [[0, .016], [.295, .022]];
const geo = new LatheGeometry(profilePoints, 22);
geo.computeVertexNormals();
const bevel = 0.03;
const MATERIALS = { steel_galv: { roughness: 0.4, metalness: 1.0 } };
const mats = new Map(); mats.get('steel_galv');
const cvs = document.createElement('canvas');
const ctx = cvs.getContext('2d');
const tex = new CanvasTexture(cvs);
const mesh = new SkinnedMesh(geo, bones);
mesh.bind(new Skeleton(bones));""",
)


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
