import os
import tempfile

import pytest

from src.database.rac_database import RACDatabase
from src.services.registro_service import RegistroService, SaveResult, EditContext
from src.services.exceptions import DuplicateRecordError, ValidationError
from src.constants import TIPO_LABELS


@pytest.fixture
def db():
    with tempfile.TemporaryDirectory() as tmpdir:
        database = RACDatabase(db_path=os.path.join(tmpdir, "test.db"))
        yield database
        database.close(skip_backup=True)


@pytest.fixture
def service(db):
    return RegistroService(db)


@pytest.fixture
def malote(db):
    return db.create_malote("2026-04-12")


@pytest.fixture
def paciente(db):
    return db.create_paciente("João Silva")


@pytest.fixture
def catalog_items(db):
    return db.get_all_items()


class TestSaveNewRegistro:
    def test_creates_new_paciente_and_registro(self, service, db, malote):
        result = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[],
        )
        assert isinstance(result, SaveResult)
        assert result.is_update is False
        assert result.registro_id is not None

        paciente = db.find_paciente_by_name("Maria Santos")
        assert paciente is not None
        assert paciente.name == "MARIA SANTOS"

        reg = db.get_registro_by_id(result.registro_id)
        assert reg is not None
        assert reg.tipo == "entrada"
        assert reg.paciente_id == paciente.id

    def test_finds_existing_paciente_by_name(self, service, db, malote):
        p = db.create_paciente("João Silva")
        result = service.save(
            tipo="entrada",
            paciente_name="João Silva",
            malote_id=malote.id,
            items=[],
        )
        assert result.registro_id is not None
        reg = db.get_registro_by_id(result.registro_id)
        assert reg.paciente_id == p.id

    def test_uses_paciente_id_when_provided(self, service, db, malote):
        p = db.create_paciente("Ana Costa")
        result = service.save(
            tipo="entrada",
            paciente_name="",
            malote_id=malote.id,
            items=[],
            paciente_id=p.id,
        )
        reg = db.get_registro_by_id(result.registro_id)
        assert reg.paciente_id == p.id

    def test_saves_items(self, service, db, malote, catalog_items):
        ids = [catalog_items[0].id, catalog_items[1].id]
        result = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(iid, 1) for iid in ids],
        )
        items = db.get_items_by_registro(result.registro_id)
        assert len(items) == 2
        assert {i.item_id for i in items} == set(ids)

    def test_waiting_docs_flag(self, service, db, malote):
        result = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[],
            waiting_docs=True,
        )
        reg = db.get_registro_by_id(result.registro_id)
        assert reg.waiting_docs is True

    def test_normalizes_paciente_name(self, service, db, malote):
        service.save(
            tipo="entrada",
            paciente_name="  ana maria  ",
            malote_id=malote.id,
            items=[],
        )
        p = db.find_paciente_by_name("ana maria")
        assert p is not None
        assert p.name == "ANA MARIA"


class TestSaveDedup:
    def test_dedup_same_tipo_paciente_malote(self, service, db, malote):
        r1 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[],
        )
        r2 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[],
        )
        assert r1.registro_id == r2.registro_id
        assert r2.is_update is True

    def test_different_tipos_create_separate(self, service, db, malote):
        r1 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[],
        )
        r2 = service.save(
            tipo="renovacao",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[],
        )
        assert r1.registro_id != r2.registro_id
        assert r2.is_update is False


class TestSaveEdit:
    def test_edit_existing_registro(self, service, db, malote, paciente, catalog_items):
        result = service.save(
            tipo="entrada",
            paciente_name=paciente.name,
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1)],
        )
        original_id = result.registro_id

        edited = service.save(
            tipo="entrada",
            paciente_name=paciente.name,
            malote_id=malote.id,
            items=[(catalog_items[1].id, 1)],
            edit_id=original_id,
            waiting_docs=True,
        )
        assert edited.registro_id == original_id
        assert edited.is_update is True

        items = db.get_items_by_registro(original_id)
        assert len(items) == 1
        assert items[0].item_id == catalog_items[1].id

        reg = db.get_registro_by_id(original_id)
        assert reg.waiting_docs is True


