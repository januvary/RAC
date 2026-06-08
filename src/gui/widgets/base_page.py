#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QLineEdit,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from typing import Callable

from src.gui.widgets.toast import ToastMixin
from src.gui.widgets.buttons import make_button
from src.gui.constants import SHORTCUT_LABELS


class BasePage(QWidget, ToastMixin):
    def __init__(self, main_window=None):
        super().__init__()
        self._mw = main_window
        self._shortcut_widgets: dict = {}
        self._shortcut_searches: list[tuple[str, QLineEdit]] = []
        self._keyboard_nav: list[tuple[QWidget, QLineEdit, Callable]] = []

    def _scaffold(self) -> QVBoxLayout:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(48, 32, 48, 32)
        outer.setSpacing(0)
        outer.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        from PySide6.QtWidgets import QWidget as _W

        container = _W()
        container.setMaximumWidth(720)
        container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        outer.addWidget(container)
        return layout

    def register_keyboard_nav(
        self, widget: QWidget, search: QLineEdit, on_enter: Callable
    ):
        widget.installEventFilter(self)
        search.installEventFilter(self)
        self._keyboard_nav.append((widget, search, on_enter))

    def _move_row(self, widget, direction):
        row = widget.currentRow()
        count = widget.count() if hasattr(widget, "count") else widget.rowCount()
        if count == 0:
            return
        if row < 0:
            new_row = 0
        else:
            new_row = row + direction
            if new_row < 0:
                new_row = 0
            elif new_row >= count:
                new_row = count - 1
        (
            widget.setCurrentCell(new_row, 0)
            if hasattr(widget, "setCurrentCell")
            else widget.setCurrentRow(new_row)
        )

    def eventFilter(self, obj, event):
        if isinstance(event, QKeyEvent) and event.type() == event.Type.KeyPress:
            for widget, search, on_enter in self._keyboard_nav:
                is_widget = obj is widget or obj is widget.viewport()
                is_search = obj is search
                if not (is_widget or is_search):
                    continue
                key = event.key()
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not is_search:
                    on_enter(widget)
                    return True
                if key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                    direction = -1 if key == Qt.Key.Key_Up else 1
                    self._move_row(widget, direction)
                    return True
                if is_widget and event.text() and not event.modifiers():
                    search.setFocus()
                    search.setText(event.text())
                    return True
                break
        return super().eventFilter(obj, event)

    def set_shortcuts_visible(self, show: bool):
        for name, widget in self._shortcut_widgets.items():
            _, label = SHORTCUT_LABELS[name]
            if show:
                key = SHORTCUT_LABELS[name][0]
                widget.setText(f"{label} ({key})")
            else:
                widget.setText(label)
        for placeholder, line_edit in self._shortcut_searches:
            line_edit.setPlaceholderText(
                f"{placeholder} (Ctrl+R)" if show else placeholder
            )

    def _add_back_button(
        self, layout: QVBoxLayout, target: str = "start"
    ) -> QHBoxLayout:
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        back_btn = make_button("Voltar", "flat")
        back_btn.clicked.connect(lambda: self._mw.navigate_to(target))
        h.addWidget(back_btn)
        self._shortcut_widgets["back"] = back_btn
        h.addStretch()

        layout.addLayout(h)
        return h
