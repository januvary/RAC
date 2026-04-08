#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Error Handling Utilities
Centralized error handling with logging and UI dialogs
"""

import sys
import traceback
from contextlib import suppress
from typing import Optional, Callable, Any
from enum import Enum
import logging


class ErrorLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class ErrorContext(Enum):
    DATABASE = "Database"
    FILE_IO = "File I/O"
    EXPORT = "Exportação"
    VALIDATION = "Validation"
    CONFIGURATION = "Configuration"
    UI = "User Interface"
    MALOTE = "Malote"
    REGISTRO = "Registro"
    AUTOCOMPLETE = "Autocomplete"
    STATE = "State Management"
    UNKNOWN = "Unknown"


class ErrorHandler:
    _instance: Optional["ErrorHandler"] = None
    _logger: Optional[logging.Logger] = None
    _show_dialog_callback: Optional[Callable[[str, str, ErrorLevel], None]] = None
    _initialized: bool = False

    def __new__(cls) -> "ErrorHandler":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            self._setup_logging()
            self._initialized = True

    @staticmethod
    def _setup_logging() -> None:
        if ErrorHandler._logger is None:
            ErrorHandler._logger = logging.getLogger("RAC")
            ErrorHandler._logger.setLevel(logging.DEBUG)

            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            ErrorHandler._logger.addHandler(console_handler)

            with suppress(Exception):
                from .paths import get_root_directory

                log_dir = get_root_directory() / "data"
                log_dir.mkdir(parents=True, exist_ok=True)
                log_file = log_dir / "rac.log"

                file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                ErrorHandler._logger.addHandler(file_handler)

    @staticmethod
    def set_dialog_callback(
        callback: Callable[[str, str, ErrorLevel], None],
    ) -> None:
        ErrorHandler._show_dialog_callback = callback

    @staticmethod
    def handle_error(
        error: Exception,
        context: ErrorContext = ErrorContext.UNKNOWN,
        level: ErrorLevel = ErrorLevel.ERROR,
        show_dialog: bool = True,
        recovery_hint: Optional[str] = None,
    ) -> str:
        handler = ErrorHandler()

        error_msg = f"[{context.value}] {type(error).__name__}: {error}"

        if handler._logger:
            log_func = {
                ErrorLevel.INFO: handler._logger.info,
                ErrorLevel.WARNING: handler._logger.warning,
                ErrorLevel.ERROR: handler._logger.error,
                ErrorLevel.CRITICAL: handler._logger.critical,
            }.get(level, handler._logger.error)

            log_func(error_msg)

            if level in (ErrorLevel.ERROR, ErrorLevel.CRITICAL):
                handler._logger.debug(traceback.format_exc())

        if show_dialog and ErrorHandler._show_dialog_callback:
            dialog_msg = error_msg
            if recovery_hint:
                dialog_msg += f"\n\nSugestão: {recovery_hint}"

            try:
                ErrorHandler._show_dialog_callback(
                    f"Erro de {context.value}", dialog_msg, level
                )
            except Exception as e:
                if handler._logger:
                    handler._logger.warning(f"Failed to show error dialog: {e}")

        return error_msg

    @staticmethod
    def log(
        message: str,
        level: ErrorLevel = ErrorLevel.INFO,
        context: ErrorContext = ErrorContext.UNKNOWN,
    ) -> None:
        handler = ErrorHandler()
        if handler._logger:
            with suppress(Exception):
                formatted_msg = f"[{context.value}] {message}"

                log_func = {
                    ErrorLevel.DEBUG: handler._logger.debug,
                    ErrorLevel.INFO: handler._logger.info,
                    ErrorLevel.WARNING: handler._logger.warning,
                    ErrorLevel.ERROR: handler._logger.error,
                    ErrorLevel.CRITICAL: handler._logger.critical,
                }.get(level, handler._logger.info)

                log_func(formatted_msg)

    @staticmethod
    def handle_database_error(
        error: Exception,
        operation: str = "database operation",
        recovery_hint: Optional[str] = None,
        show_dialog: bool = True,
    ) -> str:
        if recovery_hint is None:
            recovery_hint = (
                "Se o problema persistir, tente:\n"
                "1. Fechar e reabrir a aplicação\n"
                "2. Verificar espaço em disco\n"
                "3. Contatar suporte"
            )

        return ErrorHandler.handle_error(
            error,
            context=ErrorContext.DATABASE,
            level=ErrorLevel.ERROR,
            recovery_hint=recovery_hint,
            show_dialog=show_dialog,
        )

    @staticmethod
    def safe_execute(
        func: Callable[..., Any],
        *args: Any,
        operation_name: str = "operation",
        on_error: Optional[Callable[[Exception], None]] = None,
        context: ErrorContext = ErrorContext.UNKNOWN,
        **kwargs: Any,
    ) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                context=context,
                recovery_hint=f"Falha ao executar {operation_name}",
            )
            if on_error:
                try:
                    on_error(e)
                except Exception as callback_error:
                    ErrorHandler.log(
                        f"Error callback failed: {callback_error}",
                        level=ErrorLevel.WARNING,
                    )
            return None

    @staticmethod
    def suppress_and_log(
        func: Callable,
        *args: Any,
        operation_name: str = "operation",
        context: ErrorContext = ErrorContext.UNKNOWN,
        **kwargs: Any,
    ) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ErrorHandler.log(
                f"Suppressed error in {operation_name}: {e}",
                level=ErrorLevel.WARNING,
                context=context,
            )
            return None

    @staticmethod
    def get_logger() -> logging.Logger:
        handler = ErrorHandler()
        if handler._logger is None:
            handler._setup_logging()
        return handler._logger  # type: ignore[return-value]
