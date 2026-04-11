#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start Page — malote header, search, tipo buttons, export
"""

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QDialog,
    QListWidget, QListWidgetItem, QSizePolicy,
)
from PySide6.QtCore import Qt

from src.gui.components import (
    SectionLabel, HeadingLabel, Separator, SearchableComboBox,
    TipoButton, FlatButton, PositiveButton, PrimaryButton, ToastLabel,
)
from src.gui.constants import TIPO_LABELS
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel


_TIPO_ORDER = ["entrada", "renovacao", "retirada", "urgente"]


class StartPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self._mw = main_window
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 24, 32, 24)
        outer.setSpacing(0)
        outer.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        container = QWidget()
        container.setMaximumWidth(560)
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._build_malote_header(layout)
        layout.addSpacing(20)

        layout.addWidget(SectionLabel("Buscar registro"))
        layout.addSpacing(6)
        self._build_search(layout)
        layout.addSpacing(20)

        layout.addWidget(SectionLabel("Novo registro"))
        layout.addSpacing(6)
        self._build_tipo_grid(layout)
        layout.addSpacing(24)

        self._build_export(layout)

        outer.addWidget(container, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _build_malote_header(self, layout: QVBoxLayout):
        h = QHBoxLayout()
        h.setSpacing(0)

        malote = self._mw.state.get_active_malote()
        display = _format_malote_date(malote) if malote else "Nenhum malote ativo"
        self._malote_label = HeadingLabel(f"Malote  {display}")
        h.addWidget(self._malote_label)
        h.addStretch()

        btn_switch = FlatButton("Trocar")
        btn_switch.clicked.connect(self._show_malote_switcher)
        h.addWidget(btn_switch)

        btn_new = PrimaryButton("+ Novo")
        btn_new.clicked.connect(self._show_new_malote_dialog)
        h.addWidget(btn_new)

        layout.addLayout(h)

    def _build_search(self, layout: QVBoxLayout):
        self._search_combo = SearchableComboBox("Nome do paciente...")
        self._search_combo.selection_changed.connect(self._on_search_select)
        layout.addWidget(self._search_combo)

    def _build_tipo_grid(self, layout: QVBoxLayout):
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)

        for i, tipo_key in enumerate(_TIPO_ORDER):
            row, col = divmod(i, 2)
            btn = TipoButton(tipo_key)
            btn.clicked_tipo.connect(self._on_tipo_click)
            grid.addWidget(btn, row, col)

        layout.addWidget(grid_widget)

    def _build_export(self, layout: QVBoxLayout):
        btn = PositiveButton("Exportar Planilha")
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setFixedHeight(40)
        btn.clicked.connect(self._on_export)
        layout.addWidget(btn)

    def refresh(self):
        malote = self._mw.state.get_active_malote()
        display = _format_malote_date(malote) if malote else "Nenhum malote ativo"
        self._malote_label.setText(f"Malote  {display}")
        self._refresh_search()

    def _refresh_search(self):
        malote = self._mw.state.get_active_malote()
        if not malote:
            self._search_combo.set_options({})
            return
        resultados = self._mw.db.get_registros_by_malote(malote["id"])
        options = {}
        for reg in resultados:
            tipo = TIPO_LABELS.get(reg.get("tipo", ""), "")
            name = reg.get("paciente_name", "")
            options[str(reg["id"])] = f"{name} ({tipo})"
        self._search_combo.set_options(options)

    def _on_search_select(self, data):
        if not data:
            return
        try:
            reg_id = int(data)
            reg = self._mw.db.get_registro_by_id(reg_id)
            if reg:
                tipo = reg.get("tipo", "entrada")
                self._mw.navigate_to("entry", tipo=tipo, edit_id=reg_id)
        except (ValueError, TypeError):
            pass

    def _on_tipo_click(self, tipo_key: str):
        if not self._mw.state.has_active_malote():
            self._toast("Selecione um malote primeiro!", "warning")
            return
        self._mw.navigate_to("entry", tipo=tipo_key)

    def _on_export(self):
        if not self._mw.state.has_active_malote():
            self._toast("Selecione um malote primeiro!", "warning")
            return
        try:
            from src.export.excel_exporter import ExcelExporter
            malote = self._mw.state.get_active_malote()
            exporter = ExcelExporter(self._mw.db)
            result = exporter.export_malote(malote["id"])
            if result:
                self._toast(f"Exportado: {result}", "positive")
            else:
                self._toast("Nenhum registro para exportar", "warning")
        except Exception as e:
            ErrorHandler.handle_error(e, context=ErrorContext.EXPORT, show_dialog=False)
            self._toast(f"Erro ao exportar: {e}", "negative")

    def _show_new_malote_dialog(self):
        dlg = QDialog(self)
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
        create.clicked.connect(lambda: self._create_malote(date_input.text(), dlg))
        btn_row.addWidget(create)
        layout.addLayout(btn_row)

        date_input.returnPressed.connect(lambda: self._create_malote(date_input.text(), dlg))
        dlg.exec()

    def _create_malote(self, text: str, dlg: QDialog):
        iso = _parse_date(text)
        if not iso:
            self._toast("Data invalida. Use dd/mm ou dd/mm/aa", "warning")
            return
        try:
            malote = self._mw.db.create_malote(iso)
            self._mw.state.set_active_malote(malote)
            dlg.accept()
            self._toast(f"Malote criado: {_format_malote_date(malote)}", "positive")
            self.refresh()
        except Exception as e:
            ErrorHandler.handle_error(e, context=ErrorContext.MALOTE, show_dialog=False)
            self._toast(f"Erro: {e}", "negative")

    def _show_malote_switcher(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Malotes")
        dlg.setMinimumWidth(340)
        dlg.setMinimumHeight(200)

        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)

        layout.addWidget(HeadingLabel("Malotes"))

        malotes = self._mw.db.get_all_malotes()
        active = self._mw.state.get_active_malote()

        list_widget = QListWidget()
        for m in malotes:
            display = _format_malote_date(m)
            is_active = active and active["id"] == m["id"]
            prefix = "\u2713 " if is_active else "    "
            item = QListWidgetItem(f"{prefix}{display}")
            item.setData(Qt.ItemDataRole.UserRole, m)
            if is_active:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            list_widget.addItem(item)

        list_widget.itemClicked.connect(
            lambda item: self._select_malote(item.data(Qt.ItemDataRole.UserRole), dlg)
        )
        layout.addWidget(list_widget)

        btn_row = QHBoxLayout()
        new_m = FlatButton("Novo Malote")
        new_m.clicked.connect(lambda: [dlg.reject(), self._show_new_malote_dialog()])
        btn_row.addWidget(new_m)
        btn_row.addStretch()
        close_m = FlatButton("Fechar")
        close_m.clicked.connect(dlg.reject)
        btn_row.addWidget(close_m)
        layout.addLayout(btn_row)

        dlg.exec()

    def _select_malote(self, malote: dict, dlg: QDialog):
        self._mw.state.set_active_malote(malote)
        dlg.accept()
        self._toast(f"Malote: {_format_malote_date(malote)}", "info")
        self.refresh()

    def _toast(self, message: str, kind: str = "info"):
        toast = ToastLabel(message, kind, self.window())
        toast.adjustSize()
        toast.setFixedWidth(min(toast.width() + 32, self.width() - 48))
        toast.move(
            (self.width() - toast.width()) // 2,
            self.height() - toast.height() - 16,
        )
        toast.show()
        toast.raise_()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(3000, toast.deleteLater)


def _parse_date(text: str) -> str | None:
    from datetime import date as date_type
    text = (text or "").strip()
    if not text:
        return None
    today = date_type.today()
    for sep in ["/", "-", "."]:
        if sep in text:
            parts = text.split(sep)
            break
    else:
        return None
    try:
        if len(parts) == 2:
            day, month = int(parts[0]), int(parts[1])
            year = today.year
        elif len(parts) == 3:
            day, month = int(parts[0]), int(parts[1])
            yp = int(parts[2])
            year = 2000 + yp if yp < 100 else yp
        else:
            return None
        return date_type(year, month, day).isoformat()
    except (ValueError, IndexError):
        return None


def _format_malote_date(malote: dict | None) -> str:
    if not malote:
        return "?"
    try:
        dt = datetime.fromisoformat(malote["date"])
        return dt.strftime("%d/%m/%Y")
    except (ValueError, KeyError):
        return malote.get("date", "?")
