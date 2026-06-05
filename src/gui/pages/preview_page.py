#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Preview Page — tabbed table view of malote registros
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QHeaderView,
    QMenu,
)
from PySide6.QtCore import Qt

from src.gui.widgets import (
    MaloteLabel,
    BasePage,
    open_input_dialog,
    delete_registro_with_undo,
)
from src.gui.constants import TIPO_HEX, TIPO_LABELS
from src.gui.styles import colors, faded_tipo_color
from andaime.error_handler import ErrorHandler

from src.utils.text_utils import format_malote_date
from src.services.exceptions import DuplicateRecordError
from src.services.registro_service import RegistroService
from src.export.excel_exporter import _format_item


class PreviewPage(BasePage):
    def __init__(self, main_window):
        super().__init__(main_window)
        self._build_ui()

    def _build_ui(self):
        layout = self._scaffold()
        self._build_header(layout)
        layout.addSpacing(20)
        self._build_tabs(layout)

    def _build_header(self, layout: QVBoxLayout):
        h = self._add_back_button(layout)

        self._malote_label = MaloteLabel(self._mw)
        self._malote_label.malote_changed.connect(self.refresh)
        h.addWidget(self._malote_label, 0, Qt.AlignmentFlag.AlignTop)

    def _build_tabs(self, layout: QVBoxLayout):
        malote = self._mw.state.get_active_malote()
        if not malote:
            return

        registros = self._mw.db.get_registros_with_items_by_malote(malote.id)

        self._tabs = QTabWidget()
        self._tabs.setMinimumHeight(550)
        self._tab_tipo_keys: list[str] = []
        self._tabs.setStyleSheet(self._tab_style(list(TIPO_LABELS)[0]))
        self._tab_searches: dict[int, QLineEdit] = {}
        self._shortcut_searches: list[tuple[str, QLineEdit]] = []

        for tipo in TIPO_LABELS:
            tipo_registros = [r for r in registros if r.tipo == tipo]
            tipo_registros.sort(key=lambda r: r.paciente_name or "")

            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            tab_layout.setContentsMargins(16, 16, 16, 16)
            tab_layout.setSpacing(12)

            search = QLineEdit()
            search.setPlaceholderText("Buscar paciente ou medicamento...")
            tab_layout.addWidget(search)

            table = QTableWidget(0, 2)
            table.setHorizontalHeaderLabels(["Nome", "Medicamentos"])
            table.horizontalHeader().setStretchLastSection(True)
            table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.ResizeToContents
            )
            table.horizontalHeader().setFixedHeight(0)
            table.verticalHeader().setVisible(False)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            table.setAlternatingRowColors(True)
            table.setCursor(Qt.CursorShape.PointingHandCursor)
            table.setStyleSheet(self._table_style(tipo))
            tab_layout.addWidget(table)

            search.textChanged.connect(
                lambda text, t=table: self._filter_table(t, text)
            )

            for reg in tipo_registros:
                for process_items in reg.processes:
                    row = table.rowCount()
                    table.insertRow(row)

                    name_item = QTableWidgetItem(reg.paciente_name or "")
                    name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    name_item.setData(Qt.ItemDataRole.UserRole, reg.id)
                    table.setItem(row, 0, name_item)

                    formatted = [
                        _format_item(name).replace(" ", "\u00A0")
                        for name in process_items
                    ]
                    items_str = " / ".join(formatted)
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
            self.register_keyboard_nav(table, search, lambda t=table: self._on_enter(t))

            tab_label = f"{TIPO_LABELS.get(tipo, tipo)} ({len(tipo_registros)})"
            idx = self._tabs.addTab(tab, tab_label)
            self._tab_tipo_keys.append(tipo)
            self._tab_searches[idx] = search
            self._shortcut_searches.append(("_search_placeholder", search))

        self._tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self._tabs)

    def _on_tab_changed(self, idx):
        if 0 <= idx < len(self._tab_tipo_keys):
            tipo_key = self._tab_tipo_keys[idx]
            self._tabs.setStyleSheet(self._tab_style(tipo_key))

    def refresh(self):
        self._malote_label.refresh()

        old = self.findChild(QTabWidget)
        if old:
            old.setParent(None)
            old.deleteLater()

        main_layout = self.layout()
        if main_layout is None:
            return
        item = main_layout.itemAt(0)
        if item is None:
            return
        container = item.widget()
        if container is None:
            return
        container_layout = container.layout()
        if not isinstance(container_layout, QVBoxLayout):
            return
        self._build_tabs(container_layout)

    def _filter_table(self, table: QTableWidget, text: str):
        query = text.strip().lower()
        for row in range(table.rowCount()):
            match = False
            if not query:
                match = True
            else:
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    if item and query in item.text().lower():
                        match = True
                        break
            table.setRowHidden(row, not match)

    def _on_row_double_clicked(self, table: QTableWidget, row: int):
        item = table.item(row, 0)
        if not item:
            return
        reg_id = item.data(Qt.ItemDataRole.UserRole)
        if reg_id is None:
            return
        reg = self._mw.db.get_registro_by_id(reg_id)
        if reg:
            self._mw.navigate_to("entry", tipo=reg.tipo, edit_id=reg_id, return_to="preview")

    def _on_enter(self, table: QTableWidget):
        row = table.currentRow()
        if row >= 0:
            self._on_row_double_clicked(table, row)

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
        editar_menu = menu.addMenu("Editar")

        tipo_menu = editar_menu.addMenu("Tipo")
        for tipo in TIPO_LABELS:
            if tipo == current_tipo:
                continue
            action = tipo_menu.addAction(TIPO_LABELS.get(tipo, tipo))
            action.triggered.connect(
                lambda _checked=False, rid=reg_id, t=tipo: self._change_tipo(rid, t)
            )

        active = self._mw.state.get_active_malote()
        malotes = self._mw.db.get_all_malotes()
        other_malotes = [m for m in malotes if not active or m.id != active.id]
        if other_malotes:
            malote_menu = editar_menu.addMenu("Malote")
            for m in other_malotes:
                display = format_malote_date(m)
                action = malote_menu.addAction(display)
                action.triggered.connect(
                    lambda _checked=False, rid=reg_id, mid=m.id: self._move_to_malote(
                        rid, mid
                    )
                )

        nome_action = editar_menu.addAction("Nome do paciente")
        nome_action.triggered.connect(
            lambda _checked=False, rid=reg_id: self._edit_paciente_name(rid)
        )

        editar_menu.addSeparator()
        excluir_action = editar_menu.addAction("Excluir")
        excluir_action.triggered.connect(
            lambda _checked=False, rid=reg_id: self._confirm_delete(rid)
        )

        menu.exec(table.viewport().mapToGlobal(pos))

    def _change_tipo(self, reg_id: int, new_tipo: str):
        try:
            self._mw.db.update_registro(reg_id, tipo=new_tipo)
            self.refresh()
            self._toast("Tipo alterado", "positive")
        except DuplicateRecordError:
            self._toast("Registro já existe nesse tipo para esse paciente", "warning")
        except Exception as e:
            ErrorHandler.handle_error(e, context="Registro", show_dialog=False)
            self._toast(f"Erro: {e}", "negative")

    def _move_to_malote(self, reg_id: int, new_malote_id: int):
        try:
            self._mw.db.update_registro(reg_id, malote_id=new_malote_id)
            self.refresh()
            self._toast("Registro movido", "positive")
        except DuplicateRecordError:
            self._toast(
                "Registro já existe nesse malote para esse paciente e tipo", "warning"
            )
        except Exception as e:
            ErrorHandler.handle_error(e, context="Registro", show_dialog=False)
            self._toast(f"Erro: {e}", "negative")

    def _edit_paciente_name(self, reg_id: int):
        reg = self._mw.db.get_registro_by_id(reg_id)
        if not reg or not reg.paciente_id:
            return
        new_name = open_input_dialog(
            self,
            "Editar Nome do Paciente",
            "Nome do paciente",
            initial=reg.paciente_name or "",
        )
        if not new_name or new_name == reg.paciente_name:
            return
        try:
            self._mw.db.update_paciente(reg.paciente_id, new_name)
            self.refresh()
            self._toast("Nome do paciente atualizado", "positive")
        except Exception as e:
            ErrorHandler.handle_error(e, context="Registro", show_dialog=False)
            self._toast(f"Erro: {e}", "negative")

    def _confirm_delete(self, reg_id: int):
        delete_registro_with_undo(self, self._mw.db, reg_id, self.refresh)

    @staticmethod
    def _table_style(tipo: str) -> str:
        hex_color = TIPO_HEX.get(tipo, "#3B82F6")
        c = colors()
        return f"""
            QTableWidget {{
                border: none;
                border-radius: 6px;
                background: transparent;
                alternate-background-color: {c["table_alt_bg"]};
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
        """

    @staticmethod
    def _tab_style(tipo_key: str) -> str:
        c = colors()
        faded = faded_tipo_color(TIPO_HEX.get(tipo_key, ""))
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
                color: {faded};
                border-bottom: 2px solid {c["bg_card"]};
                font-weight: 600;
            }}
            QTabBar::tab:hover {{
                background: {c["bg_hover"]};
                color: {c["text_primary"]};
            }}
        """

    def set_shortcuts_visible(self, show: bool):
        super().set_shortcuts_visible(show)
        self._malote_label.set_shortcut_hint_visible(show)
