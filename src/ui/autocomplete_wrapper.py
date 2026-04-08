#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autocomplete Wrapper
Wrapper para adicionar autocomplete a CTkEntry existente
"""

import time
import tkinter as tk
from contextlib import suppress
from tkinter import TclError
from typing import List, Any, Callable, Optional, Union

import customtkinter as ctk
from src.ui.theme import AppTheme

EntryWidget = Union[tk.Entry, ctk.CTkEntry]


class AutocompleteWrapper:
    MIN_CHARS_TO_SEARCH = 1
    MAX_RESULTS = 10

    def __init__(
        self,
        ctk_entry: EntryWidget,
        search_function: Callable[[str], List[Any]],
        on_select_callback: Optional[Callable[[Any], Optional[str]]] = None,
        fixed_position: Optional[tuple] = None,
    ) -> None:
        self.ctk_entry = ctk_entry
        self.search_function = search_function
        self.on_select_callback = on_select_callback
        self._fixed_position = fixed_position

        self.dropdown_frame: Optional[tk.Toplevel] = None
        self.dropdown_listbox: Optional[tk.Listbox] = None
        self.current_results: List[Any] = []
        self._is_showing_dropdown = False
        self._search_timer: Optional[str] = None
        self._dropdown_created_at = 0
        self._dropdown_immunity_ms = 150

        self._root_window: Optional[Union[tk.Tk, tk.Toplevel]] = None
        self._global_click_callback_id: Optional[str] = None
        self._window_has_focus = True
        self._highlighted_index: int = -1

        self.ctk_entry.bind("<KeyRelease>", self._on_key_release)
        self.ctk_entry.bind("<Down>", self._on_arrow_down)
        self.ctk_entry.bind("<Up>", self._on_arrow_up)
        self.ctk_entry.bind("<Return>", self._on_enter_key)
        self.ctk_entry.bind("<Escape>", self._on_escape_key)
        self.ctk_entry.after(100, self._setup_global_bind)

    def _on_key_release(self, event: Any) -> None:
        if self._search_timer:
            self.ctk_entry.after_cancel(self._search_timer)

        if event.keysym in ("Up", "Down", "Left", "Right", "Return", "Escape"):
            return

        self._search_timer = self.ctk_entry.after(150, self._perform_search)

    def _setup_global_bind(self) -> None:
        self._root_window = self.ctk_entry.winfo_toplevel()
        if self._root_window:
            self._global_click_callback_id = self._root_window.bind(
                "<Button-1>", self._on_global_click, add=True
            )
            self._root_window.bind("<FocusIn>", self._on_window_focus_in, add=True)
            self._root_window.bind("<FocusOut>", self._on_window_focus_out, add=True)

    def _on_arrow_down(self, event: Any) -> str | None:
        if not self._is_showing_dropdown or not self.dropdown_listbox:
            return "break"

        num_items = len(self.current_results)
        if num_items == 0:
            return "break"

        if self._highlighted_index < 0:
            self._highlighted_index = 0
        elif self._highlighted_index < num_items - 1:
            self._highlighted_index += 1

        self._update_highlight()
        return "break"

    def _on_arrow_up(self, event: Any) -> str | None:
        if not self._is_showing_dropdown or not self.dropdown_listbox:
            return "break"

        num_items = len(self.current_results)
        if num_items == 0:
            return "break"

        if self._highlighted_index <= 0:
            self._highlighted_index = num_items - 1
        else:
            self._highlighted_index -= 1

        self._update_highlight()
        return "break"

    def _on_enter_key(self, event: Any) -> str | None:
        if self._is_showing_dropdown and self._highlighted_index >= 0:
            if self._highlighted_index < len(self.current_results):
                result = self.current_results[self._highlighted_index]

                clean_value = None
                if self.on_select_callback:
                    with suppress(Exception):
                        clean_value = self.on_select_callback(result)

                try:
                    self.ctk_entry.delete(0, "end")
                    value_to_insert = clean_value if clean_value is not None else ""
                    self.ctk_entry.insert(0, value_to_insert)
                except tk.TclError:
                    pass

                self.hide_dropdown()
                return "break"

        return None

    def _on_escape_key(self, event: Any) -> str | None:
        if self._is_showing_dropdown:
            self.hide_dropdown()
            return "break"
        return None

    def _update_highlight(self) -> None:
        if not self.dropdown_listbox:
            return

        self.dropdown_listbox.selection_clear(0, "end")

        if 0 <= self._highlighted_index < len(self.current_results):
            self.dropdown_listbox.selection_set(self._highlighted_index)
            self.dropdown_listbox.see(self._highlighted_index)

    def _on_global_click(self, event: Any) -> None:
        if not self._is_showing_dropdown or not self.dropdown_frame:
            return

        time_since_creation = (time.time() * 1000) - self._dropdown_created_at
        if time_since_creation < self._dropdown_immunity_ms:
            return

        if self._search_timer is not None:
            return

        clicked_widget = event.widget
        if clicked_widget is None:
            return

        with suppress(Exception):
            if self._is_descendant_of(clicked_widget, self.dropdown_frame):
                return
            if self._is_descendant_of(clicked_widget, self.ctk_entry):
                return
            self.hide_dropdown()

    def _is_descendant_of(self, widget: Any, ancestor: Any) -> bool:
        if widget is None or ancestor is None:
            return False
        current = widget
        while current:
            if current == ancestor:
                return True
            current = current.master
        return False

    def _on_window_focus_in(self, event: Any) -> None:
        if event.widget == self._root_window:
            self._window_has_focus = True

    def _on_window_focus_out(self, event: Any) -> None:
        if self._root_window is None:
            return
        if event.widget != self._root_window:
            return

        try:
            focused_widget = self._root_window.focus_displayof()
        except (KeyError, TclError):
            focused_widget = None

        if self._is_showing_dropdown and focused_widget is None:
            return

        if focused_widget:
            if focused_widget == self.ctk_entry:
                return
            if self.dropdown_frame and focused_widget == self.dropdown_frame:
                return

        if focused_widget is None or not self._is_descendant_of(
            focused_widget, self._root_window
        ):
            self.hide_dropdown()
            self._window_has_focus = False

    def _perform_search(self) -> None:
        query = self.ctk_entry.get().strip()

        if len(query) < self.MIN_CHARS_TO_SEARCH:
            self.hide_dropdown()
            return

        try:
            results = self.search_function(query)
            self.current_results = results

            if results:
                self._show_dropdown(results)
            else:
                self.hide_dropdown()
        except Exception:
            self.hide_dropdown()

        self._search_timer = None

    def _show_dropdown(self, results: List[Any]) -> None:
        if self._is_showing_dropdown:
            if self.dropdown_listbox:
                self.dropdown_listbox.delete(0, "end")
                for result in results[: self.MAX_RESULTS]:
                    self.dropdown_listbox.insert("end", str(result))
            return

        if self._fixed_position:
            if len(self._fixed_position) == 3:
                entry_x, entry_y, entry_width = self._fixed_position
            else:
                entry_x, entry_y = self._fixed_position
                entry_width = self.ctk_entry.winfo_width()
        else:
            try:
                entry_x = self.ctk_entry.winfo_rootx()
                entry_y = self.ctk_entry.winfo_rooty() + self.ctk_entry.winfo_height()
                entry_width = self.ctk_entry.winfo_width()
            except Exception:
                return

        self.dropdown_frame = tk.Toplevel()
        self._dropdown_created_at = int(time.time() * 1000)
        self.dropdown_frame.wm_overrideredirect(True)
        self.dropdown_frame.attributes("-topmost", True)

        est_height = self.MAX_RESULTS * 28
        est_width = entry_width + 20
        self.dropdown_frame.geometry(
            f"{est_width}x{est_height}+{entry_x}+{entry_y}"
        )

        colors = self._get_dropdown_colors()
        self.dropdown_listbox = tk.Listbox(
            self.dropdown_frame,
            height=self.MAX_RESULTS,
            selectmode="single",
            font=AppTheme.FONT_TREEVIEW if hasattr(AppTheme, 'FONT_TREEVIEW') else ("Segoe UI", 10),
            bg=colors["bg"],
            fg=colors["fg"],
            selectbackground=colors["select_bg"],
            selectforeground=colors["select_fg"],
            relief="flat",
            highlightthickness=0,
        )
        self.dropdown_listbox.pack(fill="both", expand=True)

        for result in results[: self.MAX_RESULTS]:
            self.dropdown_listbox.insert("end", str(result))

        self._highlighted_index = 0 if results else -1
        self._update_highlight()

        self.dropdown_listbox.update_idletasks()
        self.dropdown_frame.geometry(
            f"{est_width}x{est_height}+{entry_x}+{entry_y}"
        )

        self.dropdown_listbox.bind("<ButtonRelease-1>", self._on_result_selected)
        self.dropdown_listbox.bind("<Return>", self._on_result_selected)
        self.dropdown_listbox.bind("<Escape>", lambda e: self.hide_dropdown())

        self._is_showing_dropdown = True

    def _get_dropdown_colors(self) -> dict:
        is_dark = AppTheme.is_dark_mode()
        idx = 1 if is_dark else 0
        return {
            "bg": AppTheme.DROPDOWN_BG[idx],
            "fg": AppTheme.DROPDOWN_FG[idx],
            "select_bg": AppTheme.DROPDOWN_SELECTED_BG[idx],
            "select_fg": AppTheme.DROPDOWN_SELECTED_FG[idx],
        }

    def _on_result_selected(self, event: Any) -> None:
        if not self.ctk_entry or not self.ctk_entry.winfo_exists():
            self.hide_dropdown()
            return

        if self.dropdown_listbox is None:
            return

        selection = self.dropdown_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        if idx < len(self.current_results):
            result = self.current_results[idx]

            clean_value = None
            if self.on_select_callback:
                with suppress(Exception):
                    clean_value = self.on_select_callback(result)

            try:
                self.ctk_entry.delete(0, "end")
                value_to_insert = clean_value if clean_value is not None else ""
                self.ctk_entry.insert(0, value_to_insert)
                self.ctk_entry.focus_set()
            except tk.TclError:
                pass

        self.hide_dropdown()

    def hide_dropdown(self) -> None:
        if self._search_timer:
            with suppress(Exception):
                self.ctk_entry.after_cancel(self._search_timer)
            self._search_timer = None

        if self.dropdown_frame:
            with suppress(Exception):
                self.dropdown_frame.destroy()
            self.dropdown_frame = None
            self.dropdown_listbox = None

        self._is_showing_dropdown = False
        self._highlighted_index = -1

    def destroy(self) -> None:
        self.hide_dropdown()

        if self._search_timer:
            with suppress(Exception):
                self.ctk_entry.after_cancel(self._search_timer)
            self._search_timer = None

        if self._root_window and self._global_click_callback_id:
            try:
                self._root_window.unbind("<Button-1>", self._global_click_callback_id)
            except Exception:
                pass
            finally:
                self._global_click_callback_id = None
