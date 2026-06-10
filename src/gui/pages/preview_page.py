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
    confirm_delete_dialog,
    make_tab,
)
from src.gui.constants import TIPO_HEX, TIPO_LABELS
from src.gui.styles import colors, faded_tipo_color, tab_style_qss, filter_table_rows, data_view_style_qss

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
        self._tabs.setStyleSheet(tab_style_qss())
        self._tab_searches: dict[int, QLineEdit] = {}
        self._shortcut_searches: list[tuple[str, QLineEdit]] = []

        for tipo in TIPO_LABELS:
            tipo_registros = [r for r in registros if r.tipo == tipo]
            tipo_registros.sort(key=lambda r: r.paciente_name or "")

            tab, tab_layout = make_tab()

            search = QLineEdit()
            search.setPlaceholderText("Buscar paciente ou medicamento...")
            tab_layout.addWidget(search)

            table = QTableWidget(0, 2)
            table.setHorizontalHeaderLabels(["Nome", "Medicamentos"])
            table.horizontalHeader().setStretchLastSection(True)
            table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.ResizeToContents
            )
            table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
            table.verticalHeader().setVisible(False)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
            table.setAlternatingRowColors(True)
            table.setCursor(Qt.CursorShape.PointingHandCursor)
            table.setStyleSheet(data_view_style_qss(extra_header_hover=f"\n            QHeaderView::section:hover {{ color: {TIPO_HEX.get(tipo, '#3B82F6')}; }}"))
            tab_layout.addWidget(table)

            search.textChanged.connect(
                lambda text, t=table: filter_table_rows(t, text)
            )

            for reg in tipo_registros:
                for proc in reg.processes:
                    row = table.rowCount()
                    table.insertRow(row)

                    name_item = QTableWidgetItem(reg.paciente_name or "")
                    name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    name_item.setData(Qt.ItemDataRole.UserRole, reg.id)
                    table.setItem(row, 0, name_item)

                    formatted = [
                        _format_item(name)
                        for name in proc.items
                    ]
                    items_str = " / ".join(formatted)
                    meds_item = QTableWidgetItem(items_str)
                    meds_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    table.setItem(row, 1, meds_item)

            table.resizeRowsToContents()
            table.setSortingEnabled(True)

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
            self._tabs.setStyleSheet(tab_style_qss(faded_tipo_color(TIPO_HEX.get(tipo_key, ""))))

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

    def _on_row_double_clicked(self, table: QTableWidget, row: int):
        item = table.item(row, 0)
        if not item:
            return
        reg_id = item.data(Qt.ItemDataRole.UserRole)
        if reg_id is None:
            return
        reg = self._mw.db.get_registro_by_id(reg_id)
        if reg:
            self._mw.navigate_to(
                "entry", tipo=reg.tipo, edit_id=reg_id, return_to="preview"
            )

    def _on_enter(self, table: QTableWidget):
        row = table.currentRow()
        if row >= 0:
            self._on_row_double_clicked(table, row)

    def _get_selected_ids(self, table: QTableWidget) -> list[int]:
        ids = []
        for row in table.selectionModel().selectedRows():
            item = table.item(row.row(), 0)
            if item:
                reg_id = item.data(Qt.ItemDataRole.UserRole)
                if reg_id is not None:
                    ids.append(reg_id)
        return ids

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

        if not table.selectionModel().isRowSelected(row, table.rootIndex()):
            table.selectRow(row)

        selected_ids = self._get_selected_ids(table)
        is_multi = len(selected_ids) > 1

        menu = QMenu(self)
        editar_menu = menu.addMenu("Editar")

        tipo_menu = editar_menu.addMenu("Tipo")
        for tipo in TIPO_LABELS:
            if tipo == current_tipo:
                continue
            action = tipo_menu.addAction(TIPO_LABELS.get(tipo, tipo))
            action.triggered.connect(
                lambda _checked=False, ids=selected_ids, t=tipo: self._change_tipo(
                    ids, t
                )
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
                    lambda _checked=False, ids=selected_ids, mid=m.id: self._move_to_malote(
                        ids, mid
                    )
                )

        if not is_multi:
            nome_action = editar_menu.addAction("Nome do paciente")
            nome_action.triggered.connect(
                lambda _checked=False, rid=reg_id: self._edit_paciente_name(rid)
            )

        editar_menu.addSeparator()
        label = f"Excluir ({len(selected_ids)})" if is_multi else "Excluir"
        excluir_action = editar_menu.addAction(label)
        excluir_action.triggered.connect(
            lambda _checked=False, ids=selected_ids: self._confirm_delete(ids)
        )

        menu.exec(table.viewport().mapToGlobal(pos))

    def _batch_update(self, reg_ids, update_fn, singular_msg, plural_verb):
        errors = 0
        for rid in reg_ids:
            try:
                update_fn(rid)
            except DuplicateRecordError:
                errors += 1
        self.refresh()
        if errors:
            self._toast(f"{errors} registro(s) duplicado(s) ignorado(s)", "warning")
        else:
            count = len(reg_ids)
            self._toast(
                f"{count} registro(s) {plural_verb}" if count > 1 else singular_msg,
                "positive",
            )

    def _change_tipo(self, reg_ids: list[int], new_tipo: str):
        self._batch_update(
            reg_ids,
            lambda rid: self._mw.db.update_registro(rid, tipo=new_tipo),
            "Tipo alterado",
            "alterado(s)",
        )

    def _move_to_malote(self, reg_ids: list[int], new_malote_id: int):
        self._batch_update(
            reg_ids,
            lambda rid: self._mw.db.update_registro(rid, malote_id=new_malote_id),
            "Registro movido",
            "movido(s)",
        )

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
            self._handle_error(e)

    def _confirm_delete(self, reg_ids: list[int]):
        if len(reg_ids) == 1:
            delete_registro_with_undo(self, self._mw.db, reg_ids[0], self.refresh)
        else:
            if not confirm_delete_dialog(
                self,
                "Excluir Registros",
                f"Excluir {len(reg_ids)} registros selecionados?",
            ):
                return
            try:
                service = RegistroService(self._mw.db)
                for rid in reg_ids:
                    service.delete(rid)
                self.refresh()
                self._toast(f"{len(reg_ids)} registros excluidos", "info")
            except Exception as e:
                self._handle_error(e)

    def set_shortcuts_visible(self, show: bool):
        super().set_shortcuts_visible(show)
        self._malote_label.set_shortcut_hint_visible(show)
