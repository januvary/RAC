#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QLabel, QWidget
from PySide6.QtCore import Qt, QTimer


class ToastLabel(QLabel):
    def __init__(self, text: str, kind: str = "info", parent=None):
        super().__init__(text, parent)
        self.setProperty("toastkind", kind)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        self.deleteLater()


def show_toast(message: str, kind: str, parent: QWidget):
    win = parent.window()
    toast = ToastLabel(message, kind, win)
    toast.adjustSize()
    toast.setFixedWidth(min(toast.width() + 32, win.width() - 48))
    toast.move(
        (win.width() - toast.width()) // 2,
        win.height() - toast.height() - 16,
    )
    toast.show()
    toast.raise_()
    QTimer.singleShot(3000, toast.deleteLater)


class ToastMixin:
    def _toast(self, message: str, kind: str = "info"):
        show_toast(message, kind, self)
