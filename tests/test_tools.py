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
