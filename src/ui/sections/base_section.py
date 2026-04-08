#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Section Class
Classe base para todas as seções da UI com utilitários compartilhados
"""

from __future__ import annotations

import functools
from contextlib import suppress
from typing import TYPE_CHECKING, Optional, Any, Callable

import customtkinter as ctk

if TYPE_CHECKING:
    from src.ui.main import RACApp

from src.state.state_events import StateEvent, StateEventType, StateObserver
from src.ui.theme import AppTheme


def require_valid_widget(*widget_attrs: str) -> Callable:
    def decorator(method: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(method)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            for attr in widget_attrs:
                widget = getattr(self, attr, None)
                if not self.is_widget_valid(widget):
                    return None
            return method(self, *args, **kwargs)
        return wrapper
    return decorator


class BaseSection(ctk.CTkFrame, StateObserver):
    def __init__(self, parent: Any, app: RACApp, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self._app = app
        self._is_registered = False
        self._widgets_to_cleanup: list[tuple[str, Any]] = []
        self._section_header: Optional[ctk.CTkFrame] = None

        if hasattr(app, "state_manager") and app.state_manager is not None:
            self._app.after(50, lambda: app.state_manager.register_observer(self))
            self._is_registered = True

    @property
    def app(self) -> Any:
        return self._app

    def create_section_header(
        self, text: str, parent: Optional[ctk.CTkFrame] = None
    ) -> ctk.CTkFrame:
        if parent is None:
            parent = self

        header = ctk.CTkFrame(parent, fg_color=AppTheme.COLOR_BG_SECONDARY)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text=text,
            font=AppTheme.FONT_HEADER,
            text_color=AppTheme.COLOR_FG_HEADER,
            anchor="w",
        ).pack(side="left", padx=AppTheme.PADX_MEDIUM, pady=AppTheme.PADY_SMALL)

        self._section_header = header
        return header

    def create_section_container(self) -> ctk.CTkFrame:
        section_frame = ctk.CTkFrame(
            self,
            fg_color=AppTheme.COLOR_BG_SECONDARY,
            corner_radius=6,
            border_width=1,
            border_color=AppTheme.COLOR_BORDER,
        )
        section_frame.pack(fill="both", expand=True, padx=8, pady=6)

        inner_container = ctk.CTkFrame(section_frame, fg_color="transparent")
        inner_container.pack(fill="both", expand=True, padx=10, pady=10)

        return inner_container

    def register_widget(self, widget_name: str, widget: Any) -> None:
        self._widgets_to_cleanup = [
            (name, w) for name, w in self._widgets_to_cleanup if name != widget_name
        ]
        if widget is not None:
            self._widgets_to_cleanup.append((widget_name, widget))

    def cleanup_widgets(self) -> None:
        for widget_name, widget in self._widgets_to_cleanup:
            with suppress(Exception):
                setattr(self, widget_name, None)
        self._widgets_to_cleanup.clear()

    def is_widget_valid(self, widget: Any) -> bool:
        if widget is None:
            return False
        try:
            return bool(widget.winfo_exists())
        except Exception:
            return False

    def on_state_changed(self, event: StateEvent) -> None:
        try:
            if event.event_type == StateEventType.CONFIG_CHANGED:
                if self._section_header is not None:
                    if self._section_header.winfo_exists():
                        self._section_header.configure(
                            fg_color=AppTheme.COLOR_BG_SECONDARY
                        )
                        for child in self._section_header.winfo_children():
                            if isinstance(child, ctk.CTkLabel):
                                child.configure(
                                    text_color=AppTheme.COLOR_FG_HEADER
                                )
        except Exception as e:
            from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel
            ErrorHandler.log(
                f"State change error in {self.__class__.__name__}: {e}",
                level=ErrorLevel.WARNING,
                context=ErrorContext.UI,
            )

    def destroy(self) -> None:
        self._cleanup_before_destroy()

        if self._is_registered and hasattr(self.app, "state_manager"):
            try:
                self.app.state_manager.unregister_observer(self)
                self._is_registered = False
            except Exception:
                pass

        self.cleanup_widgets()
        super().destroy()

    def _cleanup_before_destroy(self) -> None:
        pass
