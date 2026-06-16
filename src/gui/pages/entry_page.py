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
    QDialog,
)
from PySide6.QtCore import Qt, QTimer
from dataclasses import dataclass
from functools import partial

from andaime.widgets import SearchableComboBox
from src.gui.widgets import (
    SectionLabel,
    TipoCombo,
    MaloteLabel,
    make_button,
    make_hbox,
    BasePage,
    CidInput,
    delete_registro_with_undo,
)
from src.gui.widgets.buttons import make_icon_button
from src.models import Registro
from src.services.registro_service import EditContext
from src.services.exceptions import ValidationError, DuplicateRecordError
from src.constants import TIPOS_WITH_MONTHS
from andaime.text import to_upper_normalized

from src.gui.styles import colors


class _CycleButton(QPushButton):
    def __init__(
        self,
        label: str,
        role: str,
        *,
        modulus: int,
        base: int,
        initial: int,
        width: int = 40,
        font_size: int = 14,
        format_fn=None,
        on_change=None,
    ):
        super().__init__(label)
        self.setProperty("btnrole", role)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(width)
        self.setStyleSheet(f"padding: 9px 0; font-size: {font_size}px; font-weight: 600;")
        self._modulus = modulus
        self._base = base
        self._value = initial
        self._format_fn = format_fn
        self._on_change = on_change

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._value = ((self._value - self._base - 1) % self._modulus) + self._base
        else:
            self._value = ((self._value - self._base + 1) % self._modulus) + self._base
        self._apply_label()
        self.setDown(True)
        QTimer.singleShot(120, lambda: self.setDown(False))
        if self._on_change:
            self._on_change(self._value)
        super().mousePressEvent(event)

    def _apply_label(self):
        self.setText(self._format_fn(self._value) if self._format_fn else str(self._value))

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, v: int):
        self._value = v
        self._apply_label()


@dataclass
class _RowData:
    group_btn: _CycleButton
    row_widget: QWidget
    months_btn: _CycleButton | None = None
    return_btn: QPushButton | None = None
    combo: SearchableComboBox | None = None
    pg: int = 1
    ms: int = -1