class TestDelete:
    def test_delete_registro(self, service, db, malote, paciente):
        result = service.save(
            tipo="entrada",
            paciente_name=paciente.name,
            malote_id=malote.id,
            items=[],
        )
        service.delete(result.registro_id)
        assert db.get_registro_by_id(result.registro_id) is None

    def test_delete_with_items_cascades(
        self, service, db, malote, paciente, catalog_items
    ):
        result = service.save(
            tipo="entrada",
            paciente_name=paciente.name,
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1)],
        )
        service.delete(result.registro_id)
        items = db.get_items_by_registro(result.registro_id)
        assert len(items) == 0

    def test_delete_invalid_id_raises(self, service):
        with pytest.raises(ValidationError):
            service.delete(0)

    def test_delete_nonexistent_raises(self, service):
        with pytest.raises(ValidationError, match="não encontrado"):
            service.delete(9999)


class TestLoadForEdit:
    def test_load_returns_registro_and_items(
        self, service, db, malote, paciente, catalog_items
    ):
        result = service.save(
            tipo="entrada",
            paciente_name=paciente.name,
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1), (catalog_items[2].id, 1)],
        )
        loaded = service.load_for_edit(result.registro_id)
        assert loaded is not None
        assert isinstance(loaded, EditContext)
        assert loaded.registro.id == result.registro_id
        assert len(loaded.items) == 2

    def test_load_nonexistent_returns_none(self, service):
        assert service.load_for_edit(9999) is None


class TestDuplicateRecordError:
    def test_change_tipo_to_duplicate_raises(self, service, db, malote, paciente):
        service.save(
            tipo="entrada",
            paciente_name=paciente.name,
            malote_id=malote.id,
            items=[],
        )
        r2 = service.save(
            tipo="renovacao",
            paciente_name=paciente.name,
            malote_id=malote.id,
            items=[],
        )
        with pytest.raises(DuplicateRecordError):
            db.update_registro(r2.registro_id, tipo="entrada")

    def test_move_to_duplicate_malote_raises(self, db, malote, paciente):
        m2 = db.create_malote("2026-04-13")
        db.create_registro("entrada", paciente.id, malote.id)
        r2 = db.create_registro("entrada", paciente.id, m2.id)
        with pytest.raises(DuplicateRecordError):
            db.update_registro(r2.id, malote_id=malote.id)


class TestValidation:
    def test_empty_tipo_raises(self, service, malote):
        with pytest.raises(ValidationError):
            service.save(
                tipo="",
                paciente_name="Maria",
                malote_id=malote.id,
                items=[],
            )

    def test_no_patient_raises(self, service, malote):
        with pytest.raises(ValidationError):
            service.save(
                tipo="entrada",
                paciente_name="",
                malote_id=malote.id,
                items=[],
                paciente_id=None,
            )

    def test_edit_nonexistent_id_raises(self, service, malote, catalog_items):
        with pytest.raises((ValidationError, Exception)):
            service.save(
                tipo="entrada",
                paciente_name="Maria Santos",
                malote_id=malote.id,
                items=[(catalog_items[0].id, 1)],
                edit_id=9999,
            )


