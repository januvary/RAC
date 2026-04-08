#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC State Manager
Centralized state management with observer pattern
"""

import threading
import copy
from typing import Optional
from pathlib import Path

from src.state.state_events import StateEvent, StateEventType, StateObserver
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel


class RACStateManager:
    def __init__(self) -> None:
        self._active_malote: Optional[dict] = None
        self._current_tipo: str = ""
        self._editing_registro: Optional[dict] = None
        self._search_query: str = ""
        self._search_results: list[dict] = []
        self._auto_return: bool = True
        self._save_path: Path = Path.home() / "Downloads"

        self._observers: list[StateObserver] = []
        self._lock = threading.RLock()

    def register_observer(self, observer: StateObserver) -> None:
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)

    def unregister_observer(self, observer: StateObserver) -> None:
        with self._lock:
            try:
                self._observers.remove(observer)
            except ValueError:
                pass

    def _notify_observers(self, event: StateEvent) -> None:
        with self._lock:
            observers = list(self._observers)

        for observer in observers:
            try:
                observer.on_state_changed(event)
            except Exception as e:
                ErrorHandler.log(
                    f"Observer error: {e}",
                    level=ErrorLevel.WARNING,
                    context=ErrorContext.STATE,
                )

    # ========== MALOTE ==========

    def get_active_malote(self) -> Optional[dict]:
        with self._lock:
            return copy.deepcopy(self._active_malote) if self._active_malote else None

    def set_active_malote(self, malote: Optional[dict]) -> None:
        with self._lock:
            self._active_malote = malote
        self._notify_observers(
            StateEvent(
                event_type=StateEventType.MALOTE_CHANGED,
                data={"malote": malote},
            )
        )

    def has_active_malote(self) -> bool:
        with self._lock:
            return self._active_malote is not None

    # ========== TIPO ==========

    def get_current_tipo(self) -> str:
        with self._lock:
            return self._current_tipo

    def set_current_tipo(self, tipo: str) -> None:
        with self._lock:
            self._current_tipo = tipo
        self._notify_observers(
            StateEvent(
                event_type=StateEventType.TIPO_SELECTED,
                data={"tipo": tipo},
            )
        )

    # ========== EDITING REGISTRO ==========

    def get_editing_registro(self) -> Optional[dict]:
        with self._lock:
            return copy.deepcopy(self._editing_registro) if self._editing_registro else None

    def set_editing_registro(self, registro: Optional[dict]) -> None:
        with self._lock:
            self._editing_registro = registro

    def is_editing(self) -> bool:
        with self._lock:
            return self._editing_registro is not None

    # ========== SEARCH ==========

    def get_search_query(self) -> str:
        with self._lock:
            return self._search_query

    def get_search_results(self) -> list[dict]:
        with self._lock:
            return list(self._search_results)

    def set_search_results(self, query: str, results: list[dict]) -> None:
        with self._lock:
            self._search_query = query
            self._search_results = results
        self._notify_observers(
            StateEvent(
                event_type=StateEventType.SEARCH_UPDATED,
                data={"query": query, "results": results},
            )
        )

    def clear_search(self) -> None:
        with self._lock:
            self._search_query = ""
            self._search_results = []
        self._notify_observers(
            StateEvent(
                event_type=StateEventType.SEARCH_UPDATED,
                data={"query": "", "results": []},
            )
        )

    # ========== REGISTRO EVENTS ==========

    def notify_registro_saved(self, registro: dict) -> None:
        self._notify_observers(
            StateEvent(
                event_type=StateEventType.REGISTRO_SAVED,
                data={"registro": registro},
            )
        )

    def notify_registro_deleted(self, registro_id: int) -> None:
        self._notify_observers(
            StateEvent(
                event_type=StateEventType.REGISTRO_DELETED,
                data={"registro_id": registro_id},
            )
        )

    # ========== CONFIG ==========

    def get_auto_return(self) -> bool:
        with self._lock:
            return self._auto_return

    def set_auto_return(self, value: bool) -> None:
        with self._lock:
            self._auto_return = value
        self._notify_observers(
            StateEvent(
                event_type=StateEventType.CONFIG_CHANGED,
                data={"key": "auto_return", "value": value},
            )
        )

    def get_save_path(self) -> Path:
        with self._lock:
            return self._save_path

    def set_save_path(self, path: Path) -> None:
        with self._lock:
            self._save_path = path
        self._notify_observers(
            StateEvent(
                event_type=StateEventType.CONFIG_CHANGED,
                data={"key": "save_path", "value": str(path)},
            )
        )
