#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry Page — record creation and editing
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QDialog,
    QSizePolicy, QFrame,
)
from PySide6.QtCore import Qt

from src.gui.components import (
    SectionLabel, HeadingLabel, SearchableComboBox, TipoCombo,
    MaloteLabel, FlatButton, PositiveButton, NegativeButton,
    DestructiveButton, ToastLabel, show_toast,
)
from src.models import Registro, RegistroItem, ItemCatalog
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel
from src.gui.styles import colors


class EntryPage(QWidget):
    def __init__(self, main_window, tipo: str, edit_id: int | None = None):
        super().__init__()
        self._mw = main_window
        self._tipo = tipo
        self._edit_id = edit_id
        self._registro: Registro | None = None
        self._selected_items: list[dict] = []
        self._focus_index: int = -1

        if edit_id:
            self._registro = self._mw.db.get_registro_by_id(int(edit_id))

        self._mw.state.set_current_tipo(tipo)
        self._mw.state.set_editing_registro(self._registro)
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

        self._build_header(layout)
        layout.addSpacing(20)

        layout.addWidget(SectionLabel("Paciente"))
        layout.addSpacing(8)
        self._build_patient_section(layout)
        layout.addSpacing(20)

        layout.addWidget(SectionLabel("Itens"))
        layout.addSpacing(8)
        self._build_items_section(layout)
        layout.addSpacing(28)

        self._build_action_bar(layout)

        outer.addWidget(container)

    def _build_header(self, layout: QVBoxLayout):
        self._tipo_combo = TipoCombo(self._tipo)

        if self._registro:
            malote = self._mw.db.get_malote_by_id(self._registro.malote_id)
            if malote:
                self._mw.state.set_active_malote(malote)

        self._malote_label = MaloteLabel(self._mw)

        self._tipo_combo.tipo_changed.connect(self._on_context_changed)
        self._malote_label.malote_changed.connect(self._on_context_changed)

        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        h.addWidget(self._tipo_combo, 0, Qt.AlignmentFlag.AlignTop)
        h.addStretch()
        h.addWidget(self._malote_label, 0, Qt.AlignmentFlag.AlignTop)

        layout.addLayout(h)

    def _build_patient_section(self, layout: QVBoxLayout):
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        self._paciente_combo = SearchableComboBox(
            "Nome do Paciente", on_search=self._search_pacientes
        )

        if self._registro and self._registro.paciente_id:
            paciente = self._mw.db.get_paciente_by_id(
                self._registro.paciente_id
            )
            if paciente:
                self._paciente_combo.set_options(
                    {str(paciente.id): paciente.name}
                )
                self._paciente_combo.set_current_by_data(
                    str(paciente.id)
                )

        self._paciente_combo.selection_changed.connect(self._on_paciente_selected)
        self._paciente_combo.exact_match_changed.connect(self._on_paciente_selected)
        h.addWidget(self._paciente_combo)

        layout.addLayout(h)

    def _search_pacientes(self, query: str) -> dict[str, str]:
        pacientes = self._mw.db.search_pacientes(query, limit=30)
        return {str(p.id): p.name for p in pacientes}

    def _build_items_section(self, layout: QVBoxLayout):
        self._catalog_options = {
            str(i.id): i.name for i in self._mw.db.get_all_items()
        }

        self._items_container = QVBoxLayout()
        self._items_container.setSpacing(0)
        layout.addLayout(self._items_container)

        add_btn = FlatButton("+ Adicionar Item")
        add_btn.clicked.connect(lambda: self._add_item_row())
        layout.addWidget(add_btn)

        if self._registro:
            items = self._mw.db.get_items_for_registro(self._registro.id)
            for item in items:
                self._add_item_row(item_id=item.item_id)
        else:
            self._add_item_row()

    def _build_action_bar(self, layout: QVBoxLayout):
        h = QHBoxLayout()
        h.setSpacing(8)

        back_btn = FlatButton("Voltar")
        back_btn.clicked.connect(lambda: self._mw.navigate_to("start"))
        h.addWidget(back_btn)
        h.addStretch()

        self._docs_check = QCheckBox("Esperando documentos")
        if self._registro and self._registro.waiting_docs:
            self._docs_check.setChecked(True)
        h.addWidget(self._docs_check)

        h.addStretch()

        self._auto_switch = QCheckBox()
        self._auto_switch.setChecked(not self._mw.state.get_auto_return())
        self._auto_switch.stateChanged.connect(
            lambda: self._mw.state.set_auto_return(not self._auto_switch.isChecked())
        )
        h.addWidget(self._auto_switch)

        if self._registro:
            delete_btn = NegativeButton("Excluir")
            delete_btn.clicked.connect(self._confirm_delete)
            h.addWidget(delete_btn)

        save_btn = PositiveButton("Salvar")
        save_btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        save_btn.clicked.connect(self._on_save)
        h.addWidget(save_btn)

        layout.addLayout(h)

    def _add_item_row(self, item_id: int | None = None):
        item_options = self._catalog_options

        row_frame = QFrame()
        row_frame.setProperty("itemrow", True)
        row_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row_h = QHBoxLayout(row_frame)
        row_h.setContentsMargins(6, 2, 6, 2)
        row_h.setSpacing(6)

        item_data: dict[str, int | None] = {"id": None}

        combo = SearchableComboBox("Buscar item...")
        combo.set_options(item_options)
        if item_id is not None:
            combo.set_current_by_data(str(item_id))
            item_data["id"] = item_id

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
        if not data:
            return
        try:
            paciente_id = int(data)
        except (ValueError, TypeError):
            return
        self._load_items_for_context(paciente_id)

    def _on_context_changed(self, *_):
        paciente_id = self._resolve_current_patient()
        if paciente_id is None:
            return
        self._load_items_for_context(paciente_id)

    def _resolve_current_patient(self) -> int | None:
        pid = self._paciente_combo.current_data()
        if not pid:
            name = self._paciente_combo.current_text().strip()
            if name:
                existing = self._mw.db.find_paciente_by_name(name)
                if existing:
                    pid = str(existing.id)
        if not pid:
            return None
        try:
            return int(pid)
        except (ValueError, TypeError):
            return None

    def _clear_item_rows(self):
        self._selected_items.clear()
        while self._items_container.count():
            w = self._items_container.takeAt(0).widget()
            if w:
                w.setParent(None)
                w.deleteLater()

    def _load_items_for_context(self, paciente_id: int):
        malote = self._mw.state.get_active_malote()
        tipo = self._tipo_combo.current_tipo()

        existing_reg = None
        if malote:
            existing_reg = self._mw.db.find_registro(tipo, paciente_id, malote.id)

        if existing_reg:
            self._registro = existing_reg
            items = self._mw.db.get_items_for_registro(existing_reg.id)
            self._clear_item_rows()
            if not items:
                self._add_item_row()
            else:
                for item in items:
                    self._add_item_row(item_id=item.item_id)
        else:
            self._registro = None
            self._clear_item_rows()
            patient_items = self._mw.db.get_items_for_paciente(paciente_id)
            if not patient_items:
                self._add_item_row()
            else:
                for item in patient_items:
                    self._add_item_row(item_id=item.id)

    def focus_next_field(self):
        total_fields = 1 + self._items_container.count()
        self._focus_index = (self._focus_index + 1) % total_fields

        if self._focus_index == 0:
            self._paciente_combo.focus_search()
            return

        row_idx = self._focus_index - 1
        if row_idx < self._items_container.count():
            item = self._items_container.itemAt(row_idx)
            frame = item.widget() if item else None
            if frame:
                combo = frame.findChild(SearchableComboBox)
                if combo:
                    combo.focus_search()
                    return

        self._focus_index = 0
        self._paciente_combo.focus_search()

    def _on_save(self):
        item_ids = [i["id"] for i in self._selected_items if i.get("id") is not None]
        tipo = self._tipo_combo.current_tipo()
        waiting_docs = self._docs_check.isChecked()

        malote = self._mw.state.get_active_malote()
        if not malote:
            self._toast("Selecione um malote", "warning")
            return
        malote_id = malote.id

        paciente_id = self._resolve_current_patient()
        if paciente_id is None:
            name = self._paciente_combo.current_text().strip()
            if not name:
                self._toast("Selecione ou digite o nome do paciente", "warning")
                return
            try:
                paciente = self._mw.db.create_paciente(name)
                paciente_id = paciente.id
            except Exception as e:
                ErrorHandler.handle_error(e, context=ErrorContext.DATABASE, show_dialog=False)
                self._toast(f"Erro ao criar paciente: {e}", "negative")
                return

        try:
            is_update = False
            if self._registro:
                is_update = True
                self._mw.db.update_registro(
                    self._registro.id, tipo=tipo, paciente_id=paciente_id,
                    malote_id=malote_id, waiting_docs=waiting_docs,
                )
                reg_id = self._registro.id
            else:
                existing = self._mw.db.find_registro(tipo, paciente_id, malote_id)
                if existing:
                    is_update = True
                    self._mw.db.update_registro(
                        existing.id, tipo=tipo, paciente_id=paciente_id,
                        malote_id=malote_id, waiting_docs=waiting_docs,
                    )
                    reg_id = existing.id
                    self._registro = existing
                else:
                    new_reg = self._mw.db.create_registro(
                        tipo, paciente_id, malote_id,
                        waiting_docs=waiting_docs,
                    )
                    reg_id = new_reg.id
                    self._registro = new_reg

            self._mw.db.set_registro_items(reg_id, item_ids)

            self._mw.state.notify_registro_saved(Registro(id=reg_id, tipo=tipo))
            msg = "Registro editado!" if is_update else "Registro salvo!"
            self._toast(msg, "positive")

            if not self._auto_switch.isChecked():
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

        c = colors()
        sub = QLabel("Esta acao nao pode ser desfeita.")
        sub.setStyleSheet(f"color: {c['text_secondary']}; font-size: 13px;")
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
        if not self._registro:
            return
        try:
            self._mw.db.delete_registro(self._registro.id)
            self._mw.state.notify_registro_deleted(self._registro.id)
            dlg.accept()
            self._toast("Registro excluido", "info")
            from PySide6.QtCore import QTimer
            QTimer.singleShot(800, lambda: self._mw.navigate_to("start"))
        except Exception as e:
            ErrorHandler.handle_error(e, context=ErrorContext.REGISTRO, show_dialog=False)
            self._toast(f"Erro: {e}", "negative")

    def _toast(self, message: str, kind: str = "info"):
        show_toast(message, kind, self)
