#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start Screen
Home base with malote display, tipo buttons, search, and export
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Optional
from datetime import datetime

import customtkinter as ctk

if TYPE_CHECKING:
    from src.ui.main import RACApp

from src.ui.sections.base_section import BaseSection
from src.ui.theme import AppTheme
from src.state.state_events import StateEvent, StateEventType
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel


class StartScreen(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app: RACApp) -> None:
        super().__init__(parent, fg_color="transparent")
        self._app = app
        self._search_timer: Optional[str] = None

        self._build_ui()

    @property
    def app(self) -> RACApp:
        return self._app

    def _build_ui(self) -> None:
        self._export_btn = None
        self._build_malote_header()

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=10)

        self._build_tipo_buttons(content)

        self._build_search_section(content)

        self._build_export_button()

    def _build_malote_header(self) -> None:
        header_frame = ctk.CTkFrame(self, fg_color=AppTheme.COLOR_BG_SECONDARY, height=60)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)

        inner = ctk.CTkFrame(header_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=15, pady=10)

        self._malote_label = ctk.CTkLabel(
            inner,
            text="Nenhum malote ativo",
            font=AppTheme.FONT_TITLE,
            text_color=AppTheme.COLOR_FG_PRIMARY,
            anchor="w",
        )
        self._malote_label.pack(side="left", fill="x", expand=True)

        self._malote_switcher_btn = ctk.CTkButton(
            inner,
            text="Trocar Malote",
            font=AppTheme.FONT_SMALL,
            width=120,
            height=32,
            fg_color=AppTheme.COLOR_ACCENT,
            hover_color=AppTheme.COLOR_ACCENT_HOVER,
            command=self._open_malote_switcher,
        )
        self._malote_switcher_btn.pack(side="right")

        self._update_malote_display()

    def _build_tipo_buttons(self, parent: ctk.CTkFrame) -> None:
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 15))

        btn_frame.grid_columnconfigure((0, 1), weight=1)
        btn_frame.grid_rowconfigure((0, 1), weight=1)

        tipos = [
            ("entrada", "Entrada", AppTheme.COLOR_ENTRADA, AppTheme.COLOR_ENTRADA_HOVER),
            ("renovacao", "Renovação", AppTheme.COLOR_RENOVACAO, AppTheme.COLOR_RENOVACAO_HOVER),
            ("retirada", "Retirada", AppTheme.COLOR_RETIRADA, AppTheme.COLOR_RETIRADA_HOVER),
            ("urgente", "Urgente", AppTheme.COLOR_URGENTE, AppTheme.COLOR_URGENTE_HOVER),
        ]

        self._tipo_buttons: dict[str, ctk.CTkButton] = {}

        for i, (tipo_key, label, color, hover_color) in enumerate(tipos):
            row, col = divmod(i, 2)
            btn = ctk.CTkButton(
                btn_frame,
                text=label,
                font=AppTheme.FONT_BUTTON,
                fg_color=color,
                hover_color=hover_color,
                height=60,
                corner_radius=8,
                command=lambda t=tipo_key: self._on_tipo_click(t),
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self._tipo_buttons[tipo_key] = btn

    def _build_search_section(self, parent: ctk.CTkFrame) -> None:
        search_frame = ctk.CTkFrame(parent, fg_color="transparent")
        search_frame.pack(fill="both", expand=True, pady=(0, 10))

        self._search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Buscar paciente...",
            font=AppTheme.FONT_BODY,
            height=36,
        )
        self._search_entry.pack(fill="x", pady=(0, 5))
        self._search_entry.bind("<KeyRelease>", self._on_search_input)

        self._results_frame = ctk.CTkScrollableFrame(
            search_frame,
            fg_color="transparent",
            height=200,
        )
        self._results_frame.pack(fill="both", expand=True)

        self._results_label = ctk.CTkLabel(
            self._results_frame,
            text="",
            font=AppTheme.FONT_SMALL,
            text_color=AppTheme.COLOR_FG_DISABLED,
        )
        self._results_label.pack(pady=10)

    def _build_export_button(self) -> None:
        self._export_btn = ctk.CTkButton(
            self,
            text="Exportar Planilha",
            font=AppTheme.FONT_BUTTON,
            fg_color=AppTheme.COLOR_SUCCESS,
            hover_color=AppTheme.COLOR_SUCCESS_HOVER,
            height=40,
            command=self._on_export,
        )
        self._export_btn.pack(fill="x", padx=20, pady=(5, 15))

    def _update_malote_display(self) -> None:
        if not self.app.state_manager:
            return

        malote = self.app.state_manager.get_active_malote()
        if malote:
            try:
                date_str = malote["date"]
                dt = datetime.fromisoformat(date_str)
                display = dt.strftime("%d/%m/%Y")
            except (ValueError, KeyError):
                display = malote.get("date", "?")

            self._malote_label.configure(text=f"Malote: {display}")
            if self._export_btn:
                self._export_btn.configure(state="normal")
        else:
            self._malote_label.configure(text="Nenhum malote ativo")
            if self._export_btn:
                self._export_btn.configure(state="disabled")

    def _on_tipo_click(self, tipo: str) -> None:
        if not self.app.state_manager or not self.app.state_manager.has_active_malote():
            return

        self.app.show_entry_screen(tipo)

    def _on_search_input(self, event) -> None:
        if self._search_timer:
            self.after_cancel(self._search_timer)

        query = self._search_entry.get().strip()
        if not query:
            self._clear_results()
            return

        self._search_timer = self.after(200, lambda: self._perform_search(query))

    def _perform_search(self, query: str) -> None:
        if not self.app.db or not self.app.state_manager:
            return

        malote = self.app.state_manager.get_active_malote()
        if not malote:
            return

        results = self.app.db.search_registros_by_patient(malote["id"], query)
        self._display_results(results)

    def _display_results(self, results: list[dict]) -> None:
        for widget in self._results_frame.winfo_children():
            widget.destroy()

        if not results:
            self._results_label = ctk.CTkLabel(
                self._results_frame,
                text="Nenhum resultado encontrado",
                font=AppTheme.FONT_SMALL,
                text_color=AppTheme.COLOR_FG_DISABLED,
            )
            self._results_label.pack(pady=10)
            return

        tipo_colors = {
            "entrada": AppTheme.COLOR_ENTRADA,
            "renovacao": AppTheme.COLOR_RENOVACAO,
            "retirada": AppTheme.COLOR_RETIRADA,
            "urgente": AppTheme.COLOR_URGENTE,
        }
        tipo_labels = AppTheme.TIPO_LABELS

        for reg in results:
            row = ctk.CTkFrame(
                self._results_frame,
                fg_color=AppTheme.COLOR_BG_TERTIARY,
                corner_radius=4,
                height=36,
            )
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            color = tipo_colors.get(reg.get("tipo", ""), AppTheme.COLOR_ACCENT)
            badge = ctk.CTkLabel(
                row,
                text=tipo_labels.get(reg.get("tipo", ""), "?"),
                font=AppTheme.FONT_SMALL_BOLD if hasattr(AppTheme, 'FONT_SMALL_BOLD') else AppTheme.FONT_SMALL,
                text_color=color,
                width=90,
                anchor="w",
            )
            badge.pack(side="left", padx=(10, 5), pady=6)

            name_label = ctk.CTkLabel(
                row,
                text=reg.get("paciente_name", ""),
                font=AppTheme.FONT_BODY,
                text_color=AppTheme.COLOR_FG_PRIMARY,
                anchor="w",
            )
            name_label.pack(side="left", fill="x", expand=True, padx=5)

            row.bind("<Button-1>", lambda e, r=reg: self._on_result_click(r))
            name_label.bind("<Button-1>", lambda e, r=reg: self._on_result_click(r))
            badge.bind("<Button-1>", lambda e, r=reg: self._on_result_click(r))

    def _clear_results(self) -> None:
        for widget in self._results_frame.winfo_children():
            widget.destroy()

        self._results_label = ctk.CTkLabel(
            self._results_frame,
            text="",
            font=AppTheme.FONT_SMALL,
            text_color=AppTheme.COLOR_FG_DISABLED,
        )
        self._results_label.pack(pady=10)

    def _on_result_click(self, registro: dict) -> None:
        self.app.show_entry_screen(registro["tipo"], registro=registro)

    def _open_malote_switcher(self) -> None:
        from src.ui.dialogs.rac_dialogs import MaloteSwitcherDialog
        dialog = MaloteSwitcherDialog(self, self.app)
        self.wait_window(dialog)

        self._update_malote_display()

    def _on_export(self) -> None:
        if not self.app.state_manager or not self.app.state_manager.has_active_malote():
            return

        def _do_export():
            try:
                from src.export.excel_exporter import ExcelExporter
                malote = self.app.state_manager.get_active_malote()
                exporter = ExcelExporter(self.app.db)
                result = exporter.export_malote(malote["id"])
                if result:
                    self._export_btn.configure(text=f"Exportado!", fg_color=AppTheme.COLOR_SUCCESS)
                    self.after(2000, lambda: self._export_btn.configure(
                        text="Exportar Planilha",
                        fg_color=AppTheme.COLOR_SUCCESS,
                    ))
            except Exception as e:
                ErrorHandler.handle_error(
                    e,
                    context=ErrorContext.EXPORT,
                    recovery_hint="Verifique permissões de escrita",
                )

        self._export_btn.configure(text="Exportando...", state="disabled")
        threading.Thread(target=_do_export, daemon=True).start()
        self.after(3000, lambda: self._export_btn.configure(state="normal"))

    def destroy(self) -> None:
        if self._search_timer:
            try:
                self.after_cancel(self._search_timer)
            except Exception:
                pass
        super().destroy()
