#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC Dialogs
Malote creation, malote switcher, new patient, and delete confirmation dialogs
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from datetime import datetime, date

import customtkinter as ctk

if TYPE_CHECKING:
    from src.ui.main import RACApp

from src.ui.theme import AppTheme
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel


class MaloteCreationDialog(ctk.CTkToplevel):
    def __init__(self, parent, app: RACApp) -> None:
        super().__init__(parent)
        self.app = app
        self.result: Optional[dict] = None

        self.title("Novo Malote")
        self.geometry("300x180")
        self.resizable(False, False)
        self.transient(parent)
        self.after(50, self._safe_grab)

        self._build_ui()

        self._date_entry.focus_set()

    def _safe_grab(self) -> None:
        try:
            self.wait_visibility()
            self.grab_set()
        except Exception:
            pass

    def _build_ui(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="Data do malote:",
            font=AppTheme.FONT_BODY,
            text_color=AppTheme.COLOR_FG_PRIMARY,
        ).pack(anchor="w", pady=(0, 5))

        self._date_entry = ctk.CTkEntry(
            frame,
            placeholder_text="dd/mm ou dd/mm/aa",
            font=AppTheme.FONT_BODY,
            height=32,
        )
        self._date_entry.pack(fill="x", pady=(0, 15))
        self._date_entry.bind("<Return>", lambda e: self._on_confirm())

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            font=AppTheme.FONT_BODY,
            width=100,
            height=32,
            fg_color=AppTheme.COLOR_DANGER,
            hover_color=AppTheme.COLOR_DANGER_HOVER,
            command=self.destroy,
        ).pack(side="right")

        ctk.CTkButton(
            btn_frame,
            text="Criar",
            font=AppTheme.FONT_BODY,
            width=100,
            height=32,
            fg_color=AppTheme.COLOR_SUCCESS,
            hover_color=AppTheme.COLOR_SUCCESS_HOVER,
            command=self._on_confirm,
        ).pack(side="right", padx=(0, 10))

    def _parse_date(self, text: str) -> Optional[str]:
        text = text.strip()
        if not text:
            return None

        today = date.today()
        separators = ["/", "-", "."]
        for sep in separators:
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
                year_part = int(parts[2])
                year = 2000 + year_part if year_part < 100 else year_part
            else:
                return None

            dt = date(year, month, day)
            return dt.isoformat()
        except (ValueError, IndexError):
            return None

    def _on_confirm(self) -> None:
        date_str = self._parse_date(self._date_entry.get())
        if not date_str:
            self._date_entry.configure(border_color=AppTheme.COLOR_DANGER)
            return

        try:
            malote = self.app.db.create_malote(date_str)
            self.app.state_manager.set_active_malote(malote)
            self.result = malote
            self.destroy()
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                context=ErrorContext.MALOTE,
            )


class MaloteSwitcherDialog(ctk.CTkToplevel):
    def __init__(self, parent, app: RACApp) -> None:
        super().__init__(parent)
        self.app = app

        self.title("Malotes")
        self.geometry("350x450")
        self.resizable(False, True)
        self.transient(parent)
        self.after(50, self._safe_grab)

        self._build_ui()

    def _safe_grab(self) -> None:
        try:
            self.wait_visibility()
            self.grab_set()
        except Exception:
            pass

    def _build_ui(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkLabel(
            header,
            text="Malotes",
            font=AppTheme.FONT_HEADER,
            text_color=AppTheme.COLOR_FG_PRIMARY,
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="+ Novo",
            font=AppTheme.FONT_SMALL,
            width=70,
            height=28,
            fg_color=AppTheme.COLOR_SUCCESS,
            hover_color=AppTheme.COLOR_SUCCESS_HOVER,
            command=self._on_new_malote,
        ).pack(side="right")

        self._list_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent"
        )
        self._list_frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        self._load_malotes()

    def _load_malotes(self) -> None:
        for widget in self._list_frame.winfo_children():
            widget.destroy()

        malotes = self.app.db.get_all_malotes()
        active = self.app.state_manager.get_active_malote() if self.app.state_manager else None

        for malote in malotes:
            try:
                dt = datetime.fromisoformat(malote["date"])
                display = dt.strftime("%d/%m/%Y")
            except (ValueError, KeyError):
                display = malote.get("date", "?")

            is_active = active and active["id"] == malote["id"]
            fg = AppTheme.COLOR_ACCENT if is_active else AppTheme.COLOR_BG_TERTIARY

            row = ctk.CTkButton(
                self._list_frame,
                text=f"{'● ' if is_active else ''}{display}",
                font=AppTheme.FONT_BODY,
                fg_color=fg if not is_active else AppTheme.COLOR_ACCENT,
                hover_color=AppTheme.COLOR_ACCENT_HOVER,
                anchor="w",
                height=36,
                command=lambda m=malote: self._on_select_malote(m),
            )
            row.pack(fill="x", pady=2)

    def _on_select_malote(self, malote: dict) -> None:
        self.app.state_manager.set_active_malote(malote)
        self.destroy()

    def _on_new_malote(self) -> None:
        dialog = MaloteCreationDialog(self, self.app)
        self.wait_window(dialog)

        if dialog.result:
            self._load_malotes()


