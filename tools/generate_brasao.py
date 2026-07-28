#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera os PNGs do brasão e RAC a partir dos SVGs, usando andaime.brasao."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from andaime.brasao import render_brasao_silhouette, recolor_brasao
from andaime.qt.theme import LIGHT as _SHARED_LIGHT, DARK as _SHARED_DARK


def main():
    """Gera brasao_light.png, brasao_dark.png, rac_light.png e rac_dark.png na pasta gui/img/"""
    app = QApplication(sys.argv)
    
    img_dir = Path(__file__).parent.parent / "src" / "gui" / "img"
    
    # Generate brasao PNGs (full color SVG)
    brasao_svg = img_dir / "brasao.svg"
    if brasao_svg.exists():
        # Light theme brasao
        brasao_light = render_brasao_silhouette(brasao_svg, height=41, supersample=2)
        brasao_light.save(str(img_dir / "brasao_light.png"))
        print(f"✓ Gerado: brasao_light.png")
        
        # Dark theme brasao (same for now)
        brasao_dark = render_brasao_silhouette(brasao_svg, height=41, supersample=2)
        brasao_dark.save(str(img_dir / "brasao_dark.png"))
        print(f"✓ Gerado: brasao_dark.png")
    
    # Generate RAC PNGs with theme colors
    rac_svg = img_dir / "RAC.svg"
    if rac_svg.exists():
        # Light theme RAC
        ink_light = _SHARED_LIGHT.get("primary", _SHARED_LIGHT.get("text", "#000000"))
        rac_silhouette_light = render_brasao_silhouette(rac_svg, height=30, supersample=2)
        rac_light = recolor_brasao(rac_silhouette_light, ink_light)
        rac_light.save(str(img_dir / "rac_light.png"))
        print(f"✓ Gerado: rac_light.png")
        
        # Dark theme RAC
        ink_dark = _SHARED_DARK.get("primary", _SHARED_DARK.get("text", "#ffffff"))
        rac_silhouette_dark = render_brasao_silhouette(rac_svg, height=30, supersample=2)
        rac_dark = recolor_brasao(rac_silhouette_dark, ink_dark)
        rac_dark.save(str(img_dir / "rac_dark.png"))
        print(f"✓ Gerado: rac_dark.png")
    
    print("\n✓ PNGs gerados com sucesso!")


if __name__ == "__main__":
    main()