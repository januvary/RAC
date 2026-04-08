#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start Page
Home base: malote display, tipo buttons, search, export
"""

from datetime import datetime

from nicegui import ui

from src.web.app import (
    get_db, get_state, get_config,
    TIPO_COLORS, TIPO_LABELS, TIPO_ICONS,
)
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel


def create_start_page():
    state = get_state()
    db = get_db()

    ui.colors(primary="#4a90e2")

    with ui.column().classes("w-full max-w-2xl mx-auto p-6 gap-4"):

        _build_malote_header(db, state)

        with ui.row().classes("w-full gap-3"):
            for tipo_key in ["entrada", "renovacao", "retirada", "urgente"]:
                _build_tipo_button(tipo_key, state)

        _build_search_section(db, state)

        ui.button(
            "Exportar Planilha",
            icon="file_download",
            color="positive",
            on_click=lambda: _on_export(db, state),
        ).classes("w-full").props("size=lg")


def _build_malote_header(db, state):
    with ui.card().classes("w-full no-shadow") as card:
        with ui.row().classes("w-full items-center justify-between"):
            malote = state.get_active_malote()
            display = _format_malote_date(malote) if malote else "Nenhum malote ativo"
            ui.label(f"Malote: {display}").classes("text-h5 text-weight-bold")

            with ui.row().classes("gap-2"):
                ui.button(
                    "Novo Malote",
                    icon="add",
                    color="positive",
                    on_click=lambda: _show_new_malote_dialog(db, state, card),
                ).props("dense")
                ui.button(
                    "Trocar",
                    icon="swap_horiz",
                    color="primary",
                    on_click=lambda: _show_malote_switcher(db, state, card),
                ).props("dense")


def _build_tipo_button(tipo_key: str, state):
    color = TIPO_COLORS[tipo_key]
    label = TIPO_LABELS[tipo_key]
    icon = TIPO_ICONS[tipo_key]

    ui.button(
        label,
        icon=icon,
        color=color,
        on_click=lambda t=tipo_key: _on_tipo_click(t, state),
    ).classes("flex-1").props("size=lg")


def _build_search_section(db, state):
    with ui.card().classes("w-full no-shadow"):
        ui.label("Buscar Paciente").classes("text-subtitle1 text-weight-medium")

        results = _get_search_options(db, state)
        search_select = ui.select(
            options=results,
            with_input=True,
            new_value_mode="add-unique",
            label="Nome do paciente...",
        ).classes("w-full").props('dense outlined :clearable="false"')

        def on_search(e):
            _perform_search(e.args if isinstance(e.args, str) else search_select.value, db, state)

        search_select.on("update:model-value", on_search)


def _get_search_options(db, state) -> dict:
    malote = state.get_active_malote()
    if not malote:
        return {}
    resultados = db.get_registros_by_malote(malote["id"])
    options = {}
    for reg in resultados:
        tipo = TIPO_LABELS.get(reg.get("tipo", ""), "")
        name = reg.get("paciente_name", "")
        label = f"{name} ({tipo})"
        options[str(reg["id"])] = label
    return options


def _perform_search(registro_id, db, state):
    if not registro_id:
        return
    try:
        reg_id = int(registro_id)
        reg = db.get_registro_by_id(reg_id)
        if reg:
            _go_to_registro(reg)
    except (ValueError, TypeError):
        pass


def _go_to_registro(registro: dict):
    tipo = registro.get("tipo", "entrada")
    reg_id = registro.get("id")
    ui.navigate.to(f"/entry/{tipo}?edit={reg_id}")


def _on_tipo_click(tipo: str, state):
    if not state.has_active_malote():
        ui.notify("Selecione um malote primeiro!", type="warning")
        return
    ui.navigate.to(f"/entry/{tipo}")


def _on_export(db, state):
    if not state.has_active_malote():
        ui.notify("Selecione um malote primeiro!", type="warning")
        return

    try:
        from src.export.excel_exporter import ExcelExporter
        malote = state.get_active_malote()
        exporter = ExcelExporter(db)
        result = exporter.export_malote(malote["id"])
        if result:
            ui.notify(f"Planilha exportada: {result}", type="positive")
        else:
            ui.notify("Nenhum registro para exportar", type="warning")
    except Exception as e:
        ErrorHandler.handle_error(e, context=ErrorContext.EXPORT, show_dialog=False)
        ui.notify(f"Erro ao exportar: {e}", type="negative")


def _show_new_malote_dialog(db, state, header_card):
    with ui.dialog() as dialog, ui.card().classes("p-6"):
        ui.label("Novo Malote").classes("text-h6")
        date_input = ui.input(
            "Data do malote",
            placeholder="dd/mm ou dd/mm/aa",
        ).classes("w-full").props('dense outlined')

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancelar", color="grey", on_click=dialog.close).props("flat")
            ui.button(
                "Criar",
                icon="check",
                color="positive",
                on_click=lambda: _create_malote(
                    date_input.value, db, state, dialog, header_card
                ),
            )

        date_input.on("keydown.enter", lambda: _create_malote(
            date_input.value, db, state, dialog, header_card
        ))

    dialog.open()


def _create_malote(date_text, db, state, dialog, header_card):
    iso_date = _parse_date(date_text)
    if not iso_date:
        ui.notify("Data inválida. Use dd/mm ou dd/mm/aa", type="warning")
        return

    try:
        malote = db.create_malote(iso_date)
        state.set_active_malote(malote)
        dialog.close()
        ui.notify(f"Malote criado: {_format_malote_date(malote)}", type="positive")
        ui.navigate.to("/")
    except Exception as e:
        ErrorHandler.handle_error(e, context=ErrorContext.MALOTE, show_dialog=False)
        ui.notify(f"Erro: {e}", type="negative")


def _show_malote_switcher(db, state, header_card):
    malotes = db.get_all_malotes()
    active = state.get_active_malote()

    with ui.dialog() as dialog, ui.card().classes("p-6 min-w-[300px]"):
        ui.label("Malotes").classes("text-h6")

        with ui.scroll_area().classes("w-full max-h-[300px]"):
            with ui.list().classes("w-full"):
                for m in malotes:
                    is_active = active and active["id"] == m["id"]
                    display = _format_malote_date(m)

                    with ui.item(on_click=lambda mal=m: _select_malote(
                        mal, state, dialog
                    )).classes("cursor-pointer"):
                        with ui.item_section().classes("w-full"):
                            with ui.row().classes("items-center w-full"):
                                if is_active:
                                    ui.icon("circle").classes("text-primary").props(
                                        "size=xs"
                                    )
                                ui.label(display).classes(
                                    "text-body1" + (" text-weight-bold" if is_active else "")
                                )

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Novo Malote", icon="add", color="positive", on_click=lambda: [
                dialog.close(),
                _show_new_malote_dialog(db, state, header_card),
            ]).props("dense")
            ui.button("Fechar", color="grey", on_click=dialog.close).props("flat")

    dialog.open()


def _select_malote(malote, state, dialog):
    state.set_active_malote(malote)
    dialog.close()
    ui.notify(f"Malote: {_format_malote_date(malote)}", type="info")
    ui.navigate.to("/")


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
