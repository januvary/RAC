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


def _get_app_icon_path():
    return Path(__file__).parent / "src" / "gui" / "img" / "folder-1486.svg"


def _apply_pending_update():
    from src.utils.updater import apply_pending_update

    if apply_pending_update():
        print("[RAC] Pending update applied.")


def _start_update_check(window):
    from src.utils.updater import UpdateCheckWorker
    from src.gui.widgets.toast import show_toast

    worker = UpdateCheckWorker(parent=window)

    def _on_available(tag, notes, url):
        show_toast(
            f"Update {tag} available. Downloading...",
            "info",
            window,
            timeout_ms=4000,
        )

    def _on_downloaded(tag):
        show_toast(
            f"Update {tag} ready. Restart to apply.",
            "info",
            window,
            timeout_ms=8000,
        )

    def _on_failed(msg):
        print(f"[RAC] Update check failed: {msg}")

    worker.update_available.connect(_on_available)
    worker.update_downloaded.connect(_on_downloaded)
    worker.update_failed.connect(_on_failed)
    worker.no_update.connect(lambda: print("[RAC] No update available."))
    worker.start()


def main():
    _apply_pending_update()

    andaime.init("RAC", "RACRegistros", root=Path(__file__).parent)

    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont, QIcon

    from src.utils.config import RACConfig
    from andaime.config import ConfigManager
    ConfigManager.init(RACConfig)

    from src.gui.styles import set_theme, get_stylesheet

    app = QApplication(sys.argv)

    icon_path = _get_app_icon_path()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

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

    _start_update_check(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
