#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pacientes Page — manage the patient list
"""

from datetime import datetime

from src.gui.widgets import BasePage, CrudList, HeadingLabel
from src.models import Paciente


def _format_last_registro(p: Paciente) -> str:
    date_raw = (p.last_registro_date or "").strip()
    if not date_raw:
        return "—"
    try:
        return datetime.fromisoformat(date_raw).strftime("%d/%m/%Y")
    except ValueError:
        return date_raw


class PacientesPage(BasePage):
    def __init__(self, main_window):
        super().__init__(main_window)
        self._build_ui()

    def _build_ui(self):
        layout = self._scaffold()
        self._add_back_button(layout)
        layout.addSpacing(20)

        self._heading = HeadingLabel("Pacientes")
        layout.addWidget(self._heading)
        layout.addSpacing(12)

        self._crud = CrudList(
            self,
            title="Pacientes",
            search_placeholder="Buscar paciente...",
            entity_label="Paciente",
            entity_label_lower="paciente",
            db_get_all=self._mw.services.paciente.all_with_last_registro,
            db_create=self._mw.services.paciente.create,
            db_update=lambda pid, name: self._mw.services.paciente.update(pid, name=name),
            db_delete=self._mw.services.paciente.delete,
            delete_in_use_msg="Não é possível excluir: paciente com registros",
            count_label=self._heading,
            secondary_header="Último registro",
            secondary_value=_format_last_registro,
            secondary_sort_key=lambda p: p.last_registro_date or "",
            on_activate=lambda pid: self._mw.navigate_to("patient", paciente_id=pid, return_to="pacientes"),
        )
        layout.addWidget(self._crud.widget)

        self._shortcut_searches = [
            ("Buscar paciente...", self._crud.search),
        ]
