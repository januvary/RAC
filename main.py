#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC Entry Point (PySide6 native desktop)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont

    from src.gui.styles import set_theme, get_stylesheet

    app = QApplication(sys.argv)

    font = QFont("Inter", 11)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    from src.utils.config import ConfigManager
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
