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
    make_tab,
)
from src.gui.styles import colors, tab_style_qss, data_view_style_qss


class _CrudTab:
    def __init__(self, page, db, tab_title, search_placeholder,
                 entity_label, entity_label_lower,
                 db_get_all, db_create, db_update, db_delete,
                 delete_in_use_msg):
        self._page = page
        self._db = db
        self._entity_label = entity_label
        self._entity_label_lower = entity_label_lower
        self._db_get_all = db_get_all
        self._db_create = db_create
        self._db_update = db_update
        self._db_delete = db_delete
        self._delete_in_use_msg = delete_in_use_msg
        self._all_items = []
        self.list_widget = None
        self.search = None
        self.widget = None
        self._build(tab_title, search_placeholder)

    def _build(self, tab_title, search_placeholder):
        tab, tab_layout = make_tab()

        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText(search_placeholder)
        self.search.textChanged.connect(self.filter)
        search_row.addWidget(self.search)
        edit_btn = make_button("Editar", "primary")
        edit_btn.clicked.connect(self.edit_selected)
        search_row.addWidget(edit_btn)
        add_btn = make_button("Adicionar", "primary")
        add_btn.clicked.connect(self.add)
        search_row.addWidget(add_btn)
        del_btn = make_button("Excluir", "negative")
        del_btn.clicked.connect(self.delete_selected)
        search_row.addWidget(del_btn)
        tab_layout.addLayout(search_row)

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setStyleSheet(data_view_style_qss(widget_type="QListWidget", include_selected=True, include_hover=True, outline="none"))
        self.list_widget.itemDoubleClicked.connect(self._edit)
        self._page.register_keyboard_nav(
            self.list_widget, self.search, lambda _: self.edit_selected()
        )
        tab_layout.addWidget(self.list_widget)

        self.load()
        self.widget = tab

    def load(self):
        self._all_items = self._db_get_all()
        self._populate(self._all_items)

    def _populate(self, items):
        self.list_widget.clear()
        for item in items:
            list_item = QListWidgetItem(item.name)
            list_item.setData(Qt.ItemDataRole.UserRole, item.id)
            self.list_widget.addItem(list_item)

    def filter(self, text: str):
        query = text.strip().lower()
        if not query:
            self._populate(self._all_items)
            return
        filtered = [i for i in self._all_items if query in i.name.lower()]
        self._populate(filtered)

    def add(self):
        name = open_input_dialog(
            self._page, f"Adicionar {self._entity_label}",
            f"Nome do {self._entity_label_lower}",
        )
        if not name:
            return
        try:
            self._db_create(name)
            self.load()
            self.search.clear()
            self._page._toast(f"{self._entity_label} adicionado", "positive")
        except Exception:
            self._page._toast("Erro: nome já existe ou inválido", "negative")

    def _edit(self, item: QListWidgetItem):
        item_id = item.data(Qt.ItemDataRole.UserRole)
        old_name = item.text()
        new_name = open_input_dialog(
            self._page, f"Editar {self._entity_label}",
            f"Nome do {self._entity_label_lower}", initial=old_name,
        )
        if not new_name or new_name == old_name:
            return
        try:
            self._db_update(item_id, new_name)
            self.load()
            self.search.clear()
            self._page._toast(f"{self._entity_label} atualizado", "positive")
        except Exception:
            self._page._toast("Erro: nome já existe ou inválido", "negative")

    def edit_selected(self):
        current = self.list_widget.currentItem()
        if current:
            self._edit(current)

    def delete_selected(self):
        current = self.list_widget.currentItem()
        if not current:
            return
        item_id = current.data(Qt.ItemDataRole.UserRole)
        name = current.text()
        if not confirm_delete_dialog(
            self._page, f"Excluir {self._entity_label}", f'Excluir "{name}"?',
        ):
            return
        if self._db_delete(item_id):
            self.load()
            self.search.clear()
            self._page._toast(f"{self._entity_label} excluído", "positive")
        else:
            self._page._toast(self._delete_in_use_msg, "warning")


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
        self._tabs.setStyleSheet(tab_style_qss())

        self._items_tab = _CrudTab(
            self, self._mw.db,
            tab_title="Medicamentos",
            search_placeholder="Buscar medicamento...",
            entity_label="Medicamento",
            entity_label_lower="medicamento",
            db_get_all=self._mw.db.get_all_items,
            db_create=self._mw.db.create_item,
            db_update=self._mw.db.update_item,
            db_delete=self._mw.db.delete_item,
            delete_in_use_msg="Não é possível excluir: medicamento em uso",
        )
        self._tabs.addTab(self._items_tab.widget, "Medicamentos")

        self._pacientes_tab = _CrudTab(
            self, self._mw.db,
            tab_title="Pacientes",
            search_placeholder="Buscar paciente...",
            entity_label="Paciente",
            entity_label_lower="paciente",
            db_get_all=self._mw.db.get_all_pacientes,
            db_create=self._mw.db.create_paciente,
            db_update=self._mw.db.update_paciente,
            db_delete=self._mw.db.delete_paciente,
            delete_in_use_msg="Não é possível excluir: paciente com registros",
        )
        self._tabs.addTab(self._pacientes_tab.widget, "Pacientes")

        self._shortcut_searches = [
            ("Buscar medicamento...", self._items_tab.search),
            ("Buscar paciente...", self._pacientes_tab.search),
        ]

        layout.addWidget(self._tabs)
