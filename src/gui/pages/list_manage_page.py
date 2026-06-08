#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
List Manage Page — tabbed view for managing medications and patients
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
)
from PySide6.QtCore import Qt

from src.gui.widgets import (
    make_button,
    BasePage,
    confirm_delete_dialog,
    open_input_dialog,
)
from src.gui.styles import colors


class ListManagePage(BasePage):
    def __init__(self, main_window):
        super().__init__(main_window)
        self._build_ui()

    def _build_ui(self):
        layout = self._scaffold()
        self._add_back_button(layout)
        layout.addSpacing(20)
        self._build_tabs(layout)

    def _build_tabs(self, layout: QVBoxLayout):
        self._tabs = QTabWidget()
        self._tabs.setMinimumHeight(500)
        self._tabs.setStyleSheet(self._tab_style())

        self._build_items_tab()
        self._build_pacientes_tab()

        layout.addWidget(self._tabs)

    def _build_items_tab(self):
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(16, 16, 16, 16)
        tab_layout.setSpacing(12)

        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        self._item_search = QLineEdit()
        self._item_search.setPlaceholderText("Buscar medicamento...")
        self._item_search.textChanged.connect(self._filter_items)
        search_row.addWidget(self._item_search)
        edit_btn = make_button("Editar", "primary")
        edit_btn.clicked.connect(self._edit_selected_item)
        search_row.addWidget(edit_btn)
        add_btn = make_button("Adicionar", "primary")
        add_btn.clicked.connect(self._add_item)
        search_row.addWidget(add_btn)
        del_btn = make_button("Excluir", "negative")
        del_btn.clicked.connect(self._delete_selected_item)
        search_row.addWidget(del_btn)
        tab_layout.addLayout(search_row)

        self._shortcut_searches = [
            ("Buscar medicamento...", self._item_search),
        ]

        self._item_list = QListWidget()
        self._item_list.setAlternatingRowColors(True)
        self._item_list.setStyleSheet(self._list_style())
        self._item_list.itemDoubleClicked.connect(self._edit_item)
        self.register_keyboard_nav(
            self._item_list, self._item_search, lambda _: self._edit_selected_item()
        )
        tab_layout.addWidget(self._item_list)

        self._load_items()
        self._tabs.addTab(tab, "Medicamentos")

    def _build_pacientes_tab(self):
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(16, 16, 16, 16)
        tab_layout.setSpacing(12)

        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        self._paciente_search = QLineEdit()
        self._paciente_search.setPlaceholderText("Buscar paciente...")
        self._paciente_search.textChanged.connect(self._filter_pacientes)
        search_row.addWidget(self._paciente_search)
        edit_btn = make_button("Editar", "primary")
        edit_btn.clicked.connect(self._edit_selected_paciente)
        search_row.addWidget(edit_btn)
        add_btn = make_button("Adicionar", "primary")
        add_btn.clicked.connect(self._add_paciente)
        search_row.addWidget(add_btn)
        del_btn = make_button("Excluir", "negative")
        del_btn.clicked.connect(self._delete_selected_paciente)
        search_row.addWidget(del_btn)
        tab_layout.addLayout(search_row)

        self._shortcut_searches.append(
            ("Buscar paciente...", self._paciente_search),
        )

        self._paciente_list = QListWidget()
        self._paciente_list.setAlternatingRowColors(True)
        self._paciente_list.setStyleSheet(self._list_style())
        self._paciente_list.itemDoubleClicked.connect(self._edit_paciente)
        self.register_keyboard_nav(
            self._paciente_list,
            self._paciente_search,
            lambda _: self._edit_selected_paciente(),
        )
        tab_layout.addWidget(self._paciente_list)

        self._load_pacientes()
        self._tabs.addTab(tab, "Pacientes")

    def _load_items(self):
        self._all_items = self._mw.db.get_all_items()
        self._populate_items(self._all_items)

    def _populate_items(self, items):
        self._item_list.clear()
        for item in items:
            list_item = QListWidgetItem(item.name)
            list_item.setData(Qt.ItemDataRole.UserRole, item.id)
            self._item_list.addItem(list_item)

    def _filter_items(self, text: str):
        query = text.strip().lower()
        if not query:
            self._populate_items(self._all_items)
            return
        filtered = [i for i in self._all_items if query in i.name.lower()]
        self._populate_items(filtered)

    def _add_item(self):
        name = open_input_dialog(self, "Adicionar Medicamento", "Nome do medicamento")
        if not name:
            return
        try:
            self._mw.db.create_item(name)
            self._load_items()
            self._item_search.clear()
            self._toast("Medicamento adicionado", "positive")
        except Exception:
            self._toast("Erro: nome já existe ou inválido", "negative")

    def _edit_item(self, item: QListWidgetItem):
        item_id = item.data(Qt.ItemDataRole.UserRole)
        old_name = item.text()
        new_name = open_input_dialog(
            self, "Editar Medicamento", "Nome do medicamento", initial=old_name
        )
        if not new_name or new_name == old_name:
            return
        try:
            self._mw.db.update_item(item_id, new_name)
            self._load_items()
            self._item_search.clear()
            self._toast("Medicamento atualizado", "positive")
        except Exception:
            self._toast("Erro: nome já existe ou inválido", "negative")

    def _edit_selected_item(self):
        current = self._item_list.currentItem()
        if current:
            self._edit_item(current)

    def _delete_selected_item(self):
        current = self._item_list.currentItem()
        if not current:
            return
        item_id = current.data(Qt.ItemDataRole.UserRole)
        name = current.text()
        if not confirm_delete_dialog(self, "Excluir Medicamento", f'Excluir "{name}"?'):
            return
        if self._mw.db.delete_item(item_id):
            self._load_items()
            self._item_search.clear()
            self._toast("Medicamento excluído", "positive")
        else:
            self._toast("Não é possível excluir: medicamento em uso", "warning")

    def _load_pacientes(self):
        self._all_pacientes = self._mw.db.get_all_pacientes()
        self._populate_pacientes(self._all_pacientes)

    def _populate_pacientes(self, pacientes):
        self._paciente_list.clear()
        for p in pacientes:
            list_item = QListWidgetItem(p.name)
            list_item.setData(Qt.ItemDataRole.UserRole, p.id)
            self._paciente_list.addItem(list_item)

    def _filter_pacientes(self, text: str):
        query = text.strip().lower()
        if not query:
            self._populate_pacientes(self._all_pacientes)
            return
        filtered = [p for p in self._all_pacientes if query in p.name.lower()]
        self._populate_pacientes(filtered)

    def _add_paciente(self):
        name = open_input_dialog(self, "Adicionar Paciente", "Nome do paciente")
        if not name:
            return
        try:
            self._mw.db.create_paciente(name)
            self._load_pacientes()
            self._paciente_search.clear()
            self._toast("Paciente adicionado", "positive")
        except Exception:
            self._toast("Erro: nome já existe ou inválido", "negative")

    def _edit_paciente(self, item: QListWidgetItem):
        paciente_id = item.data(Qt.ItemDataRole.UserRole)
        old_name = item.text()
        new_name = open_input_dialog(
            self, "Editar Paciente", "Nome do paciente", initial=old_name
        )
        if not new_name or new_name == old_name:
            return
        try:
            self._mw.db.update_paciente(paciente_id, new_name)
            self._load_pacientes()
            self._paciente_search.clear()
            self._toast("Paciente atualizado", "positive")
        except Exception:
            self._toast("Erro: nome já existe ou inválido", "negative")

    def _edit_selected_paciente(self):
        current = self._paciente_list.currentItem()
        if current:
            self._edit_paciente(current)

    def _delete_selected_paciente(self):
        current = self._paciente_list.currentItem()
        if not current:
            return
        paciente_id = current.data(Qt.ItemDataRole.UserRole)
        name = current.text()
        if not confirm_delete_dialog(self, "Excluir Paciente", f'Excluir "{name}"?'):
            return
        if self._mw.db.delete_paciente(paciente_id):
            self._load_pacientes()
            self._paciente_search.clear()
            self._toast("Paciente excluído", "positive")
        else:
            self._toast("Não é possível excluir: paciente com registros", "warning")

    @staticmethod
    def _list_style() -> str:
        c = colors()
        return f"""
            QListWidget {{
                border: none;
                border-radius: 6px;
                background: transparent;
                alternate-background-color: {c["table_alt_bg"]};
                font-size: 13px;
                color: {c["text_primary"]};
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {c["gridline"]};
            }}
            QListWidget::item:selected {{
                background-color: {c["selection_bg"]};
                color: {c["selection_text"]};
            }}
            QListWidget::item:hover {{
                background-color: {c["bg_hover"]};
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
