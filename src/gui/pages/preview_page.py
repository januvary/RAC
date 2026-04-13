#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Preview Page — tabbed table view of malote registros
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QSizePolicy,
    QHeaderView, QMenu,
)
from PySide6.QtCore import Qt

from src.gui.components import (
    HeadingLabel, FlatButton, ToastLabel, PrimaryButton,
    MaloteLabel, show_toast,
)
from src.gui.constants import TIPO_HEX, TIPO_LABELS
from src.gui.styles import colors
from src.utils.error_handler import ErrorHandler, ErrorContext
from src.utils.text_utils import format_malote_date, parse_date, to_upper_normalized
import sqlite3

_TIPO_ORDER = ["entrada", "renovacao", "retirada", "urgente"]

_TIPO_TITLES = {
    "entrada": "ENTRADAS",
    "renovacao": "RENOVAÇÕES",
    "retirada": "RETIRADAS",
    "urgente": "URGENTES",
}


class PreviewPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self._mw = main_window
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(48, 32, 48, 32)
        outer.setSpacing(0)
        outer.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        container = QWidget()
        container.setMaximumWidth(720)
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._build_header(layout)
        layout.addSpacing(20)

        self._build_tabs(layout)

        outer.addWidget(container)

    def _build_header(self, layout: QVBoxLayout):
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        back_btn = FlatButton("Voltar")
        back_btn.clicked.connect(lambda: self._mw.navigate_to("start"))
        h.addWidget(back_btn)
        h.addStretch()

        self._malote_label = MaloteLabel(self._mw)
        self._malote_label.malote_changed.connect(self.refresh)
        h.addWidget(self._malote_label, 0, Qt.AlignmentFlag.AlignTop)

        layout.addLayout(h)

    def _build_tabs(self, layout: QVBoxLayout):
        malote = self._mw.state.get_active_malote()
        if not malote:
            return

        registros = self._mw.db.get_registros_with_items_by_malote(malote.id)

        self._tabs = QTabWidget()
        self._tabs.setMinimumHeight(550)
        self._tabs.setStyleSheet(self._tab_style())

        for tipo in _TIPO_ORDER:
            tipo_registros = [r for r in registros if r.tipo == tipo]
            tipo_registros.sort(key=lambda r: r.paciente_name or "")

            table = QTableWidget(0, 2)
            table.setHorizontalHeaderLabels(["Nome", "Medicamentos"])
            table.horizontalHeader().setStretchLastSection(True)
            table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.ResizeToContents
            )
            table.verticalHeader().setVisible(False)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            table.setAlternatingRowColors(True)
            table.setCursor(Qt.CursorShape.PointingHandCursor)
            table.setStyleSheet(self._table_style(tipo))

            for reg in tipo_registros:
                row = table.rowCount()
                table.insertRow(row)

                name_item = QTableWidgetItem(to_upper_normalized(reg.paciente_name or ""))
                name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                name_item.setData(Qt.ItemDataRole.UserRole, reg.id)
                table.setItem(row, 0, name_item)

                items_str = "\n".join(to_upper_normalized(i) for i in reg.items)
                meds_item = QTableWidgetItem(items_str)
                meds_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 1, meds_item)

            table.resizeRowsToContents()
            table.cellDoubleClicked.connect(
                lambda r, c, t=table: self._on_row_double_clicked(t, r)
            )
            table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            table.customContextMenuRequested.connect(
                lambda pos, t=table, tp=tipo: self._show_row_menu(t, tp, pos)
            )

            tab_label = f"{TIPO_LABELS.get(tipo, tipo)} ({len(tipo_registros)})"
            self._tabs.addTab(table, tab_label)

        layout.addWidget(self._tabs)

    def refresh(self):
        self._malote_label.refresh()

        old = self.findChild(QTabWidget)
        if old:
            old.setParent(None)
            old.deleteLater()

        container = self.layout().itemAt(0).widget()
        self._build_tabs(container.layout())

    def _on_row_double_clicked(self, table: QTableWidget, row: int):
        item = table.item(row, 0)
        if not item:
            return
        reg_id = item.data(Qt.ItemDataRole.UserRole)
        if reg_id is None:
            return
        reg = self._mw.db.get_registro_by_id(reg_id)
        if reg:
            self._mw.navigate_to("entry", tipo=reg.tipo, edit_id=reg_id)

    def _show_row_menu(self, table: QTableWidget, current_tipo: str, pos):
        row = table.rowAt(pos.y())
        if row < 0:
            return
        item = table.item(row, 0)
        if not item:
            return
        reg_id = item.data(Qt.ItemDataRole.UserRole)
        if reg_id is None:
            return

        menu = QMenu(self)

        tipo_menu = menu.addMenu("Alterar tipo")
        for tipo in _TIPO_ORDER:
            if tipo == current_tipo:
                continue
            action = tipo_menu.addAction(TIPO_LABELS.get(tipo, tipo))
            action.triggered.connect(
                lambda checked=False, rid=reg_id, t=tipo: self._change_tipo(rid, t)
            )

        active = self._mw.state.get_active_malote()
        malotes = self._mw.db.get_all_malotes()
        other_malotes = [m for m in malotes if not active or m.id != active.id]
        if other_malotes:
            malote_menu = menu.addMenu("Mover para malote")
            for m in other_malotes:
                display = format_malote_date(m)
                action = malote_menu.addAction(display)
                action.triggered.connect(
                    lambda checked=False, rid=reg_id, mid=m.id: self._move_to_malote(rid, mid)
                )

        menu.exec(table.viewport().mapToGlobal(pos))

    def _change_tipo(self, reg_id: int, new_tipo: str):
        try:
            self._mw.db.update_registro(reg_id, tipo=new_tipo)
            self.refresh()
            self._toast("Tipo alterado", "positive")
        except sqlite3.IntegrityError:
            self._toast("Registro já existe nesse tipo para esse paciente", "warning")
        except Exception as e:
            ErrorHandler.handle_error(e, context=ErrorContext.REGISTRO, show_dialog=False)
            self._toast(f"Erro: {e}", "negative")

    def _move_to_malote(self, reg_id: int, new_malote_id: int):
        try:
            self._mw.db.update_registro(reg_id, malote_id=new_malote_id)
            self.refresh()
            self._toast("Registro movido", "positive")
        except sqlite3.IntegrityError:
            self._toast("Registro já existe nesse malote para esse paciente e tipo", "warning")
        except Exception as e:
            ErrorHandler.handle_error(e, context=ErrorContext.REGISTRO, show_dialog=False)
            self._toast(f"Erro: {e}", "negative")

    def _toast(self, message: str, kind: str = "info"):
        show_toast(message, kind, self)

    @staticmethod
    def _table_style(tipo: str) -> str:
        hex_color = TIPO_HEX.get(tipo, "#3B82F6")
        c = colors()
        return f"""
            QTableWidget {{
                border: 1px solid {c["border_light"]};
                border-radius: 6px;
                background: {c["bg_card"]};
                alternate-background-color: {c["bg_card_alt"]};
                gridline-color: {c["gridline"]};
                font-size: 13px;
                color: {c["text_primary"]};
            }}
            QTableWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {c["gridline"]};
                color: {c["text_primary"]};
            }}
            QTableWidget::item:selected {{
                background-color: {c["selection_bg"]};
                color: {c["selection_text"]};
            }}
            QHeaderView::section {{
                background-color: {c["bg_card"]};
                border: none;
                border-bottom: 2px solid {hex_color};
                padding: 10px 12px;
                font-weight: 600;
                font-size: 13px;
                color: {c["text_primary"]};
            }}
        """

    @staticmethod
    def _tab_style() -> str:
        c = colors()
        return f"""
            QTabWidget::pane {{
                border: 1px solid {c["border_light"]};
                border-radius: 6px;
                background: {c["bg_card"]};
            }}
            QTabBar::tab {{
                padding: 8px 20px;
                border: 1px solid {c["border_light"]};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                background: {c["bg_card_alt"]};
                color: {c["text_secondary"]};
                font-size: 13px;
                font-weight: 500;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {c["bg_card"]};
                color: #3B82F6;
                border-bottom: 2px solid {c["bg_card"]};
                font-weight: 600;
            }}
            QTabBar::tab:hover {{
                background: {c["bg_hover"]};
                color: {c["text_primary"]};
            }}
        """
