#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC Entry Point (PySide6 native desktop)
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import andaime


def _load_bundled_fonts():
    from PySide6.QtGui import QFontDatabase
    from andaime.paths import get_root_directory

    fonts_dir = get_root_directory() / "fonts"
    if fonts_dir.is_dir():
        db = QFontDatabase()
        for f in fonts_dir.iterdir():
            if f.suffix in (".ttf", ".otf"):
                db.addApplicationFont(str(f))


def main():
    andaime.init("RAC", "RACRegistros", root=Path(__file__).parent)

    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont

    from src.utils.config import RACConfig
    from andaime.config import ConfigManager
    ConfigManager.init(RACConfig)

    from src.gui.styles import set_theme, get_stylesheet

    app = QApplication(sys.argv)

    _load_bundled_fonts()

    font = QFont("Geist", 11)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    config = ConfigManager()
    theme = config.get("theme", "dark")
    set_theme(theme)
    app.setStyleSheet(get_stylesheet())

    from src.gui.main_window import MainWindow

    window = MainWindow()
    window.init_backend()
    window.navigate_to("start")
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
