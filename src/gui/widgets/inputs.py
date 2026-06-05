#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QHBoxLayout,
    QSizePolicy,
    QWidget,
    QLineEdit,
    QStyledItemDelegate,
)
from PySide6.QtCore import Qt, Signal, QTimer, QStringListModel, QEvent
from PySide6.QtGui import QColor, QPalette, QPainter
from PySide6.QtWidgets import QStyleOptionViewItem, QStyle

from PySide6.QtWidgets import QCompleter

from src.gui.widgets._completer import (
    _SearchCompleter,
    _CenteredComboBox,
    _ThemedComboDelegate,
)
from src.gui.constants import TIPO_LABELS, TIPO_SYMBOLS, TIPO_HEX
from src.gui.styles import colors, faded_tipo_color
from andaime.text import normalize_text


class SearchableComboBox(QWidget):
    selection_changed = Signal(object)
    exact_match_changed = Signal(object)

    def __init__(
        self,
        placeholder: str = "Buscar...",
        parent=None,
        on_search=None,
        on_delete_empty=None,
    ):
        super().__init__(parent)
        self._on_search = on_search
        self._on_delete_empty = on_delete_empty
        self._selected_key: str | None = None
        self._selected_label: str | None = None
        self._options: dict[str, str] = {}
        self._search_labels: dict[str, str] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._model = QStringListModel(self)
        self._completer = _SearchCompleter(self._model, self)
        if on_search:
            self._completer.setCompletionMode(
                QCompleter.CompletionMode.UnfilteredPopupCompletion
            )
        else:
            self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.activated.connect(self._on_activated)

        self._line_edit = QLineEdit()
        self._line_edit.setPlaceholderText(placeholder)
        self._line_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._line_edit.setCompleter(self._completer)
        self._line_edit.textEdited.connect(self._on_text_edited)
        self._line_edit.textChanged.connect(self._on_text_changed)
        self._line_edit.installEventFilter(self)

        layout.addWidget(self._line_edit)

    def set_options(self, options: dict[str, str]):
        self._options = options.copy()
        self._search_labels = {v: k for k, v in options.items()}
        self._model.setStringList(list(options.values()))
        if self._selected_key and self._selected_key in self._options:
            self._selected_label = self._options[self._selected_key]

    def current_data(self) -> str | None:
        return self._selected_key

    def set_current_by_data(self, data: str):
        label = self._options.get(data)
        if label is not None:
            self._selected_key = data
            self._selected_label = label
            self._line_edit.setText(label)

    def current_text(self) -> str:
        return self._line_edit.text()

    def focus_search(self):
        self._line_edit.setFocus()
        self._line_edit.selectAll()

    def eventFilter(self, obj, event):
        if (
            obj is self._line_edit
            and event.type() == QEvent.Type.KeyPress
            and event.key() == Qt.Key.Key_Delete
            and self._line_edit.text().strip() == ""
            and self._on_delete_empty
        ):
            self._on_delete_empty()
            return True
        return super().eventFilter(obj, event)

    def clear(self):
        self._selected_key = None
        self._selected_label = None
        self._line_edit.clear()

    def add_option(self, key: str, label: str):
        self._options[key] = label
        self._search_labels[label] = key
        self._model.setStringList(list(self._options.values()))

    def _on_text_edited(self, text: str):
        if self._on_search:
            self._do_search(text)
        elif text:
            QTimer.singleShot(0, lambda: self._explicit_complete(text))
        else:
            popup = self._completer.popup()
            if popup:
                popup.hide()

    def _explicit_complete(self, text: str):
        self._completer.setCompletionPrefix(text)
        self._completer.complete()

    def _on_text_changed(self, text: str):
        if self._selected_label and text != self._selected_label:
            self._selected_key = None
            self._selected_label = None
            self.selection_changed.emit(None)

    def _on_activated(self, text: str):
        key = self._search_labels.get(text)
        if key is not None:
            self._selected_key = key
            self._selected_label = text
            self._line_edit.setText(text)
            self.selection_changed.emit(key)

    def _do_search(self, text: str):
        query = text.strip()
        if not query:
            self._model.setStringList([])
            self._search_labels.clear()
            return
        assert self._on_search is not None
        results = self._on_search(query)
        if results is None:
            return
        labels = list(results.values())
        self._search_labels = {v: k for k, v in results.items()}
        self._model.setStringList(labels)
        self._completer.setCompletionPrefix("")
        self._completer.complete()
        normalized_query = normalize_text(query)
        for key, label in results.items():
            if normalize_text(label) == normalized_query:
                self.exact_match_changed.emit(key)
                break


class _TipoComboDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        tipo_key = index.data(Qt.ItemDataRole.UserRole)
        text = index.data(Qt.ItemDataRole.DisplayRole)
        painter.save()
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.color(QPalette.ColorRole.Highlight))
            painter.setPen(option.palette.color(QPalette.ColorRole.HighlightedText))
        else:
            if tipo_key:
                hex_color = TIPO_HEX.get(tipo_key, "")
                if hex_color:
                    painter.setPen(QColor(faded_tipo_color(hex_color)))
                else:
                    painter.setPen(option.palette.color(QPalette.ColorRole.Text))
            else:
                painter.setPen(option.palette.color(QPalette.ColorRole.Text))
        painter.setFont(option.font)
        painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()


class TipoCombo(QWidget):
    tipo_changed = Signal(str)

    def __init__(self, current_tipo: str, parent=None):
        super().__init__(parent)
        self._tipo = current_tipo

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

        self.setFixedHeight(28)

        self._combo = _CenteredComboBox()
        self._combo.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._combo.setMinimumWidth(130)
        self._combo.setItemDelegate(_TipoComboDelegate(self._combo))
        self._combo._popup_bg = ""
        self._combo.setHideCurrentItem(True)
        self._layout.addWidget(self._combo)

        self._combo.currentIndexChanged.connect(self._on_index_changed)

        self._combo.blockSignals(True)
        for key in TIPO_LABELS:
            self._combo.addItem(f"{TIPO_SYMBOLS[key]}  {TIPO_LABELS[key]}", key)
        self._combo.blockSignals(False)

        self._update_display(current_tipo)
        idx = self._combo.findData(current_tipo)
        if idx >= 0:
            self._combo.setCurrentIndex(idx)

    def current_tipo(self) -> str:
        return self._tipo

    def set_tipo(self, tipo_key: str):
        idx = self._combo.findData(tipo_key)
        if idx >= 0:
            self._combo.setCurrentIndex(idx)

    def _on_index_changed(self, idx):
        data = self._combo.itemData(idx)
        if data and data != self._tipo:
            self._tipo = data
            self._update_display(data)
            self.tipo_changed.emit(data)

    def _update_display(self, tipo_key: str):
        c = colors()
        dropdown_bg = c["bg_input"]
        self._combo._popup_bg = dropdown_bg
        hex_color = TIPO_HEX.get(tipo_key, "")
        faded = faded_tipo_color(hex_color)
        self._combo.setStyleSheet(f"""
            QComboBox {{
                border: none;
                border-radius: 6px;
                padding: 2px 6px;
                background: transparent;
                color: {faded};
                font-size: 16px;
                font-weight: 600;
                min-height: 22px;
                max-height: 28px;
            }}
            QComboBox:hover {{
                background: {c["bg_hover"]};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 16px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                border: none;
                background-color: {dropdown_bg};
                selection-background-color: {c["selection_bg"]};
                selection-color: {c["selection_text"]};
                outline: none;
                padding: 2px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 10px;
                min-height: 22px;
            }}
        """)
