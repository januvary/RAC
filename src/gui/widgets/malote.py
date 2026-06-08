#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from contextlib import suppress

from PySide6.QtWidgets import (
    QLabel,
    QSizePolicy,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QDialog,
    QLineEdit,
    QMenu,
)
from PySide6.QtCore import Qt, Signal

from src.gui.widgets.buttons import make_button
from src.gui.widgets.labels import HeadingLabel
from src.gui.widgets.toast import show_toast
from src.gui.widgets.dialogs import confirm_delete_dialog, make_dialog_button_row, scaffold_dialog

def _activate_malote_if_changed(mw, malote, label):
    current = mw.state.get_active_malote()
    if not current or current.id != malote.id or current.date != malote.date:
        mw.state.set_active_malote(malote)
        label.malote_changed.emit()


class MaloteLabel(QWidget):
    malote_changed = Signal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self._mw = main_window

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._shortcut_hint = QLabel("")
        self._shortcut_hint.setFixedHeight(28)
        self._shortcut_hint.setFixedWidth(52)
        self._shortcut_hint.setStyleSheet(
            "color: #9CA3AF; font-size: 14px; border: none;"
        )
        layout.addWidget(self._shortcut_hint)

        self._date_label = QLabel()
        self._date_label.setProperty("malotelabel", "true")
        self._date_label.setFixedHeight(28)
        self._date_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self._date_label.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(self._date_label)

        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.refresh()

    def mousePressEvent(self, event):
        _show_malote_dialog(self)

    def open_dialog(self):
        _show_malote_dialog(self)

    def refresh(self):
        from src.utils.text_utils import format_malote_date

        malote = self._mw.state.get_active_malote()
        display = format_malote_date(malote) if malote else "Nenhum malote ativo"
        self._date_label.setText(display)

    def set_shortcut_hint_visible(self, show: bool):
        self._shortcut_hint.setText("(Ctrl+D)" if show else "")


def _show_malote_dialog(label: MaloteLabel):
    from datetime import datetime
    from src.utils.text_utils import format_malote_date
    from src.gui.widgets._malote_tree import (
        make_malote_tree as _make_tree,
        populate_malote_tree as _populate,
        wire_tree_keyboard as _wire_kb,
    )
    from PySide6.QtWidgets import QHeaderView

    parent = label.window()
    mw = label._mw

    dlg = QDialog(parent)
    dlg.setWindowTitle("Malotes")
    dlg.setMinimumWidth(340)
    dlg.setMinimumHeight(350)

    layout = QVBoxLayout(dlg)
    layout.setSpacing(12)

    layout.addWidget(HeadingLabel("Malotes"))

    tree = _make_tree()
    tree.setColumnCount(2)
    hdr = tree.header()
    hdr.setStretchLastSection(False)
    hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

    def _decorate(child, m, dt):
        active = mw.state.get_active_malote()
        is_active = active and active.id == m.id
        display = format_malote_date(m)
        prefix = "\u2713 " if is_active else "    "
        child.setText(0, f"{prefix}{display}")
        if is_active:
            font = child.font(0)
            font.setBold(True)
            child.setFont(0, font)

        arrival_str = m.arrival_date
        if not arrival_str:
            try:
                from src.utils.date_calculator import calculate_arrival_date

                send_dt = datetime.fromisoformat(m.date).date()
                arrival_str = calculate_arrival_date(send_dt).isoformat()
            except (ValueError, TypeError):
                arrival_str = None
        if arrival_str:
            with suppress(ValueError, TypeError):
                arrival = datetime.fromisoformat(arrival_str).date()
                child.setText(1, f"\u279c {arrival.strftime('%d/%m/%Y')}")
                child.setTextAlignment(1, Qt.AlignmentFlag.AlignRight)
                font = child.font(1)
                font.setPointSize(font.pointSize() - 1)
                child.setFont(1, font)

    def _populate_tree():
        malotes = mw.db.get_all_malotes()
        _populate(
            tree,
            malotes,
            format_display=lambda _m, _dt: "",
            decorate_item=_decorate,
        )

    _populate_tree()

    def on_item_clicked(item, _column):
        malote = item.data(0, Qt.ItemDataRole.UserRole)
        if malote:
            mw.state.set_active_malote(malote)
            dlg.accept()
            label.refresh()
            _activate_malote_if_changed(mw, malote, label)
        else:
            item.setExpanded(not item.isExpanded())

    tree.itemClicked.connect(on_item_clicked)
    _wire_kb(tree, lambda item: on_item_clicked(item, 0))
    tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def _show_tree_menu(pos):
        item = tree.itemAt(pos)
        if not item:
            return
        malote = item.data(0, Qt.ItemDataRole.UserRole)
        if not malote:
            return

        menu = QMenu(tree)
        edit_menu = menu.addMenu("Editar")
        envio_action = edit_menu.addAction("Data de envio")
        retorno_action = edit_menu.addAction("Data de retorno")
        has_registros = mw.db.get_registros_by_malote(malote.id)
        if not has_registros:
            delete_action = menu.addAction("Excluir")
        else:
            delete_action = None

        action = menu.exec(tree.viewport().mapToGlobal(pos))
        if action == envio_action:
            _show_date_dialog(label, malote, "send", _populate_tree)
        elif action == retorno_action:
            _show_date_dialog(label, malote, "arrival", _populate_tree)
        elif action == delete_action and delete_action is not None:
            if not confirm_delete_dialog(
                parent,
                "Excluir Malote",
                f'Excluir malote "{format_malote_date(malote)}"?',
            ):
                return

            deleted = mw.db.delete_malote(malote.id)
            if deleted:
                current_active = mw.state.get_active_malote()
                if current_active and current_active.id == malote.id:
                    remaining = [
                        m for m in mw.db.get_all_malotes() if m.id != malote.id
                    ]
                    mw.state.set_active_malote(remaining[0] if remaining else None)
                label.refresh()
                label.malote_changed.emit()
                _populate_tree()
                show_toast("Malote excluído", "positive", label)
            else:
                show_toast(
                    "Malote possui registros e não pode ser excluído", "negative", label
                )

    tree.customContextMenuRequested.connect(_show_tree_menu)
    layout.addWidget(tree)

    btn_row = QHBoxLayout()
    new_m = make_button("Novo Malote", "flat")
    new_m.setAutoDefault(False)

    def _on_new_malote(_):
        _show_new_malote_dialog(label)
        _populate_tree()

    new_m.clicked.connect(_on_new_malote)
    btn_row.addWidget(new_m)
    btn_row.addStretch()
    close_m = make_button("Fechar", "flat")
    close_m.setAutoDefault(False)
    close_m.clicked.connect(dlg.reject)
    btn_row.addWidget(close_m)
    layout.addLayout(btn_row)

    dlg.exec()