class TestDoubleSaveWorkflow:
    """Simulates the entry page: save once, add items, save again."""

    def test_save_then_save_more_items_same_triple(
        self, service, db, malote, catalog_items
    ):
        r1 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1)],
        )
        assert r1.is_update is False

        r2 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1), (catalog_items[1].id, 1)],
            edit_id=None,
        )
        assert r2.registro_id == r1.registro_id
        assert r2.is_update is True

        items = db.get_items_by_registro(r1.registro_id)
        assert len(items) == 2

    def test_save_then_change_tipo_creates_new(
        self, service, db, malote, catalog_items
    ):
        r1 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1)],
        )
        assert r1.is_update is False

        r2 = service.save(
            tipo="renovacao",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1), (catalog_items[1].id, 1)],
            edit_id=None,
        )
        assert r2.is_update is False
        assert r2.registro_id != r1.registro_id

        items1 = db.get_items_by_registro(r1.registro_id)
        items2 = db.get_items_by_registro(r2.registro_id)
        assert len(items1) == 1
        assert len(items2) == 2

    def test_save_then_change_tipo_with_edit_id_raises_duplicate(
        self, service, db, malote, catalog_items
    ):
        r1 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1)],
        )
        r2 = service.save(
            tipo="renovacao",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[],
        )
        assert r2.is_update is False

        with pytest.raises(DuplicateRecordError):
            service.save(
                tipo="entrada",
                paciente_name="Maria Santos",
                malote_id=malote.id,
                items=[(catalog_items[0].id, 1), (catalog_items[1].id, 1)],
                edit_id=r2.registro_id,
            )

    def test_save_new_then_edit_id_set_resolves_correctly(
        self, service, db, malote, catalog_items
    ):
        r1 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1)],
        )
        edit_id = r1.registro_id

        r2 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1), (catalog_items[1].id, 1)],
            edit_id=edit_id,
        )
        assert r2.registro_id == edit_id
        assert r2.is_update is True

        items = db.get_items_by_registro(edit_id)
        assert len(items) == 2

    def test_save_new_patient_by_name_twice(self, service, db, malote, catalog_items):
        r1 = service.save(
            tipo="entrada",
            paciente_name="New Patient",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1)],
            paciente_id=None,
        )
        assert r1.is_update is False

        found = db.find_paciente_by_name("New Patient")
        assert found is not None

        r2 = service.save(
            tipo="entrada",
            paciente_name="New Patient",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1), (catalog_items[1].id, 1)],
            paciente_id=None,
        )
        assert r2.registro_id == r1.registro_id
        assert r2.is_update is True

    def test_three_saves_progressive_items(self, service, db, malote, catalog_items):
        ids = [c.id for c in catalog_items[:5]]

        r1 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(ids[0], 1)],
        )
        r2 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(ids[0], 1), (ids[1], 1)],
        )
        r3 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(ids[0], 1), (ids[1], 1), (ids[2], 1)],
        )

        assert r1.registro_id == r2.registro_id == r3.registro_id
        assert r2.is_update is True
        assert r3.is_update is True

        items = db.get_items_by_registro(r1.registro_id)
        assert len(items) == 3

    def test_save_with_two_malotes_same_patient(self, service, db, catalog_items):
        m1 = db.create_malote("2026-04-12")
        m2 = db.create_malote("2026-04-13")

        r1 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=m1.id,
            items=[(catalog_items[0].id, 1)],
        )
        r2 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=m2.id,
            items=[(catalog_items[1].id, 1)],
        )
        assert r1.registro_id != r2.registro_id

        r1_again = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=m1.id,
            items=[(catalog_items[0].id, 1), (catalog_items[2].id, 1)],
        )
        assert r1_again.registro_id == r1.registro_id
        items = db.get_items_by_registro(r1.registro_id)
        assert len(items) == 2


