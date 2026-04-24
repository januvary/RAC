#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QComboBox,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QLineEdit,
    QWidget,
)
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QPainter, QFontMetrics

from PySide6.QtWidgets import QCompleter


class _SearchCompleter(QCompleter):
    def __init__(self, model, parent=None):
        super().__init__(model, parent)
        self._escape_pressed = False
        self._user_selected = False
        self._activated = False
        self._spurious_close = False
        self._reshow_count = 0
        self.activated.connect(lambda _: setattr(self, "_activated", True))

    def _is_spurious_hide(self, obj) -> bool:
        if obj is not self.popup():
            return False
        widget = self.widget()
        if not isinstance(widget, QLineEdit):
            return False
        if not widget.text().strip():
            return False
        if self._escape_pressed or self._user_selected or self._activated:
            return False
        if not self._spurious_close:
            return False
        if self._reshow_count >= 3:
            return False
        return True

    def _reshow(self):
        if self._escape_pressed or self._user_selected or self._activated:
            return
        widget = self.widget()
        if not isinstance(widget, QLineEdit) or not widget.text().strip():
            return
        self._reshow_count += 1
        super().complete()

    def eventFilter(self, obj, event):
        et = event.type()

        if et == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Escape:
                self._escape_pressed = True
        elif et == QEvent.Type.MouseButtonPress and obj is self.popup():
            self._user_selected = True
        elif et == QEvent.Type.Close and obj is self.popup():
            self._spurious_close = True

        if et == QEvent.Type.Hide and self._is_spurious_hide(obj):
            QTimer.singleShot(0, self._reshow)

        result = super().eventFilter(obj, event)

        if et == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
            self._escape_pressed = False

        return result

    def complete(self, rect=None):
        self._escape_pressed = False
        self._user_selected = False
        self._activated = False
        self._spurious_close = False
        self._reshow_count = 0
        if rect is not None:
            super().complete(rect)
        else:
            super().complete()


class _CenteredDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter
        super().paint(painter, option, index)


class _NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()


class _CenteredComboBox(_NoScrollComboBox):
    _tipo_bg: str = ""

    def showPopup(self):
        super().showPopup()
        popup = self.findChild(QWidget)
        if popup and self._tipo_bg:
            popup.setStyleSheet(
                f"background-color: {self._tipo_bg}; border: none;"
            )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(self.palette().text().color())
        painter.setFont(self.font())

        text = self.currentText()
        fm = QFontMetrics(self.font())
        text_width = fm.horizontalAdvance(text)
        text_height = fm.height()

        x = (self.width() - text_width) / 2
        y = (self.height() - text_height) / 2 + fm.ascent()

        painter.drawText(int(x), int(y), text)
        painter.end()
