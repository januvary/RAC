#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC Application Main
Main application window with screen management
"""

import customtkinter as ctk
from typing import Optional

from src.utils.config import ConfigManager
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel
from src.utils.paths import ensure_data_dir_exists
from src.database.rac_database import RACDatabase
from src.state.rac_state_manager import RACStateManager


class RACApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("RAC - Registros Alto Custo")
        self.geometry("800x600")
        self.minsize(700, 500)

        self.db: Optional[RACDatabase] = None
        self.state_manager: Optional[RACStateManager] = None
        self._config_manager: Optional[ConfigManager] = None
        self._current_screen: Optional[ctk.CTkFrame] = None

        ensure_data_dir_exists()

        self._config_manager = ConfigManager()
        self._config_manager.apply_theme()

        self._setup_ui()

        self.after(100, self._deferred_init)

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_ui(self) -> None:
        self._screen_container = ctk.CTkFrame(self, fg_color="transparent")
        self._screen_container.pack(fill="both", expand=True)

    def _deferred_init(self) -> None:
        try:
            self.db = RACDatabase()
            self.state_manager = RACStateManager()

            auto_return = self._config_manager.get("auto_return", True)
            self.state_manager.set_auto_return(auto_return)

            save_path = self._config_manager.get("save_path")
            if save_path:
                from pathlib import Path
                self.state_manager.set_save_path(Path(save_path))

            last_malote_id = self._config_manager.get("last_malote_id")
            if last_malote_id:
                malote = self.db.get_malote_by_id(last_malote_id)
                if malote:
                    self.state_manager.set_active_malote(malote)

            self.show_start_screen()

            ErrorHandler.log(
                "RAC inicializado com sucesso",
                level=ErrorLevel.INFO,
                context=ErrorContext.UI,
            )
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                context=ErrorContext.DATABASE,
                recovery_hint="Verifique se o banco de dados está acessível",
            )

    def show_start_screen(self) -> None:
        self._switch_screen("start")

    def show_entry_screen(
        self, tipo: str, registro: Optional[dict] = None
    ) -> None:
        self.state_manager.set_current_tipo(tipo)
        self.state_manager.set_editing_registro(registro)
        self._switch_screen("entry", tipo=tipo, registro=registro)

    def _switch_screen(self, screen_name: str, **kwargs) -> None:
        if self._current_screen is not None:
            self._current_screen.destroy()
            self._current_screen = None

        if screen_name == "start":
            from src.ui.screens.start_screen import StartScreen
            self._current_screen = StartScreen(self._screen_container, self)
        elif screen_name == "entry":
            from src.ui.screens.entry_screen import EntryScreen
            self._current_screen = EntryScreen(
                self._screen_container,
                self,
                tipo=kwargs.get("tipo", ""),
                registro=kwargs.get("registro"),
            )

        if self._current_screen:
            self._current_screen.pack(fill="both", expand=True)

    def _on_closing(self) -> None:
        try:
            if self.state_manager:
                malote = self.state_manager.get_active_malote()
                if malote:
                    self._config_manager.set("last_malote_id", malote["id"])

                auto_return = self.state_manager.get_auto_return()
                self._config_manager.set("auto_return", auto_return)

            if self.db:
                self.db.close()
        except Exception as e:
            ErrorHandler.log(
                f"Erro ao fechar: {e}",
                level=ErrorLevel.WARNING,
                context=ErrorContext.UI,
            )

        self.destroy()
