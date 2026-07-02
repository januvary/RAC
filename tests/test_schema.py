import os
import sqlite3
import tempfile

import pytest

from src.database.rac_database import RACDatabase
from src.database.definitive_catalog import DEFINITIVE_CATALOG


@pytest.fixture
def db_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def _open_raw(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _get_stored_version(db_path: str) -> int:
    conn = _open_raw(db_path)
    row = conn.execute(
        "SELECT value FROM _schema_meta WHERE key = 'version'"
    ).fetchone()
    conn.close()
    return int(row["value"]) if row else 0


def _get_tables(db_path: str) -> set[str]:
    conn = _open_raw(db_path)
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()
    return tables


def _get_columns(db_path: str, table: str) -> set[str]:
    conn = _open_raw(db_path)
    cols = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    conn.close()
    return cols


EXPECTED_TABLES = {
    "malotes",
    "pacientes",
    "items_catalog",
    "registros",
    "registro_items",
    "processes",
    "_schema_meta",
}


class TestFreshSchema:
    def test_creates_all_tables(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        db = RACDatabase(db_path=db_path)
        db.close(skip_backup=True)

        tables = _get_tables(db_path)
        assert EXPECTED_TABLES.issubset(tables)

    def test_sets_version(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        db = RACDatabase(db_path=db_path)
        db.close(skip_backup=True)

        assert _get_stored_version(db_path) == RACDatabase.SCHEMA_VERSION

    def test_seeds_catalog(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        db = RACDatabase(db_path=db_path)
        db.close(skip_backup=True)

        conn = _open_raw(db_path)
        count = conn.execute("SELECT COUNT(*) FROM items_catalog").fetchone()[0]
        conn.close()
        assert count > 0

    def test_registro_items_has_process_id(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        db = RACDatabase(db_path=db_path)
        db.close(skip_backup=True)

        cols = _get_columns(db_path, "registro_items")
        assert "process_id" in cols

    def test_items_catalog_has_cids(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        db = RACDatabase(db_path=db_path)
        db.close(skip_backup=True)

        cols = _get_columns(db_path, "items_catalog")
        assert "cids" in cols

    def test_registro_items_has_cid(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        db = RACDatabase(db_path=db_path)
        db.close(skip_backup=True)

        cols = _get_columns(db_path, "registro_items")
        assert "cid" in cols

    def test_pacientes_has_no_cid(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        db = RACDatabase(db_path=db_path)
        db.close(skip_backup=True)

        cols = _get_columns(db_path, "pacientes")
        assert "cid" not in cols

    def test_malotes_has_arrival_date(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        db = RACDatabase(db_path=db_path)
        db.close(skip_backup=True)

        cols = _get_columns(db_path, "malotes")
        assert "arrival_date" in cols


class TestIdempotentReopen:
    def test_reopen_preserves_data_and_version(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        db = RACDatabase(db_path=db_path)
        db.create_paciente("João Silva")
        db.close(skip_backup=True)

        db2 = RACDatabase(db_path=db_path)
        p = db2.find_paciente_by_name("João Silva")
        db2.close(skip_backup=True)

        assert p is not None
        assert p.name == "JOAO SILVA"
        assert _get_stored_version(db_path) == RACDatabase.SCHEMA_VERSION

    def test_reopen_does_not_duplicate_catalog(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        db = RACDatabase(db_path=db_path)
        db.close(skip_backup=True)

        db2 = RACDatabase(db_path=db_path)
        db2.close(skip_backup=True)

        conn = _open_raw(db_path)
        count = conn.execute("SELECT COUNT(*) FROM items_catalog").fetchone()[0]
        conn.close()
        assert count == len(DEFINITIVE_CATALOG)
