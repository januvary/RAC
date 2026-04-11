#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry Page — record creation and editing
"""

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QCheckBox, QDialog,
    QSizePolicy, QFrame,
)
from PySide6.QtCore import Qt

from src.gui.components import (
    SectionLabel, HeadingLabel, Separator, SearchableComboBox, TipoLabel,
    FlatButton, PositiveButton, NegativeButton, PrimaryButton,
    DestructiveButton, ToastLabel,
)
from src.gui.constants import TIPO_HEX
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel


class EntryPage(QWidget):
    def __init__(self, main_window, tipo: str, edit_id: int | None = None):
        super().__init__()
        self._mw = main_window
        self._tipo = tipo
        self._edit_id = edit_id
        self._registro = None
        self._selected_items: list[dict] = []

        if edit_id:
            self._registro = self._mw.db.get_registro_by_id(int(edit_id))

        self._mw.state.set_current_tipo(tipo)
        self._mw.state.set_editing_registro(self._registro)
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

        self._build_header(layout)
        layout.addSpacing(16)

        layout.addWidget(SectionLabel("Paciente"))
        layout.addSpacing(6)
        self._build_patient_section(layout)
        layout.addSpacing(16)

        layout.addWidget(SectionLabel("Itens"))
        layout.addSpacing(6)
        self._build_items_section(layout)
        layout.addSpacing(24)

        self._build_action_bar(layout)

        outer.addWidget(container, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _build_header(self, layout: QVBoxLayout):
        tipo_label = TipoLabel(self._tipo)

        h = QHBoxLayout()
        h.setSpacing(8)

        malote = self._mw.state.get_active_malote()
        malote_text = _format_malote_date(malote) if malote else ""
        malote_label = QLabel(malote_text)
        malote_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        h.addWidget(malote_label)
        h.addStretch()
        h.addWidget(tipo_label)

        layout.addLayout(h)

    def _build_patient_section(self, layout: QVBoxLayout):
        h = QHBoxLayout()
        h.setSpacing(8)

        pacientes = self._mw.db.search_pacientes("", limit=1000)
        options = {str(p["id"]): p["name"] for p in pacientes}

        self._paciente_combo = SearchableComboBox("Nome do Paciente")
        self._paciente_combo.set_options(options)

        if self._registro and self._registro.get("paciente_id"):
            self._paciente_combo.set_current_by_data(
                str(self._registro["paciente_id"])
            )

        self._paciente_combo.selection_changed.connect(self._on_paciente_selected)
        h.addWidget(self._paciente_combo)

        btn_new = PrimaryButton("+ Novo")
        btn_new.setFixedWidth(80)
        btn_new.clicked.connect(self._create_patient_inline)
        h.addWidget(btn_new)

        layout.addLayout(h)

    def _build_items_section(self, layout: QVBoxLayout):
        self._items_container = QVBoxLayout()
        self._items_container.setSpacing(6)
        layout.addLayout(self._items_container)

        add_btn = FlatButton("+ Adicionar Item")
        add_btn.clicked.connect(lambda: self._add_item_row())
        layout.addWidget(add_btn)

        if self._registro:
            items = self._mw.db.get_items_for_registro(self._registro["id"])
            for item in items:
                self._add_item_row(prefill=item)
        else:
            self._add_item_row()

    def _build_action_bar(self, layout: QVBoxLayout):
        h = QHBoxLayout()
        h.setSpacing(8)

        back_btn = FlatButton("Voltar")
        back_btn.clicked.connect(lambda: self._mw.navigate_to("start"))
        h.addWidget(back_btn)
        h.addStretch()

        auto_return = self._mw.state.get_auto_return()
        self._auto_switch = QCheckBox("Auto-retorno")
        self._auto_switch.setChecked(auto_return)
        self._auto_switch.stateChanged.connect(
            lambda: self._mw.state.set_auto_return(self._auto_switch.isChecked())
        )
        h.addWidget(self._auto_switch)

        if self._registro:
            delete_btn = NegativeButton("Excluir")
            delete_btn.clicked.connect(self._confirm_delete)
            h.addWidget(delete_btn)

        save_btn = PositiveButton("Salvar")
        save_btn.setMinimumWidth(100)
        save_btn.clicked.connect(self._on_save)
        h.addWidget(save_btn)

        layout.addLayout(h)

    def _add_item_row(self, prefill: dict | None = None):
        all_items = self._mw.db.get_all_items()
        item_options = {str(i["id"]): i["name"] for i in all_items}

        row_frame = QFrame()
        row_frame.setProperty("itemrow", True)
        row_h = QHBoxLayout(row_frame)
        row_h.setContentsMargins(6, 2, 6, 2)
        row_h.setSpacing(6)

        item_data = {"id": None}

        combo = SearchableComboBox("Buscar item...")
        combo.set_options(item_options)
        if prefill:
            iid = str(prefill.get("item_id", prefill.get("id")))
            combo.set_current_by_data(iid)
            item_data["id"] = int(iid)

        combo.selection_changed.connect(
            lambda val, d=item_data: d.update({"id": int(val) if val else None})
        )
        row_h.addWidget(combo)

        remove_btn = QPushButton("\u00d7")
        remove_btn.setProperty("btnrole", "remove")
        remove_btn.setFixedSize(28, 28)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.clicked.connect(
            lambda checked=False, d=item_data, f=row_frame: self._remove_item(d, f)
        )
        row_h.addWidget(remove_btn)

        self._items_container.addWidget(row_frame)
        self._selected_items.append(item_data)

    def _remove_item(self, item_data: dict, frame: QFrame):
        if item_data in self._selected_items:
            self._selected_items.remove(item_data)
        frame.setParent(None)
        frame.deleteLater()

    def _on_paciente_selected(self, data):
        if not data or self._registro:
            return
        try:
            paciente_id = int(data)
        except (ValueError, TypeError):
            return
        self._load_patient_items(paciente_id)

    def _load_patient_items(self, paciente_id: int):
        self._selected_items.clear()
        while self._items_container.count():
            w = self._items_container.takeAt(0).widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        patient_items = self._mw.db.get_unique_items_for_paciente(paciente_id)
        if not patient_items:
            self._add_item_row()
        else:
            for item in patient_items:
                self._add_item_row(prefill=item)

    def _create_patient_inline(self):
        name = self._paciente_combo.current_text().strip()
        if not name:
            self._toast("Digite o nome do paciente", "warning")
            return
        try:
            paciente = self._mw.db.create_paciente(name)
            pid = str(paciente["id"])
            self._paciente_combo.add_option(pid, name)
            self._paciente_combo.set_current_by_data(pid)
            self._toast(f"Paciente criado: {name}", "positive")
        except Exception as e:
            ErrorHandler.handle_error(e, context=ErrorContext.DATABASE, show_dialog=False)
            self._toast(f"Erro: {e}", "negative")

    def _on_save(self):
        pid = self._paciente_combo.current_data()
        if not pid:
            self._toast("Selecione um paciente", "warning")
            return

        malote = self._mw.state.get_active_malote()
        if not malote:
            self._toast("Nenhum malote ativo", "warning")
            return

        item_ids = [i["id"] for i in self._selected_items if i.get("id") is not None]

        try:
            paciente_id = int(pid)

            if self._registro:
                self._mw.db.update_registro(self._registro["id"], paciente_id=paciente_id)
                reg_id = self._registro["id"]
            else:
                new_reg = self._mw.db.create_registro(self._tipo, paciente_id, malote["id"])
                reg_id = new_reg["id"]

            if item_ids:
                self._mw.db.set_registro_items(reg_id, item_ids)

            self._mw.state.notify_registro_saved({"id": reg_id, "tipo": self._tipo})
            self._toast("Registro salvo!", "positive")

            if self._auto_switch.isChecked():
                from PySide6.QtCore import QTimer
                QTimer.singleShot(800, lambda: self._mw.navigate_to("start"))

        except Exception as e:
            ErrorHandler.handle_error(e, context=ErrorContext.REGISTRO, show_dialog=False)
            self._toast(f"Erro ao salvar: {e}", "negative")

    def _confirm_delete(self):
        if not self._registro:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Excluir Registro")
        dlg.setMinimumWidth(340)

        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)

        layout.addWidget(HeadingLabel("Excluir este registro?"))

        sub = QLabel("Esta acao nao pode ser desfeita.")
        sub.setStyleSheet("color: #6B7280; font-size: 13px;")
        layout.addWidget(sub)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = FlatButton("Cancelar")
        cancel.clicked.connect(dlg.reject)
        btn_row.addWidget(cancel)
        delete_btn = DestructiveButton("Excluir")
        delete_btn.clicked.connect(lambda: self._do_delete(dlg))
        btn_row.addWidget(delete_btn)
        layout.addLayout(btn_row)

        dlg.exec()

    def _do_delete(self, dlg: QDialog):
        try:
            self._mw.db.delete_registro(self._registro["id"])
            self._mw.state.notify_registro_deleted(self._registro["id"])
            dlg.accept()
            self._toast("Registro excluido", "info")
            from PySide6.QtCore import QTimer
            QTimer.singleShot(800, lambda: self._mw.navigate_to("start"))
        except Exception as e:
            ErrorHandler.handle_error(e, context=ErrorContext.REGISTRO, show_dialog=False)
            self._toast(f"Erro: {e}", "negative")

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


def _format_malote_date(malote: dict | None) -> str:
    if not malote:
        return "?"
    try:
        dt = datetime.fromisoformat(malote["date"])
        return dt.strftime("%d/%m/%Y")
    except (ValueError, KeyError):
        return malote.get("date", "?")
