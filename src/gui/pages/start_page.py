#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start Page — malote header, search, tipo buttons, export
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QDialog,
    QSizePolicy,
    QFileDialog,
)
from PySide6.QtCore import Qt

from src.gui.components import (
    SectionLabel, HeadingLabel, Separator, SearchableComboBox,
    TipoButton, FlatButton, PositiveButton, PrimaryButton, ToastLabel,
    MaloteLabel, show_toast,
)
from src.gui.constants import TIPO_LABELS
from src.models import Malote
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel
from src.utils.text_utils import parse_date, format_malote_date
from src.export.excel_exporter import ExcelExporter, SavePathError
from pathlib import Path


_TIPO_ORDER = ["entrada", "renovacao", "retirada", "urgente"]


class StartPage(QWidget):
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

        self._build_malote_header(layout)
        layout.addSpacing(20)

        layout.addWidget(SectionLabel("Buscar registro"))
        layout.addSpacing(8)
        self._build_search(layout)
        layout.addSpacing(20)
        layout.addSpacing(8)
        self._build_tipo_grid(layout)
        layout.addSpacing(28)

        self._build_export(layout)

        outer.addWidget(container)

    def _build_malote_header(self, layout: QVBoxLayout):
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        self._malote_label = MaloteLabel(self._mw)
        h.addStretch()
        h.addWidget(self._malote_label, 0, Qt.AlignmentFlag.AlignTop)

        layout.addLayout(h)

    def _build_search(self, layout: QVBoxLayout):
        self._search_combo = SearchableComboBox("Nome do paciente...")
        self._search_combo.selection_changed.connect(self._on_search_select)
        layout.addWidget(self._search_combo)
        self._refresh_search()

    def _build_tipo_grid(self, layout: QVBoxLayout):
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)

        for i, tipo_key in enumerate(_TIPO_ORDER):
            row, col = divmod(i, 2)
            btn = TipoButton(tipo_key)
            btn.clicked_tipo.connect(self._on_tipo_click)
            grid.addWidget(btn, row, col)

        layout.addWidget(grid_widget)

    def _build_export(self, layout: QVBoxLayout):
        preview_btn = PrimaryButton("Visualizar Malote")
        preview_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        preview_btn.setFixedHeight(48)
        preview_btn.clicked.connect(self._on_preview)
        layout.addWidget(preview_btn)
        layout.addSpacing(8)

        btn = PositiveButton("Exportar Planilha")
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setFixedHeight(48)
        btn.clicked.connect(self._on_export)
        layout.addWidget(btn)

    def refresh(self):
        self._malote_label.refresh()
        self._refresh_search()

    def _refresh_search(self):
        malote = self._mw.state.get_active_malote()
        if not malote:
            self._search_combo.set_options({})
            return
        resultados = self._mw.db.get_registros_by_malote(malote.id)
        options = {}
        for reg in resultados:
            tipo = TIPO_LABELS.get(reg.tipo, "")
            name = reg.paciente_name or ""
            options[str(reg.id)] = f"{name} ({tipo})"
        self._search_combo.set_options(options)

    def _on_search_select(self, data):
        if not data:
            return
        try:
            reg_id = int(data)
            reg = self._mw.db.get_registro_by_id(reg_id)
            if reg:
                tipo = reg.tipo
                self._mw.navigate_to("entry", tipo=tipo, edit_id=reg_id)
        except (ValueError, TypeError):
            pass

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
        try:
            malote = self._mw.state.get_active_malote()
            exporter = ExcelExporter(self._mw.db)
            result = exporter.export_malote(malote.id)
            if result:
                self._toast(f"Exportado: {result}", "positive")
            else:
                self._toast("Nenhum registro para exportar", "warning")
        except SavePathError:
            folder = QFileDialog.getExistingDirectory(
                self, "Selecionar pasta para salvar",
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
            ErrorHandler.handle_error(e, context=ErrorContext.EXPORT, show_dialog=False)
            self._toast(f"Erro ao exportar: {e}", "negative")

    def _toast(self, message: str, kind: str = "info"):
        show_toast(message, kind, self)
