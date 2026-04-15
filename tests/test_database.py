import os
import sqlite3
import tempfile

import pytest

from src.database.rac_database import RACDatabase
from src.models import Malote, Paciente, Registro, ItemCatalog, RegistroExport


@pytest.fixture
def db():
    with tempfile.TemporaryDirectory() as tmpdir:
        database = RACDatabase(db_path=os.path.join(tmpdir, "test.db"))
        yield database
        database.close(skip_backup=True)


@pytest.fixture
def malote(db):
    return db.create_malote("2026-04-12")


@pytest.fixture
def paciente(db):
    return db.create_paciente("João Silva")


@pytest.fixture
def catalog_items(db):
    return db.get_all_items()


@pytest.fixture
def registro(db, malote, paciente):
    return db.create_registro("entrada", paciente.id, malote.id)


@pytest.fixture
def full_setup(db, malote, paciente, catalog_items):
    reg = db.create_registro("entrada", paciente.id, malote.id)
    items = catalog_items[:3]
    db.set_registro_items(reg.id, [i.id for i in items])
    return {
        "db": db,
        "malote": malote,
        "paciente": paciente,
        "registro": reg,
        "items": items,
    }


class TestMaloteCRUD:
    def test_create_returns_malote(self, db):
        m = db.create_malote("2026-04-12")
        assert isinstance(m, Malote)
        assert m.id is not None
        assert m.date == "2026-04-12"

    def test_create_idempotent(self, db):
        m1 = db.create_malote("2026-04-12")
        m2 = db.create_malote("2026-04-12")
        assert m1.id == m2.id

    def test_get_by_id(self, db):
        created = db.create_malote("2026-04-12")
        found = db.get_malote_by_id(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.date == "2026-04-12"

    def test_get_by_id_not_found(self, db):
        assert db.get_malote_by_id(9999) is None

    def test_get_all_sorted_by_date_desc(self, db):
        db.create_malote("2026-01-01")
        db.create_malote("2026-03-15")
        db.create_malote("2026-02-28")
        all_m = db.get_all_malotes()
        dates = [m.date for m in all_m]
        assert dates == sorted(dates, reverse=True)

    def test_get_recent_limits(self, db):
        for i in range(10):
            db.create_malote(f"2026-01-{i+1:02d}")
        recent = db.get_recent_malotes(limit=5)
        assert len(recent) == 5

    def test_delete_empty_malote(self, db):
        m = db.create_malote("2026-04-12")
        assert db.delete_malote(m.id) is True
        assert db.get_malote_by_id(m.id) is None

    def test_delete_malote_with_registros(self, db, registro):
        malote = db.get_malote_by_id(registro.malote_id)
        assert db.delete_malote(malote.id) is False


class TestPacienteCRUD:
    def test_create_returns_paciente(self, db):
        p = db.create_paciente("Maria Santos")
        assert isinstance(p, Paciente)
        assert p.id is not None
        assert p.name == "MARIA SANTOS"

    def test_create_strips_whitespace(self, db):
        p = db.create_paciente("  Maria Santos  ")
        assert p.name == "MARIA SANTOS"

    def test_find_by_name_exact(self, db):
        db.create_paciente("João Silva")
        found = db.find_paciente_by_name("João Silva")
        assert found is not None
        assert found.name == "JOAO SILVA"

    def test_find_by_name_case_insensitive(self, db):
        db.create_paciente("João Silva")
        found = db.find_paciente_by_name("joão silva")
        assert found is not None
        assert found.name == "JOAO SILVA"

    def test_find_by_name_not_found(self, db):
        assert db.find_paciente_by_name("Ninguém") is None

    def test_find_by_name_accent_insensitive(self, db):
        db.create_paciente("João Silva")
        found = db.find_paciente_by_name("Joao Silva")
        assert found is not None
        assert found.name == "JOAO SILVA"

    def test_search_fuzzy(self, db):
        db.create_paciente("João Silva")
        db.create_paciente("Maria Santos")
        results = db.search_pacientes("silva")
        assert len(results) == 1
        assert results[0].name == "JOAO SILVA"

    def test_search_fuzzy_accent_insensitive(self, db):
        db.create_paciente("João Silva")
        results = db.search_pacientes("joao")
        assert len(results) == 1
        assert results[0].name == "JOAO SILVA"

    def test_delete_paciente_with_registros(self, db, registro):
        paciente = db.get_paciente_by_id(registro.paciente_id)
        assert db.delete_paciente(paciente.id) is False

    def test_delete_paciente_without_registros(self, db):
        p = db.create_paciente("Removível")
        assert db.delete_paciente(p.id) is True
        assert db.get_paciente_by_id(p.id) is None


class TestRegistroCRUD:
    def test_create_returns_registro(self, db, malote, paciente):
        r = db.create_registro("entrada", paciente.id, malote.id)
        assert isinstance(r, Registro)
        assert r.id is not None
        assert r.tipo == "entrada"
        assert r.paciente_id == paciente.id
        assert r.malote_id == malote.id

    def test_create_with_waiting_docs(self, db, malote, paciente):
        r = db.create_registro("entrada", paciente.id, malote.id, waiting_docs=True)
        assert r.waiting_docs is True

    def test_get_by_id_joins_patient_and_malote(self, db, malote, paciente):
        r = db.create_registro("entrada", paciente.id, malote.id)
        found = db.get_registro_by_id(r.id)
        assert found is not None
        assert found.paciente_name == "JOAO SILVA"
        assert found.malote_date == "2026-04-12"

    def test_find_by_tipo_paciente_malote(self, db, malote, paciente):
        r = db.create_registro("entrada", paciente.id, malote.id)
        found = db.find_registro("entrada", paciente.id, malote.id)
        assert found is not None
        assert found.id == r.id

    def test_find_not_found(self, db, malote, paciente):
        db.create_registro("entrada", paciente.id, malote.id)
        found = db.find_registro("renovacao", paciente.id, malote.id)
        assert found is None

    def test_update_tipo(self, db, malote, paciente):
        r = db.create_registro("entrada", paciente.id, malote.id)
        db.update_registro(r.id, tipo="renovacao")
        updated = db.get_registro_by_id(r.id)
        assert updated.tipo == "renovacao"

    def test_update_malote(self, db, paciente):
        m1 = db.create_malote("2026-04-12")
        m2 = db.create_malote("2026-04-13")
        r = db.create_registro("entrada", paciente.id, m1.id)
        db.update_registro(r.id, malote_id=m2.id)
        updated = db.get_registro_by_id(r.id)
        assert updated.malote_id == m2.id

    def test_delete(self, db, malote, paciente):
        r = db.create_registro("entrada", paciente.id, malote.id)
        assert db.delete_registro(r.id) is True
        assert db.get_registro_by_id(r.id) is None

    def test_get_by_malote(self, db, malote, paciente):
        db.create_registro("entrada", paciente.id, malote.id)
        db.create_registro("renovacao", paciente.id, malote.id)
        regs = db.get_registros_by_malote(malote.id)
        assert len(regs) == 2

    def test_get_by_malote_and_tipo(self, db, malote, paciente):
        db.create_registro("entrada", paciente.id, malote.id)
        db.create_registro("renovacao", paciente.id, malote.id)
        regs = db.get_registros_by_malote_and_tipo(malote.id, "entrada")
        assert len(regs) == 1
        assert regs[0].tipo == "entrada"


class TestUniqueConstraint:
    def test_same_tipo_paciente_malote_raises_integrity_error(
        self, db, malote, paciente
    ):
        r1 = db.create_registro("entrada", paciente.id, malote.id)
        assert r1.id is not None
        with pytest.raises(Exception):
            import sqlite3

            conn = sqlite3.connect(db.db_path)
            try:
                conn.execute(
                    "INSERT INTO registros (tipo, paciente_id, malote_id, created_at) VALUES (?, ?, ?, ?)",
                    ("entrada", paciente.id, malote.id, "2026-01-01"),
                )
            finally:
                conn.close()

    def test_create_duplicate_registro_raises_integrity_error(
        self, db, malote, paciente
    ):
        db.create_registro("entrada", paciente.id, malote.id)
        with pytest.raises(sqlite3.IntegrityError):
            db.create_registro("entrada", paciente.id, malote.id)

    def test_different_tipos_allowed(self, db, malote, paciente):
        r1 = db.create_registro("entrada", paciente.id, malote.id)
        r2 = db.create_registro("renovacao", paciente.id, malote.id)
        assert r1.id != r2.id

    def test_different_malotes_allowed(self, db, paciente):
        m1 = db.create_malote("2026-04-12")
        m2 = db.create_malote("2026-04-13")
        r1 = db.create_registro("entrada", paciente.id, m1.id)
        r2 = db.create_registro("entrada", paciente.id, m2.id)
        assert r1.id != r2.id

    def test_different_pacientes_allowed(self, db, malote):
        p1 = db.create_paciente("Alice")
        p2 = db.create_paciente("Bob")
        r1 = db.create_registro("entrada", p1.id, malote.id)
        r2 = db.create_registro("entrada", p2.id, malote.id)
        assert r1.id != r2.id


class TestRegistroItems:
    def test_set_and_get_items(self, db, malote, paciente, catalog_items):
        r = db.create_registro("entrada", paciente.id, malote.id)
        item_ids = [catalog_items[0].id, catalog_items[1].id]
        db.set_registro_items(r.id, item_ids)
        items = db.get_items_for_registro(r.id)
        assert len(items) == 2
        returned_ids = {i.item_id for i in items}
        assert returned_ids == set(item_ids)

    def test_set_items_replaces(self, db, malote, paciente, catalog_items):
        r = db.create_registro("entrada", paciente.id, malote.id)
        db.set_registro_items(r.id, [catalog_items[0].id])
        db.set_registro_items(r.id, [catalog_items[1].id, catalog_items[2].id])
        items = db.get_items_for_registro(r.id)
        assert len(items) == 2

    def test_set_items_empty_clears(self, db, malote, paciente, catalog_items):
        r = db.create_registro("entrada", paciente.id, malote.id)
        db.set_registro_items(r.id, [catalog_items[0].id])
        db.set_registro_items(r.id, [])
        items = db.get_items_for_registro(r.id)
        assert len(items) == 0

    def test_cascade_delete_on_registro(self, db, malote, paciente, catalog_items):
        r = db.create_registro("entrada", paciente.id, malote.id)
        db.set_registro_items(r.id, [catalog_items[0].id])
        db.delete_registro(r.id)
        items = db.get_items_for_registro(r.id)
        assert len(items) == 0

    def test_get_items_for_paciente_distinct(self, full_setup):
        db = full_setup["db"]
        malote = full_setup["malote"]
        paciente = full_setup["paciente"]
        items = full_setup["items"]

        r2 = db.create_registro("renovacao", paciente.id, malote.id)
        db.set_registro_items(r2.id, [items[0].id, items[2].id])

        patient_items = db.get_items_for_paciente(paciente.id)
        assert len(patient_items) == 3
        returned_ids = {i.id for i in patient_items}
        assert returned_ids == {i.id for i in items}


class TestExportHelpers:
    def test_get_registros_with_items(self, full_setup):
        db = full_setup["db"]
        malote = full_setup["malote"]

        exports = db.get_registros_with_items_by_malote(malote.id)
        assert len(exports) == 1
        assert isinstance(exports[0], RegistroExport)
        assert exports[0].paciente_name == "JOAO SILVA"
        assert exports[0].tipo == "entrada"
        assert len(exports[0].items) == 3

    def test_export_multiple_registros(self, full_setup):
        db = full_setup["db"]
        malote = full_setup["malote"]
        items = full_setup["items"]

        p2 = db.create_paciente("Ana Costa")
        r2 = db.create_registro("renovacao", p2.id, malote.id)
        db.set_registro_items(r2.id, [items[0].id])

        exports = db.get_registros_with_items_by_malote(malote.id)
        assert len(exports) == 2
        tipos = {e.tipo for e in exports}
        assert tipos == {"entrada", "renovacao"}

    def test_export_empty_malote(self, db):
        m = db.create_malote("2026-04-12")
        exports = db.get_registros_with_items_by_malote(m.id)
        assert len(exports) == 0


class TestCatalog:
    def test_catalog_seeded(self, db):
        items = db.get_all_items()
        assert len(items) > 0
        assert all(isinstance(i, ItemCatalog) for i in items)

    def test_catalog_sorted_by_name(self, db):
        items = db.get_all_items()
        names = [i.name for i in items]
        assert names == sorted(names, key=str.lower)

    def test_search_items(self, db):
        results = db.search_items("ABATA")
        assert len(results) > 0
        for r in results:
            assert "ABATA" in r.name

    def test_search_items_accent_insensitive(self, db):
        results = db.search_items("acido")
        assert len(results) > 0
        assert any("ACIDO" in r.name for r in results)


class TestSearchRegistrosByPatient:
    def test_search_by_name(self, full_setup):
        db = full_setup["db"]
        malote = full_setup["malote"]
        results = db.search_registros_by_patient(malote.id, "silva")
        assert len(results) == 1
        assert results[0].paciente_name == "JOAO SILVA"

    def test_search_by_name_accent_insensitive(self, full_setup):
        db = full_setup["db"]
        malote = full_setup["malote"]
        results = db.search_registros_by_patient(malote.id, "joao")
        assert len(results) == 1
        assert results[0].paciente_name == "JOAO SILVA"

    def test_search_no_match(self, full_setup):
        db = full_setup["db"]
        malote = full_setup["malote"]
        results = db.search_registros_by_patient(malote.id, "xyz")
        assert len(results) == 0
