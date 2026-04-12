#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Window — QStackedWidget page navigation
"""

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence

from src.database.rac_database import RACDatabase
from src.state.rac_state_manager import RACStateManager
from src.utils.config import ConfigManager
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RAC - Registros Alto Custo")
        self.setMinimumSize(750, 600)
        self.resize(900, 700)

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
        self.db = RACDatabase()
        self.state = RACStateManager()

        auto_return = self.config.get("auto_return", True)
        self.state.set_auto_return(auto_return)

        last_malote_id = self.config.get("last_malote_id")
        if last_malote_id:
            malote = self.db.get_malote_by_id(last_malote_id)
            if malote:
                self.state.set_active_malote(malote)

        self._setup_shortcuts()

        ErrorHandler.log(
            "RAC inicializado",
            level=ErrorLevel.INFO,
            context=ErrorContext.UI,
        )

    def shutdown_backend(self):
        if self.state and self.config:
            malote = self.state.get_active_malote()
            if malote:
                self.config.set("last_malote_id", malote.id)
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
        elif page_name == "preview":
            self._show_preview_page()

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

    def _clear_above_start(self):
        while self._stack.count() > 1:
            w = self._stack.widget(self._stack.count() - 1)
            if w is None:
                break
            self._stack.removeWidget(w)
            w.deleteLater()

    def _show_entry_page(self, tipo: str, edit_id: int | None = None):
        from src.gui.pages.entry_page import EntryPage
        self._clear_above_start()

        page = EntryPage(self, tipo, edit_id)
        self._stack.addWidget(page)
        self._stack.setCurrentWidget(page)

    def _show_preview_page(self):
        from src.gui.pages.preview_page import PreviewPage
        self._clear_above_start()

        page = PreviewPage(self)
        self._stack.addWidget(page)
        self._stack.setCurrentWidget(page)

    _TIPO_KEYS = ["entrada", "renovacao", "retirada", "urgente"]

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+S"), self, self._shortcut_save)
        QShortcut(QKeySequence("Ctrl+E"), self, self._shortcut_export)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self._shortcut_back)
        QShortcut(QKeySequence("Ctrl+D"), self, self._shortcut_malote_dialog)
        QShortcut(QKeySequence("Ctrl+R"), self, self._shortcut_focus_search)
        QShortcut(QKeySequence("Ctrl+G"), self, self._shortcut_preview)
        for i in range(len(self._TIPO_KEYS)):
            idx = i
            QShortcut(
                QKeySequence(f"Ctrl+{idx + 1}"),
                self,
                lambda checked=False, ii=idx: self._shortcut_tipo(ii),
            )

    def _current_page(self):
        return self._stack.currentWidget()

    def _shortcut_save(self):
        page = self._current_page()
        from src.gui.pages.entry_page import EntryPage
        if isinstance(page, EntryPage):
            page._on_save()

    def _shortcut_export(self):
        page = self._current_page()
        from src.gui.pages.start_page import StartPage
        if isinstance(page, StartPage):
            page._on_export()

    def _shortcut_back(self):
        page = self._current_page()
        from src.gui.pages.entry_page import EntryPage
        from src.gui.pages.preview_page import PreviewPage
        if isinstance(page, (EntryPage, PreviewPage)):
            self.navigate_to("start")

    def _shortcut_malote_dialog(self):
        page = self._current_page()
        from src.gui.pages.start_page import StartPage
        from src.gui.pages.preview_page import PreviewPage
        from src.gui.pages.entry_page import EntryPage
        if isinstance(page, StartPage):
            page._malote_label.mousePressEvent(None)
        elif isinstance(page, PreviewPage):
            page._malote_label.mousePressEvent(None)
        elif isinstance(page, EntryPage):
            page._malote_label.mousePressEvent(None)

    def _shortcut_focus_search(self):
        page = self._current_page()
        from src.gui.pages.start_page import StartPage
        from src.gui.pages.entry_page import EntryPage
        if isinstance(page, StartPage):
            page._search_combo.focus_search()
        elif isinstance(page, EntryPage):
            page.focus_next_field()

    def _shortcut_preview(self):
        page = self._current_page()
        from src.gui.pages.start_page import StartPage
        if isinstance(page, StartPage):
            self.navigate_to("preview")

    def _shortcut_tipo(self, idx: int):
        page = self._current_page()
        from src.gui.pages.start_page import StartPage
        from src.gui.pages.entry_page import EntryPage
        from src.gui.pages.preview_page import PreviewPage
        tipo = self._TIPO_KEYS[idx]
        if isinstance(page, StartPage):
            if self.state and self.state.has_active_malote():
                self.navigate_to("entry", tipo=tipo)
        elif isinstance(page, EntryPage):
            page._tipo_combo.set_tipo(tipo)
        elif isinstance(page, PreviewPage):
            if page._tabs and idx < page._tabs.count():
                page._tabs.setCurrentIndex(idx)

    def closeEvent(self, event):
        self.shutdown_backend()
        super().closeEvent(event)
