#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry Page
Record creation and editing
"""

from nicegui import ui, app as nicegui_app
from starlette.requests import Request

from src.web.app import (
    get_db, get_state, get_config,
    TIPO_COLORS, TIPO_LABELS, TIPO_ICONS,
)
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel


def create_entry_page(tipo: str, request: Request = None):
    db = get_db()
    state = get_state()

    edit_id = None
    if request:
        edit_id = request.query_params.get("edit")

    registro = None
    if edit_id:
        registro = db.get_registro_by_id(int(edit_id))

    state.set_current_tipo(tipo)
    state.set_editing_registro(registro)

    color = TIPO_COLORS.get(tipo, "primary")
    label = TIPO_LABELS.get(tipo, tipo)
    icon = TIPO_ICONS.get(tipo, "edit")

    selected_paciente = {"data": registro} if registro else {"data": None}
    selected_items: list[dict] = []

    ui.colors(primary=color)

    with ui.column().classes("w-full max-w-2xl mx-auto p-6 gap-4"):

        with ui.card().classes("w-full no-shadow"):
            with ui.row().classes("w-full items-center justify-between"):
                malote = state.get_active_malote()
                malote_text = _format_malote_date(malote) if malote else ""
                ui.label(malote_text).classes("text-subtitle1")
                ui.badge(label, color=color).classes("text-body1")

        with ui.card().classes("w-full no-shadow"):
            ui.label("Paciente").classes("text-subtitle1 text-weight-medium")

            with ui.row().classes("w-full items-center gap-2"):
                pacientes = db.search_pacientes("", limit=1000)
                paciente_options = {
                    str(p["id"]): p["name"] for p in pacientes
                }

                paciente_select = ui.select(
                    options=paciente_options,
                    with_input=True,
                    new_value_mode="add-unique",
                    label="Buscar paciente...",
                ).classes("flex-1").props('dense outlined')

                if registro and registro.get("paciente_id"):
                    pid = str(registro["paciente_id"])
                    paciente_select.set_value(pid)

                ui.button(
                    "+ Novo",
                    icon="person_add",
                    color="positive",
                    on_click=lambda: _show_new_patient_dialog(db, paciente_select),
                ).props("dense")

        with ui.card().classes("w-full no-shadow"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label("Itens").classes("text-subtitle1 text-weight-medium")
                ui.button(
                    "Adicionar Item",
                    icon="add",
                    color=color,
                    on_click=lambda: _add_item_row(db, items_container, selected_items),
                ).props("dense")

            items_container = ui.column().classes("w-full gap-2")

            if registro:
                items = db.get_items_for_registro(registro["id"])
                for item in items:
                    _add_item_row(db, items_container, selected_items, prefill=item)
            else:
                _add_item_row(db, items_container, selected_items)

        with ui.row().classes("w-full items-center justify-between"):
            ui.button(
                "Voltar",
                color="grey",
                on_click=lambda: ui.navigate.to("/"),
            ).props("flat")

            with ui.row().classes("items-center gap-4"):
                auto_return = state.get_auto_return()
                auto_switch = ui.switch(
                    "Auto-retorno",
                    value=auto_return,
                    on_change=lambda: state.set_auto_return(auto_switch.value),
                )

                if registro:
                    ui.button(
                        "Excluir",
                        icon="delete",
                        color="negative",
                        on_click=lambda: _confirm_delete(
                            db, state, registro["id"]
                        ),
                    ).props("flat")

                ui.button(
                    "Salvar",
                    icon="save",
                    color="positive",
                    on_click=lambda: _on_save(
                        db, state, tipo, registro,
                        paciente_select, selected_items,
                        auto_switch.value,
                    ),
                ).props("size=lg")


def _add_item_row(db, container, selected_items, prefill: dict | None = None):
    all_items = db.get_all_items()
    item_options = {str(i["id"]): i["name"] for i in all_items}

    item_data = {"id": None}

    with container:
        with ui.row().classes("w-full items-center gap-2") as row:
            item_select = ui.select(
                options=item_options,
                with_input=True,
                new_value_mode="add-unique",
                label="Buscar item...",
            ).classes("flex-1").props("dense outlined")

            if prefill:
                iid = str(prefill.get("item_id", prefill.get("id")))
                item_select.set_value(iid)
                item_data["id"] = int(iid)

            def _on_item_change(e, d=item_data, sel=item_select):
                val = e.args if isinstance(e.args, (str, int)) else sel.value
                d["id"] = int(val) if val else None

            item_select.on("update:model-value", _on_item_change)

            ui.button(
                icon="remove_circle",
                color="negative",
                on_click=lambda: [
                    selected_items.remove(item_data) if item_data in selected_items else None,
                    row.delete(),
                ],
            ).props("flat dense round")

    selected_items.append(item_data)


def _show_new_patient_dialog(db, paciente_select):
    with ui.dialog() as dialog, ui.card().classes("p-6"):
        ui.label("Novo Paciente").classes("text-h6")
        name_input = ui.input("Nome").classes("w-full").props('dense outlined')

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancelar", color="grey", on_click=dialog.close).props("flat")
            ui.button(
                "Criar",
                icon="check",
                color="positive",
                on_click=lambda: _create_patient(
                    name_input.value, db, paciente_select, dialog
                ),
            )

        name_input.on("keydown.enter", lambda: _create_patient(
            name_input.value, db, paciente_select, dialog
        ))

    dialog.open()


def _create_patient(name, db, paciente_select, dialog):
    name = (name or "").strip()
    if not name:
        ui.notify("Nome não pode estar vazio", type="warning")
        return

    try:
        paciente = db.create_paciente(name)
        pid = str(paciente["id"])
        paciente_select.options[pid] = name
        paciente_select.update()
        paciente_select.set_value(pid)
        dialog.close()
        ui.notify(f"Paciente criado: {name}", type="positive")
    except Exception as e:
        ErrorHandler.handle_error(e, context=ErrorContext.DATABASE, show_dialog=False)
        ui.notify(f"Erro: {e}", type="negative")


def _on_save(db, state, tipo, registro, paciente_select, selected_items, auto_return):
    pid = paciente_select.value
    if not pid:
        ui.notify("Selecione um paciente", type="warning")
        return

    malote = state.get_active_malote()
    if not malote:
        ui.notify("Nenhum malote ativo", type="warning")
        return

    item_ids = [
        item["id"] for item in selected_items
        if item.get("id") is not None
    ]

    try:
        paciente_id = int(pid)

        if registro:
            db.update_registro(registro["id"], paciente_id=paciente_id)
            reg_id = registro["id"]
        else:
            new_reg = db.create_registro(tipo, paciente_id, malote["id"])
            reg_id = new_reg["id"]

        if item_ids:
            db.set_registro_items(reg_id, item_ids)

        state.notify_registro_saved({"id": reg_id, "tipo": tipo})
        ui.notify("Registro salvo!", type="positive")

        if auto_return:
            ui.navigate.to("/")
    except Exception as e:
        ErrorHandler.handle_error(e, context=ErrorContext.REGISTRO, show_dialog=False)
        ui.notify(f"Erro ao salvar: {e}", type="negative")


def _confirm_delete(db, state, registro_id):
    with ui.dialog() as dialog, ui.card().classes("p-6"):
        ui.label("Excluir este registro?").classes("text-h6")
        ui.label("Esta ação não pode ser desfeita.").classes("text-grey")

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancelar", color="grey", on_click=dialog.close).props("flat")
            ui.button(
                "Excluir",
                icon="delete",
                color="negative",
                on_click=lambda: _do_delete(db, state, registro_id, dialog),
            )

    dialog.open()


def _do_delete(db, state, registro_id, dialog):
    try:
        db.delete_registro(registro_id)
        state.notify_registro_deleted(registro_id)
        dialog.close()
        ui.notify("Registro excluído", type="info")
        ui.navigate.to("/")
    except Exception as e:
        ErrorHandler.handle_error(e, context=ErrorContext.REGISTRO, show_dialog=False)
        ui.notify(f"Erro: {e}", type="negative")


def _format_malote_date(malote: dict | None) -> str:
    from datetime import datetime
    if not malote:
        return "?"
    try:
        dt = datetime.fromisoformat(malote["date"])
        return dt.strftime("%d/%m/%Y")
    except (ValueError, KeyError):
        return malote.get("date", "?")