class TestComplexWorkflows:
    """Multi-step workflows: save, change, save, change back, etc."""

    def test_save_new_change_tipo_save_change_back_to_original_tipo(
        self, service, db, malote, catalog_items
    ):
        r_entrada = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1)],
        )
        assert r_entrada.is_update is False

        r_renovacao = service.save(
            tipo="renovacao",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[1].id, 1)],
        )
        assert r_renovacao.is_update is False
        assert r_renovacao.registro_id != r_entrada.registro_id

        r_entrada2 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1), (catalog_items[2].id, 1)],
        )
        assert r_entrada2.registro_id == r_entrada.registro_id
        assert r_entrada2.is_update is True

        items_entrada = db.get_items_by_registro(r_entrada.registro_id)
        items_renovacao = db.get_items_by_registro(r_renovacao.registro_id)
        assert len(items_entrada) == 2
        assert len(items_renovacao) == 1

    def test_cycle_all_tipos(self, service, db, malote, catalog_items):
        paciente_name = "Maria Santos"
        tipos = list(TIPO_LABELS.keys())
        n = len(tipos)
        ids = [c.id for c in catalog_items[:n]]
        result_ids = []

        for i, tipo in enumerate(tipos):
            r = service.save(
                tipo=tipo,
                paciente_name=paciente_name,
                malote_id=malote.id,
                items=[(ids[i], 1)],
            )
            assert r.is_update is False
            result_ids.append(r.registro_id)

        assert len(set(result_ids)) == n

        for i, tipo in enumerate(tipos):
            r = service.save(
                tipo=tipo,
                paciente_name=paciente_name,
                malote_id=malote.id,
                items=[(ids[i], 1), (ids[(i + 1) % n], 1)],
            )
            assert r.is_update is True
            assert r.registro_id == result_ids[i]

        for i, rid in enumerate(result_ids):
            items = db.get_items_by_registro(rid)
            assert len(items) == 2

    def test_save_edit_change_tipo_back_forth(self, service, db, malote, catalog_items):
        r1 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1)],
        )
        r2 = service.save(
            tipo="renovacao",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[1].id, 1)],
        )

        with pytest.raises(DuplicateRecordError):
            service.save(
                tipo="entrada",
                paciente_name="Maria Santos",
                malote_id=malote.id,
                items=[(catalog_items[2].id, 1)],
                edit_id=r2.registro_id,
            )

        items_r1 = db.get_items_by_registro(r1.registro_id)
        items_r2 = db.get_items_by_registro(r2.registro_id)
        assert len(items_r1) == 1
        assert len(items_r2) == 1

    def test_two_patients_same_tipo_same_malote(
        self, service, db, malote, catalog_items
    ):
        r_a = service.save(
            tipo="entrada",
            paciente_name="Alice",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1)],
        )
        r_b = service.save(
            tipo="entrada",
            paciente_name="Bob",
            malote_id=malote.id,
            items=[(catalog_items[1].id, 1)],
        )
        assert r_a.registro_id != r_b.registro_id

        r_a2 = service.save(
            tipo="entrada",
            paciente_name="Alice",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1), (catalog_items[2].id, 1)],
        )
        assert r_a2.registro_id == r_a.registro_id

        r_b2 = service.save(
            tipo="entrada",
            paciente_name="Bob",
            malote_id=malote.id,
            items=[(catalog_items[1].id, 1), (catalog_items[3].id, 1)],
        )
        assert r_b2.registro_id == r_b.registro_id

    def test_change_malote_save_change_back(self, service, db, catalog_items):
        m1 = db.create_malote("2026-04-12")
        m2 = db.create_malote("2026-04-13")

        r_m1 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=m1.id,
            items=[(catalog_items[0].id, 1)],
        )
        r_m2 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=m2.id,
            items=[(catalog_items[1].id, 1)],
        )
        assert r_m1.registro_id != r_m2.registro_id

        r_m1_again = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=m1.id,
            items=[(catalog_items[0].id, 1), (catalog_items[2].id, 1)],
        )
        assert r_m1_again.registro_id == r_m1.registro_id
        items = db.get_items_by_registro(r_m1.registro_id)
        assert len(items) == 2

    def test_edit_id_from_first_save_prevents_duplicate_on_second_save(
        self, service, db, malote, catalog_items
    ):
        r1 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1)],
        )
        edit_id = r1.registro_id

        r2 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1), (catalog_items[1].id, 1)],
            edit_id=edit_id,
        )
        assert r2.registro_id == edit_id
        assert r2.is_update is True

        all_regs = db.get_registros_by_malote(malote.id)
        assert len(all_regs) == 1

    def test_without_edit_id_after_first_save_changes_tipo_creates_orphan(
        self, service, db, malote, catalog_items
    ):
        r1 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1)],
        )

        r2 = service.save(
            tipo="renovacao",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[1].id, 1)],
            edit_id=None,
        )
        assert r2.is_update is False

        all_regs = db.get_registros_by_malote(malote.id)
        assert len(all_regs) == 2

        items_r1 = db.get_items_by_registro(r1.registro_id)
        assert len(items_r1) == 1
        assert items_r1[0].item_id == catalog_items[0].id

    def test_rename_patient_while_editing(self, service, db, malote, catalog_items):
        r1 = service.save(
            tipo="entrada",
            paciente_name="Maria Santos",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1)],
        )

        existing_patient = db.find_paciente_by_name("Maria Santos")
        assert existing_patient is not None

        db.update_paciente(existing_patient.id, "Maria Oliveira")

        r2 = service.save(
            tipo="entrada",
            paciente_name="Maria Oliveira",
            malote_id=malote.id,
            items=[(catalog_items[0].id, 1), (catalog_items[1].id, 1)],
            edit_id=r1.registro_id,
        )
        assert r2.registro_id == r1.registro_id
        reg = db.get_registro_by_id(r1.registro_id)
        assert reg.paciente_id == existing_patient.id
