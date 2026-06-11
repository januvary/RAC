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
    QLineEdit,
    QDialog,
)
from PySide6.QtCore import Qt, QTimer

from andaime.widgets import SearchableComboBox
from src.gui.widgets import (
    SectionLabel,
    TipoCombo,
    MaloteLabel,
    make_button,
    make_hbox,
    BasePage,
    delete_registro_with_undo,
)
from src.gui.widgets.buttons import make_icon_button
from src.gui.widgets.dialogs import make_dialog_button_row
from src.models import Registro
from src.services.registro_service import RegistroService
from src.services.exceptions import ValidationError, DuplicateRecordError
from andaime.text import to_upper_normalized

from src.gui.styles import colors


class _CidInput(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("CID")
        self.setFixedWidth(170)
        self._formatting = False
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text: str):
        if self._formatting:
            return
        self._formatting = True
        cursor = self.cursorPosition()
        formatted = self._format_all(text.upper())
        if formatted != text:
            new_cursor = cursor + (len(formatted) - len(text))
            self.setText(formatted)
            self.setCursorPosition(max(0, min(new_cursor, len(formatted))))
        self._formatting = False

    def _format_all(self, raw: str) -> str:
        cids = []
        current = ""
        trailing_sep = False
        i = 0
        while i < len(raw):
            ch = raw[i]
            if ch in (";", ",", " "):
                if current:
                    cids.append(self._format_single(current))
                    current = ""
                trailing_sep = True
                i += 1
                continue
            if ch == " " and not current and not trailing_sep:
                i += 1
                continue
            trailing_sep = False
            current += ch
            i += 1
        if current:
            cids.append(self._format_single(current))
            trailing_sep = False
        result = "; ".join(cids)
        if trailing_sep:
            result += "; "
        return result

    @staticmethod
    def _format_single(cid: str) -> str:
        cleaned = ""
        for ch in cid:
            if ch.isalpha():
                if not cleaned:
                    cleaned += ch.upper()
            elif ch.isdigit():
                cleaned += ch
            elif ch == "." and len(cleaned) >= 3 and "." not in cleaned:
                cleaned += ch
        if len(cleaned) >= 3 and "." not in cleaned:
            cleaned = cleaned[:3] + "." + cleaned[3:]
        if len(cleaned) > 5:
            cleaned = cleaned[:5]
        return cleaned

    def focusOutEvent(self, event):
        self._formatting = True
        formatted = self._format_all(self.text().upper())
        self.setText(formatted)
        self._formatting = False
        super().focusOutEvent(event)


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
        self._months_buttons: list[QPushButton] = []
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
        QTimer.singleShot(0, self._refresh_return_dates)

    def _build_header(self, layout: QVBoxLayout):
        self._tipo_combo = TipoCombo(self._tipo)

        if self._edit_registro:
            malote = self._mw.db.get_malote_by_id(self._edit_registro.malote_id)
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

        self._cid_input = _CidInput()

        if self._edit_registro and self._edit_registro.paciente_id:
            paciente = self._mw.db.get_paciente_by_id(self._edit_registro.paciente_id)
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
        add_btn.clicked.connect(lambda: (self._add_item_row(), self._refresh_return_dates()))
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

        group_btn = make_icon_button(str(process_group), "positive", font_size=14)
        group_btn.setToolTip("Grupo do item (clique p/ alterar)")
        group_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pg = process_group

        _orig_mouse = group_btn.mousePressEvent

        def _cycle_group(event):
            nonlocal pg
            if event.button() == Qt.MouseButton.RightButton:
                pg = ((pg - 2) % 5) + 1
            else:
                pg = (pg % 5) + 1
            group_btn.setText(str(pg))
            group_btn.setDown(True)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(120, lambda: group_btn.setDown(False))
            self._refresh_return_dates()
            _orig_mouse(event)

        group_btn.mousePressEvent = _cycle_group
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

        return_label = make_icon_button("--/--/----", "positive", width=85, font_size=11)
        return_label.setToolTip("Data prevista de retorno (clique p/ ver opções)")
        return_label.clicked.connect(lambda _checked=False: self._show_return_date_popup(return_label, pg))
        row_h.addWidget(return_label)

        months_btn = make_icon_button(f"{months_supply}m", "positive", width=36, font_size=11)
        months_btn.setToolTip("Meses de medicação (clique p/ alterar)")
        months_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ms = months_supply

        _orig_mouse_months = months_btn.mousePressEvent

        def _cycle_months(event):
            nonlocal ms
            if event.button() == Qt.MouseButton.RightButton:
                ms = (ms - 1) % 7
            else:
                ms = (ms + 1) % 7
            months_btn.setText(f"{ms}m")
            months_btn.setDown(True)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(120, lambda: months_btn.setDown(False))
            self._sync_months_for_group(pg, ms)
            self._refresh_return_dates()
            _orig_mouse_months(event)

        months_btn.mousePressEvent = _cycle_months
        months_btn.setVisible(self._tipo == "retirada")
        self._months_buttons.append(months_btn)
        row_h.addWidget(months_btn)

        remove_btn = make_icon_button("\u00d7", "positive", font_size=16)
        remove_btn.setToolTip("Remover item")
        remove_btn.clicked.connect(lambda _checked=False, w=row: self._remove_item(w))
        row_h.addWidget(remove_btn)

        self._items_container.addWidget(row)
        return combo

    def _sync_months_for_group(self, group_number: int, new_ms: int):
        for i in range(self._items_container.count()):
            item = self._items_container.itemAt(i)
            if not item:
                continue
            frame = item.widget()
            if not frame:
                continue
            group_btn = None
            months_btn = None
            for child in frame.findChildren(QPushButton):
                text = child.text()
                if text.isdigit() and len(text) == 1:
                    group_btn = child
                elif text.endswith("m") and len(text) == 2 and text[0].isdigit():
                    months_btn = child
            if group_btn and int(group_btn.text()) == group_number and months_btn:
                months_btn.setText(f"{new_ms}m")

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
        visible = tipo == "retirada"
        for btn in self._months_buttons:
            btn.setVisible(visible)
        self._refresh_return_dates()

    def _on_waiting_docs_toggled(self, checked: bool):
        if checked:
            for i in range(self._items_container.count()):
                item = self._items_container.itemAt(i)
                if not item:
                    continue
                frame = item.widget()
                if not frame:
                    continue
                for child in frame.findChildren(QPushButton):
                    if "/" in child.text():
                        child.setText("--/--/----")
        else:
            self._refresh_return_dates()

    def _refresh_return_dates(self):
        from datetime import date as date_cls
        from src.utils.date_calculator import calculate_return_dates

        malote = self._mw.state.get_active_malote()
        tipo = self._tipo_combo.current_tipo()
        if not malote or not tipo:
            return

        arrival_date = None
        if malote.arrival_date:
            try:
                arrival_date = date_cls.fromisoformat(malote.arrival_date)
            except (ValueError, TypeError):
                pass
        if arrival_date is None and malote.date:
            try:
                from src.utils.date_calculator import calculate_arrival_date
                arrival_date = calculate_arrival_date(date_cls.fromisoformat(malote.date))
            except (ValueError, TypeError):
                pass

        paciente_id = self._resolve_current_patient()

        row_data: dict[int, tuple[int, list[QPushButton]]] = {}
        for i in range(self._items_container.count()):
            item = self._items_container.itemAt(i)
            if not item:
                continue
            frame = item.widget()
            if not frame:
                continue
            group_btn = None
            months_btn = None
            return_btn = None
            for child in frame.findChildren(QPushButton):
                text = child.text()
                if text.isdigit() and len(text) == 1:
                    group_btn = child
                elif text.endswith("m") and len(text) == 2 and text[0].isdigit():
                    months_btn = child
                elif "/" in text:
                    return_btn = child
            pg = int(group_btn.text()) if group_btn else 1
            ms = int(months_btn.text().rstrip("m")) if months_btn else 0
            if pg not in row_data:
                row_data[pg] = (ms, [])
            if return_btn:
                row_data[pg][1].append(return_btn)

        process_groups = [(g, ms) for g, (ms, _) in row_data.items()]
        if not process_groups:
            return

        returns = calculate_return_dates(
            tipo=tipo,
            arrival_date=arrival_date,
            process_groups=process_groups,
            db=self._mw.db,
            paciente_id=paciente_id,
            current_malote_id=malote.id,
            waiting_docs=self._docs_check.isChecked(),
        )

        for ret in returns:
            _, return_btns = row_data.get(ret.group_number, (0, []))
            for return_btn in return_btns:
                if ret.expected_return_date:
                    return_btn.setText(ret.expected_return_date.strftime("%d/%m/%Y"))
                else:
                    return_btn.setText("--/--/----")

    def _get_return_buttons_for_group(self, group_number: int) -> list[QPushButton]:
        buttons: list[QPushButton] = []
        for i in range(self._items_container.count()):
            item = self._items_container.itemAt(i)
            if not item:
                continue
            frame = item.widget()
            if not frame:
                continue
            group_btn = None
            return_btn = None
            for child in frame.findChildren(QPushButton):
                text = child.text()
                if text.isdigit() and len(text) == 1:
                    group_btn = child
                elif "/" in text:
                    return_btn = child
            if group_btn and int(group_btn.text()) == group_number and return_btn:
                buttons.append(return_btn)
        return buttons

    def _show_return_date_popup(self, return_label: QPushButton, group_number: int):
        try:
            self._do_show_return_date_popup(return_label, group_number)
        except Exception as e:
            from andaime.error_handler import ErrorHandler
            ErrorHandler.handle_error(e, context="ReturnDatePopup", show_dialog=True)

    def _do_show_return_date_popup(self, return_label: QPushButton, group_number: int):
        from datetime import date as date_cls, timedelta
        from src.utils.date_calculator import (
            _rank_candidates,
            calculate_return_dates,
        )
        from src.gui.widgets.dialogs import scaffold_dialog

        malote = self._mw.state.get_active_malote()
        if not malote:
            return

        arrival_date = None
        if malote.arrival_date:
            try:
                arrival_date = date_cls.fromisoformat(malote.arrival_date)
            except (ValueError, TypeError):
                pass
        if arrival_date is None and malote.date:
            try:
                from src.utils.date_calculator import calculate_arrival_date
                arrival_date = calculate_arrival_date(date_cls.fromisoformat(malote.date))
            except (ValueError, TypeError):
                pass

        ms = 0
        for i in range(self._items_container.count()):
            item = self._items_container.itemAt(i)
            if not item:
                continue
            frame = item.widget()
            if not frame:
                continue
            gb = None
            mb = None
            for child in frame.findChildren(QPushButton):
                text = child.text()
                if text.isdigit() and len(text) == 1:
                    gb = child
                elif text.endswith("m") and len(text) == 2 and text[0].isdigit():
                    mb = child
            if gb and int(gb.text()) == group_number and mb:
                ms = int(mb.text().rstrip("m"))
                break

        tipo = self._tipo_combo.current_tipo()
        paciente_id = self._resolve_current_patient()

        dlg = QDialog(self.window())
        dlg.setMinimumWidth(300)
        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setSpacing(6)

        if arrival_date is None:
            dlg.reject()
            return

        if tipo == "retirada" and ms > 0:
            reference_arrival = arrival_date
            if self._mw.db and paciente_id:
                last = self._mw.db.get_last_retirada_arrival_for_patient(paciente_id, group_number)
                if last:
                    try:
                        reference_arrival = date_cls.fromisoformat(last)
                    except (ValueError, TypeError):
                        pass

            if reference_arrival is None:
                dlg.reject()
                return

            runs_out = reference_arrival + timedelta(days=ms * 30)
            candidates = _rank_candidates(runs_out, db=self._mw.db, top=4)

            for sc in candidates:
                date_str = sc.date.strftime("%d/%m/%Y")
                day_name = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][sc.date.weekday()]
                label_text = f"{date_str}  ({day_name})  —  {sc.load} retorno(s)"
                btn = make_button(label_text, "flat")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)

                def _pick(checked=False, d=date_str, dialog=dlg, gn=group_number):
                    for btn in self._get_return_buttons_for_group(gn):
                        btn.setText(d)
                    dialog.accept()

                btn.clicked.connect(_pick)
                dlg_layout.addWidget(btn)
        else:
            from src.utils.date_calculator import _get_candidate_days_after_arrival

            candidates = _get_candidate_days_after_arrival(arrival_date)
            for c in candidates:
                date_str = c.strftime("%d/%m/%Y")
                day_name = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][c.weekday()]
                btn = make_button(f"{date_str}  ({day_name})", "flat")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)

                def _pick(checked=False, d=date_str, dialog=dlg, gn=group_number):
                    for btn in self._get_return_buttons_for_group(gn):
                        btn.setText(d)
                    dialog.accept()

                btn.clicked.connect(_pick)
                dlg_layout.addWidget(btn)

        btn_row, [cancel_btn] = make_dialog_button_row([("Fechar", "flat")])
        cancel_btn.setAutoDefault(False)
        cancel_btn.clicked.connect(dlg.reject)
        dlg_layout.addLayout(btn_row)

        dlg.exec()

    def _load_cid_for_paciente(self, paciente_id: int):
        paciente = self._mw.db.get_paciente_by_id(paciente_id)
        if paciente:
            self._cid_input.setText(paciente.cid or "")
        else:
            self._cid_input.clear()

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
        self._months_buttons.clear()
        while self._items_container.count():
            item = self._items_container.takeAt(0)
            w = item.widget() if item else None
            if w:
                w.setParent(None)
                w.deleteLater()

    def _collect_items(self) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
        items = []
        months_by_group: dict[int, int] = {}
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
            months_btn = None
            for child in frame.findChildren(QPushButton):
                text = child.text()
                if text.isdigit() and len(text) == 1:
                    group_btn = child
                elif text.endswith("m") and text[:-1].isdigit():
                    months_btn = child
            pg = int(group_btn.text()) if group_btn else 1
            ms = int(months_btn.text().rstrip("m")) if months_btn else 0
            items.append((int(data), pg))
            if pg not in months_by_group:
                months_by_group[pg] = ms
        process_months = [(g, m) for g, m in months_by_group.items()]
        return items, process_months

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
            processes = self._mw.db.get_processes_for_registro(existing_reg.id)
            months_by_group = {p.group_number: p.months_supply for p in processes}
            if items:
                for item in items:
                    ms = months_by_group.get(item.process_group, 0)
                    self._add_item_row(
                        item_id=item.item_id,
                        process_group=item.process_group,
                        months_supply=ms,
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
        items, process_months = self._collect_items()
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

        self._save_cid(paciente_id or self._resolve_current_patient())

        if self._auto_switch.isChecked():
            QTimer.singleShot(350, self._reset_form)
        else:
            QTimer.singleShot(350, lambda: self._mw.navigate_to(self._return_to))

    def _save_cid(self, paciente_id: int | None):
        if paciente_id is None:
            return
        cid = self._cid_input.text().strip()
        paciente = self._mw.db.get_paciente_by_id(paciente_id)
        if paciente and paciente.cid != cid:
            self._mw.db.update_paciente(paciente_id, paciente.name, cid=cid)

    def _reset_form(self):
        self._edit_id = None
        self._edit_registro = None
        self._paciente_combo.set_options({})
        self._paciente_combo.clear()
        self._cid_input.clear()
        self._clear_item_rows()
        self._add_item_row()
        self._docs_check.setChecked(False)
        self._update_registro_status(False)
        self._refresh_return_dates()
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
