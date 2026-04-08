#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry Screen
Record entry/editing screen for registros
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from datetime import datetime

import customtkinter as ctk

if TYPE_CHECKING:
    from src.ui.main import RACApp

from src.ui.theme import AppTheme
from src.ui.autocomplete_wrapper import AutocompleteWrapper
from src.state.state_events import StateEvent, StateEventType
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel


class EntryScreen(ctk.CTkFrame):
    def __init__(
        self,
        parent: ctk.CTkFrame,
        app: RACApp,
        tipo: str,
        registro: Optional[dict] = None,
    ) -> None:
        super().__init__(parent, fg_color="transparent")
        self._app = app
        self._tipo = tipo
        self._registro = registro
        self._selected_paciente: Optional[dict] = None
        self._selected_items: list[dict] = []
        self._item_autocomplete: Optional[AutocompleteWrapper] = None
        self._paciente_autocomplete: Optional[AutocompleteWrapper] = None

        self._build_ui()

        if registro:
            self._load_registro(registro)

    @property
    def app(self) -> RACApp:
        return self._app

    def _build_ui(self) -> None:
        self._build_header()
        self._build_patient_section()
        self._build_items_section()
        self._build_actions()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=AppTheme.COLOR_BG_SECONDARY, height=50)
        header.pack(fill="x", padx=10, pady=(10, 5))
        header.pack_propagate(False)

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=15, pady=8)

        tipo_colors = {
            "entrada": AppTheme.COLOR_ENTRADA,
            "renovacao": AppTheme.COLOR_RENOVACAO,
            "retirada": AppTheme.COLOR_RETIRADA,
            "urgente": AppTheme.COLOR_URGENTE,
        }

        malote_text = ""
        if self.app.state_manager:
            malote = self.app.state_manager.get_active_malote()
            if malote:
                try:
                    dt = datetime.fromisoformat(malote["date"])
                    malote_text = dt.strftime("%d/%m/%Y")
                except (ValueError, KeyError):
                    malote_text = malote.get("date", "")

        title_label = ctk.CTkLabel(
            inner,
            text=malote_text,
            font=AppTheme.FONT_HEADER,
            text_color=AppTheme.COLOR_FG_PRIMARY,
            anchor="w",
        )
        title_label.pack(side="left")

        tipo_label = ctk.CTkLabel(
            inner,
            text=AppTheme.TIPO_LABELS.get(self._tipo, self._tipo),
            font=AppTheme.FONT_BODY,
            text_color=tipo_colors.get(self._tipo, AppTheme.COLOR_ACCENT),
            anchor="e",
        )
        tipo_label.pack(side="right")

    def _build_patient_section(self) -> None:
        patient_frame = ctk.CTkFrame(self, fg_color="transparent")
        patient_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            patient_frame,
            text="Paciente:",
            font=AppTheme.FONT_BODY,
            text_color=AppTheme.COLOR_FG_PRIMARY,
            anchor="w",
        ).pack(side="left", padx=(0, 5))

        self._patient_entry = ctk.CTkEntry(
            patient_frame,
            placeholder_text="Buscar paciente...",
            font=AppTheme.FONT_BODY,
            height=32,
        )
        self._patient_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self._new_patient_btn = ctk.CTkButton(
            patient_frame,
            text="+ Novo",
            font=AppTheme.FONT_SMALL,
            width=70,
            height=32,
            fg_color=AppTheme.COLOR_ACCENT,
            hover_color=AppTheme.COLOR_ACCENT_HOVER,
            command=self._on_new_patient,
        )
        self._new_patient_btn.pack(side="right")

        self._paciente_autocomplete = AutocompleteWrapper(
            self._patient_entry,
            search_function=self._search_pacientes,
            on_select_callback=self._on_paciente_selected,
        )

    def _build_items_section(self) -> None:
        items_container = ctk.CTkFrame(self, fg_color="transparent")
        items_container.pack(fill="both", expand=True, padx=10, pady=5)

        header_row = ctk.CTkFrame(items_container, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(
            header_row,
            text="Itens:",
            font=AppTheme.FONT_BODY,
            text_color=AppTheme.COLOR_FG_PRIMARY,
            anchor="w",
        ).pack(side="left")

        self._add_item_btn = ctk.CTkButton(
            header_row,
            text="+ Adicionar Item",
            font=AppTheme.FONT_SMALL,
            width=120,
            height=28,
            fg_color=AppTheme.COLOR_ACCENT,
            hover_color=AppTheme.COLOR_ACCENT_HOVER,
            command=self._on_add_item,
        )
        self._add_item_btn.pack(side="right")

        self._items_list = ctk.CTkScrollableFrame(
            items_container,
            fg_color="transparent",
        )
        self._items_list.pack(fill="both", expand=True)

    def _build_actions(self) -> None:
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.pack(fill="x", padx=10, pady=(5, 10))

        self._back_btn = ctk.CTkButton(
            actions_frame,
            text="← Voltar",
            font=AppTheme.FONT_BODY,
            width=100,
            height=36,
            fg_color=AppTheme.COLOR_DANGER,
            hover_color=AppTheme.COLOR_DANGER_HOVER,
            command=self._on_back,
        )
        self._back_btn.pack(side="left")

        auto_return = True
        if self.app.state_manager:
            auto_return = self.app.state_manager.get_auto_return()

        self._auto_return_var = ctk.BooleanVar(value=auto_return)
        self._auto_return_cb = ctk.CTkCheckBox(
            actions_frame,
            text="Auto-retorno",
            variable=self._auto_return_var,
            font=AppTheme.FONT_SMALL,
            command=self._on_auto_return_toggle,
        )
        self._auto_return_cb.pack(side="left", padx=15)

        self._save_btn = ctk.CTkButton(
            actions_frame,
            text="Salvar",
            font=AppTheme.FONT_BUTTON,
            width=150,
            height=36,
            fg_color=AppTheme.COLOR_SUCCESS,
            hover_color=AppTheme.COLOR_SUCCESS_HOVER,
            command=self._on_save,
        )
        self._save_btn.pack(side="right")

        if self._registro:
            self._delete_btn = ctk.CTkButton(
                actions_frame,
                text="Excluir",
                font=AppTheme.FONT_SMALL,
                width=80,
                height=36,
                fg_color=AppTheme.COLOR_DANGER,
                hover_color=AppTheme.COLOR_DANGER_HOVER,
                command=self._on_delete,
            )
            self._delete_btn.pack(side="right", padx=(0, 10))

    def _load_registro(self, registro: dict) -> None:
        if not self.app.db:
            return

        paciente = self.app.db.get_paciente_by_id(registro["paciente_id"])
        if paciente:
            self._selected_paciente = paciente
            self._patient_entry.delete(0, "end")
            self._patient_entry.insert(0, paciente["name"])

        items = self.app.db.get_items_for_registro(registro["id"])
        for item in items:
            self._add_item_row(item)

    def _search_pacientes(self, query: str) -> list[str]:
        if not self.app.db:
            return []
        results = self.app.db.search_pacientes(query, limit=10)
        return [r["name"] for r in results]

    def _on_paciente_selected(self, name: str) -> Optional[str]:
        if not self.app.db:
            return name

        results = self.app.db.search_pacientes(name, limit=1)
        for r in results:
            if r["name"] == name:
                self._selected_paciente = r
                return name

        return name

    def _on_new_patient(self) -> None:
        from src.ui.dialogs.rac_dialogs import NewPatientDialog

        typed_name = self._patient_entry.get().strip()
        dialog = NewPatientDialog(self, self.app, typed_name)
        self.wait_window(dialog)

        if dialog.result:
            self._selected_paciente = dialog.result
            self._patient_entry.delete(0, "end")
            self._patient_entry.insert(0, dialog.result["name"])

    def _on_add_item(self) -> None:
        row_frame = ctk.CTkFrame(self._items_list, fg_color=AppTheme.COLOR_BG_TERTIARY, height=36)
        row_frame.pack(fill="x", pady=2)
        row_frame.pack_propagate(False)

        entry = ctk.CTkEntry(
            row_frame,
            placeholder_text="Buscar item...",
            font=AppTheme.FONT_BODY,
            height=28,
        )
        entry.pack(side="left", fill="x", expand=True, padx=(5, 2), pady=4)

        remove_btn = ctk.CTkButton(
            row_frame,
            text="✕",
            font=AppTheme.FONT_SMALL,
            width=28,
            height=28,
            fg_color=AppTheme.COLOR_DANGER,
            hover_color=AppTheme.COLOR_DANGER_HOVER,
            command=lambda: self._remove_item_row(row_frame, None),
        )
        remove_btn.pack(side="right", padx=(2, 5), pady=4)

        item_data: dict = {"entry": entry, "row": row_frame, "item": None}

        autocomplete = AutocompleteWrapper(
            entry,
            search_function=self._search_items,
            on_select_callback=lambda name, d=item_data: self._on_item_selected(name, d),
        )
        item_data["autocomplete"] = autocomplete

        self._selected_items.append(item_data)
        entry.focus_set()

    def _search_items(self, query: str) -> list[str]:
        if not self.app.db:
            return []
        results = self.app.db.search_items(query, limit=10)
        return [r["name"] for r in results]

    def _on_item_selected(self, name: str, item_data: dict) -> Optional[str]:
        if not self.app.db:
            return name

        items = self.app.db.search_items(name, limit=1)
        for item in items:
            if item["name"] == name:
                item_data["item"] = item
                return name

        return name

    def _add_item_row(self, item: dict) -> None:
        row_frame = ctk.CTkFrame(self._items_list, fg_color=AppTheme.COLOR_BG_TERTIARY, height=36)
        row_frame.pack(fill="x", pady=2)
        row_frame.pack_propagate(False)

        entry = ctk.CTkEntry(
            row_frame,
            font=AppTheme.FONT_BODY,
            height=28,
        )
        entry.pack(side="left", fill="x", expand=True, padx=(5, 2), pady=4)
        entry.insert(0, item.get("item_name", item.get("name", "")))
        entry.configure(state="disabled")

        remove_btn = ctk.CTkButton(
            row_frame,
            text="✕",
            font=AppTheme.FONT_SMALL,
            width=28,
            height=28,
            fg_color=AppTheme.COLOR_DANGER,
            hover_color=AppTheme.COLOR_DANGER_HOVER,
            command=lambda: self._remove_item_row(row_frame, item_data),
        )
        remove_btn.pack(side="right", padx=(2, 5), pady=4)

        item_data = {
            "entry": entry,
            "row": row_frame,
            "item": item,
            "autocomplete": None,
        }
        self._selected_items.append(item_data)

    def _remove_item_row(self, row_frame: ctk.CTkFrame, item_data: Optional[dict]) -> None:
        row_frame.destroy()
        if item_data and item_data in self._selected_items:
            self._selected_items.remove(item_data)
        elif item_data is None:
            self._selected_items = [
                i for i in self._selected_items
                if i["row"] != row_frame
            ]

    def _on_auto_return_toggle(self) -> None:
        if self.app.state_manager:
            self.app.state_manager.set_auto_return(self._auto_return_var.get())

    def _on_save(self) -> None:
        if not self.app.db or not self.app.state_manager:
            return

        if not self._selected_paciente:
            self._patient_entry.focus_set()
            return

        malote = self.app.state_manager.get_active_malote()
        if not malote:
            return

        item_ids = []
        for item_data in self._selected_items:
            if item_data.get("item") and item_data["item"].get("id"):
                item_ids.append(item_data["item"]["id"])

        try:
            if self._registro:
                self.app.db.update_registro(
                    self._registro["id"],
                    paciente_id=self._selected_paciente["id"],
                )
                registro_id = self._registro["id"]
            else:
                registro = self.app.db.create_registro(
                    tipo=self._tipo,
                    paciente_id=self._selected_paciente["id"],
                    malote_id=malote["id"],
                )
                registro_id = registro["id"]

            if item_ids:
                self.app.db.set_registro_items(registro_id, item_ids)

            self.app.state_manager.notify_registro_saved(
                {"id": registro_id, "tipo": self._tipo}
            )

            if self._auto_return_var.get():
                self.app.show_start_screen()
            else:
                self._clear_form()

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                context=ErrorContext.REGISTRO,
                recovery_hint="Verifique os dados e tente novamente",
            )

    def _on_delete(self) -> None:
        if not self._registro or not self.app.db or not self.app.state_manager:
            return

        from src.ui.dialogs.rac_dialogs import ConfirmDeleteDialog
        dialog = ConfirmDeleteDialog(self, self.app)
        self.wait_window(dialog)

        if dialog.result:
            try:
                self.app.db.delete_registro(self._registro["id"])
                self.app.state_manager.notify_registro_deleted(self._registro["id"])
                self.app.show_start_screen()
            except Exception as e:
                ErrorHandler.handle_error(
                    e,
                    context=ErrorContext.REGISTRO,
                )

    def _on_back(self) -> None:
        self.app.show_start_screen()

    def _clear_form(self) -> None:
        self._selected_paciente = None
        self._selected_items = []
        self._patient_entry.delete(0, "end")

        for widget in self._items_list.winfo_children():
            widget.destroy()

        self._patient_entry.focus_set()

    def destroy(self) -> None:
        for item_data in self._selected_items:
            ac = item_data.get("autocomplete")
            if ac:
                try:
                    ac.destroy()
                except Exception:
                    pass

        if self._paciente_autocomplete:
            try:
                self._paciente_autocomplete.destroy()
            except Exception:
                pass

        super().destroy()