class NewPatientDialog(ctk.CTkToplevel):
    def __init__(self, parent, app: RACApp, prefill: str = "") -> None:
        super().__init__(parent)
        self.app = app
        self.result: Optional[dict] = None

        self.title("Novo Paciente")
        self.geometry("300x180")
        self.resizable(False, False)
        self.transient(parent)
        self.after(50, self._safe_grab)

        self._build_ui(prefill)

    def _safe_grab(self) -> None:
        try:
            self.wait_visibility()
            self.grab_set()
        except Exception:
            pass

    def _build_ui(self, prefill: str) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="Nome do paciente:",
            font=AppTheme.FONT_BODY,
            text_color=AppTheme.COLOR_FG_PRIMARY,
        ).pack(anchor="w", pady=(0, 5))

        self._name_entry = ctk.CTkEntry(
            frame,
            font=AppTheme.FONT_BODY,
            height=32,
        )
        self._name_entry.pack(fill="x", pady=(0, 15))

        if prefill:
            self._name_entry.insert(0, prefill)

        self._name_entry.focus_set()
        self._name_entry.bind("<Return>", lambda e: self._on_confirm())

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            font=AppTheme.FONT_BODY,
            width=100,
            height=32,
            fg_color=AppTheme.COLOR_DANGER,
            hover_color=AppTheme.COLOR_DANGER_HOVER,
            command=self.destroy,
        ).pack(side="right")

        ctk.CTkButton(
            btn_frame,
            text="Criar",
            font=AppTheme.FONT_BODY,
            width=100,
            height=32,
            fg_color=AppTheme.COLOR_SUCCESS,
            hover_color=AppTheme.COLOR_SUCCESS_HOVER,
            command=self._on_confirm,
        ).pack(side="right", padx=(0, 10))

    def _on_confirm(self) -> None:
        name = self._name_entry.get().strip()
        if not name:
            self._name_entry.configure(border_color=AppTheme.COLOR_DANGER)
            return

        try:
            paciente = self.app.db.create_paciente(name)
            self.result = paciente
            self.destroy()
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                context=ErrorContext.DATABASE,
                recovery_hint="Paciente já existe?",
            )


class ConfirmDeleteDialog(ctk.CTkToplevel):
    def __init__(self, parent, app: RACApp) -> None:
        super().__init__(parent)
        self.app = app
        self.result: bool = False

        self.title("Confirmar Exclusão")
        self.geometry("300x150")
        self.resizable(False, False)
        self.transient(parent)
        self.after(50, self._safe_grab)

        self._build_ui()

    def _safe_grab(self) -> None:
        try:
            self.wait_visibility()
            self.grab_set()
        except Exception:
            pass

    def _build_ui(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="Excluir este registro?",
            font=AppTheme.FONT_HEADER,
            text_color=AppTheme.COLOR_FG_PRIMARY,
        ).pack(anchor="w", pady=(0, 15))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            font=AppTheme.FONT_BODY,
            width=100,
            height=32,
            fg_color=AppTheme.COLOR_ACCENT,
            hover_color=AppTheme.COLOR_ACCENT_HOVER,
            command=self.destroy,
        ).pack(side="right")

        ctk.CTkButton(
            btn_frame,
            text="Excluir",
            font=AppTheme.FONT_BODY,
            width=100,
            height=32,
            fg_color=AppTheme.COLOR_DANGER,
            hover_color=AppTheme.COLOR_DANGER_HOVER,
            command=self._on_confirm,
        ).pack(side="right", padx=(0, 10))

    def _on_confirm(self) -> None:
        self.result = True
        self.destroy()
