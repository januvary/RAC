#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC State Manager
Centralized state management with observer pattern
"""

from __future__ import annotations

import threading
import copy
from typing import Optional
from pathlib import Path

from src.models import Malote, Registro


class RACStateManager:
    def __init__(self) -> None:
        self._active_malote: Optional[Malote] = None
        self._current_tipo: str = ""
        self._editing_registro: Optional[Registro] = None
        self._auto_return: bool = True
        self._save_path: Path = Path.home() / "Downloads"
        self._lock = threading.RLock()

    # ========== MALOTE ==========

    def get_active_malote(self) -> Optional[Malote]:
        with self._lock:
            return copy.deepcopy(self._active_malote) if self._active_malote else None

    def set_active_malote(self, malote: Optional[Malote]) -> None:
        with self._lock:
            self._active_malote = malote

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

    # ========== EDITING REGISTRO ==========

    def get_editing_registro(self) -> Optional[Registro]:
        with self._lock:
            return copy.deepcopy(self._editing_registro) if self._editing_registro else None

    def set_editing_registro(self, registro: Optional[Registro]) -> None:
        with self._lock:
            self._editing_registro = registro

    def is_editing(self) -> bool:
        with self._lock:
            return self._editing_registro is not None

    def notify_registro_saved(self, registro: Registro) -> None:
        with self._lock:
            self._editing_registro = None

    def notify_registro_deleted(self, registro_id: int) -> None:
        with self._lock:
            if self._editing_registro and self._editing_registro.id == registro_id:
                self._editing_registro = None

    # ========== CONFIG ==========

    def get_auto_return(self) -> bool:
        with self._lock:
            return self._auto_return

    def set_auto_return(self, value: bool) -> None:
        with self._lock:
            self._auto_return = value

    def get_save_path(self) -> Path:
        with self._lock:
            return self._save_path

    def set_save_path(self, path: Path) -> None:
        with self._lock:
            self._save_path = path
