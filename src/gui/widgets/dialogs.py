#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QDialog,
)

from src.gui.widgets.buttons import make_button
from src.gui.widgets.labels import HeadingLabel
from src.gui.styles import colors
from src.gui.widgets.toast import show_toast
from src.services.registro_service import RegistroService
from andaime.error_handler import ErrorHandler


def confirm_delete_dialog(
    parent: QWidget,
    title: str,
    message: str,
    destructive_label: str = "Excluir",
) -> bool:
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setMinimumWidth(340)

    layout = QVBoxLayout(dlg)
    layout.setSpacing(12)

    layout.addWidget(HeadingLabel(title))
    layout.addSpacing(4)

    msg = QLabel(message)
    msg.setWordWrap(True)
    c = colors()
    msg.setStyleSheet(f"color: {c['text_secondary']}; font-size: 13px;")
    layout.addWidget(msg)

    btn_row = QHBoxLayout()
    btn_row.addStretch()
    cancel = make_button("Cancelar", "flat")
    cancel.clicked.connect(dlg.reject)
    btn_row.addWidget(cancel)
    delete_btn = make_button(destructive_label, "negative")
    delete_btn.clicked.connect(dlg.accept)
    btn_row.addWidget(delete_btn)
    layout.addLayout(btn_row)

    return dlg.exec() == QDialog.DialogCode.Accepted


def open_input_dialog(
    parent: QWidget,
    title: str,
    placeholder: str,
    initial: str = "",
    confirm_label: str = "Confirmar",
) -> str | None:
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setMinimumWidth(340)

    layout = QVBoxLayout(dlg)
    layout.setSpacing(16)

    layout.addWidget(HeadingLabel(title))
    layout.addSpacing(4)

    input_field = QLineEdit()
    input_field.setPlaceholderText(placeholder)
    input_field.setText(initial)
    if initial:
        input_field.selectAll()
    layout.addWidget(input_field)

    btn_row = QHBoxLayout()
    btn_row.addStretch()
    cancel = make_button("Cancelar", "flat")
    cancel.clicked.connect(dlg.reject)
    btn_row.addWidget(cancel)
    confirm = make_button(confirm_label, "primary")
    btn_row.addWidget(confirm)
    layout.addLayout(btn_row)

    input_field.returnPressed.connect(dlg.accept)
    confirm.clicked.connect(dlg.accept)

    if dlg.exec() != QDialog.DialogCode.Accepted:
        return None
    return input_field.text().strip() or None


def delete_registro_with_undo(page, db, reg_id: int, on_refresh, on_error=None):
    if not confirm_delete_dialog(
        page, "Excluir Registro", "Esta ação não pode ser desfeita."
    ):
        return

    try:
        reg = db.get_registro_by_id(reg_id)
        items = db.get_items_for_registro(reg_id) if reg else []
        snapshot = (reg, items) if reg else None

        service = RegistroService(db)
        service.delete(reg_id)
        on_refresh()

        if snapshot:

            def undo():
                r, old_items = snapshot
                new_reg = db.create_registro(
                    tipo=r.tipo,
                    paciente_id=r.paciente_id,
                    malote_id=r.malote_id,
                    waiting_docs=r.waiting_docs,
                )
                item_tuples = [(i.item_id, i.process_group) for i in old_items]
                if item_tuples:
                    db.set_registro_items(new_reg.id, item_tuples)
                on_refresh()

            show_toast(
                "Registro excluido",
                "info",
                page,
                action_label="Desfazer",
                action_callback=undo,
                timeout_ms=5000,
            )
        else:
            show_toast("Registro excluido", "info", page)
    except Exception as e:
        ErrorHandler.handle_error(e, context="Registro", show_dialog=False)
        if on_error:
            on_error(e)
        else:
            show_toast(f"Erro: {e}", "negative", page)
