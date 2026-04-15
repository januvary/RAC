#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry Page — record creation and editing
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QDialog,
    QSizePolicy,
    QFrame,
)
from PySide6.QtCore import Qt, QTimer

from src.gui.components import (
    SectionLabel,
    HeadingLabel,
    SearchableComboBox,
    TipoCombo,
    MaloteLabel,
    FlatButton,
    PositiveButton,
    NegativeButton,
    DestructiveButton,
    ToastMixin,
)
from src.models import Registro
from src.services.registro_service import RegistroService
from src.services.exceptions import ValidationError, DuplicateRecordError
from src.utils.error_handler import ErrorHandler, ErrorContext
from src.utils.text_utils import to_upper_normalized
from src.gui.styles import colors


class EntryPage(QWidget, ToastMixin):
    def __init__(self, main_window, tipo: str, edit_id: int | None = None):
        super().__init__()
        self._mw = main_window
        self._tipo = tipo
        self._edit_id: int | None = edit_id
        self._edit_registro: Registro | None = None
        self._focus_index: int = -1

        if edit_id:
            self._edit_registro = self._mw.db.get_registro_by_id(edit_id)

        self._mw.state.set_current_tipo(tipo)
        self._build_ui()

    @property
    def _is_editing(self) -> bool:
        return self._edit_id is not None

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(48, 32, 48, 32)
        outer.setSpacing(0)
        outer.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        container = QWidget()
        container.setMaximumWidth(720)
        container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )
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

        if self._edit_registro:
            malote = self._mw.db.get_malote_by_id(self._edit_registro.malote_id)
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

        self._status_label = QLabel()
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h.addWidget(self._status_label)

        h.addStretch()
        h.addWidget(self._malote_label, 0, Qt.AlignmentFlag.AlignTop)

        layout.addLayout(h)
        self._update_registro_status(self._is_editing)

    def _build_patient_section(self, layout: QVBoxLayout):
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        self._paciente_combo = SearchableComboBox(
            "Nome do Paciente", on_search=self._search_pacientes
        )

        if self._edit_registro and self._edit_registro.paciente_id:
            paciente = self._mw.db.get_paciente_by_id(self._edit_registro.paciente_id)
            if paciente:
                self._paciente_combo.set_options({str(paciente.id): paciente.name})
                self._paciente_combo.set_current_by_data(str(paciente.id))

        self._paciente_combo.selection_changed.connect(self._on_paciente_selected)
        self._paciente_combo.exact_match_changed.connect(self._on_paciente_selected)
        h.addWidget(self._paciente_combo)

        layout.addLayout(h)

    def _search_pacientes(self, query: str) -> dict[str, str]:
        pacientes = self._mw.db.search_pacientes(query, limit=30)
        return {str(p.id): p.name for p in pacientes}

    def _search_items(self, query: str) -> dict[str, str]:
        normalized = to_upper_normalized(query)
        return {k: v for k, v in self._catalog_options.items() if normalized in v}

    def _build_items_section(self, layout: QVBoxLayout):
        self._catalog_options = {str(i.id): i.name for i in self._mw.db.get_all_items()}

        self._items_container = QVBoxLayout()
        self._items_container.setSpacing(0)
        layout.addLayout(self._items_container)

        add_btn = FlatButton("+ Adicionar Item")
        add_btn.clicked.connect(self._add_item_row)
        layout.addWidget(add_btn)

        if self._edit_registro:
            items = self._mw.db.get_items_for_registro(self._edit_registro.id)
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
        if self._edit_registro and self._edit_registro.waiting_docs:
            self._docs_check.setChecked(True)
        h.addWidget(self._docs_check)

        h.addStretch()

        self._auto_switch = QCheckBox()
        self._auto_switch.setChecked(not self._mw.state.get_auto_return())
        self._auto_switch.stateChanged.connect(
            lambda: self._mw.state.set_auto_return(not self._auto_switch.isChecked())
        )
        h.addWidget(self._auto_switch)

        if self._is_editing:
            self._delete_btn = NegativeButton("Excluir")
            self._delete_btn.clicked.connect(self._confirm_delete)
            h.addWidget(self._delete_btn)
        else:
            self._delete_btn = None

        save_btn = PositiveButton("Salvar")
        save_btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        save_btn.clicked.connect(self._on_save)
        h.addWidget(save_btn)

        layout.addLayout(h)

    def _update_registro_status(self, editing: bool):
        c = colors()
        if editing:
            self._status_label.setText("Editando registro")
            self._status_label.setStyleSheet(
                f"color: {c['text_secondary']}; font-size: 12px; font-style: italic;"
            )
        else:
            self._status_label.setText("Novo registro")
            self._status_label.setStyleSheet(
                f"color: {c['text_secondary']}; font-size: 12px; font-style: italic;"
            )

    def _add_item_row(self, item_id: int | None = None):
        row_frame = QFrame()
        row_frame.setProperty("itemrow", True)
        row_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row_h = QHBoxLayout(row_frame)
        row_h.setContentsMargins(6, 2, 6, 2)
        row_h.setSpacing(6)

        combo = SearchableComboBox("Buscar item...", on_search=self._search_items)
        combo.set_options(self._catalog_options)
        if item_id is not None:
            combo.set_current_by_data(str(item_id))
        row_h.addWidget(combo)

        remove_btn = QPushButton("\u00d7")
        remove_btn.setProperty("btnrole", "remove")
        remove_btn.setFixedSize(28, 28)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.clicked.connect(
            lambda _checked=False, f=row_frame: self._remove_item(f)
        )
        row_h.addWidget(remove_btn)

        self._items_container.addWidget(row_frame)
        return combo

    def _remove_item(self, frame: QFrame):
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
        while self._items_container.count():
            item = self._items_container.takeAt(0)
            w = item.widget() if item else None
            if w:
                w.setParent(None)
                w.deleteLater()

    def _collect_item_ids(self) -> list[int]:
        ids = []
        for i in range(self._items_container.count()):
            item = self._items_container.itemAt(i)
            if not item:
                continue
            frame = item.widget()
            if not frame:
                continue
            combo = frame.findChild(SearchableComboBox)
            data = combo.current_data() if combo else None
            if data:
                ids.append(int(data))
        return ids

    def _load_items_for_context(self, paciente_id: int):
        malote = self._mw.state.get_active_malote()
        tipo = self._tipo_combo.current_tipo()

        existing_reg = None
        if malote:
            existing_reg = self._mw.db.find_registro(tipo, paciente_id, malote.id)

        self._clear_item_rows()
        if existing_reg:
            self._update_registro_status(True)
            items = self._mw.db.get_items_for_registro(existing_reg.id)
            if items:
                for item in items:
                    self._add_item_row(item_id=item.item_id)
            else:
                self._add_item_row()
        else:
            self._update_registro_status(False)
            patient_items = self._mw.db.get_items_for_paciente(paciente_id)
            if patient_items:
                for item in patient_items:
                    self._add_item_row(item_id=item.id)
            else:
                self._add_item_row()

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
        item_ids = self._collect_item_ids()
        tipo = self._tipo_combo.current_tipo()
        waiting_docs = self._docs_check.isChecked()

        malote = self._mw.state.get_active_malote()
        if not malote:
            self._toast("Selecione um malote", "warning")
            return

        paciente_name = self._paciente_combo.current_text().strip()
        paciente_id = self._resolve_current_patient()

        service = RegistroService(self._mw.db)

        try:
            result = service.save(
                tipo=tipo,
                paciente_name=paciente_name,
                malote_id=malote.id,
                item_ids=item_ids,
                edit_id=self._edit_id,
                waiting_docs=waiting_docs,
                paciente_id=paciente_id,
            )
        except ValidationError as e:
            self._toast(str(e), "warning")
            return
        except DuplicateRecordError:
            self._toast("Já existe um registro com esse tipo/paciente/malote", "warning")
            return
        except Exception as e:
            ErrorHandler.handle_error(
                e, context=ErrorContext.REGISTRO, show_dialog=False
            )
            self._toast(f"Erro ao salvar: {e}", "negative")
            return

        msg = "Registro editado!" if result.is_update else "Registro salvo!"
        self._toast(msg, "positive")

        if not self._auto_switch.isChecked():
            QTimer.singleShot(600, lambda: self._mw.navigate_to("start"))
        else:
            QTimer.singleShot(600, self._reset_form)

    def _reset_form(self):
        self._edit_id = None
        self._edit_registro = None
        self._paciente_combo.set_options({})
        self._paciente_combo.clear()
        self._clear_item_rows()
        self._add_item_row()
        self._docs_check.setChecked(False)
        self._update_registro_status(False)
        if self._delete_btn:
            self._delete_btn.hide()

    def _confirm_delete(self):
        if not self._edit_id:
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
        if not self._edit_id:
            return
        try:
            service = RegistroService(self._mw.db)
            service.delete(self._edit_id)
            dlg.accept()
            self._toast("Registro excluido", "info")
            QTimer.singleShot(800, lambda: self._mw.navigate_to("start"))
        except Exception as e:
            ErrorHandler.handle_error(
                e, context=ErrorContext.REGISTRO, show_dialog=False
            )
            self._toast(f"Erro: {e}", "negative")
