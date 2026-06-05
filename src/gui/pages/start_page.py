#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start Page — malote header, search, tipo buttons, export
"""

from contextlib import suppress
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QSizePolicy,
    QFileDialog,
)
from PySide6.QtCore import Qt

from src.gui.widgets import (
    SectionLabel,
    SearchableComboBox,
    TipoButton,
    make_button,
    MaloteLabel,
    ThemeToggleButton,
    BasePage,
)
from src.gui.constants import (
    TIPO_LABELS,
    SHORTCUT_LABELS,
    TIPO_SHORTCUT_KEYS,
    TIPO_SYMBOLS,
)
from andaime.error_handler import ErrorHandler

from src.export.excel_exporter import ExcelExporter, SavePathError
from src.models import Malote
from src.utils.text_utils import format_malote_date


class StartPage(BasePage):
    def __init__(self, main_window):
        super().__init__(main_window)
        self._pre_search_malote = None
        self._build_ui()

    def _build_ui(self):
        layout = self._scaffold()
        self._build_malote_header(layout)
        layout.addSpacing(20)

        layout.addWidget(SectionLabel("Buscar registro"))
        layout.addSpacing(8)
        self._build_search(layout)
        layout.addSpacing(20)
        layout.addWidget(SectionLabel("Criar novo registro"))
        layout.addSpacing(8)
        self._build_tipo_grid(layout)
        layout.addSpacing(28)

        self._build_export(layout)

    def _build_malote_header(self, layout: QVBoxLayout):
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        theme_btn = ThemeToggleButton()
        h.addWidget(theme_btn, 0, Qt.AlignmentFlag.AlignTop)

        self._malote_label = MaloteLabel(self._mw)
        self._malote_label.malote_changed.connect(self.refresh)
        self._mw.theme_changed.connect(self._on_theme_changed)
        h.addStretch()
        h.addWidget(self._malote_label, 0, Qt.AlignmentFlag.AlignTop)

        layout.addLayout(h)

    def _build_search(self, layout: QVBoxLayout):
        self._search_combo = SearchableComboBox(
            "Nome do paciente...", on_search=self._search_registros
        )
        self._search_combo.selection_changed.connect(self._on_search_select)
        layout.addWidget(self._search_combo)
        self._shortcut_searches = [
            ("Nome do paciente...", self._search_combo._line_edit),
        ]

    def _build_tipo_grid(self, layout: QVBoxLayout):
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(5)

        self._tipo_btns: list[TipoButton] = []
        for i, tipo_key in enumerate(TIPO_LABELS):
            row, col = divmod(i, 2)
            btn = TipoButton(tipo_key)
            btn.clicked_tipo.connect(self._on_tipo_click)
            self._tipo_btns.append(btn)
            grid.addWidget(btn, row, col)

        layout.addWidget(grid_widget)

    def _build_export(self, layout: QVBoxLayout):
        self._shortcut_widgets = {}

        row = QHBoxLayout()
        row.setSpacing(4)

        _, preview_label = SHORTCUT_LABELS["preview"]
        preview_btn = make_button(preview_label, "primary")
        preview_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        preview_btn.setFixedHeight(54)
        preview_btn.clicked.connect(self._on_preview)
        row.addWidget(preview_btn)
        self._shortcut_widgets["preview"] = preview_btn

        _, export_label = SHORTCUT_LABELS["export"]
        btn = make_button(export_label, "positive")
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setFixedHeight(54)
        btn.clicked.connect(self._on_export)
        row.addWidget(btn)
        self._shortcut_widgets["export"] = btn

        layout.addLayout(row)
        layout.addSpacing(7)

        manage_btn = make_button("Gerenciar Listas", "flat")
        manage_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        manage_btn.setFixedHeight(54)
        manage_btn.clicked.connect(self._on_lists)
        layout.addWidget(manage_btn)
        self._shortcut_widgets["lists"] = manage_btn

        stats_btn = make_button("Estatisticas", "flat")
        stats_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        stats_btn.setFixedHeight(54)
        stats_btn.clicked.connect(self._on_stats)
        layout.addWidget(stats_btn)
        self._shortcut_widgets["stats"] = stats_btn

    def refresh(self):
        if self._pre_search_malote is not None:
            self._mw.state.set_active_malote(self._pre_search_malote)
            self._pre_search_malote = None
        self._malote_label.refresh()
        self._search_combo.set_options({})
        self._search_combo.clear()

    def _search_registros(self, query: str) -> dict[str, str]:
        if not query:
            return {}
        malote = self._mw.state.get_active_malote()
        active_id = malote.id if malote else None
        resultados = self._mw.db.search_registros_by_patient(query, active_id)
        return {
            str(
                r.id
            ): f"{r.paciente_name or ''} ({TIPO_LABELS.get(r.tipo, '')}) — {format_malote_date(Malote(date=r.malote_date or ''))}"
            for r in resultados
        }

    def _on_search_select(self, data):
        if not data:
            return
        with suppress(ValueError, TypeError):
            reg_id = int(data)
            reg = self._mw.db.get_registro_by_id(reg_id)
            if reg:
                self._pre_search_malote = self._mw.state.get_active_malote()
                tipo = reg.tipo
                self._mw.navigate_to("entry", tipo=tipo, edit_id=reg_id)

    def _on_tipo_click(self, tipo_key: str):
        if not self._mw.state.has_active_malote():
            self._toast("Selecione um malote primeiro!", "warning")
            return
        self._mw.navigate_to("entry", tipo=tipo_key)

    def _on_preview(self):
        if not self._mw.state.has_active_malote():
            self._toast("Selecione um malote primeiro!", "warning")
            return
        self._mw.navigate_to("preview")

    def _on_export(self):
        if not self._mw.state.has_active_malote():
            self._toast("Selecione um malote primeiro!", "warning")
            return
        malote = self._mw.state.get_active_malote()
        exporter = ExcelExporter(self._mw.db)
        try:
            result = exporter.export_malote(malote.id)
            if result:
                self._toast(f"Exportado: {result}", "positive")
            else:
                self._toast("Nenhum registro para exportar", "warning")
        except SavePathError:
            folder = QFileDialog.getExistingDirectory(
                self,
                "Selecionar pasta para salvar",
                str(Path.home()),
            )
            if not folder:
                return
            self._mw.config.set("save_path", folder)
            try:
                result = exporter.export_malote(malote.id)
                if result:
                    self._toast(f"Exportado: {result}", "positive")
                else:
                    self._toast("Nenhum registro para exportar", "warning")
            except SavePathError as e:
                self._toast(f"Erro ao exportar: {e}", "negative")
        except Exception as e:
            ErrorHandler.handle_error(e, context="Exportação", show_dialog=False)
            self._toast(f"Erro ao exportar: {e}", "negative")

    def _on_lists(self):
        self._mw.navigate_to("lists")

    def _on_stats(self):
        self._mw.navigate_to("stats")

    def _on_theme_changed(self):
        self._malote_label.refresh()
        for btn in self._tipo_btns:
            btn.refresh_style()

    def set_shortcuts_visible(self, show: bool):
        super().set_shortcuts_visible(show)
        for btn in self._tipo_btns:
            label = TIPO_LABELS[btn.tipo_key]
            symbol = TIPO_SYMBOLS[btn.tipo_key]
            if show:
                key = TIPO_SHORTCUT_KEYS[btn.tipo_key]
                btn.setText(f"{symbol}  {label}  ({key})")
            else:
                btn.setText(f"{symbol}  {label}")
        self._malote_label.set_shortcut_hint_visible(show)
