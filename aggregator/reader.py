#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Per-unit database reader — opens a unit's registros.db read-only and
extracts stats for the aggregator.

No imports from src.* — this module is self-contained and only depends on
stdlib + the aggregator models.  The database is opened in URI read-only
mode (?mode=ro) so it never interferes with the unit's write access.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from aggregator.models import AggregateStats, TipoBreakdown, UsafaStats


def _dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


def _open_readonly(db_path: Path) -> sqlite3.Connection:
    """Open a SQLite database in URI read-only mode.

    Raises FileNotFoundError if the file doesn't exist, and
    sqlite3.OperationalError if the database is locked.
    """
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=10)
    conn.row_factory = _dict_factory
    return conn


def _count_registros(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS cnt FROM registros").fetchone()
    return int(row["cnt"]) if row else 0


def _count_pacientes(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COUNT(DISTINCT paciente_id) AS cnt FROM registros"
    ).fetchone()
    return int(row["cnt"]) if row else 0


def _count_malotes(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS cnt FROM malotes").fetchone()
    return int(row["cnt"]) if row else 0


def _stats_by_tipo(conn: sqlite3.Connection) -> dict[str, TipoBreakdown]:
    """Tipo breakdown: registros, pacientes, and distinct items per tipo.

    Mirrors RACDatabase.get_stats_by_tipo() (no date filters).
    """
    rows = conn.execute(
        "SELECT r.tipo, "
        "COUNT(*) AS registros, "
        "COUNT(DISTINCT r.paciente_id) AS pacientes "
        "FROM registros r "
        "JOIN malotes m ON r.malote_id = m.id "
        "GROUP BY r.tipo ORDER BY r.tipo"
    ).fetchall()

    item_rows = conn.execute(
        "SELECT r.tipo, COUNT(DISTINCT ri.item_id) AS items "
        "FROM registro_items ri "
        "JOIN registros r ON ri.registro_id = r.id "
        "JOIN malotes m ON r.malote_id = m.id "
        "GROUP BY r.tipo"
    ).fetchall()
    item_map = {r["tipo"]: int(r["items"]) for r in item_rows}

    result: dict[str, TipoBreakdown] = {}
    for r in rows:
        result[r["tipo"]] = TipoBreakdown(
            registros=int(r["registros"]),
            pacientes=int(r["pacientes"]),
            items=item_map.get(r["tipo"], 0),
        )
    return result


def _top_items(conn: sqlite3.Connection, limit: int = 20) -> list[dict]:
    """Top medications by usage count.

    Mirrors RACDatabase.get_stats_top_itens() (no date filters).
    """
    rows = conn.execute(
        "SELECT ic.name AS medicamento, COUNT(*) AS registros "
        "FROM registro_items ri "
        "JOIN items_catalog ic ON ri.item_id = ic.id "
        "JOIN registros r ON ri.registro_id = r.id "
        "JOIN malotes m ON r.malote_id = m.id "
        "GROUP BY ri.item_id "
        "ORDER BY registros DESC "
        "LIMIT ?",
        (limit,),
    ).fetchall()
    return [
        {"medicamento": r["medicamento"], "registros": int(r["registros"])}
        for r in rows
    ]


def read_unit(
    unit_folder: Path,
    *,
    usafa_id: str | None = None,
    usafa_name: str | None = None,
) -> UsafaStats | None:
    """Read stats from a unit's data folder.

    Expected layout::

        <unit_folder>/
        ├── data/
        │   ├── registros.db
        │   └── config.json   (optional, for usafa_id/usafa_name)
        └── ...

    If ``usafa_id`` / ``usafa_name`` are not provided, they are read from
    ``config.json``.  Falls back to the folder name for ``usafa_id``.

    Returns ``None`` if the database file doesn't exist or can't be read.
    """
    db_path = unit_folder / "data" / "registros.db"
    if not db_path.exists():
        return None

    # Read identity from config.json if not provided
    if usafa_id is None or usafa_name is None:
        config_path = unit_folder / "data" / "config.json"
        if config_path.exists():
            try:
                cfg = json.loads(config_path.read_text(encoding="utf-8"))
                if usafa_id is None:
                    usafa_id = cfg.get("usafa_id", unit_folder.name)
                if usafa_name is None:
                    usafa_name = cfg.get("usafa_name", unit_folder.name)
            except (json.JSONDecodeError, OSError):
                pass
    if usafa_id is None:
        usafa_id = unit_folder.name
    if usafa_name is None:
        usafa_name = unit_folder.name

    try:
        conn = _open_readonly(db_path)
    except (FileNotFoundError, sqlite3.OperationalError):
        return None

    try:
        by_tipo = _stats_by_tipo(conn)
        top_items = _top_items(conn)
        registros = _count_registros(conn)
        pacientes = _count_pacientes(conn)
        malotes = _count_malotes(conn)
    finally:
        conn.close()

    return UsafaStats(
        usafa_id=usafa_id,
        usafa_name=usafa_name,
        exported_at=datetime.now().isoformat(),
        registros=registros,
        pacientes=pacientes,
        malotes=malotes,
        by_tipo=by_tipo,
        top_items=top_items,
    )


def aggregate(units: list[UsafaStats]) -> AggregateStats:
    """Combine per-unit stats into aggregate totals.

    This replaces merge_snapshots() from the old sync module.
    """
    by_tipo: dict[str, int] = {}
    item_counts: dict[str, int] = {}
    total_registros = 0
    total_pacientes = 0

    for u in units:
        total_registros += u.registros
        total_pacientes += u.pacientes
        for tipo, breakdown in u.by_tipo.items():
            by_tipo[tipo] = by_tipo.get(tipo, 0) + breakdown.registros
        for item in u.top_items:
            name = item.get("medicamento", "")
            if name:
                item_counts[name] = item_counts.get(name, 0) + item.get("registros", 0)

    top_items = [
        {"medicamento": name, "registros": count}
        for name, count in sorted(item_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

    return AggregateStats(
        usafas=units,
        total_registros=total_registros,
        total_pacientes=total_pacientes,
        total_usafas=len(units),
        by_tipo=by_tipo,
        top_items=top_items,
    )
