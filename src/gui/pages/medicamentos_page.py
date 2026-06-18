#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medicamentos Page — manage the medication (item catalog) list
"""

from src.gui.widgets import BasePage, CrudList, HeadingLabel


class MedicamentosPage(BasePage):
    def __init__(self, main_window):
        super().__init__(main_window)
        self._build_ui()

    def _build_ui(self):
        layout = self._scaffold()
        self._add_back_button(layout)
        layout.addSpacing(20)

        self._heading = HeadingLabel("Medicamentos")
        layout.addWidget(self._heading)
        layout.addSpacing(12)

        self._crud = CrudList(
            self,
            title="Medicamentos",
            search_placeholder="Buscar medicamento...",
            entity_label="Medicamento",
            entity_label_lower="medicamento",
            db_get_all=self._mw.services.item_catalog.all,
            db_create=self._mw.services.item_catalog.create,
            db_update=self._mw.services.item_catalog.update,
            db_delete=self._mw.services.item_catalog.delete,
            delete_in_use_msg="Não é possível excluir: medicamento em uso",
            count_label=self._heading,
        )
        layout.addWidget(self._crud.widget)

        self._shortcut_searches = [
            ("Buscar medicamento...", self._crud.search),
        ]
