#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC Database
SQLite database layer for Registros Alto Custo
"""

import sqlite3
from typing import Optional
from datetime import datetime

from src.utils.database_base import BaseDatabase, _db_op
from src.utils.paths import resolve_db_path
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel
from src.utils.text_utils import to_upper_normalized
from src.database.definitive_catalog import DEFINITIVE_CATALOG
from src.services.exceptions import DuplicateRecordError
from src.models import (
    Malote,
    Paciente,
    ItemCatalog,
    Registro,
    RegistroItem,
    RegistroExport,
)


class RACDatabase(BaseDatabase):
    SCHEMA_VERSION = 1

    _MIGRATIONS: dict[int, str] = {}

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_path = resolve_db_path("registros.db", create_dir=True)
        super().__init__(db_path=db_path, entity_name="registros")

    def _resolve_default_db_path(self) -> str:
        return resolve_db_path("registros.db", create_dir=True)

    def _create_schema(self) -> None:
        stored_version = self._ensure_schema_version()

        if stored_version == self.SCHEMA_VERSION:
            self._seed_catalog_if_empty()
            return

        if stored_version == 0:
            self._create_fresh_schema()

        self._run_migrations(max(stored_version, 0))
        self._set_schema_version(self.SCHEMA_VERSION)
        self._seed_catalog_if_empty()

    def _create_fresh_schema(self) -> None:
        with self._cursor() as cur:
            cur.executescript("""
                CREATE TABLE IF NOT EXISTS malotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pacientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
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
                    created_at TEXT NOT NULL,
                    waiting_docs INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS registro_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    registro_id INTEGER NOT NULL REFERENCES registros(id) ON DELETE CASCADE,
                    item_id INTEGER NOT NULL REFERENCES items_catalog(id)
                );

                CREATE INDEX IF NOT EXISTS idx_registros_malote ON registros(malote_id);
                CREATE INDEX IF NOT EXISTS idx_registros_paciente ON registros(paciente_id);
                CREATE INDEX IF NOT EXISTS idx_registros_tipo ON registros(tipo);
                CREATE INDEX IF NOT EXISTS idx_pacientes_nome ON pacientes(name COLLATE NOCASE);
                CREATE INDEX IF NOT EXISTS idx_registro_items_registro ON registro_items(registro_id);
                CREATE INDEX IF NOT EXISTS idx_registro_items_item ON registro_items(item_id);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_registros_unique ON registros(tipo, paciente_id, malote_id);
                """)
            self._commit()

    def _run_migrations(self, from_version: int) -> None:
        for version in sorted(self._MIGRATIONS):
            if version <= from_version:
                continue
            sql = self._MIGRATIONS[version]
            with self._cursor() as cur:
                try:
                    cur.executescript(sql)
                    self._commit()
                except Exception as e:
                    raise RuntimeError(f"Migration v{version} failed: {e}") from e
            ErrorHandler.log(
                f"Migration v{version} applied successfully",
                level=ErrorLevel.INFO,
                context=ErrorContext.DATABASE,
            )

    def _log_initialization_success(self) -> None:
        count = self._get_catalog_count()
        ErrorHandler.log(
            f"RACDatabase inicializado - {count} itens no catálogo",
            level=ErrorLevel.INFO,
            context=ErrorContext.DATABASE,
        )

    def _seed_catalog_if_empty(self) -> None:
        with self._cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM items_catalog")
            count = cur.fetchone()[0]

            if count == 0:
                for name, unidade in DEFINITIVE_CATALOG:
                    cur.execute(
                        "INSERT INTO items_catalog (name, unidade) VALUES (?, ?)",
                        (to_upper_normalized(name), unidade),
                    )
                self._commit()
                ErrorHandler.log(
                    f"Catálogo inicializado com {len(DEFINITIVE_CATALOG)} itens",
                    level=ErrorLevel.INFO,
                    context=ErrorContext.DATABASE,
                )

    def _get_catalog_count(self) -> int:
        with self._cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM items_catalog")
            return cur.fetchone()[0]

    # ========== MALOTE ==========

    @_db_op("write")
    def create_malote(self, date: str) -> Malote:
        with self._cursor() as cur:
            cur.execute("SELECT id FROM malotes WHERE date = ?", (date,))
            existing = cur.fetchone()
            if existing:
                return Malote(id=existing["id"], date=date)
            cur.execute("INSERT INTO malotes (date) VALUES (?)", (date,))
            self._commit()
            return Malote(id=cur.lastrowid, date=date)

    @_db_op("read")
    def get_malote_by_id(self, malote_id: int) -> Optional[Malote]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM malotes WHERE id = ?", (malote_id,))
            row = cur.fetchone()
            return Malote.from_row(dict(row)) if row else None

    @_db_op("read")
    def get_recent_malotes(self, limit: int = 5) -> list[Malote]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM malotes ORDER BY date DESC, id DESC LIMIT ?",
                (limit,),
            )
            return [Malote.from_row(dict(r)) for r in cur.fetchall()]

    @_db_op("read")
    def get_all_malotes(self) -> list[Malote]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM malotes ORDER BY date DESC, id DESC")
            return [Malote.from_row(dict(r)) for r in cur.fetchall()]

    @_db_op("write")
    def update_malote(self, malote_id: int, date: str) -> bool:
        with self._cursor() as cur:
            cur.execute("UPDATE malotes SET date = ? WHERE id = ?", (date, malote_id))
            self._commit()
            return cur.rowcount > 0

    @_db_op("write")
    def delete_malote(self, malote_id: int) -> bool:
        with self._cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM registros WHERE malote_id = ?",
                (malote_id,),
            )
            if cur.fetchone()[0] > 0:
                return False
            cur.execute("DELETE FROM malotes WHERE id = ?", (malote_id,))
            self._commit()
            return True

    # ========== PACIENTE ==========

    @_db_op("write")
    def create_paciente(self, name: str) -> Paciente:
        normalized = to_upper_normalized(name.strip())
        with self._cursor() as cur:
            cur.execute("INSERT INTO pacientes (name) VALUES (?)", (normalized,))
            self._commit()
            return Paciente(id=cur.lastrowid, name=normalized)

    @_db_op("read")
    def get_paciente_by_id(self, paciente_id: int) -> Optional[Paciente]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM pacientes WHERE id = ?", (paciente_id,))
            row = cur.fetchone()
            return Paciente.from_row(dict(row)) if row else None

    @_db_op("read")
    def find_paciente_by_name(self, name: str) -> Optional[Paciente]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM pacientes WHERE name = ? LIMIT 1",
                (to_upper_normalized(name),),
            )
            row = cur.fetchone()
            return Paciente.from_row(dict(row)) if row else None

    @_db_op("read")
    def search_pacientes(self, query: str, limit: int = 10) -> list[Paciente]:
        with self._cursor() as cur:
            normalized = to_upper_normalized(query)
            cur.execute(
                "SELECT * FROM pacientes WHERE name LIKE ? ORDER BY name LIMIT ?",
                (f"%{normalized}%", limit),
            )
            return [Paciente.from_row(dict(r)) for r in cur.fetchall()]

    @_db_op("write")
    def update_paciente(self, paciente_id: int, name: str) -> bool:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE pacientes SET name = ? WHERE id = ?",
                (to_upper_normalized(name.strip()), paciente_id),
            )
            self._commit()
            return cur.rowcount > 0

    @_db_op("write")
    def delete_paciente(self, paciente_id: int) -> bool:
        with self._cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM registros WHERE paciente_id = ?",
                (paciente_id,),
            )
            if cur.fetchone()[0] > 0:
                return False
            cur.execute("DELETE FROM pacientes WHERE id = ?", (paciente_id,))
            self._commit()
            return True

    # ========== REGISTRO ==========

    @_db_op("write")
    def create_registro(
        self,
        tipo: str,
        paciente_id: int,
        malote_id: int,
        waiting_docs: bool = False,
    ) -> Registro:
        with self._cursor() as cur:
            now = datetime.now().isoformat()
            wd = 1 if waiting_docs else 0
            cur.execute(
                "INSERT INTO registros (tipo, paciente_id, malote_id, created_at, waiting_docs) VALUES (?, ?, ?, ?, ?)",
                (tipo, paciente_id, malote_id, now, wd),
            )
            self._commit()
            return Registro(
                id=cur.lastrowid,
                tipo=tipo,
                paciente_id=paciente_id,
                malote_id=malote_id,
                created_at=now,
                waiting_docs=waiting_docs,
            )

    @_db_op("read")
    def get_registro_by_id(self, registro_id: int) -> Optional[Registro]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT r.*, p.name as paciente_name, m.date as malote_date "
                "FROM registros r "
                "JOIN pacientes p ON r.paciente_id = p.id "
                "JOIN malotes m ON r.malote_id = m.id "
                "WHERE r.id = ?",
                (registro_id,),
            )
            row = cur.fetchone()
            return Registro.from_row(dict(row)) if row else None

    @_db_op("read")
    def find_registro(
        self, tipo: str, paciente_id: int, malote_id: int
    ) -> Optional[Registro]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT r.*, p.name as paciente_name, m.date as malote_date "
                "FROM registros r "
                "JOIN pacientes p ON r.paciente_id = p.id "
                "JOIN malotes m ON r.malote_id = m.id "
                "WHERE r.tipo = ? AND r.paciente_id = ? AND r.malote_id = ? "
                "LIMIT 1",
                (tipo, paciente_id, malote_id),
            )
            row = cur.fetchone()
            return Registro.from_row(dict(row)) if row else None

    @_db_op("read")
    def get_registros_by_malote(self, malote_id: int) -> list[Registro]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT r.*, p.name as paciente_name "
                "FROM registros r "
                "JOIN pacientes p ON r.paciente_id = p.id "
                "WHERE r.malote_id = ? "
                "ORDER BY p.name COLLATE NOCASE",
                (malote_id,),
            )
            return [Registro.from_row(dict(r)) for r in cur.fetchall()]

    @_db_op("read")
    def get_registros_by_malote_and_tipo(
        self, malote_id: int, tipo: str
    ) -> list[Registro]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT r.*, p.name as paciente_name "
                "FROM registros r "
                "JOIN pacientes p ON r.paciente_id = p.id "
                "WHERE r.malote_id = ? AND r.tipo = ? "
                "ORDER BY p.name COLLATE NOCASE",
                (malote_id, tipo),
            )
            return [Registro.from_row(dict(r)) for r in cur.fetchall()]

    @_db_op("write")
    def update_registro(self, registro_id: int, **fields) -> bool:
        allowed = {"tipo", "paciente_id", "malote_id", "waiting_docs"}
        updates = {}
        for k, v in fields.items():
            if k not in allowed:
                continue
            if k == "waiting_docs":
                updates[k] = 1 if v else 0
            else:
                updates[k] = v

        if not updates:
            return False

        with self._cursor() as cur:
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [registro_id]
            try:
                cur.execute(
                    f"UPDATE registros SET {set_clause} WHERE id = ?",
                    values,
                )
                self._commit()
                return cur.rowcount > 0
            except sqlite3.IntegrityError:
                raise DuplicateRecordError(
                    f"Duplicate: tipo={updates.get('tipo')}, "
                    f"paciente_id={updates.get('paciente_id')}, "
                    f"malote_id={updates.get('malote_id')}"
                )

    @_db_op("write")
    def delete_registro(self, registro_id: int) -> bool:
        with self._cursor() as cur:
            cur.execute("DELETE FROM registros WHERE id = ?", (registro_id,))
            self._commit()
            return cur.rowcount > 0

    @_db_op("read")
    def search_registros_by_patient(
        self, malote_id: int, query: str, limit: int = 20
    ) -> list[Registro]:
        with self._cursor() as cur:
            normalized = to_upper_normalized(query)
            cur.execute(
                "SELECT r.*, p.name as paciente_name, m.date as malote_date "
                "FROM registros r "
                "JOIN pacientes p ON r.paciente_id = p.id "
                "JOIN malotes m ON r.malote_id = m.id "
                "WHERE r.malote_id = ? AND p.name LIKE ? "
                "ORDER BY p.name COLLATE NOCASE "
                "LIMIT ?",
                (malote_id, f"%{normalized}%", limit),
            )
            return [Registro.from_row(dict(r)) for r in cur.fetchall()]

    # ========== REGISTRO ITEMS ==========

    @_db_op("write")
    def set_registro_items(self, registro_id: int, item_ids: list[int]) -> None:
        with self._cursor() as cur:
            cur.execute(
                "DELETE FROM registro_items WHERE registro_id = ?",
                (registro_id,),
            )
            if item_ids:
                cur.executemany(
                    "INSERT INTO registro_items (registro_id, item_id) VALUES (?, ?)",
                    [(registro_id, iid) for iid in item_ids],
                )
            self._commit()

    @_db_op("read")
    def get_items_for_registro(self, registro_id: int) -> list[RegistroItem]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT ri.*, ic.name as item_name, ic.unidade "
                "FROM registro_items ri "
                "JOIN items_catalog ic ON ri.item_id = ic.id "
                "WHERE ri.registro_id = ?",
                (registro_id,),
            )
            return [RegistroItem.from_row(dict(r)) for r in cur.fetchall()]

    @_db_op("read")
    def get_items_for_paciente(self, paciente_id: int) -> list[ItemCatalog]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT DISTINCT ri.item_id as id, ic.name, ic.unidade "
                "FROM registro_items ri "
                "JOIN registros r ON ri.registro_id = r.id "
                "JOIN items_catalog ic ON ri.item_id = ic.id "
                "WHERE r.paciente_id = ? "
                "ORDER BY ic.name COLLATE NOCASE",
                (paciente_id,),
            )
            return [ItemCatalog.from_row(dict(r)) for r in cur.fetchall()]

    # ========== ITEMS CATALOG ==========

    @_db_op("read")
    def get_all_items(self) -> list[ItemCatalog]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM items_catalog ORDER BY name COLLATE NOCASE")
            return [ItemCatalog.from_row(dict(r)) for r in cur.fetchall()]

    @_db_op("read")
    def search_items(self, query: str, limit: int = 10) -> list[ItemCatalog]:
        with self._cursor() as cur:
            normalized = to_upper_normalized(query)
            cur.execute(
                "SELECT * FROM items_catalog WHERE name LIKE ? ORDER BY name COLLATE NOCASE LIMIT ?",
                (f"%{normalized}%", limit),
            )
            return [ItemCatalog.from_row(dict(r)) for r in cur.fetchall()]

    @_db_op("write")
    def create_item(self, name: str, unidade: str = "un") -> ItemCatalog:
        normalized = to_upper_normalized(name.strip())
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO items_catalog (name, unidade) VALUES (?, ?)",
                (normalized, unidade),
            )
            self._commit()
            return ItemCatalog(id=cur.lastrowid, name=normalized, unidade=unidade)

    @_db_op("write")
    def update_item(self, item_id: int, name: str) -> bool:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE items_catalog SET name = ? WHERE id = ?",
                (to_upper_normalized(name.strip()), item_id),
            )
            self._commit()
            return cur.rowcount > 0

    @_db_op("write")
    def delete_item(self, item_id: int) -> bool:
        with self._cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM registro_items WHERE item_id = ?",
                (item_id,),
            )
            if cur.fetchone()[0] > 0:
                return False
            cur.execute("DELETE FROM items_catalog WHERE id = ?", (item_id,))
            self._commit()
            return cur.rowcount > 0

    # ========== PACIENTE (listagem) ==========

    @_db_op("read")
    def get_all_pacientes(self) -> list[Paciente]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM pacientes ORDER BY name COLLATE NOCASE")
            return [Paciente.from_row(dict(r)) for r in cur.fetchall()]

    # ========== EXPORT HELPERS ==========

    @_db_op("read")
    def get_registros_with_items_by_malote(
        self, malote_id: int
    ) -> list[RegistroExport]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT r.id, r.tipo, r.paciente_id, p.name as paciente_name, "
                "ic.name as item_name "
                "FROM registros r "
                "JOIN pacientes p ON r.paciente_id = p.id "
                "LEFT JOIN registro_items ri ON ri.registro_id = r.id "
                "LEFT JOIN items_catalog ic ON ri.item_id = ic.id "
                "WHERE r.malote_id = ? AND r.waiting_docs = 0 "
                "ORDER BY r.tipo, p.name COLLATE NOCASE, ic.name",
                (malote_id,),
            )
            rows = cur.fetchall()

        registros_map: dict[int, RegistroExport] = {}
        for row in rows:
            r = dict(row)
            reg_id = r["id"]
            if reg_id not in registros_map:
                registros_map[reg_id] = RegistroExport.from_row(r)
            item_name = r.get("item_name")
            if item_name:
                registros_map[reg_id].items.append(item_name)

        return list(registros_map.values())
