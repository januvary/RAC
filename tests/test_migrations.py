import os
import sqlite3
import tempfile

import pytest

from src.database.rac_database import RACDatabase


@pytest.fixture
def db_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture(autouse=True)
def _isolate_schema():
    original_version = RACDatabase.SCHEMA_VERSION
    original_migrations = RACDatabase._MIGRATIONS.copy()
    yield
    RACDatabase.SCHEMA_VERSION = original_version
    RACDatabase._MIGRATIONS = original_migrations


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


def _create_v1_db(db_path: str) -> None:
    RACDatabase.SCHEMA_VERSION = 1
    RACDatabase._MIGRATIONS = {}
    db = RACDatabase(db_path=db_path)
    db.close(skip_backup=True)


class TestFreshDB:
    def test_creates_all_tables(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        _create_v1_db(db_path)

        conn = _open_raw(db_path)
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()

        expected = {
            "malotes",
            "pacientes",
            "items_catalog",
            "registros",
            "registro_items",
            "_schema_meta",
        }
        assert expected.issubset(tables)

    def test_sets_version(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        _create_v1_db(db_path)
        assert _get_stored_version(db_path) == RACDatabase.SCHEMA_VERSION

    def test_seeds_catalog(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        _create_v1_db(db_path)

        conn = _open_raw(db_path)
        count = conn.execute("SELECT COUNT(*) FROM items_catalog").fetchone()[0]
        conn.close()
        assert count > 0

    def test_idempotent_reopen(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        _create_v1_db(db_path)

        db2 = RACDatabase(db_path=db_path)
        conn = _open_raw(db_path)
        count = conn.execute("SELECT COUNT(*) FROM items_catalog").fetchone()[0]
        conn.close()
        db2.close(skip_backup=True)
        assert count > 0
        assert _get_stored_version(db_path) == RACDatabase.SCHEMA_VERSION


class TestMigrationFramework:
    def test_migration_applies_sql(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        _create_v1_db(db_path)

        RACDatabase._MIGRATIONS[2] = """
            ALTER TABLE pacientes ADD COLUMN observacao TEXT DEFAULT '';
        """
        RACDatabase.SCHEMA_VERSION = 2

        db = RACDatabase(db_path=db_path)
        conn = _open_raw(db_path)
        cols = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(pacientes)").fetchall()
        }
        conn.close()
        db.close(skip_backup=True)

        assert "observacao" in cols
        assert _get_stored_version(db_path) == 2

    def test_multiple_migrations_run_in_order(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        _create_v1_db(db_path)

        RACDatabase._MIGRATIONS[2] = """
            ALTER TABLE pacientes ADD COLUMN col_v2 TEXT DEFAULT '';
        """
        RACDatabase._MIGRATIONS[3] = """
            ALTER TABLE pacientes ADD COLUMN col_v3 TEXT DEFAULT '';
        """
        RACDatabase.SCHEMA_VERSION = 3

        db = RACDatabase(db_path=db_path)
        conn = _open_raw(db_path)
        cols = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(pacientes)").fetchall()
        }
        conn.close()
        db.close(skip_backup=True)

        assert "col_v2" in cols
        assert "col_v3" in cols
        assert _get_stored_version(db_path) == 3

    def test_already_applied_migrations_skip(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        _create_v1_db(db_path)

        RACDatabase._MIGRATIONS[2] = """
            ALTER TABLE pacientes ADD COLUMN col_v2 TEXT DEFAULT '';
        """
        RACDatabase.SCHEMA_VERSION = 2

        db = RACDatabase(db_path=db_path)
        db.close(skip_backup=True)

        db2 = RACDatabase(db_path=db_path)
        conn = _open_raw(db_path)
        cols = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(pacientes)").fetchall()
        }
        conn.close()
        db2.close(skip_backup=True)

        assert _get_stored_version(db_path) == 2
        assert "col_v2" in cols

    def test_migration_failure_raises_runtime_error(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        _create_v1_db(db_path)

        RACDatabase._MIGRATIONS[2] = """
            ALTER TABLE pacientes ADD COLUMN col_v2 TEXT DEFAULT '';
        """
        RACDatabase._MIGRATIONS[3] = """
            ALTER TABLE nonexistent_table ADD COLUMN broken TEXT;
        """
        RACDatabase.SCHEMA_VERSION = 3

        with pytest.raises(RuntimeError, match="Migration v3 failed"):
            RACDatabase(db_path=db_path)

        assert _get_stored_version(db_path) == 1

    def test_migration_preserves_data(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        _create_v1_db(db_path)

        RACDatabase.SCHEMA_VERSION = 1
        RACDatabase._MIGRATIONS = {}
        db = RACDatabase(db_path=db_path)
        db.create_paciente("João Silva")
        db.close(skip_backup=True)

        RACDatabase._MIGRATIONS[2] = """
            ALTER TABLE pacientes ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1;
        """
        RACDatabase.SCHEMA_VERSION = 2

        db2 = RACDatabase(db_path=db_path)
        p = db2.find_paciente_by_name("João Silva")
        conn = _open_raw(db_path)
        row = conn.execute(
            "SELECT name, ativo FROM pacientes WHERE id = ?", (p.id,)
        ).fetchone()
        conn.close()
        db2.close(skip_backup=True)

        assert row["name"] == "JOAO SILVA"
        assert row["ativo"] == 1

    def test_empty_migrations_with_version_bump(self, db_dir):
        db_path = os.path.join(db_dir, "test.db")
        _create_v1_db(db_path)

        RACDatabase.SCHEMA_VERSION = 2

        db = RACDatabase(db_path=db_path)
        db.close(skip_backup=True)
        assert _get_stored_version(db_path) == 2