class EntryPage(BasePage):
    def __init__(
        self,
        main_window,
        tipo: str,
        edit_id: int | None = None,
        return_to: str = "start",
        paciente_id: int | None = None,
    ):
        super().__init__(main_window)
        self._tipo = tipo
        self._edit_id: int | None = edit_id
        self._edit_ctx: EditContext | None = None
        self._focus_index: int = -1
        self._return_to = return_to
        self._pre_paciente_id: int | None = paciente_id
        self._rows: list[_RowData] = []
        self._shortcut_widgets: dict[str, QPushButton | QLabel | QCheckBox] = {}
        self._delete_btn: QPushButton | None = None

        if edit_id:
            self._edit_ctx = self._mw.services.registro.load_for_edit(edit_id)

        self._mw.state.set_current_tipo(tipo)
        self._build_ui()

    @property
    def _is_editing(self) -> bool:
        return self._edit_id is not None

    @property
    def _edit_registro(self) -> Registro | None:
        return self._edit_ctx.registro if self._edit_ctx else None

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
        QTimer.singleShot(0, self._refresh_return_dates)
        if self._pre_paciente_id and not self._edit_id:
            QTimer.singleShot(
                0, lambda: self._on_paciente_selected(str(self._pre_paciente_id))
            )

    def _build_header(self, layout: QVBoxLayout):
        self._tipo_combo = TipoCombo(self._tipo)

        if self._edit_registro:
            malote = self._mw.services.malote.get(self._edit_registro.malote_id)
            if malote:
                self._mw.state.set_active_malote(malote)

        self._malote_label = MaloteLabel(self._mw)

        self._tipo_combo.tipo_changed.connect(self._on_context_changed)
        self._tipo_combo.tipo_changed.connect(self._on_tipo_changed_months)
        self._malote_label.malote_changed.connect(self._on_malote_changed)

        h = self._add_back_button(layout, target=self._return_to)
        h.addWidget(self._tipo_combo, 0, Qt.AlignmentFlag.AlignVCenter)
        h.addStretch()
        h.addWidget(self._malote_label, 0, Qt.AlignmentFlag.AlignTop)

    def _build_patient_section(self, layout: QVBoxLayout):
        h = make_hbox()

        self._paciente_combo = SearchableComboBox(
            "Nome do Paciente", on_search=self._search_pacientes
        )

        self._cid_input = CidInput()

        prefill_id = self._edit_registro.paciente_id if self._edit_registro else self._pre_paciente_id
        if prefill_id:
            paciente = self._mw.services.paciente.get(prefill_id)
            if paciente:
                self._paciente_combo.set_options({str(paciente.id): paciente.name})
                self._paciente_combo.set_current_by_data(str(paciente.id))
                self._cid_input.setText(paciente.cid or "")

        self._paciente_combo.selection_changed.connect(self._on_paciente_selected)
        self._paciente_combo.exact_match_changed.connect(self._on_paciente_selected)
        h.addWidget(self._paciente_combo)
        h.addWidget(self._cid_input)

        self._shortcut_searches = [
            ("Nome do Paciente", self._paciente_combo._line_edit),
        ]

        layout.addLayout(h)

    def _search_pacientes(self, query: str) -> dict[str, str]:
        pacientes = self._mw.services.paciente.search(query, limit=30)
        return {str(p.id): p.name for p in pacientes}

    def _search_items(self, query: str) -> dict[str, str]:
        normalized = to_upper_normalized(query)
        return {k: v for k, v in self._catalog_options.items() if normalized in v}

    def _build_items_section(self, layout: QVBoxLayout):
        self._catalog_options = {str(i.id): i.name for i in self._mw.services.item_catalog.all()}

        self._items_container = QVBoxLayout()
        self._items_container.setSpacing(4)
        layout.addLayout(self._items_container)

        layout.addSpacing(4)
        add_btn = make_button("+ Adicionar Item", "flat")
        add_btn.clicked.connect(lambda: (self._add_item_row(), self._refresh_return_dates()))
        self._shortcut_widgets["add_item"] = add_btn
        layout.addWidget(add_btn)

        if self._edit_ctx:
            months_by_group = dict(self._edit_ctx.processes)
            for item_id, process_group in self._edit_ctx.items:
                ms = months_by_group.get(process_group, 0)
                self._add_item_row(
                    item_id=item_id,
                    process_group=process_group,
                    months_supply=ms,
                )
        else:
            self._add_item_row()

    def _build_action_bar(self, layout: QVBoxLayout):
        h = QHBoxLayout()
        h.setSpacing(8)

        self._docs_check = QCheckBox("Esperando documentos")
        self._docs_check.setToolTip("Exclui este registro da planilha exportada.")
        if self._edit_registro and self._edit_registro.waiting_docs:
            self._docs_check.setChecked(True)
        self._docs_check.toggled.connect(self._on_waiting_docs_toggled)
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
        self._status_label.setText("Editando registro" if editing else "Novo registro")
        self._status_label.setStyleSheet(
            f"color: {c['text_secondary']}; font-size: 12px; font-style: italic;"
        )

    def _add_item_row(self, item_id: int | None = None, process_group: int = 1, months_supply: int | None = None):
        if months_supply is None:
            months_supply = 1 if self._tipo == "retirada" else 0
        row = QWidget()
        row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row_h = make_hbox(spacing=2)
        row.setLayout(row_h)

        rd: _RowData
        rd = _RowData(
            group_btn=_CycleButton(
                str(process_group), "positive",
                modulus=5, base=1, initial=process_group, font_size=14,
                on_change=lambda v: self._on_group_changed(rd, v),
            ),
            row_widget=row, pg=process_group, ms=months_supply,
        )
        rd.group_btn.setToolTip("Grupo do item (clique p/ alterar)")
        row_h.addWidget(rd.group_btn)

        combo = SearchableComboBox(
            "Buscar item...",
            on_search=self._search_items,
            on_delete_empty=lambda w=row: self._remove_item(w),
        )
        combo.set_options(self._catalog_options)
        if item_id is not None:
            combo.set_current_by_data(str(item_id))
        rd.combo = combo
        row_h.addWidget(combo)

        return_label = make_icon_button("--/--/----", "positive", width=85, font_size=11)
        return_label.setToolTip("Data prevista de retorno (clique p/ ver opções)")
        return_label.clicked.connect(lambda _checked=False: self._show_return_date_popup(rd))
        rd.return_btn = return_label
        row_h.addWidget(return_label)

        rd.months_btn = _CycleButton(
            f"{months_supply}m", "positive",
            modulus=7, base=0, initial=months_supply, width=36, font_size=11,
            format_fn=lambda v: f"{v}m",
            on_change=lambda v: self._on_months_changed(rd, v),
        )
        rd.months_btn.setToolTip("Meses de medicação (clique p/ alterar)")
        rd.months_btn.setVisible(self._tipo in TIPOS_WITH_MONTHS)
        self._rows.append(rd)
        row_h.addWidget(rd.months_btn)

        remove_btn = make_icon_button("\u00d7", "positive", font_size=16)
        remove_btn.setToolTip("Remover item")
        remove_btn.clicked.connect(lambda _checked=False, w=row: self._remove_item(w))
        row_h.addWidget(remove_btn)

        self._items_container.addWidget(row)
        return combo

    def _on_group_changed(self, rd: _RowData, new_pg: int):
        rd.pg = new_pg
        self._refresh_return_dates()

    def _on_months_changed(self, rd: _RowData, new_ms: int):
        rd.ms = new_ms
        self._sync_months_for_group(rd.pg, new_ms)
        self._refresh_return_dates()

    def _sync_months_for_group(self, group_number: int, new_ms: int):
        for rd in self._rows:
            if rd.pg == group_number and rd.months_btn:
                rd.ms = new_ms
                rd.months_btn.value = new_ms

    def _remove_item(self, widget: QWidget):
        self._rows = [rd for rd in self._rows if rd.row_widget is not widget]
        widget.setParent(None)
        widget.deleteLater()

    def _on_paciente_selected(self, data):
        if not data:
            return
        try:
            paciente_id = int(data)
        except (ValueError, TypeError):
            return
        if getattr(self, "_last_paciente_id", None) == paciente_id:
            return
        self._last_paciente_id = paciente_id
        self._load_cid_for_paciente(paciente_id)
        self._load_items_for_context(paciente_id)
        self._refresh_return_dates()

    def _on_context_changed(self, *_):
        paciente_id = self._resolve_current_patient()
        if paciente_id is None:
            return
        self._load_items_for_context(paciente_id)
        self._refresh_return_dates()

    def _on_malote_changed(self, *_):
        self._refresh_return_dates()

    def _on_tipo_changed_months(self, tipo: str):
        self._tipo = tipo
        visible = tipo in TIPOS_WITH_MONTHS
        for rd in self._rows:
            if rd.months_btn:
                rd.months_btn.setVisible(visible)
        self._refresh_return_dates()

    def _on_waiting_docs_toggled(self, checked: bool):
        if checked:
            for rd in self._rows:
                if rd.return_btn:
                    rd.return_btn.setText("--/--/----")
        else:
            self._refresh_return_dates()

    def _refresh_return_dates(self):
        from src.utils.date_calculator import calculate_return_dates, resolve_arrival_from_malote

        malote = self._mw.state.get_active_malote()
        tipo = self._tipo_combo.current_tipo()
        if not malote or not tipo:
            return

        arrival_date = resolve_arrival_from_malote(malote)

        row_data: dict[int, tuple[int, list[_RowData]]] = {}
        for rd in self._rows:
            if rd.pg not in row_data:
                row_data[rd.pg] = (rd.ms, [])
            row_data[rd.pg][1].append(rd)

        process_groups = [(g, ms) for g, (ms, _) in row_data.items()]
        if not process_groups:
            return

        returns = calculate_return_dates(
            tipo=tipo,
            arrival_date=arrival_date,
            process_groups=process_groups,
            db=self._mw.db,
            current_malote_id=malote.id,
            waiting_docs=self._docs_check.isChecked(),
        )

        for ret in returns:
            _, rows = row_data.get(ret.group_number, (0, []))
            for rd in rows:
                if rd.return_btn:
                    if ret.expected_return_date:
                        rd.return_btn.setText(ret.expected_return_date.strftime("%d/%m/%Y"))
                    else:
                        rd.return_btn.setText("--/--/----")

    def _get_return_buttons_for_group(self, group_number: int) -> list[QPushButton]:
        return [rd.return_btn for rd in self._rows if rd.pg == group_number and rd.return_btn]

    def _show_return_date_popup(self, rd: _RowData):
        try:
            self._do_show_return_date_popup(rd)
        except Exception as e:
            from andaime.error_handler import ErrorHandler
            ErrorHandler.handle_error(e, context="ReturnDatePopup", show_dialog=True)

    def _do_show_return_date_popup(self, rd: _RowData):
        from datetime import date, timedelta
        from src.utils.date_calculator import (
            find_nearest_arrival_after,
            get_candidate_days_after_arrival,
            resolve_arrival_from_malote,
        )
        malote = self._mw.state.get_active_malote()
        if not malote:
            return

        arrival_date = resolve_arrival_from_malote(malote)

        ms = rd.ms
        tipo = self._tipo_combo.current_tipo()

        dlg = QDialog(self.window())
        dlg.setMinimumWidth(300)
        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setSpacing(6)

        if arrival_date is None:
            dlg.reject()
            return

        if tipo in TIPOS_WITH_MONTHS and ms > 0:
            runs_out = date.today() + timedelta(days=ms * 30)
            nearest = find_nearest_arrival_after(runs_out, db=self._mw.db, top=1)
            best_arrival = nearest[0][0] if nearest else arrival_date
            candidates = get_candidate_days_after_arrival(best_arrival)
        else:
            candidates = get_candidate_days_after_arrival(arrival_date)

        for c in candidates:
            date_str = c.strftime("%d/%m/%Y")
            day_name = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][c.weekday()]
            btn = make_button(f"{date_str}  ({day_name})", "flat")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(
                partial(self._apply_return_date, date_str, dlg, rd.pg)
            )
            dlg_layout.addWidget(btn)

        dlg.exec()

    def _apply_return_date(self, date_str: str, dialog: QDialog, group_number: int):
        for b in self._get_return_buttons_for_group(group_number):
            b.setText(date_str)
        dialog.accept()

    def _load_cid_for_paciente(self, paciente_id: int):
        paciente = self._mw.services.paciente.get(paciente_id)
        if paciente:
            self._cid_input.setText(paciente.cid or "")
        else:
            self._cid_input.clear()

    def _resolve_current_patient(self) -> int | None:
        pid = self._paciente_combo.current_data()
        if not pid:
            name = self._paciente_combo.current_text().strip()
            if name:
                existing = self._mw.services.paciente.find_by_name(name)
                if existing:
                    pid = str(existing.id)
        if not pid:
            return None
        try:
            return int(pid)
        except (ValueError, TypeError):
            return None

    def _clear_item_rows(self):
        self._rows.clear()
        while self._items_container.count():
            item = self._items_container.takeAt(0)
            w = item.widget() if item else None
            if w:
                w.setParent(None)
                w.deleteLater()

    def _collect_items(self) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
        items = []
        months_by_group: dict[int, int] = {}
        for rd in self._rows:
            data = rd.combo.current_data() if rd.combo else None
            if not data:
                continue
            items.append((int(data), rd.pg))
            if rd.pg not in months_by_group:
                months_by_group[rd.pg] = rd.ms
        process_months = [(g, m) for g, m in months_by_group.items()]
        return items, process_months

    def _load_items_for_context(self, paciente_id: int):
        malote = self._mw.state.get_active_malote()
        tipo = self._tipo_combo.current_tipo()

        ctx = self._mw.services.registro.load_for_context(
            tipo, paciente_id, malote.id if malote else None
        )

        self._clear_item_rows()
        if ctx.registro:
            self._update_registro_status(True)
            months_by_group = dict(ctx.processes)
            if ctx.items:
                for item_id, process_group in ctx.items:
                    ms = months_by_group.get(process_group, 0)
                    self._add_item_row(
                        item_id=item_id,
                        process_group=process_group,
                        months_supply=ms,
                    )
            else:
                self._add_item_row()
        else:
            self._update_registro_status(False)
            if ctx.suggested_item_ids:
                for item_id in ctx.suggested_item_ids:
                    self._add_item_row(item_id=item_id)
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
        items, process_months = self._collect_items()
        if not items:
            self._toast("Adicione pelo menos um item", "warning")
            return
        tipo = self._tipo_combo.current_tipo()
        waiting_docs = self._docs_check.isChecked()

        malote = self._mw.state.get_active_malote()
        if not malote:
            self._toast("Selecione um malote", "warning")
            return

        paciente_name = self._paciente_combo.current_text().strip()
        paciente_id = self._resolve_current_patient()

        service = self._mw.services.registro

        try:
            result = service.save(
                tipo=tipo,
                paciente_name=paciente_name,
                malote_id=malote.id,
                items=items,
                edit_id=self._edit_id,
                waiting_docs=waiting_docs,
                paciente_id=paciente_id,
                process_months=process_months,
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
            self._handle_error(e, context="Registro")
            return

        msg = "Registro editado!" if result.is_update else "Registro salvo!"
        self._toast(msg, "positive")

        self._save_cid(paciente_id)

        if self._auto_switch.isChecked():
            QTimer.singleShot(350, self._reset_form)
        else:
            QTimer.singleShot(350, lambda: self._mw.navigate_to(self._return_to))

    def _save_cid(self, paciente_id: int | None):
        if paciente_id is None:
            return
        try:
            cid = self._cid_input.text().strip()
            self._mw.services.paciente.update(paciente_id, cid=cid)
        except Exception as e:
            self._handle_error(e, context="CID")

    def _reset_form(self):
        self._edit_id = None
        self._edit_ctx = None
        self._paciente_combo.set_options({})
        self._paciente_combo.clear()
        self._cid_input.clear()
        self._clear_item_rows()
        self._add_item_row()
        self._docs_check.blockSignals(True)
        self._docs_check.setChecked(False)
        self._docs_check.blockSignals(False)
        self._update_registro_status(False)
        self._refresh_return_dates()
        if self._delete_btn:
            self._delete_btn.hide()
        self._paciente_combo.focus_search()

    def _confirm_delete(self):
        if not self._edit_id:
            return

        delete_registro_with_undo(
            self,
            self._mw.db,
            self._edit_id,
            on_refresh=lambda: QTimer.singleShot(
                800, lambda: self._mw.navigate_to(self._return_to)
            ),
        )