def _show_new_malote_dialog(label: MaloteLabel):
    from datetime import datetime
    from src.utils.text_utils import parse_date, format_malote_date
    from src.utils.date_calculator import next_send_date, calculate_arrival_date
    from andaime.error_handler import ErrorHandler
    from datetime import date as date_cls

    parent = label.window()
    mw = label._mw

    dlg, layout = scaffold_dialog(parent, "Novo Malote", spacing=16)

    date_input = QLineEdit()
    date_input.setPlaceholderText("dd/mm ou dd/mm/aa")
    with suppress(Exception):
        from datetime import date as date_cls

        existing = set()
        for m in mw.db.get_all_malotes():
            with suppress(ValueError, TypeError):
                existing.add(datetime.fromisoformat(m.date).date())
        suggested = next_send_date(existing)
        date_input.setText(suggested.strftime("%d/%m/%Y"))
    date_input.selectAll()
    layout.addWidget(date_input)

    btn_row, [cancel, create] = make_dialog_button_row([
        ("Cancelar", "flat"),
        ("Criar", "primary"),
    ])
    cancel.clicked.connect(dlg.reject)

    def do_create():
        iso = parse_date(date_input.text())
        if not iso:
            show_toast("Data inválida", "negative", label)
            return
        try:
            arrival_iso = None
            with suppress(ValueError, TypeError):
                send_dt = date_cls.fromisoformat(iso)
                arrival = calculate_arrival_date(send_dt)
                arrival_iso = arrival.isoformat()
            malote = mw.db.create_malote(iso, arrival_date=arrival_iso)
            _activate_malote_if_changed(mw, malote, label)
            dlg.accept()
            label.refresh()
            show_toast(
                f"Malote criado: {format_malote_date(malote)}", "positive", label
            )
        except Exception as e:
            ErrorHandler.handle_error(e, context="Malote", show_dialog=False)
            show_toast(f"Erro: {e}", "negative", label)

    create.clicked.connect(do_create)
    layout.addLayout(btn_row)

    date_input.returnPressed.connect(do_create)
    dlg.exec()


def _show_date_dialog(label: MaloteLabel, malote, field: str, on_done):
    from src.utils.text_utils import parse_date
    from andaime.error_handler import ErrorHandler

    parent = label.window()
    mw = label._mw

    if field == "send":
        title = "Data de Envio"
        current_iso = malote.date
    else:
        title = "Data de Retorno"
        current_iso = malote.arrival_date or ""
        if not current_iso:
            with suppress(ValueError, TypeError):
                from src.utils.date_calculator import calculate_arrival_date
                from datetime import date as date_cls

                send_dt = date_cls.fromisoformat(malote.date)
                current_iso = calculate_arrival_date(send_dt).isoformat()

    dlg, layout = scaffold_dialog(parent, title, spacing=16)
    layout.addSpacing(4)

    date_input = QLineEdit()
    date_input.setPlaceholderText("dd/mm ou dd/mm/aa")
    try:
        from datetime import datetime

        dt = datetime.fromisoformat(current_iso)
        date_input.setText(dt.strftime("%d/%m/%Y"))
    except (ValueError, TypeError):
        date_input.setText(current_iso or "")
    if date_input.text():
        date_input.selectAll()
    layout.addWidget(date_input)

    btn_row, [cancel, save] = make_dialog_button_row([
        ("Cancelar", "flat"),
        ("Salvar", "primary"),
    ])
    cancel.clicked.connect(dlg.reject)

    def do_save():
        iso = parse_date(date_input.text())
        if not iso:
            show_toast("Data inválida", "negative", label)
            return
        if iso == current_iso:
            dlg.accept()
            return
        try:
            if field == "send":
                mw.db.update_malote(malote.id, date=iso)
                malote.date = iso
            else:
                mw.db.update_malote(malote.id, arrival_date=iso)
                malote.arrival_date = iso
            if (
                mw.state.get_active_malote()
                and mw.state.get_active_malote().id == malote.id
            ):
                mw.state.set_active_malote(malote)
                label.malote_changed.emit()
            label.refresh()
            dlg.accept()
            on_done()
            show_toast("Malote atualizado", "positive", label)
        except Exception as e:
            ErrorHandler.handle_error(e, context="Malote", show_dialog=False)
            show_toast(f"Erro: {e}", "negative", label)

    save.clicked.connect(do_save)
    layout.addLayout(btn_row)

    date_input.returnPressed.connect(do_save)
    dlg.exec()
