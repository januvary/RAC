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
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPainter, QFontMetrics

from src.gui.constants import TIPO_HEX, TIPO_LABELS, TIPO_SYMBOLS
from src.gui.styles import colors


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

    def __init__(
        self, placeholder: str = "Buscar...", parent=None, on_search=None
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._combo = _NoScrollComboBox()
        self._combo.setEditable(True)
        self._combo.setInsertPolicy(_NoScrollComboBox.InsertPolicy.NoInsert)
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

        if completer:
            completer.activated.connect(self._on_completer_activated)

        layout.addWidget(self._combo)
        self._data_map: dict[str, dict] = {}

        self._on_search = on_search
        if on_search:
            line_edit = self._combo.lineEdit()
            if line_edit:
                line_edit.textEdited.connect(self._do_search)

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

    def focus_search(self):
        line_edit = self._combo.lineEdit()
        if line_edit:
            line_edit.setFocus()
            line_edit.selectAll()
        else:
            self._combo.setFocus()

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

    def _on_completer_activated(self, text: str):
        idx = self._combo.findText(text, Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchCaseSensitive)
        if idx >= 0:
            self._combo.setCurrentIndex(idx)

    def _do_search(self, text: str = ""):
        if not self._on_search:
            return
        text = ""
        line_edit = self._combo.lineEdit()
        if line_edit:
            text = line_edit.text().strip()
        results = self._on_search(text)
        if results is not None:
            current_text = ""
            if line_edit:
                current_text = line_edit.text()
            self._combo.blockSignals(True)
            self._combo.clear()
            self._data_map.clear()
            for key, label in results.items():
                self._combo.addItem(label, key)
                self._data_map[key] = {"id": key, "name": label}
            if line_edit:
                line_edit.setText(current_text)
            self._combo.blockSignals(False)
            completer = self._combo.completer()
            if completer:
                completer.setModel(self._combo.model())


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
