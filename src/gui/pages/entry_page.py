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
    QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer

from src.gui.widgets import (
    SectionLabel,
    SearchableComboBox,
    TipoCombo,
    MaloteLabel,
    make_button,
    BasePage,
    delete_registro_with_undo,
)
from src.models import Registro
from src.services.registro_service import RegistroService
from src.services.exceptions import ValidationError, DuplicateRecordError
from andaime.error_handler import ErrorHandler
from andaime.text import to_upper_normalized

from src.gui.styles import colors


class EntryPage(BasePage):
    def __init__(
        self,
        main_window,
        tipo: str,
        edit_id: int | None = None,
        return_to: str = "start",
    ):
        super().__init__(main_window)
        self._tipo = tipo
        self._edit_id: int | None = edit_id
        self._edit_registro: Registro | None = None
        self._focus_index: int = -1
        self._return_to = return_to
        self._shortcut_widgets: dict[str, QPushButton | QLabel | QCheckBox] = {}
        self._delete_btn: QPushButton | None = None

        if edit_id:
            self._edit_registro = self._mw.db.get_registro_by_id(edit_id)

        self._mw.state.set_current_tipo(tipo)
        self._build_ui()

    @property
    def _is_editing(self) -> bool:
        return self._edit_id is not None

    def _build_ui(self):
        layout = self._scaffold()
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

        QTimer.singleShot(0, self._paciente_combo.focus_search)

    def _build_header(self, layout: QVBoxLayout):
        self._tipo_combo = TipoCombo(self._tipo)

        if self._edit_registro:
            malote = self._mw.db.get_malote_by_id(self._edit_registro.malote_id)
            if malote:
                self._mw.state.set_active_malote(malote)

        self._malote_label = MaloteLabel(self._mw)

        self._tipo_combo.tipo_changed.connect(self._on_context_changed)
        self._malote_label.malote_changed.connect(self._on_context_changed)

        h = self._add_back_button(layout, target=self._return_to)
        h.addWidget(self._tipo_combo, 0, Qt.AlignmentFlag.AlignVCenter)
        h.addStretch()
        h.addWidget(self._malote_label, 0, Qt.AlignmentFlag.AlignTop)

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

        self._shortcut_searches = [
            ("Nome do Paciente", self._paciente_combo._line_edit),
        ]

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
        self._items_container.setSpacing(4)
        layout.addLayout(self._items_container)

        layout.addSpacing(4)
        add_btn = make_button("+ Adicionar Item", "flat")
        add_btn.clicked.connect(self._add_item_row)
        self._shortcut_widgets["add_item"] = add_btn
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

        self._docs_check = QCheckBox("Esperando documentos")
        self._docs_check.setToolTip("Exclui este registro da planilha exportada.")
        if self._edit_registro and self._edit_registro.waiting_docs:
            self._docs_check.setChecked(True)
        h.addWidget(self._docs_check)
        self._shortcut_widgets["toggle_docs"] = self._docs_check

        h.addStretch()

        self._status_label = QLabel()
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h.addWidget(self._status_label)

        h.addStretch()

        stay_label = QLabel("Ficar nesta tela")
        c = colors()
        stay_label.setStyleSheet(
            f"color: {c['text_secondary']}; font-size: 12px; border: none;"
        )
        h.addWidget(stay_label)
        self._shortcut_widgets["toggle_stay"] = stay_label

        self._auto_switch = QCheckBox()
        self._auto_switch.setChecked(self._mw.state.get_stay_on_page())
        self._auto_switch.stateChanged.connect(
            lambda: self._mw.state.set_stay_on_page(self._auto_switch.isChecked())
        )
        h.addWidget(self._auto_switch)

        if self._is_editing:
            self._delete_btn = make_button("Excluir", "negative")
            self._delete_btn.clicked.connect(self._confirm_delete)
            h.addWidget(self._delete_btn)
        else:
            self._delete_btn = None

        save_btn = make_button("Salvar", "positive")
        save_btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        save_btn.clicked.connect(self._on_save)
        h.addWidget(save_btn)
        self._shortcut_widgets["save"] = save_btn

        layout.addLayout(h)
        self._update_registro_status(self._is_editing)

    def set_shortcuts_visible(self, show: bool):
        super().set_shortcuts_visible(show)
        self._malote_label.set_shortcut_hint_visible(show)

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

    def _add_item_row(self, item_id: int | None = None, process_group: int = 1):
        row = QWidget()
        row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row_h = QHBoxLayout(row)
        row_h.setContentsMargins(0, 0, 0, 0)
        row_h.setSpacing(2)

        group_btn = make_button(str(process_group), "positive")
        group_btn.setFixedWidth(40)
        group_btn.setStyleSheet("padding: 9px 0; font-size: 14px; font-weight: 600;")
        group_btn.setToolTip("Grupo do item (clique p/ alterar)")
        group_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pg = process_group

        def _cycle_group(_checked=False, _btn=group_btn):
            nonlocal pg
            pg = (pg % 5) + 1
            _btn.setText(str(pg))

        group_btn.clicked.connect(_cycle_group)
        row_h.addWidget(group_btn)

        combo = SearchableComboBox(
            "Buscar item...",
            on_search=self._search_items,
            on_delete_empty=lambda w=row: self._remove_item(w),
        )
        combo.set_options(self._catalog_options)
        if item_id is not None:
            combo.set_current_by_data(str(item_id))
        row_h.addWidget(combo)

        remove_btn = make_button("\u00d7", "positive")
        remove_btn.setFixedWidth(40)
        remove_btn.setStyleSheet("padding: 9px 0; font-size: 16px; font-weight: 600;")
        remove_btn.setToolTip("Remover item")
        remove_btn.clicked.connect(lambda _checked=False, w=row: self._remove_item(w))
        row_h.addWidget(remove_btn)

        self._items_container.addWidget(row)
        return combo

    def _remove_item(self, widget: QWidget):
        widget.setParent(None)
        widget.deleteLater()

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

    def _collect_items(self) -> list[tuple[int, int]]:
        items = []
        for i in range(self._items_container.count()):
            item = self._items_container.itemAt(i)
            if not item:
                continue
            frame = item.widget()
            if not frame:
                continue
            combo = frame.findChild(SearchableComboBox)
            data = combo.current_data() if combo else None
            if not data:
                continue
            group_btn = None
            for child in frame.findChildren(QPushButton):
                if child.text().isdigit():
                    group_btn = child
                    break
            pg = int(group_btn.text()) if group_btn else 1
            items.append((int(data), pg))
        return items

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
                    self._add_item_row(
                        item_id=item.item_id, process_group=item.process_group
                    )
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
        for _ in range(total_fields):
            self._focus_index = (self._focus_index + 1) % total_fields
            combo = self._combo_at(self._focus_index)
            if combo and combo._line_edit.hasFocus():
                continue
            if combo:
                combo.focus_search()
            return

    def _combo_at(self, index: int):
        if index == 0:
            return self._paciente_combo
        row_idx = index - 1
        if row_idx < self._items_container.count():
            item = self._items_container.itemAt(row_idx)
            frame = item.widget() if item else None
            if frame:
                return frame.findChild(SearchableComboBox)
        return None

    def _on_save(self):
        items = self._collect_items()
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
                items=items,
                edit_id=self._edit_id,
                waiting_docs=waiting_docs,
                paciente_id=paciente_id,
            )
        except ValidationError as e:
            self._toast(str(e), "warning")
            return
        except DuplicateRecordError:
            self._toast(
                "Já existe um registro com esse tipo/paciente/malote", "warning"
            )
            return
        except Exception as e:
            ErrorHandler.handle_error(e, context="Registro", show_dialog=False)
            self._toast(f"Erro ao salvar: {e}", "negative")
            return

        msg = "Registro editado!" if result.is_update else "Registro salvo!"
        self._toast(msg, "positive")

        if self._auto_switch.isChecked():
            QTimer.singleShot(350, self._reset_form)
        else:
            QTimer.singleShot(350, lambda: self._mw.navigate_to(self._return_to))

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
        self._paciente_combo.focus_search()

    def _confirm_delete(self):
        if not self._edit_id:
            return

        def navigate_start():
            from PySide6.QtCore import QTimer

            QTimer.singleShot(800, lambda: self._mw.navigate_to(self._return_to))

        delete_registro_with_undo(
            self,
            self._mw.db,
            self._edit_id,
            on_refresh=navigate_start,
        )
