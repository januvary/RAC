#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Database Module
Simplified SQLite base class for RAC - single connection, optimized for performance
"""

import sqlite3
import time
import threading
import shutil
from abc import ABC, abstractmethod
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Literal, Optional

from src.utils.paths import resolve_db_path
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel


class BaseDatabase(ABC):
    def __init__(
        self, db_path: Optional[str] = None, entity_name: str = "registros"
    ) -> None:
        if db_path is None:
            db_path = self._resolve_default_db_path()
            ErrorHandler.log(
                f"{self.__class__.__name__}: Usando banco de dados: {db_path}",
                level=ErrorLevel.INFO,
                context=ErrorContext.DATABASE,
            )

        self.db_path = db_path
        self._entity_name = entity_name
        self.conn: Optional[sqlite3.Connection] = None
        self._conn_open_time: Optional[float] = None
        self._lock = threading.RLock()
        self._initialize()

    @abstractmethod
    def _create_schema(self) -> None:
        pass

    def _ensure_schema_version(self) -> int:
        cursor = self._get_cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS _schema_meta (key TEXT PRIMARY KEY, value TEXT)"
        )
        self._commit()
        cursor.execute("SELECT value FROM _schema_meta WHERE key = 'version'")
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            return 0
        stored = int(row["value"] if isinstance(row, dict) else row[0])
        return stored

    def _set_schema_version(self, version: int) -> None:
        cursor = self._get_cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO _schema_meta (key, value) VALUES (?, ?)",
            ("version", str(version)),
        )
        self._commit()
        cursor.close()

    def _resolve_default_db_path(self) -> str:
        return resolve_db_path("database.db", create_dir=True)

    def __enter__(self) -> "BaseDatabase":
        return self

    def __exit__(self, _exc_type: Any, _exc_val: Any, _exc_tb: Any) -> Literal[False]:
        self.close()
        return False

    def __del__(self) -> None:
        with suppress(Exception):
            self.close()

    def _setup_pragmas(self) -> None:
        cursor = self._get_cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=TRUNCATE")
        cursor.execute("PRAGMA synchronous=FULL")
        cursor.execute("PRAGMA cache_size=-2000")
        cursor.execute("PRAGMA busy_timeout=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

    def _initialize(self) -> None:
        max_retries = 5

        for attempt in range(max_retries):
            try:
                self.conn = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    timeout=30,
                )
                self.conn.row_factory = sqlite3.Row
                self._conn_open_time = time.time()
                self._create_schema()
                self._setup_pragmas()

                self._log_initialization_success()
                return

            except sqlite3.OperationalError as e:
                error_str = str(e)
                is_io_error = (
                    "disk I/O error" in error_str or "database is locked" in error_str
                )
                is_last_attempt = attempt == max_retries - 1

                if is_io_error and not is_last_attempt:
                    delay = 2**attempt
                    ErrorHandler.log(
                        f"Erro de I/O ao conectar {self.__class__.__name__} "
                        f"(tentativa {attempt + 1}/{max_retries}). "
                        f"Aguardando {delay}s...",
                        level=ErrorLevel.WARNING,
                        context=ErrorContext.DATABASE,
                    )
                    time.sleep(delay)
                else:
                    ErrorHandler.handle_database_error(
                        e,
                        operation=f"Falha ao abrir banco: {self.db_path}",
                    )
                    raise

    def _log_initialization_success(self) -> None:
        ErrorHandler.log(
            f"{self.__class__.__name__} inicializado com sucesso",
            level=ErrorLevel.INFO,
            context=ErrorContext.DATABASE,
        )

    def _reconnect_unlocked(self) -> None:
        if self.conn:
            with suppress(Exception):
                self.conn.close()

        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._conn_open_time = time.time()

            cursor = self.conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=TRUNCATE")
            cursor.execute("PRAGMA synchronous=FULL")
            cursor.execute("PRAGMA busy_timeout=10000")
            cursor.execute("PRAGMA cache_size=-2000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()

            ErrorHandler.log(
                f"Conexão {self.__class__.__name__} renovada",
                level=ErrorLevel.INFO,
                context=ErrorContext.DATABASE,
            )
        except Exception as e:
            ErrorHandler.handle_database_error(
                e,
                operation=f"reconectar ao banco de {self._entity_name}",
            )
            raise

    def _get_cursor(self) -> sqlite3.Cursor:
        with self._lock:
            assert self.conn is not None, "Database connection not initialized"
            return self.conn.cursor()

    def _get_connection(self) -> sqlite3.Connection:
        with self._lock:
            assert self.conn is not None, "Database connection not initialized"
            return self.conn

    def _commit(self) -> None:
        with self._lock:
            assert self.conn is not None, "Database connection not initialized"
            self.conn.commit()

    def _rollback(self) -> None:
        with self._lock:
            assert self.conn is not None, "Database connection not initialized"
            self.conn.rollback()

    def _retry_on_transient_error(
        self,
        operation: Callable,
        max_retries: int = 3,
        operation_type: str = "operation",
    ) -> Any:
        for attempt in range(max_retries):
            try:
                return operation()
            except sqlite3.OperationalError as e:
                error_str = str(e)
                is_transient = (
                    "database is locked" in error_str
                    or "disk I/O error" in error_str
                    or "unable to open database" in error_str
                )

                if is_transient and attempt < max_retries - 1:
                    delay = (2**attempt) * 0.5
                    ErrorHandler.log(
                        f"Problema durante {operation_type} (tentativa {attempt + 1}/{max_retries}), "
                        f"tentando novamente em {delay:.1f}s...",
                        level=ErrorLevel.WARNING,
                        context=ErrorContext.DATABASE,
                    )
                    time.sleep(delay)
                else:
                    raise

    def _backup_database(self) -> None:
        try:
            backup_dir = Path(self.db_path).parent / "backups"
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            db_name = Path(self.db_path).stem
            backup_path = backup_dir / f"{db_name}_{timestamp}.db"

            shutil.copy2(self.db_path, backup_path)

            backups = sorted(backup_dir.glob(f"{db_name}_*.db"))
            for old_backup in backups[:-10]:
                old_backup.unlink()

            ErrorHandler.log(
                f"Backup de {db_name} criado: {backup_path}",
                level=ErrorLevel.INFO,
                context=ErrorContext.DATABASE,
            )
        except Exception as e:
            ErrorHandler.log(
                f"Erro ao criar backup: {e}",
                level=ErrorLevel.WARNING,
                context=ErrorContext.DATABASE,
            )

    def close(self, skip_backup: bool = False) -> None:
        if self.conn:
            try:
                if not skip_backup:
                    self._backup_database()
                self.conn.close()
                self.conn = None
                ErrorHandler.log(
                    f"{self.__class__.__name__} conexão fechada",
                    level=ErrorLevel.INFO,
                    context=ErrorContext.DATABASE,
                )
            except Exception as e:
                ErrorHandler.log(
                    f"Erro ao fechar {self.__class__.__name__}: {e}",
                    level=ErrorLevel.WARNING,
                    context=ErrorContext.DATABASE,
                )
                self.conn = None
