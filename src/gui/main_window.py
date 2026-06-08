#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Window — QStackedWidget page navigation
"""

from contextlib import suppress

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QShortcut, QKeySequence

from src.database.rac_database import RACDatabase
from src.state.rac_state_manager import RACStateManager
from andaime.config import ConfigManager
from andaime.error_handler import ErrorHandler, ErrorLevel

from src.gui.constants import TIPO_LABELS


class MainWindow(QMainWindow):
    theme_changed = Signal()

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
        self.installEventFilter(self)

        self.db: RACDatabase | None = None
        self.state: RACStateManager | None = None
        self.config: ConfigManager | None = None
        self._shortcut_peek_active = False

    def init_backend(self):
        self.config = ConfigManager()
        self.db = RACDatabase()
        self.state = RACStateManager()

        saved_theme = self.config.get("theme", "light")
        from src.gui.styles import set_theme

        set_theme(saved_theme)

        stay_on_page = self.config.get("stay_on_page", False)
        self.state.set_stay_on_page(stay_on_page)

        last_malote_id = self.config.get("last_malote_id")
        if last_malote_id:
            malote = self.db.get_malote_by_id(last_malote_id)
            if malote:
                self.state.set_active_malote(malote)

        self._setup_shortcuts()

    def eventFilter(self, obj, event):
        with suppress(Exception):
            etype = event.type()
            if etype == QEvent.Type.KeyPress:
                if (
                    event.key() == Qt.Key.Key_Shift
                    and event.modifiers() & Qt.KeyboardModifier.ControlModifier
                ):
                    self._toggle_shortcut_peek(True)
                elif (
                    event.key() == Qt.Key.Key_Control
                    and event.modifiers() & Qt.KeyboardModifier.ShiftModifier
                ):
                    self._toggle_shortcut_peek(True)
            elif etype == QEvent.Type.KeyRelease:
                if event.key() in (Qt.Key.Key_Shift, Qt.Key.Key_Control):
                    mods = event.modifiers()
                    has_ctrl = mods & Qt.KeyboardModifier.ControlModifier
                    has_shift = mods & Qt.KeyboardModifier.ShiftModifier
                    if not (has_ctrl and has_shift):
                        self._toggle_shortcut_peek(False)
        return super().eventFilter(obj, event)

    def _toggle_shortcut_peek(self, show: bool):
        if show == self._shortcut_peek_active:
            return
        self._shortcut_peek_active = show
        page = self._current_page()
        if page and hasattr(page, "set_shortcuts_visible"):
            page.set_shortcuts_visible(show)

        ErrorHandler.log(
            "RAC inicializado",
            level=ErrorLevel.INFO,
            context="User Interface",
        )

    def shutdown_backend(self):
        if self.state and self.config:
            malote = self.state.get_active_malote()
            if malote:
                self.config.set("last_malote_id", malote.id)
            self.config.set("stay_on_page", self.state.get_stay_on_page())
        if self.db:
            self.db.close()

    def navigate_to(self, page_name: str, **kwargs):
        self._toggle_shortcut_peek(False)
        if page_name == "start":
            self._show_start_page()
        elif page_name == "entry":
            tipo = kwargs.get("tipo", "entrada")
            edit_id = kwargs.get("edit_id")
            return_to = kwargs.get("return_to", "start")
            self._show_entry_page(tipo, edit_id, return_to)
        elif page_name == "preview":
            self._show_preview_page()
        elif page_name == "lists":
            self._show_list_manage_page()
        elif page_name == "stats":
            self._show_stats_page()

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

    def _push_page(self, page_class, *args, **kwargs):
        self._clear_above_start()
        page = page_class(self, *args, **kwargs)
        self._stack.addWidget(page)
        self._stack.setCurrentWidget(page)

    def _show_entry_page(
        self, tipo: str, edit_id: int | None = None, return_to: str = "start"
    ):
        from src.gui.pages.entry_page import EntryPage

        self._push_page(EntryPage, tipo, edit_id, return_to)

    def _show_preview_page(self):
        from src.gui.pages.preview_page import PreviewPage

        self._push_page(PreviewPage)

    def _show_list_manage_page(self):
        from src.gui.pages.list_manage_page import ListManagePage

        self._push_page(ListManagePage)

    def _show_stats_page(self):
        from src.gui.pages.stats_page import StatsPage

        self._push_page(StatsPage)

    _TIPO_SHORTCUTS = {
        0: "entrada",
        1: "renovacao",
        2: "retirada",
        3: "urgente",
    }

    def _setup_shortcuts(self):
        shortcuts = [
            ("Ctrl+S", self._shortcut_save),
            ("Ctrl+E", self._shortcut_export),
            (Qt.Key.Key_Escape, self._shortcut_back),
            ("Ctrl+D", self._shortcut_malote_dialog),
            ("Ctrl+R", self._shortcut_focus_search),
            ("Ctrl+G", self._shortcut_preview),
            ("Ctrl+T", self._shortcut_lists),
            ("Ctrl+F", self._shortcut_add_item),
            ("Ctrl+W", self._shortcut_toggle_docs),
            ("Ctrl+Q", self._shortcut_toggle_stay_on_page),
            ("Ctrl+Y", self._shortcut_stats),
        ]
        for key, handler in shortcuts:
            seq = QKeySequence(key)
            QShortcut(seq, self, handler)
            if isinstance(key, str):
                shifted = QKeySequence(key.replace("Ctrl+", "Ctrl+Shift+"))
                QShortcut(shifted, self, handler)
        for idx, tipo in self._TIPO_SHORTCUTS.items():
            handler = lambda _checked=False, t=tipo: self._shortcut_tipo_by_key(t)
            for modifier in ("Ctrl+", "Ctrl+Shift+"):
                QShortcut(QKeySequence(f"{modifier}{idx + 1}"), self, handler)

    def _current_page(self):
        return self._stack.currentWidget()

    def _on_page(self, page_class, fn):
        page = self._current_page()
        if isinstance(page, page_class):
            fn(page)

    def _shortcut_save(self):
        from src.gui.pages.entry_page import EntryPage

        self._on_page(EntryPage, lambda p: p._on_save())

    def _shortcut_export(self):
        from src.gui.pages.start_page import StartPage

        self._on_page(StartPage, lambda p: p._on_export())

    def _shortcut_back(self):
        from src.gui.pages.entry_page import EntryPage
        from src.gui.pages.preview_page import PreviewPage
        from src.gui.pages.list_manage_page import ListManagePage

        self._on_page(EntryPage, lambda p: self.navigate_to(p._return_to))
        self._on_page((PreviewPage, ListManagePage), lambda p: self.navigate_to("start"))

    def _shortcut_malote_dialog(self):
        page = self._current_page()
        if hasattr(page, '_malote_label'):
            page._malote_label.open_dialog()

    def _shortcut_focus_search(self):
        page = self._current_page()
        from src.gui.pages.start_page import StartPage
        from src.gui.pages.entry_page import EntryPage
        from src.gui.pages.list_manage_page import ListManagePage
        from src.gui.pages.preview_page import PreviewPage

        if isinstance(page, StartPage):
            page._search_combo.focus_search()
        elif isinstance(page, EntryPage):
            page.focus_next_field()
        elif isinstance(page, ListManagePage):
            search = (
                page._items_tab.search
                if page._tabs.currentIndex() == 0
                else page._pacientes_tab.search
            )
            search.setFocus()
            search.selectAll()
        elif isinstance(page, PreviewPage):
            search = page._tab_searches.get(page._tabs.currentIndex())
            if search:
                search.setFocus()
                search.selectAll()

    def _shortcut_add_item(self):
        from src.gui.pages.entry_page import EntryPage

        def _do(p):
            combo = p._add_item_row()
            if combo:
                combo.focus_search()
        self._on_page(EntryPage, _do)

    def _shortcut_toggle_docs(self):
        from src.gui.pages.entry_page import EntryPage

        self._on_page(EntryPage, lambda p: p._docs_check.toggle())

    def _shortcut_toggle_stay_on_page(self):
        from src.gui.pages.entry_page import EntryPage

        self._on_page(EntryPage, lambda p: p._auto_switch.toggle())

    def _navigate_from_start(self, target: str):
        from src.gui.pages.start_page import StartPage

        self._on_page(StartPage, lambda p: self.navigate_to(target))

    def _shortcut_preview(self):
        self._navigate_from_start("preview")

    def _shortcut_lists(self):
        self._navigate_from_start("lists")

    def _shortcut_stats(self):
        self._navigate_from_start("stats")

    def _shortcut_tipo_by_key(self, tipo: str):
        from src.gui.pages.start_page import StartPage
        from src.gui.pages.entry_page import EntryPage
        from src.gui.pages.preview_page import PreviewPage

        if self.state and self.state.has_active_malote():
            self._on_page(StartPage, lambda p: self.navigate_to("entry", tipo=tipo))
        self._on_page(EntryPage, lambda p: p._tipo_combo.set_tipo(tipo))

        def _set_tab(p):
            idx = list(TIPO_LABELS.keys()).index(tipo)
            if p._tabs and idx < p._tabs.count():
                p._tabs.setCurrentIndex(idx)
        self._on_page(PreviewPage, _set_tab)

    def closeEvent(self, event):
        self.shutdown_backend()
        super().closeEvent(event)
