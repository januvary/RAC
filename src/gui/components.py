#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reusable Qt widgets for RAC — native Qt feel
"""

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel,
    QComboBox, QCompleter, QPushButton, QSizePolicy, QWidget,
)
from PySide6.QtCore import Qt, Signal

from src.gui.constants import TIPO_HEX, TIPO_LABELS, TIPO_SYMBOLS


class Separator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("separator", True)
        self.setFixedHeight(1)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class SectionLabel(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("heading", "section")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class HeadingLabel(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("heading", "true")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class SearchableComboBox(QWidget):
    selection_changed = Signal(object)

    def __init__(self, placeholder: str = "Buscar...", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._combo = QComboBox()
        self._combo.setEditable(True)
        self._combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._combo.setPlaceholderText(placeholder)
        self._combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        completer = self._combo.completer()
        if completer:
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self._combo.currentIndexChanged.connect(self._on_index_changed)
        layout.addWidget(self._combo)
        self._data_map: dict[str, dict] = {}

    def set_options(self, options: dict[str, str]):
        self._combo.blockSignals(True)
        self._combo.clear()
        self._data_map.clear()
        for key, label in options.items():
            self._combo.addItem(label, key)
            self._data_map[key] = {"id": key, "name": label}
        self._combo.blockSignals(False)
        if self._combo.completer():
            self._combo.completer().setModel(self._combo.model())

    def current_data(self) -> str | None:
        idx = self._combo.currentIndex()
        if idx < 0:
            return None
        return self._combo.itemData(idx)

    def set_current_by_data(self, data: str):
        idx = self._combo.findData(data)
        if idx >= 0:
            self._combo.setCurrentIndex(idx)

    def current_text(self) -> str:
        return self._combo.currentText()

    def add_option(self, key: str, label: str):
        self._combo.addItem(label, key)
        self._data_map[key] = {"id": key, "name": label}
        if self._combo.completer():
            self._combo.completer().setModel(self._combo.model())

    def _on_index_changed(self, idx):
        if idx >= 0:
            self.selection_changed.emit(self._combo.itemData(idx))
        else:
            self.selection_changed.emit(None)


class TipoButton(QPushButton):
    clicked_tipo = Signal(str)

    def __init__(self, tipo_key: str, parent=None):
        label = TIPO_LABELS[tipo_key]
        symbol = TIPO_SYMBOLS[tipo_key]
        hex_color = TIPO_HEX[tipo_key]

        super().__init__(f"{symbol}  {label}", parent)
        self.tipo_key = tipo_key
        self.setProperty("tipobtn", True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(56)
        self.setStyleSheet(f"""
            QPushButton[tipobtn="true"] {{
                border-left: 3px solid {hex_color};
            }}
            QPushButton[tipobtn="true"]:hover {{
                border-left: 3px solid {hex_color};
            }}
        """)
        self.clicked.connect(lambda: self.clicked_tipo.emit(self.tipo_key))


class FlatButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("btnrole", "flat")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class PrimaryButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("btnrole", "primary")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class PositiveButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("btnrole", "positive")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class NegativeButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("btnrole", "negative")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class DestructiveButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("btnrole", "destructive")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class TipoLabel(QWidget):
    def __init__(self, tipo_key: str, parent=None):
        super().__init__(parent)
        hex_color = TIPO_HEX[tipo_key]
        symbol = TIPO_SYMBOLS[tipo_key]
        label = TIPO_LABELS[tipo_key]

        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)

        dot = QLabel("\u25CF")
        dot.setStyleSheet(f"color: {hex_color}; font-size: 14px; border: none;")
        dot.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        h.addWidget(dot)

        text = QLabel(f"{symbol} {label}")
        text.setStyleSheet("color: #374151; font-size: 13px; font-weight: 600; border: none;")
        text.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        h.addWidget(text)


class ToastLabel(QLabel):
    def __init__(self, text: str, kind: str = "info", parent=None):
        super().__init__(text, parent)
        colors = {
            "positive": ("#059669", "#ECFDF5"),
            "warning": ("#D97706", "#FFFBEB"),
            "negative": ("#DC2626", "#FEF2F2"),
            "info": ("#2563EB", "#EFF6FF"),
        }
        fg, bg = colors.get(kind, colors["info"])
        self.setStyleSheet(f"""
            background-color: {bg};
            color: {fg};
            border: 1px solid {fg}33;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 500;
            font-size: 13px;
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mousePressEvent = lambda e: self.deleteLater()
