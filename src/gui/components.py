#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reusable Qt widgets for RAC — native Qt feel
"""

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel,
    QComboBox, QCompleter, QPushButton, QSizePolicy, QWidget,
    QStyledItemDelegate, QStyleOptionViewItem, QLineEdit, QDialog,
    QTreeWidget, QTreeWidgetItem,
)
from PySide6.QtCore import Qt, Signal, QTimer, QStringListModel, QEvent
from PySide6.QtGui import QPainter, QFontMetrics

from src.gui.constants import TIPO_HEX, TIPO_LABELS, TIPO_SYMBOLS
from src.gui.styles import colors
from src.utils.text_utils import normalize_text


class _SearchCompleter(QCompleter):
    def __init__(self, model, parent=None):
        super().__init__(model, parent)
        self._escape_pressed = False
        self._user_selected = False
        self._activated = False
        self._spurious_close = False
        self._reshow_count = 0
        self.activated.connect(lambda _: setattr(self, '_activated', True))

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
    exact_match_changed = Signal(object)

    def __init__(
        self, placeholder: str = "Buscar...", parent=None, on_search=None
    ):
        super().__init__(parent)
        self._on_search = on_search
        self._selected_key: str | None = None
        self._selected_label: str | None = None
        self._options: dict[str, str] = {}
        self._search_labels: dict[str, str] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._model = QStringListModel(self)
        self._completer = _SearchCompleter(self._model, self)
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

        layout.addWidget(self._line_edit)

    def set_options(self, options: dict[str, str]):
        self._options = dict(options)
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
        results = self._on_search(query)
        if results is None:
            return
        labels = list(results.values())
        self._search_labels = {v: k for k, v in results.items()}
        self._model.setStringList(labels)
        self._completer.setCompletionPrefix(query)
        self._completer.complete()
        normalized_query = normalize_text(query)
        for key, label in results.items():
            if normalize_text(label) == normalized_query:
                self.exact_match_changed.emit(key)
                break


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
        self.setFixedHeight(68)
        c = colors()
        self.setStyleSheet(f"""
            QPushButton[tipobtn="true"] {{
                background-color: {c["bg_card"]};
                border: 1px solid {c["border_light"]};
                border-left: 3px solid {hex_color};
                border-radius: 8px;
                padding: 20px 16px;
                font-size: 15px;
                font-weight: 500;
                color: {c["text_primary"]};
            }}
            QPushButton[tipobtn="true"]:hover {{
                background-color: {c["bg_card_alt"]};
                border-left: 3px solid {hex_color};
                border-color: {c["border"]};
            }}
            QPushButton[tipobtn="true"]:pressed {{
                background-color: {c["bg_hover"]};
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

        c = colors()
        text = QLabel(f"{symbol} {label}")
        text.setStyleSheet(f"color: {c['text_primary']}; font-size: 14px; font-weight: 600; border: none;")
        text.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        h.addWidget(text)


class TipoCombo(QWidget):
    tipo_changed = Signal(str)

    def __init__(self, current_tipo: str, parent=None):
        super().__init__(parent)
        self._tipo = current_tipo

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

        self.setFixedHeight(28)

        self._dot = QLabel()
        self._dot.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._layout.addWidget(self._dot)

        self._combo = _CenteredComboBox()
        self._combo.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._combo.setMinimumWidth(130)
        self._combo.setItemDelegate(_CenteredDelegate(self._combo))
        self._layout.addWidget(self._combo)

        self._combo.currentIndexChanged.connect(self._on_index_changed)

        self._combo.blockSignals(True)
        for key in TIPO_LABELS:
            self._combo.addItem(TIPO_LABELS[key], key)
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
        hex_color = TIPO_HEX[tipo_key]
        symbol = TIPO_SYMBOLS[tipo_key]
        self._dot.setText(f"{symbol}")
        self._dot.setStyleSheet(f"color: {hex_color}; font-size: 14px; font-weight: 600; border: none;")

        c = colors()
        self._combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {c["border"]};
                border-left: 3px solid {hex_color};
                border-radius: 6px;
                padding: 2px 10px;
                background: {c["bg_card"]};
                color: {c["text_primary"]};
                font-size: 14px;
                font-weight: 600;
                min-height: 22px;
                max-height: 28px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 0px;
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 0px;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {c["border_light"]};
                border-radius: 6px;
                background-color: {c["bg_card"]};
                color: {c["text_primary"]};
                selection-background-color: {c["selection_bg"]};
                selection-color: {c["selection_text"]};
                outline: none;
                padding: 2px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 10px;
                min-height: 22px;
                color: {c["text_primary"]};
            }}
        """)


class MaloteLabel(QLabel):
    malote_changed = Signal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self._mw = main_window
        c = colors()
        self.setStyleSheet(f"color: {c['text_primary']}; font-size: 22px; font-weight: 400;")
        self.setFixedHeight(28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.mousePressEvent = lambda e: _show_malote_dialog(self)
        self.refresh()

    def refresh(self):
        from src.utils.text_utils import format_malote_date
        malote = self._mw.state.get_active_malote()
        display = format_malote_date(malote) if malote else "Nenhum malote ativo"
        self.setText(display)


def _show_malote_dialog(label: MaloteLabel):
    from datetime import datetime
    from src.utils.text_utils import format_malote_date

    parent = label.window()
    mw = label._mw

    dlg = QDialog(parent)
    dlg.setWindowTitle("Malotes")
    dlg.setMinimumWidth(340)
    dlg.setMinimumHeight(200)

    layout = QVBoxLayout(dlg)
    layout.setSpacing(12)

    layout.addWidget(HeadingLabel("Malotes"))

    malotes = mw.db.get_all_malotes()
    active = mw.state.get_active_malote()

    tree = QTreeWidget()
    tree.setHeaderHidden(True)
    tree.setRootIsDecorated(True)
    tree.setAnimated(True)

    current_year = datetime.now().year
    year_items: dict[int, QTreeWidgetItem] = {}

    for m in malotes:
        try:
            year = datetime.fromisoformat(m.date).year
        except (ValueError, TypeError):
            year = current_year

        is_active = active and active.id == m.id
        display = format_malote_date(m)
        prefix = "\u2713 " if is_active else "    "
        text = f"{prefix}{display}"

        child = QTreeWidgetItem()
        child.setText(0, text)
        child.setData(0, Qt.ItemDataRole.UserRole, m)
        if is_active:
            font = child.font(0)
            font.setBold(True)
            child.setFont(0, font)

        if year < current_year:
            if year not in year_items:
                year_item = QTreeWidgetItem()
                year_item.setText(0, str(year))
                year_item.setChildIndicatorPolicy(
                    QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
                )
                year_item.setExpanded(False)
                year_items[year] = year_item
                tree.addTopLevelItem(year_item)
            year_items[year].addChild(child)
        else:
            tree.addTopLevelItem(child)

    def on_item_clicked(item, _column):
        malote = item.data(0, Qt.ItemDataRole.UserRole)
        if malote:
            mw.state.set_active_malote(malote)
            dlg.accept()
            label.refresh()
            label.malote_changed.emit()
        else:
            item.setExpanded(not item.isExpanded())

    tree.itemClicked.connect(on_item_clicked)
    layout.addWidget(tree)

    btn_row = QHBoxLayout()
    new_m = FlatButton("Novo Malote")
    new_m.clicked.connect(lambda: [dlg.reject(), _show_new_malote_dialog(label)])
    btn_row.addWidget(new_m)
    btn_row.addStretch()
    close_m = FlatButton("Fechar")
    close_m.clicked.connect(dlg.reject)
    btn_row.addWidget(close_m)
    layout.addLayout(btn_row)

    dlg.exec()


def _show_new_malote_dialog(label: MaloteLabel):
    from src.utils.text_utils import parse_date, format_malote_date
    from src.utils.error_handler import ErrorHandler, ErrorContext

    parent = label.window()
    mw = label._mw

    dlg = QDialog(parent)
    dlg.setWindowTitle("Novo Malote")
    dlg.setMinimumWidth(340)

    layout = QVBoxLayout(dlg)
    layout.setSpacing(16)

    layout.addWidget(HeadingLabel("Novo Malote"))

    date_input = QLineEdit()
    date_input.setPlaceholderText("dd/mm ou dd/mm/aa")
    layout.addWidget(date_input)

    btn_row = QHBoxLayout()
    btn_row.addStretch()
    cancel = FlatButton("Cancelar")
    cancel.clicked.connect(dlg.reject)
    btn_row.addWidget(cancel)
    create = PrimaryButton("Criar")

    def do_create():
        iso = parse_date(date_input.text())
        if not iso:
            return
        try:
            malote = mw.db.create_malote(iso)
            mw.state.set_active_malote(malote)
            dlg.accept()
            label.refresh()
            label.malote_changed.emit()
            show_toast(f"Malote criado: {format_malote_date(malote)}", "positive", label)
        except Exception as e:
            ErrorHandler.handle_error(e, context=ErrorContext.MALOTE, show_dialog=False)
            show_toast(f"Erro: {e}", "negative", label)

    create.clicked.connect(do_create)
    btn_row.addWidget(create)
    layout.addLayout(btn_row)

    date_input.returnPressed.connect(do_create)
    dlg.exec()


class ToastLabel(QLabel):
    def __init__(self, text: str, kind: str = "info", parent=None):
        super().__init__(text, parent)
        c = colors()
        colors_map = {
            "positive": (c["toast_positive_fg"], c["toast_positive_bg"]),
            "warning": (c["toast_warning_fg"], c["toast_warning_bg"]),
            "negative": (c["toast_negative_fg"], c["toast_negative_bg"]),
            "info": (c["toast_info_fg"], c["toast_info_bg"]),
        }
        fg, bg = colors_map.get(kind, colors_map["info"])
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


def show_toast(message: str, kind: str, parent: QWidget):
    toast = ToastLabel(message, kind, parent.window())
    toast.adjustSize()
    toast.setFixedWidth(min(toast.width() + 32, parent.width() - 48))
    toast.move(
        (parent.width() - toast.width()) // 2,
        parent.height() - toast.height() - 16,
    )
    toast.show()
    toast.raise_()
    QTimer.singleShot(3000, toast.deleteLater)
