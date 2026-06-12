#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC Database
SQLite database layer for Registros Alto Custo
"""

import sqlite3
import operator
import contextlib
from typing import Optional
from datetime import date, datetime

from andaime.database import BaseDatabase, db_op
from andaime.paths import resolve_db_path
from andaime.error_handler import ErrorHandler, ErrorLevel
from andaime.text import to_upper_normalized

from src.database.definitive_catalog import DEFINITIVE_CATALOG
from src.constants import TIPO_LABELS
from src.services.exceptions import DuplicateRecordError
from src.models import (
    Malote,
    Paciente,
    ItemCatalog,
    Registro,
    RegistroItem,
    RegistroExport,
    Process,
)


class RACDatabase(BaseDatabase):
    SCHEMA_VERSION = 5

    _MIGRATIONS: dict[int, str] = {
        2: "ALTER TABLE malotes ADD COLUMN arrival_date TEXT;",
        3: "ALTER TABLE registro_items ADD COLUMN process_group INTEGER NOT NULL DEFAULT 1;",
        4: "ALTER TABLE pacientes ADD COLUMN cid TEXT DEFAULT '';",
    }

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_path = resolve_db_path("registros.db", create_dir=True)
        super().__init__(db_path=db_path, entity_name="registros")

    def _resolve_default_db_path(self) -> str:
        return resolve_db_path("registros.db", create_dir=True)



    def _search_by_name(
        self, table: str, name_column: str, query: str, limit: int
    ) -> list[dict]:
        normalized = to_upper_normalized(query)
        return self._fetch_all(
            f"SELECT * FROM {table} WHERE {name_column} LIKE ? "
            f"ORDER BY {name_column} COLLATE NOCASE LIMIT ?",
            (f"%{normalized}%", limit),
        )

    def _create_schema(self) -> None:
        stored_version = self._ensure_schema_version()

        if stored_version == self.SCHEMA_VERSION:
            self._ensure_v5_column()
            self._seed_catalog_if_empty()
            return

        if stored_version == 0:
            has_existing = False
            with self._cursor() as cur:
                cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='registros'"
                )
                has_existing = cur.fetchone() is not None
            if has_existing:
                self._run_migrations(4)
                self._set_schema_version(self.SCHEMA_VERSION)
            else:
                self._create_fresh_schema()
                self._set_schema_version(self.SCHEMA_VERSION)
        else:
            self._run_migrations(stored_version)
            self._set_schema_version(self.SCHEMA_VERSION)
        self._seed_catalog_if_empty()

    def _ensure_v5_column(self) -> None:
        with self._cursor() as cur:
            cur.execute(
                "SELECT name FROM pragma_table_info('registro_items') WHERE name='process_id'"
            )
            if cur.fetchone():
                return
        self._migrate_v5()

    def _create_fresh_schema(self) -> None:
        with self._cursor() as cur:
            cur.executescript("""
                CREATE TABLE IF NOT EXISTS malotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    arrival_date TEXT
                );

                CREATE TABLE IF NOT EXISTS pacientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    cid TEXT NOT NULL DEFAULT ''
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

                CREATE TABLE IF NOT EXISTS processes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    registro_id INTEGER NOT NULL REFERENCES registros(id) ON DELETE CASCADE,
                    group_number INTEGER NOT NULL DEFAULT 1,
                    months_supply INTEGER NOT NULL DEFAULT 0,
                    expected_return_date TEXT
                );

                CREATE TABLE IF NOT EXISTS registro_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    registro_id INTEGER NOT NULL REFERENCES registros(id) ON DELETE CASCADE,
                    process_id INTEGER REFERENCES processes(id),
                    item_id INTEGER NOT NULL REFERENCES items_catalog(id),
                    process_group INTEGER NOT NULL DEFAULT 1
                );

                CREATE INDEX IF NOT EXISTS idx_registros_malote ON registros(malote_id);
                CREATE INDEX IF NOT EXISTS idx_registros_paciente ON registros(paciente_id);
                CREATE INDEX IF NOT EXISTS idx_registros_tipo ON registros(tipo);
                CREATE INDEX IF NOT EXISTS idx_pacientes_nome ON pacientes(name COLLATE NOCASE);
                CREATE INDEX IF NOT EXISTS idx_registro_items_registro ON registro_items(registro_id);
                CREATE INDEX IF NOT EXISTS idx_registro_items_item ON registro_items(item_id);
                CREATE INDEX IF NOT EXISTS idx_registro_items_process ON registro_items(process_id);
                CREATE INDEX IF NOT EXISTS idx_processes_registro ON processes(registro_id);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_registros_unique ON registros(tipo, paciente_id, malote_id);
                """)
            self._commit()

    def _run_migrations(self, from_version: int) -> None:
        if self.SCHEMA_VERSION >= 5 and from_version < 5:
            self._migrate_v5()
            ErrorHandler.log(
                "Migration v5 applied successfully",
                level=ErrorLevel.INFO,
                context="Database",
            )
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
                context="Database",
            )

    def _migrate_v5(self) -> None:
        with self._cursor() as cur:
            cur.execute(
                "SELECT name FROM pragma_table_info('registro_items') WHERE name='process_id'"
            )
            if cur.fetchone():
                return
            cur.execute(
                "ALTER TABLE registro_items ADD COLUMN process_id INTEGER REFERENCES processes(id)"
            )
            self._commit()
            cur.executescript("""
                CREATE TABLE IF NOT EXISTS processes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    registro_id INTEGER NOT NULL REFERENCES registros(id) ON DELETE CASCADE,
                    group_number INTEGER NOT NULL DEFAULT 1,
                    months_supply INTEGER NOT NULL DEFAULT 0,
                    expected_return_date TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_processes_registro ON processes(registro_id);
            """)
            existing = cur.execute(
                "SELECT DISTINCT registro_id, process_group FROM registro_items"
            ).fetchall()
            for row in existing:
                rid = row["registro_id"]
                pg = row["process_group"]
                cur.execute(
                    "INSERT INTO processes (registro_id, group_number) VALUES (?, ?)",
                    (rid, pg),
                )
                pid = cur.lastrowid
                cur.execute(
                    "UPDATE registro_items SET process_id = ? WHERE registro_id = ? AND process_group = ?",
                    (pid, rid, pg),
                )
            try:
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_registro_items_process ON registro_items(process_id)"
                )
            except Exception:
                pass
            self._commit()

    def _log_initialization_success(self) -> None:
        count = self._get_catalog_count()
        ErrorHandler.log(
            f"RACDatabase inicializado - {count} itens no catálogo",
            level=ErrorLevel.INFO,
            context="Database",
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
                    context="Database",
                )

    def _get_catalog_count(self) -> int:
        return self._fetch_count("items_catalog")

    # ========== MALOTE ==========

    @db_op("write")
    def create_malote(self, date: str, arrival_date: str | None = None) -> Malote:
        with self._cursor() as cur:
            cur.execute("SELECT id, arrival_date FROM malotes WHERE date = ?", (date,))
            existing = cur.fetchone()
            if existing:
                return Malote(
                    id=existing["id"], date=date, arrival_date=existing["arrival_date"]
                )
            cur.execute(
                "INSERT INTO malotes (date, arrival_date) VALUES (?, ?)",
                (date, arrival_date),
            )
            self._commit()
            return Malote(id=cur.lastrowid, date=date, arrival_date=arrival_date)

    @db_op("read")
    def get_malote_by_id(self, malote_id: int) -> Optional[Malote]:
        row = self._fetch_by_id("malotes", malote_id)
        return Malote.from_row(row) if row else None

    @db_op("read")
    def get_recent_malotes(self, limit: int = 5) -> list[Malote]:
        return [Malote.from_row(r) for r in self._fetch_all(
            "SELECT * FROM malotes ORDER BY date DESC, id DESC LIMIT ?",
            (limit,),
        )]

    @db_op("read")
    def get_all_malotes(self) -> list[Malote]:
        return [Malote.from_row(r) for r in self._fetch_all_table(
            "malotes", "date DESC, id DESC"
        )]

    @db_op("read")
    def get_malote_dates(self) -> set:
        dates = set()
        for r in self._fetch_all("SELECT date FROM malotes"):
            with contextlib.suppress(ValueError, TypeError):
                dates.add(datetime.fromisoformat(r["date"]).date())
        return dates

    @db_op("write")
    def update_malote(
        self, malote_id: int, date: str | None = None, arrival_date: str | None = None
    ) -> bool:
        updates = {}
        if date is not None:
            updates["date"] = date
        if arrival_date is not None:
            updates["arrival_date"] = arrival_date
        if not updates:
            return False
        return self._update_row("malotes", malote_id, **updates)

    @db_op("write")
    def delete_malote(self, malote_id: int) -> bool:
        return self._delete_row("malotes", malote_id, guards=[("registros", "malote_id")])

    # ========== PACIENTE ==========

    @db_op("write")
    def create_paciente(self, name: str) -> Paciente:
        normalized = to_upper_normalized(name.strip())
        pid = self._insert_row("pacientes", name=normalized)
        return Paciente(id=pid, name=normalized)

    @db_op("read")
    def get_paciente_by_id(self, paciente_id: int) -> Optional[Paciente]:
        row = self._fetch_by_id("pacientes", paciente_id)
        return Paciente.from_row(row) if row else None

    @db_op("read")
    def find_paciente_by_name(self, name: str) -> Optional[Paciente]:
        row = self._fetch_one(
            "SELECT * FROM pacientes WHERE name = ? LIMIT 1",
            (to_upper_normalized(name),),
        )
        return Paciente.from_row(row) if row else None

    @db_op("read")
    def search_pacientes(self, query: str, limit: int = 10) -> list[Paciente]:
        return [Paciente.from_row(r) for r in self._search_by_name(
            "pacientes", "name", query, limit,
        )]

    @db_op("write")
    def update_paciente(self, paciente_id: int, name: str, cid: str | None = None) -> bool:
        updates = {"name": to_upper_normalized(name.strip())}
        if cid is not None:
            updates["cid"] = cid
        return self._update_row("pacientes", paciente_id, **updates)

    @db_op("write")
    def delete_paciente(self, paciente_id: int) -> bool:
        return self._delete_row("pacientes", paciente_id, guards=[("registros", "paciente_id")])

    # ========== REGISTRO ==========

    @db_op("write")
    def create_registro(
        self,
        tipo: str,
        paciente_id: int,
        malote_id: int,
        waiting_docs: bool = False,
    ) -> Registro:
        now = datetime.now().isoformat()
        wd = 1 if waiting_docs else 0
        rid = self._insert_row(
            "registros",
            tipo=tipo,
            paciente_id=paciente_id,
            malote_id=malote_id,
            created_at=now,
            waiting_docs=wd,
        )
        return Registro(
            id=rid,
            tipo=tipo,
            paciente_id=paciente_id,
            malote_id=malote_id,
            created_at=now,
            waiting_docs=waiting_docs,
        )

    @db_op("read")
    def get_registro_by_id(self, registro_id: int) -> Optional[Registro]:
        row = self._fetch_one(
            "SELECT r.*, p.name as paciente_name, m.date as malote_date "
            "FROM registros r "
            "JOIN pacientes p ON r.paciente_id = p.id "
            "JOIN malotes m ON r.malote_id = m.id "
            "WHERE r.id = ?",
            (registro_id,),
        )
        return Registro.from_row(row) if row else None

    @db_op("read")
    def find_registro(
        self, tipo: str, paciente_id: int, malote_id: int
    ) -> Optional[Registro]:
        row = self._fetch_one(
            "SELECT r.*, p.name as paciente_name, m.date as malote_date "
            "FROM registros r "
            "JOIN pacientes p ON r.paciente_id = p.id "
            "JOIN malotes m ON r.malote_id = m.id "
            "WHERE r.tipo = ? AND r.paciente_id = ? AND r.malote_id = ? "
            "LIMIT 1",
            (tipo, paciente_id, malote_id),
        )
        return Registro.from_row(row) if row else None

    @db_op("read")
    def get_registros_by_malote(self, malote_id: int) -> list[Registro]:
        return [Registro.from_row(r) for r in self._fetch_all(
            "SELECT r.*, p.name as paciente_name "
            "FROM registros r "
            "JOIN pacientes p ON r.paciente_id = p.id "
            "WHERE r.malote_id = ? "
            "ORDER BY p.name COLLATE NOCASE",
            (malote_id,),
        )]

    @db_op("read")
    def get_registros_by_malote_and_tipo(
        self, malote_id: int, tipo: str
    ) -> list[Registro]:
        return [Registro.from_row(r) for r in self._fetch_all(
            "SELECT r.*, p.name as paciente_name "
            "FROM registros r "
            "JOIN pacientes p ON r.paciente_id = p.id "
            "WHERE r.malote_id = ? AND r.tipo = ? "
            "ORDER BY p.name COLLATE NOCASE",
            (malote_id, tipo),
        )]

    @db_op("write")
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

    @db_op("write")
    def delete_registro(self, registro_id: int) -> bool:
        with self._cursor() as cur:
            cur.execute("DELETE FROM registros WHERE id = ?", (registro_id,))
            self._commit()
            return cur.rowcount > 0

    @db_op("read")
    def search_registros_by_patient(
        self, query: str, active_malote_id: int | None = None, limit: int = 20
    ) -> list[Registro]:
        normalized = to_upper_normalized(query)
        return [Registro.from_row(r) for r in self._fetch_all(
            "SELECT r.*, p.name as paciente_name, m.date as malote_date "
            "FROM registros r "
            "JOIN pacientes p ON r.paciente_id = p.id "
            "JOIN malotes m ON r.malote_id = m.id "
            "WHERE p.name LIKE ? "
            "ORDER BY "
            "CASE WHEN r.malote_id = ? THEN 0 ELSE 1 END, "
            "m.date DESC, "
            "p.name COLLATE NOCASE "
            "LIMIT ?",
            (f"%{normalized}%", active_malote_id or 0, limit),
        )]

    @db_op("read")
    def get_registros_for_paciente(self, paciente_id: int) -> list[Registro]:
        return [Registro.from_row(r) for r in self._fetch_all(
            "SELECT r.*, p.name as paciente_name, m.date as malote_date "
            "FROM registros r "
            "JOIN pacientes p ON r.paciente_id = p.id "
            "JOIN malotes m ON r.malote_id = m.id "
            "WHERE r.paciente_id = ? "
            "ORDER BY m.date DESC, r.tipo",
            (paciente_id,),
        )]

    # ========== REGISTRO ITEMS ==========

    @db_op("write")
    def set_registro_items(
        self, registro_id: int, items: list[tuple[int, int]]
    ) -> None:
        with self._cursor() as cur:
            cur.execute(
                "DELETE FROM registro_items WHERE registro_id = ?",
                (registro_id,),
            )
            if items:
                cur.executemany(
                    "INSERT INTO registro_items (registro_id, item_id, process_group) VALUES (?, ?, ?)",
                    [(registro_id, iid, pg) for iid, pg in items],
                )
            self._commit()

    @db_op("write")
    def set_registro_items_with_process(
        self, registro_id: int, items: list[tuple[int, int, int | None]]
    ) -> None:
        with self._cursor() as cur:
            cur.execute(
                "DELETE FROM registro_items WHERE registro_id = ?",
                (registro_id,),
            )
            if items:
                cur.executemany(
                    "INSERT INTO registro_items (registro_id, item_id, process_group, process_id) VALUES (?, ?, ?, ?)",
                    [
                        (registro_id, iid, pg, pid)
                        for iid, pg, pid in items
                    ],
                )
            self._commit()

    @db_op("read")
    def get_items_for_registro(self, registro_id: int) -> list[RegistroItem]:
        return [RegistroItem.from_row(r) for r in self._fetch_all(
            "SELECT ri.*, ic.name as item_name, ic.unidade "
            "FROM registro_items ri "
            "JOIN items_catalog ic ON ri.item_id = ic.id "
            "WHERE ri.registro_id = ? "
            "ORDER BY ri.process_group, ic.name COLLATE NOCASE",
            (registro_id,),
        )]

    @db_op("read")
    def get_items_for_paciente(self, paciente_id: int) -> list[ItemCatalog]:
        return [ItemCatalog.from_row(r) for r in self._fetch_all(
            "SELECT DISTINCT ri.item_id as id, ic.name, ic.unidade "
            "FROM registro_items ri "
            "JOIN registros r ON ri.registro_id = r.id "
            "JOIN items_catalog ic ON ri.item_id = ic.id "
            "WHERE r.paciente_id = ? "
            "ORDER BY ic.name COLLATE NOCASE",
            (paciente_id,),
        )]

    # ========== PROCESSES ==========

    @db_op("write")
    def create_process(
        self,
        registro_id: int,
        group_number: int = 1,
        months_supply: int = 0,
        expected_return_date: str | None = None,
    ) -> Process:
        pid = self._insert_row(
            "processes",
            registro_id=registro_id,
            group_number=group_number,
            months_supply=months_supply,
            expected_return_date=expected_return_date,
        )
        return Process(
            id=pid,
            registro_id=registro_id,
            group_number=group_number,
            months_supply=months_supply,
            expected_return_date=expected_return_date,
        )

    @db_op("write")
    def set_processes(
        self,
        registro_id: int,
        processes: list[tuple[int, int, str | None]],
    ) -> list[Process]:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE registro_items SET process_id = NULL WHERE registro_id = ?",
                (registro_id,),
            )
            cur.execute(
                "DELETE FROM processes WHERE registro_id = ?",
                (registro_id,),
            )
            result = []
            for group_number, months_supply, expected_return_date in processes:
                cur.execute(
                    "INSERT INTO processes (registro_id, group_number, months_supply, expected_return_date) VALUES (?, ?, ?, ?)",
                    (registro_id, group_number, months_supply, expected_return_date),
                )
                result.append(Process(
                    id=cur.lastrowid,
                    registro_id=registro_id,
                    group_number=group_number,
                    months_supply=months_supply,
                    expected_return_date=expected_return_date,
                ))
            self._commit()
            return result

    @db_op("read")
    def get_processes_for_registro(self, registro_id: int) -> list[Process]:
        return [Process.from_row(r) for r in self._fetch_all(
            "SELECT * FROM processes WHERE registro_id = ? ORDER BY group_number",
            (registro_id,),
        )]

    @db_op("write")
    def update_process(self, process_id: int, **fields) -> bool:
        allowed = {"group_number", "months_supply", "expected_return_date"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return False
        return self._update_row("processes", process_id, **updates)

    @db_op("read")
    def get_malote_arrivals_between(self, start_iso: str, end_iso: str) -> list[str]:
        from src.utils.date_calculator import calculate_arrival_date

        rows = self._fetch_all(
            "SELECT arrival_date, date FROM malotes ORDER BY date ASC",
        )
        result = []
        for r in rows:
            arrival = r["arrival_date"]
            if not arrival and r["date"]:
                try:
                    arrival = calculate_arrival_date(
                        date.fromisoformat(r["date"])
                    ).isoformat()
                except (ValueError, TypeError):
                    continue
            if arrival and start_iso <= arrival <= end_iso:
                result.append(arrival)
        return result

    @db_op("read")
    def count_return_dates_between(self, start_iso: str, end_iso: str) -> dict[str, int]:
        rows = self._fetch_all(
            "SELECT p.expected_return_date, COUNT(*) as cnt "
            "FROM processes p "
            "WHERE p.expected_return_date IS NOT NULL "
            "AND p.expected_return_date >= ? AND p.expected_return_date <= ? "
            "GROUP BY p.expected_return_date",
            (start_iso, end_iso),
        )
        return {r["expected_return_date"]: r["cnt"] for r in rows}

    @db_op("read")
    def get_earlier_malote(self, current_malote_id: int) -> Optional[Malote]:
        current = self.get_malote_by_id(current_malote_id)
        if not current:
            return None
        row = self._fetch_one(
            "SELECT * FROM malotes WHERE date < ? ORDER BY date DESC LIMIT 1",
            (current.date,),
        )
        return Malote.from_row(row) if row else None

    @db_op("read")
    def get_next_malote(self, current_malote_id: int) -> Optional[Malote]:
        current = self.get_malote_by_id(current_malote_id)
        if not current:
            return None
        row = self._fetch_one(
            "SELECT * FROM malotes WHERE date > ? ORDER BY date ASC LIMIT 1",
            (current.date,),
        )
        return Malote.from_row(row) if row else None

    # ========== ITEMS CATALOG ==========

    @db_op("read")
    def get_all_items(self) -> list[ItemCatalog]:
        return [ItemCatalog.from_row(r) for r in self._fetch_all_table(
            "items_catalog", "name COLLATE NOCASE"
        )]

    @db_op("read")
    def search_items(self, query: str, limit: int = 10) -> list[ItemCatalog]:
        return [ItemCatalog.from_row(r) for r in self._search_by_name(
            "items_catalog", "name", query, limit,
        )]

    @db_op("write")
    def create_item(self, name: str, unidade: str = "un") -> ItemCatalog:
        normalized = to_upper_normalized(name.strip())
        iid = self._insert_row("items_catalog", name=normalized, unidade=unidade)
        return ItemCatalog(id=iid, name=normalized, unidade=unidade)

    @db_op("write")
    def update_item(self, item_id: int, name: str) -> bool:
        return self._update_row(
            "items_catalog", item_id, name=to_upper_normalized(name.strip())
        )

    @db_op("write")
    def delete_item(self, item_id: int) -> bool:
        return self._delete_row(
            "items_catalog", item_id, guards=[("registro_items", "item_id")]
        )

    # ========== PACIENTE (listagem) ==========

    @db_op("read")
    def get_all_pacientes(self) -> list[Paciente]:
        return [Paciente.from_row(r) for r in self._fetch_all_table(
            "pacientes", "name COLLATE NOCASE"
        )]

    # ========== EXPORT HELPERS ==========

    @db_op("read")
    def get_registros_with_items_by_malote(
        self, malote_id: int
    ) -> list[RegistroExport]:
        from src.models import ProcessExport

        rows = self._fetch_all(
            "SELECT r.id, r.tipo, r.paciente_id, p.name as paciente_name, "
            "ic.name as item_name, ri.process_group, "
            "pr.expected_return_date, pr.group_number as process_group_number "
            "FROM registros r "
            "JOIN pacientes p ON r.paciente_id = p.id "
            "LEFT JOIN registro_items ri ON ri.registro_id = r.id "
            "LEFT JOIN items_catalog ic ON ri.item_id = ic.id "
            "LEFT JOIN processes pr ON pr.id = ri.process_id "
            "WHERE r.malote_id = ? AND r.waiting_docs = 0 "
            "ORDER BY r.tipo, p.name COLLATE NOCASE, ri.process_group, ic.name",
            (malote_id,),
        )

        registros_map: dict[int, RegistroExport] = {}
        groups_map: dict[int, dict[int, list[str]]] = {}
        return_dates_map: dict[int, dict[int, str | None]] = {}
        for r in rows:
            reg_id = r["id"]
            if reg_id not in registros_map:
                registros_map[reg_id] = RegistroExport.from_row(r)
                groups_map[reg_id] = {}
                return_dates_map[reg_id] = {}
            item_name = r.get("item_name")
            if item_name:
                pg = r.get("process_group", 1) or 1
                groups_map[reg_id].setdefault(pg, []).append(item_name)
                if pg not in return_dates_map[reg_id]:
                    return_dates_map[reg_id][pg] = r.get("expected_return_date")

        for reg_id, groups in groups_map.items():
            sorted_groups = sorted(groups.items(), key=operator.itemgetter(0))
            registros_map[reg_id].processes = [
                ProcessExport(
                    group_number=pg,
                    items=items,
                    expected_return_date=return_dates_map.get(reg_id, {}).get(pg),
                )
                for pg, items in sorted_groups if items
            ]

        return list(registros_map.values())

    # ========== STATISTICS ==========

    def _stats_where(
        self,
        cur,
        tipo: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[str, list]:
        clauses: list[str] = []
        params: list = []
        if tipo:
            clauses.append("r.tipo = ?")
            params.append(tipo)
        if date_from:
            clauses.append("m.date >= ?")
            params.append(date_from)
        if date_to:
            clauses.append("m.date <= ?")
            params.append(date_to)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        return where, params

    @db_op("read")
    def get_stats_summary(
        self,
        tipo: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, int]:
        with self._cursor() as cur:
            where, params = self._stats_where(cur, tipo, date_from, date_to)
            cur.execute(
                f"SELECT COUNT(*) AS total_registros, "
                f"COUNT(DISTINCT r.paciente_id) AS total_pacientes, "
                f"COUNT(DISTINCT r.malote_id) AS total_malotes "
                f"FROM registros r JOIN malotes m ON r.malote_id = m.id{where}",
                params,
            )
            row = dict(cur.fetchone())
            cur.execute(
                f"SELECT COUNT(DISTINCT ri.item_id) AS total_items "
                f"FROM registro_items ri "
                f"JOIN registros r ON ri.registro_id = r.id "
                f"JOIN malotes m ON r.malote_id = m.id{where}",
                params,
            )
            row2 = dict(cur.fetchone())
            return {
                "total_registros": row["total_registros"] or 0,
                "total_pacientes": row["total_pacientes"] or 0,
                "total_items": row2["total_items"] or 0,
                "total_malotes": row["total_malotes"] or 0,
            }

    @db_op("read")
    def get_stats_by_tipo(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        with self._cursor() as cur:
            where, params = self._stats_where(cur, date_from=date_from, date_to=date_to)
            cur.execute(
                f"SELECT r.tipo, "
                f"COUNT(*) AS registros, "
                f"COUNT(DISTINCT r.paciente_id) AS pacientes "
                f"FROM registros r JOIN malotes m ON r.malote_id = m.id{where} "
                f"GROUP BY r.tipo ORDER BY r.tipo",
                params,
            )
            tipo_rows = [dict(r) for r in cur.fetchall()]
            cur.execute(
                f"SELECT r.tipo, COUNT(DISTINCT ri.item_id) AS items "
                f"FROM registro_items ri "
                f"JOIN registros r ON ri.registro_id = r.id "
                f"JOIN malotes m ON r.malote_id = m.id{where} "
                f"GROUP BY r.tipo",
                params,
            )
            item_map = {dict(r)["tipo"]: dict(r)["items"] for r in cur.fetchall()}
            for row in tipo_rows:
                row["items"] = item_map.get(row["tipo"], 0)
            return tipo_rows

    @db_op("read")
    def get_stats_totals(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        with self._cursor() as cur:
            where, params = self._stats_where(cur, date_from=date_from, date_to=date_to)
            cur.execute(
                f"SELECT COUNT(*) AS registros, "
                f"COUNT(DISTINCT paciente_id) AS pacientes "
                f"FROM registros r JOIN malotes m ON r.malote_id = m.id{where}",
                params,
            )
            return dict(cur.fetchone())

    @db_op("read")
    def get_malote_date_range(self) -> tuple[str | None, str | None]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT MIN(date) AS dmin, MAX(date) AS dmax FROM malotes"
            )
            row = cur.fetchone()
            if row and row["dmin"]:
                return row["dmin"], row["dmax"]
            return None, None

    @db_op("read")
    def get_stats_top_medications(
        self,
        tipo: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        with self._cursor() as cur:
            where, params = self._stats_where(cur, tipo, date_from, date_to)
            cur.execute(
                f"SELECT ic.name AS medicamento, COUNT(*) AS registros "
                f"FROM registro_items ri "
                f"JOIN items_catalog ic ON ri.item_id = ic.id "
                f"JOIN registros r ON ri.registro_id = r.id "
                f"JOIN malotes m ON r.malote_id = m.id{where} "
                f"GROUP BY ri.item_id ORDER BY registros DESC",
                params,
            )
            return [dict(r) for r in cur.fetchall()]

    @db_op("read")
    def get_stats_top_patients(
        self,
        tipo: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        with self._cursor() as cur:
            where, params = self._stats_where(cur, tipo, date_from, date_to)
            cur.execute(
                f"SELECT p.name AS paciente, "
                f"COUNT(*) AS registros, "
                f"COUNT(DISTINCT m.id) AS malotes "
                f"FROM registros r "
                f"JOIN pacientes p ON r.paciente_id = p.id "
                f"JOIN malotes m ON r.malote_id = m.id{where} "
                f"GROUP BY r.paciente_id ORDER BY registros DESC LIMIT ?",
                params + [limit],
            )
            patient_rows = [dict(r) for r in cur.fetchall()]
            pids_where = where.replace("r.", "rr.").replace("m.", "mm.")
            for row in patient_rows:
                cur.execute(
                    f"SELECT COUNT(DISTINCT ri.item_id) AS items "
                    f"FROM registro_items ri "
                    f"JOIN registros rr ON ri.registro_id = rr.id "
                    f"JOIN pacientes p ON rr.paciente_id = p.id "
                    f"JOIN malotes mm ON rr.malote_id = mm.id "
                    f"WHERE p.name = ?{(' AND' + pids_where.replace(' WHERE ', '')) if pids_where and 'WHERE' in pids_where else ''}",
                    [row["paciente"]] + params,
                )
                row["items"] = dict(cur.fetchone())["items"] or 0
            return patient_rows

    @db_op("read")
    def get_stats_malote_timeline(
        self,
        tipo: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        with self._cursor() as cur:
            where_base, params = self._stats_where(cur, tipo, date_from, date_to)
            cur.execute(
                f"SELECT m.date, m.id AS malote_id "
                f"FROM malotes m "
                f"WHERE m.id IN (SELECT DISTINCT r.malote_id FROM registros r JOIN malotes m ON r.malote_id = m.id{where_base}) "
                f"ORDER BY m.date DESC",
                params,
            )
            malotes = [dict(r) for r in cur.fetchall()]
            result = []
            for mal in malotes:
                row: dict = {"date": mal["date"], "malote_id": mal["malote_id"]}
                for t in TIPO_LABELS:
                    cur.execute(
                        "SELECT COUNT(*) AS cnt FROM registros r "
                        "JOIN pacientes p ON r.paciente_id = p.id "
                        "WHERE r.malote_id = ? AND r.tipo = ?",
                        (mal["malote_id"], t),
                    )
                    row[t] = dict(cur.fetchone())["cnt"] or 0
                row["total"] = sum(row[t] for t in TIPO_LABELS)
                if row["total"] > 0:
                    result.append(row)
            return result
