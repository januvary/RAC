#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC Database
SQLite database layer for Registros Alto Custo
"""

import sqlite3
from typing import Optional
from datetime import datetime

from src.utils.database_base import BaseDatabase
from src.utils.paths import resolve_db_path
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel
from src.utils.text_utils import normalize_text
from src.database.definitive_catalog import DEFINITIVE_CATALOG


class RACDatabase(BaseDatabase):
    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_path = resolve_db_path("registros.db", create_dir=True)
        super().__init__(db_path=db_path, entity_name="registros")

    def _resolve_default_db_path(self) -> str:
        return resolve_db_path("registros.db", create_dir=True)

    def _create_schema(self) -> None:
        cursor = self._get_cursor()

        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS malotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pacientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS items_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                unidade TEXT NOT NULL DEFAULT 'un'
            );

            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
                malote_id INTEGER NOT NULL REFERENCES malotes(id),
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS registro_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                registro_id INTEGER NOT NULL REFERENCES registros(id) ON DELETE CASCADE,
                item_id INTEGER NOT NULL REFERENCES items_catalog(id)
            );
            """
        )

        cursor.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_registros_malote ON registros(malote_id);
            CREATE INDEX IF NOT EXISTS idx_registros_paciente ON registros(paciente_id);
            CREATE INDEX IF NOT EXISTS idx_registros_tipo ON registros(tipo);
            CREATE INDEX IF NOT EXISTS idx_pacientes_nome ON pacientes(name COLLATE NOCASE);
            CREATE INDEX IF NOT EXISTS idx_registro_items_registro ON registro_items(registro_id);
            CREATE INDEX IF NOT EXISTS idx_registro_items_item ON registro_items(item_id);
            """
        )

        self._commit()
        cursor.close()

        self._seed_catalog_if_empty()

    def _log_initialization_success(self) -> None:
        count = self._get_catalog_count()
        ErrorHandler.log(
            f"RACDatabase inicializado - {count} itens no catálogo",
            level=ErrorLevel.INFO,
            context=ErrorContext.DATABASE,
        )

    def _seed_catalog_if_empty(self) -> None:
        cursor = self._get_cursor()
        cursor.execute("SELECT COUNT(*) FROM items_catalog")
        count = cursor.fetchone()[0]

        if count == 0:
            for name, unidade in DEFINITIVE_CATALOG:
                cursor.execute(
                    "INSERT INTO items_catalog (name, unidade) VALUES (?, ?)",
                    (name, unidade),
                )
            self._commit()
            ErrorHandler.log(
                f"Catálogo inicializado com {len(DEFINITIVE_CATALOG)} itens",
                level=ErrorLevel.INFO,
                context=ErrorContext.DATABASE,
            )
        cursor.close()

    def _get_catalog_count(self) -> int:
        cursor = self._get_cursor()
        cursor.execute("SELECT COUNT(*) FROM items_catalog")
        count = cursor.fetchone()[0]
        cursor.close()
        return count

    # ========== MALOTE ==========

    def create_malote(self, date: str) -> dict:
        def _op():
            cursor = self._get_cursor()
            cursor.execute("INSERT INTO malotes (date) VALUES (?)", (date,))
            self._commit()
            malote_id = cursor.lastrowid
            cursor.close()
            return {"id": malote_id, "date": date}

        return self._retry_on_transient_error(_op, operation_type="write")

    def get_malote_by_id(self, malote_id: int) -> Optional[dict]:
        def _op():
            cursor = self._get_cursor()
            cursor.execute("SELECT * FROM malotes WHERE id = ?", (malote_id,))
            row = cursor.fetchone()
            cursor.close()
            return dict(row) if row else None

        return self._retry_on_transient_error(_op, operation_type="read")

    def get_recent_malotes(self, limit: int = 5) -> list[dict]:
        def _op():
            cursor = self._get_cursor()
            cursor.execute(
                "SELECT * FROM malotes ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
            cursor.close()
            return [dict(r) for r in rows]

        return self._retry_on_transient_error(_op, operation_type="read")

    def get_all_malotes(self) -> list[dict]:
        def _op():
            cursor = self._get_cursor()
            cursor.execute("SELECT * FROM malotes ORDER BY id DESC")
            rows = cursor.fetchall()
            cursor.close()
            return [dict(r) for r in rows]

        return self._retry_on_transient_error(_op, operation_type="read")

    def delete_malote(self, malote_id: int) -> bool:
        def _op():
            cursor = self._get_cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM registros WHERE malote_id = ?",
                (malote_id,),
            )
            count = cursor.fetchone()[0]
            if count > 0:
                cursor.close()
                return False

            cursor.execute("DELETE FROM malotes WHERE id = ?", (malote_id,))
            self._commit()
            cursor.close()
            return True

        return self._retry_on_transient_error(_op, operation_type="write")

    # ========== PACIENTE ==========

    def create_paciente(self, name: str) -> dict:
        def _op():
            cursor = self._get_cursor()
            cursor.execute("INSERT INTO pacientes (name) VALUES (?)", (name.strip(),))
            self._commit()
            paciente_id = cursor.lastrowid
            cursor.close()
            return {"id": paciente_id, "name": name.strip()}

        return self._retry_on_transient_error(_op, operation_type="write")

    def get_paciente_by_id(self, paciente_id: int) -> Optional[dict]:
        def _op():
            cursor = self._get_cursor()
            cursor.execute("SELECT * FROM pacientes WHERE id = ?", (paciente_id,))
            row = cursor.fetchone()
            cursor.close()
            return dict(row) if row else None

        return self._retry_on_transient_error(_op, operation_type="read")

    def search_pacientes(self, query: str, limit: int = 10) -> list[dict]:
        def _op():
            cursor = self._get_cursor()
            normalized = normalize_text(query)
            cursor.execute(
                "SELECT * FROM pacientes WHERE LOWER(name) LIKE ? ORDER BY name LIMIT ?",
                (f"%{normalized}%", limit),
            )
            rows = cursor.fetchall()
            cursor.close()
            return [dict(r) for r in rows]

        return self._retry_on_transient_error(_op, operation_type="read")

    def update_paciente(self, paciente_id: int, name: str) -> bool:
        def _op():
            cursor = self._get_cursor()
            cursor.execute(
                "UPDATE pacientes SET name = ? WHERE id = ?",
                (name.strip(), paciente_id),
            )
            self._commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0

        return self._retry_on_transient_error(_op, operation_type="write")

    def delete_paciente(self, paciente_id: int) -> bool:
        def _op():
            cursor = self._get_cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM registros WHERE paciente_id = ?",
                (paciente_id,),
            )
            count = cursor.fetchone()[0]
            if count > 0:
                cursor.close()
                return False

            cursor.execute("DELETE FROM pacientes WHERE id = ?", (paciente_id,))
            self._commit()
            cursor.close()
            return True

        return self._retry_on_transient_error(_op, operation_type="write")

    # ========== REGISTRO ==========

    def create_registro(
        self, tipo: str, paciente_id: int, malote_id: int
    ) -> dict:
        def _op():
            cursor = self._get_cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO registros (tipo, paciente_id, malote_id, created_at) VALUES (?, ?, ?, ?)",
                (tipo, paciente_id, malote_id, now),
            )
            self._commit()
            registro_id = cursor.lastrowid
            cursor.close()
            return {
                "id": registro_id,
                "tipo": tipo,
                "paciente_id": paciente_id,
                "malote_id": malote_id,
                "created_at": now,
            }

        return self._retry_on_transient_error(_op, operation_type="write")

    def get_registro_by_id(self, registro_id: int) -> Optional[dict]:
        def _op():
            cursor = self._get_cursor()
            cursor.execute(
                "SELECT r.*, p.name as paciente_name, m.date as malote_date "
                "FROM registros r "
                "JOIN pacientes p ON r.paciente_id = p.id "
                "JOIN malotes m ON r.malote_id = m.id "
                "WHERE r.id = ?",
                (registro_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            return dict(row) if row else None

        return self._retry_on_transient_error(_op, operation_type="read")

    def get_registros_by_malote(self, malote_id: int) -> list[dict]:
        def _op():
            cursor = self._get_cursor()
            cursor.execute(
                "SELECT r.*, p.name as paciente_name "
                "FROM registros r "
                "JOIN pacientes p ON r.paciente_id = p.id "
                "WHERE r.malote_id = ? "
                "ORDER BY p.name COLLATE NOCASE",
                (malote_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            return [dict(r) for r in rows]

        return self._retry_on_transient_error(_op, operation_type="read")

    def get_registros_by_malote_and_tipo(
        self, malote_id: int, tipo: str
    ) -> list[dict]:
        def _op():
            cursor = self._get_cursor()
            cursor.execute(
                "SELECT r.*, p.name as paciente_name "
                "FROM registros r "
                "JOIN pacientes p ON r.paciente_id = p.id "
                "WHERE r.malote_id = ? AND r.tipo = ? "
                "ORDER BY p.name COLLATE NOCASE",
                (malote_id, tipo),
            )
            rows = cursor.fetchall()
            cursor.close()
            return [dict(r) for r in rows]

        return self._retry_on_transient_error(_op, operation_type="read")

    def update_registro(self, registro_id: int, **fields) -> bool:
        allowed = {"tipo", "paciente_id", "malote_id"}
        updates = {k: v for k, v in fields.items() if k in allowed}

        if not updates:
            return False

        def _op():
            cursor = self._get_cursor()
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [registro_id]
            cursor.execute(
                f"UPDATE registros SET {set_clause} WHERE id = ?",
                values,
            )
            self._commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0

        return self._retry_on_transient_error(_op, operation_type="write")

    def delete_registro(self, registro_id: int) -> bool:
        def _op():
            cursor = self._get_cursor()
            cursor.execute("DELETE FROM registros WHERE id = ?", (registro_id,))
            self._commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0

        return self._retry_on_transient_error(_op, operation_type="write")

    def search_registros_by_patient(
        self, malote_id: int, query: str, limit: int = 20
    ) -> list[dict]:
        def _op():
            cursor = self._get_cursor()
            normalized = normalize_text(query)
            cursor.execute(
                "SELECT r.*, p.name as paciente_name, m.date as malote_date "
                "FROM registros r "
                "JOIN pacientes p ON r.paciente_id = p.id "
                "JOIN malotes m ON r.malote_id = m.id "
                "WHERE r.malote_id = ? AND LOWER(p.name) LIKE ? "
                "ORDER BY p.name COLLATE NOCASE "
                "LIMIT ?",
                (malote_id, f"%{normalized}%", limit),
            )
            rows = cursor.fetchall()
            cursor.close()
            return [dict(r) for r in rows]

        return self._retry_on_transient_error(_op, operation_type="read")

    # ========== REGISTRO ITEMS ==========

    def set_registro_items(self, registro_id: int, item_ids: list[int]) -> None:
        def _op():
            cursor = self._get_cursor()
            cursor.execute(
                "DELETE FROM registro_items WHERE registro_id = ?",
                (registro_id,),
            )
            if item_ids:
                cursor.executemany(
                    "INSERT INTO registro_items (registro_id, item_id) VALUES (?, ?)",
                    [(registro_id, iid) for iid in item_ids],
                )
            self._commit()
            cursor.close()

        self._retry_on_transient_error(_op, operation_type="write")

    def get_items_for_registro(self, registro_id: int) -> list[dict]:
        def _op():
            cursor = self._get_cursor()
            cursor.execute(
                "SELECT ri.*, ic.name as item_name, ic.unidade "
                "FROM registro_items ri "
                "JOIN items_catalog ic ON ri.item_id = ic.id "
                "WHERE ri.registro_id = ?",
                (registro_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            return [dict(r) for r in rows]

        return self._retry_on_transient_error(_op, operation_type="read")

    # ========== ITEMS CATALOG ==========

    def get_all_items(self) -> list[dict]:
        def _op():
            cursor = self._get_cursor()
            cursor.execute("SELECT * FROM items_catalog ORDER BY name COLLATE NOCASE")
            rows = cursor.fetchall()
            cursor.close()
            return [dict(r) for r in rows]

        return self._retry_on_transient_error(_op, operation_type="read")

    def search_items(self, query: str, limit: int = 10) -> list[dict]:
        def _op():
            cursor = self._get_cursor()
            normalized = normalize_text(query)
            cursor.execute(
                "SELECT * FROM items_catalog WHERE LOWER(name) LIKE ? ORDER BY name COLLATE NOCASE LIMIT ?",
                (f"%{normalized}%", limit),
            )
            rows = cursor.fetchall()
            cursor.close()
            return [dict(r) for r in rows]

        return self._retry_on_transient_error(_op, operation_type="read")

    # ========== EXPORT HELPERS ==========

    def get_registros_with_items_by_malote(self, malote_id: int) -> list[dict]:
        def _op():
            cursor = self._get_cursor()
            cursor.execute(
                "SELECT r.id, r.tipo, r.paciente_id, p.name as paciente_name "
                "FROM registros r "
                "JOIN pacientes p ON r.paciente_id = p.id "
                "WHERE r.malote_id = ? "
                "ORDER BY r.tipo, p.name COLLATE NOCASE",
                (malote_id,),
            )
            registros = [dict(r) for r in cursor.fetchall()]

            for reg in registros:
                cursor.execute(
                    "SELECT ic.name "
                    "FROM registro_items ri "
                    "JOIN items_catalog ic ON ri.item_id = ic.id "
                    "WHERE ri.registro_id = ? "
                    "ORDER BY ic.name",
                    (reg["id"],),
                )
                reg["items"] = [dict(r)["name"] for r in cursor.fetchall()]

            cursor.close()
            return registros

        return self._retry_on_transient_error(_op, operation_type="read")
