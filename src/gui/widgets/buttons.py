#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QPushButton, QSizePolicy
from PySide6.QtCore import Qt, Signal

from src.gui.styles import tipo_button_qss, toggle_theme, get_stylesheet, get_theme
from src.gui.constants import TIPO_LABELS, TIPO_SYMBOLS, TIPO_HEX


def make_button(text: str, role: str, parent=None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setProperty("btnrole", role)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


class TipoButton(QPushButton):
    clicked_tipo = Signal(str)

    def __init__(self, tipo_key: str, parent=None):
        label = TIPO_LABELS[tipo_key]
        symbol = TIPO_SYMBOLS[tipo_key]
        self._hex_color = TIPO_HEX[tipo_key]

        super().__init__(f"{symbol}  {label}", parent)
        self.tipo_key = tipo_key
        self.setProperty("tipobtn", True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(68)
        self._apply_style()
        self.clicked.connect(lambda: self.clicked_tipo.emit(self.tipo_key))

    def _apply_style(self):
        self.setStyleSheet(tipo_button_qss(self._hex_color))

    def refresh_style(self):
        self._apply_style()


class ThemeToggleButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("btnrole", "theme-toggle")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(28, 28)
        self.clicked.connect(self._toggle)
        self._update_icon()

    def _toggle(self):
        from PySide6.QtWidgets import QApplication

        toggle_theme()
        QApplication.instance().setStyleSheet(get_stylesheet())
        self._update_icon()
        window = self.window()
        if hasattr(window, "theme_changed"):
            window.theme_changed.emit()

    def _update_icon(self):
        self.setText("\u263e" if get_theme() == "dark" else "\u2600")
