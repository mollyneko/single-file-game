#!/usr/bin/env python3
"""Create a new single-file game from a starter template.

    python scaffold.py --name "Orb Runner" --mode 2d --out orb-runner.html
    python scaffold.py --name "Night Shift" --mode 3d --accent "#7fd6a8"

The template already contains the shell described in SKILL.md: design tokens, boot screen,
title layer, canvas, HUD, pause and game-over cards, input, audio bus, save bus, error
boundary and a marked GAME block. You replace the GAME block; keep the shell.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
TEMPLATES = {"2d": "starter-2d.html", "3d": "starter-3d.html"}


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "game"


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    v = value.lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def build(name: str, mode: str, accent: str | None) -> str:
    src = (ASSETS / TEMPLATES[mode]).read_text(encoding="utf-8")
    slug = slugify(name)
    safe = name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # title + boot mark + first headline
    src = re.sub(r"<title>.*?</title>", f"<title>{safe} — Single-File Game</title>", src, count=1, flags=re.S)
    src = re.sub(
        r'(<div class="boot-mark">).*?(</div>)', rf"\g<1>{safe.upper()}\g<2>", src, count=1, flags=re.S
    )
    src = re.sub(r"<h1>.*?</h1>", f"<h1>{safe}</h1>", src, count=1, flags=re.S)

    # storage namespace: one save key per generated game
    src = src.replace("starter2d:", f"{slug}:").replace("starter3d:", f"{slug}:")

    if accent:
        rgb = hex_to_rgb(accent)
        src = re.sub(r"(--(?:amber|signal)\s*:\s*)#[0-9a-fA-F]{3,6}", rf"\g<1>{accent}", src)
        src = src.replace("#ffb454", accent)
        src = src.replace("rgb(255,180,84)", f"rgb({rgb[0]},{rgb[1]},{rgb[2]})")

    return src


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Scaffold a single-file HTML game.")
    ap.add_argument("--name", required=True, help='game title, e.g. "Orb Runner"')
    ap.add_argument("--mode", default="2d", choices=sorted(TEMPLATES), help="2d canvas or 3d webgl2")
    ap.add_argument("--out", type=Path, help="output file (default: ./<slug>.html)")
    ap.add_argument("--accent", help="accent colour, e.g. #ffb454")
    ap.add_argument("--force", action="store_true", help="overwrite an existing file")
    args = ap.parse_args(argv)

    out = args.out or Path(f"{slugify(args.name)}.html")
    if out.exists() and not args.force:
        print(f"refusing to overwrite {out} (use --force)", file=sys.stderr)
        return 1

    html = build(args.name, args.mode, args.accent)
    out.write_text(html, encoding="utf-8")

    print(f"created {out}  ({len(html.encode('utf-8')) / 1024:.0f} KB, {args.mode})")
    print("next:")
    print("  1. open it in a browser — it is playable already")
    print("  2. replace everything between the GAME markers")
    print(f"  3. python {Path(__file__).parent.name}/check_single_file.py {out} --strict")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
