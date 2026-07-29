#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate pre-rendered PNG icons for RAC from Material Symbols SVGs.

Tipo icons are tinted to their respective color. Right-column shortcut icons
are rendered in black (light theme) and white (dark theme).
"""

import subprocess
import sys
from pathlib import Path

ICON_DIR = Path(__file__).resolve().parent.parent / "src" / "gui" / "img" / "material-icons"

TIPO_COLORS = {
    "arrow_upward": "#10B981",
    "autorenew": "#3B82F6",
    "arrow_downward": "#D97706",
    "frame_source": "#EF4444",
    "home": "#06B6D4",
}

RIGHT_ICONS = [
    "view_list",
    "file_export",
    "pill",
    "person",
    "leaderboard",
]


TPL_FILL = ['#000000', '#ffffff', '#e3e3e3']


def svg_recolored(svg_path: Path, color: str) -> str:
    text = svg_path.read_text(encoding="utf-8")
    for old in TPL_FILL:
        text = text.replace(f'fill="{old}"', f'fill="{color}"')
        text = text.replace(f"fill='{old}'", f'fill="{color}"')
    if 'fill="' not in text and 'fill=\'' not in text:
        text = text.replace('<svg ', f'<svg fill="{color}" ', 1)
    return text


def render_to_png(svg_text: str, output: Path, size: int = 24) -> None:
    tmp = output.with_suffix(".tmp.svg")
    tmp.write_text(svg_text, encoding="utf-8")
    try:
        cmd = [
            "convert", "-background", "none", "-density", "300",
            str(tmp), "-resize", f"{size}x{size}",
            str(output),
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to render {output}: {e.stderr}", file=sys.stderr)
        raise
    finally:
        tmp.unlink(missing_ok=True)


def main():
    if not ICON_DIR.exists():
        print(f"Icon directory not found: {ICON_DIR}", file=sys.stderr)
        sys.exit(1)

    # Tipo icons: colored
    for name, color in TIPO_COLORS.items():
        svg = ICON_DIR / f"{name}.svg"
        if not svg.exists():
            print(f"Missing SVG: {svg}", file=sys.stderr)
            continue
        render_to_png(svg_recolored(svg, color), ICON_DIR / f"{name}-color.png")
        print(f"Generated {name}-color.png ({color})")

    # Right-column shortcut icons: black/white
    for name in RIGHT_ICONS:
        svg = ICON_DIR / f"{name}.svg"
        if not svg.exists():
            print(f"Missing SVG: {svg}", file=sys.stderr)
            continue
        render_to_png(svg_recolored(svg, "#000000"), ICON_DIR / f"{name}.png")
        render_to_png(svg_recolored(svg, "#ffffff"), ICON_DIR / f"{name}-white.png")
        print(f"Generated {name}.png / {name}-white.png")


if __name__ == "__main__":
    main()
