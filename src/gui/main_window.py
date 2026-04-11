#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Window — QStackedWidget page navigation
"""

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.database.rac_database import RACDatabase
from src.state.rac_state_manager import RACStateManager
from src.utils.config import ConfigManager
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel
from src.gui.styles import STYLESHEET


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RAC - Registros Alto Custo")
        self.setMinimumSize(750, 600)
        self.resize(900, 700)

        self.setStyleSheet(STYLESHEET)

        font = QFont("Inter", 10)
        font.setStyleHint(QFont.StyleHint.SansSerif)
        self.setFont(font)

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        self._pages: dict[str, QWidget] = {}

        self.db: RACDatabase | None = None
        self.state: RACStateManager | None = None
        self.config: ConfigManager | None = None

    def init_backend(self):
        self.config = ConfigManager()
        self.config.apply_theme()
        self.db = RACDatabase()
        self.state = RACStateManager()

        auto_return = self.config.get("auto_return", True)
        self.state.set_auto_return(auto_return)

        last_malote_id = self.config.get("last_malote_id")
        if last_malote_id:
            malote = self.db.get_malote_by_id(last_malote_id)
            if malote:
                self.state.set_active_malote(malote)

        ErrorHandler.log(
            "RAC inicializado",
            level=ErrorLevel.INFO,
            context=ErrorContext.UI,
        )

    def shutdown_backend(self):
        if self.state and self.config:
            malote = self.state.get_active_malote()
            if malote:
                self.config.set("last_malote_id", malote["id"])
            self.config.set("auto_return", self.state.get_auto_return())
        if self.db:
            self.db.close()

    def navigate_to(self, page_name: str, **kwargs):
        if page_name == "start":
            self._show_start_page()
        elif page_name == "entry":
            tipo = kwargs.get("tipo", "entrada")
            edit_id = kwargs.get("edit_id")
            self._show_entry_page(tipo, edit_id)

    def _show_start_page(self):
        from src.gui.pages.start_page import StartPage
        for i in range(self._stack.count()):
            w = self._stack.widget(i)
            if isinstance(w, StartPage):
                w.refresh()
                self._stack.setCurrentWidget(w)
                return

        page = StartPage(self)
        self._stack.addWidget(page)
        self._stack.setCurrentWidget(page)

    def _show_entry_page(self, tipo: str, edit_id: int | None = None):
        from src.gui.pages.entry_page import EntryPage
        while self._stack.count() > 1:
            w = self._stack.widget(self._stack.count() - 1)
            if isinstance(w, EntryPage):
                self._stack.removeWidget(w)
                w.deleteLater()

        page = EntryPage(self, tipo, edit_id)
        self._stack.addWidget(page)
        self._stack.setCurrentWidget(page)

    def closeEvent(self, event):
        self.shutdown_backend()
        super().closeEvent(event)
