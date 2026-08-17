"""AvisoService tests — full-stack port of the synthetic simulation.

Scenarios mirror the prototype's synthetic grid but go through the real
service + database: retiradas are saved via RegistroService with
process_months (the production path), then detection runs against stored
state.
"""

import os
import tempfile
from datetime import date, timedelta

import pytest

from src.database.rac_database import RACDatabase
from src.services.aviso_service import AvisoService
from src.services.registro_service import RegistroService


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
def aviso(db):
    return AvisoService(db)


@pytest.fixture
def paciente(db):
    return db.create_paciente("Maria Santos")


@pytest.fixture
def med(db):
    return db.get_all_items()[0].id


def _shift(base: date, days: int) -> str:
    return (base + timedelta(days=days)).isoformat()


JAN5 = date(2026, 1, 5)


def _anchor(service, paciente, iso, tipo="renovacao"):
    return service.save(
        tipo=tipo,
        paciente_name=paciente.name,
        malote_id=service._db.create_malote(iso).id,
        items=[],
    )


def _ret(service, paciente, iso, med_id, months, extra_items=()):
    return service.save(
        tipo="retirada",
        paciente_name=paciente.name,
        malote_id=service._db.create_malote(iso).id,
        items=[(med_id, 1, "", 0), *extra_items],
        process_months=[(1, months)] if months is not None else None,
    )


class TestDetection:
    def test_monthly_six_pickups_triggers_on_sixth(self, service, aviso, paciente, med):
        _anchor(service, paciente, JAN5.isoformat())
        for i in range(5):
            r = _ret(service, paciente, _shift(JAN5, 15 + 30 * i), med, 1)
            assert aviso.detect_for_retirada(r.registro_id) == []
        r6 = _ret(service, paciente, _shift(JAN5, 165), med, 1)
        labels = aviso.detect_for_retirada(r6.registro_id)
        assert len(labels) == 1
        lab = labels[0]
        assert lab.n == 1
        # D1 = month(2026-01-05 + 6 months) = July/2026
        assert (lab.d1.month, lab.d1.year) == (7, 2026)
        assert (lab.deadline.month, lab.deadline.year) == (7, 2026)

    def test_single_six_month_recibo_triggers_immediately(self, service, aviso, paciente, med):
        _anchor(service, paciente, JAN5.isoformat())
        r = _ret(service, paciente, _shift(JAN5, 15), med, 6)
        labels = aviso.detect_for_retirada(r.registro_id)
        assert len(labels) == 1
        assert labels[0].n == 6

    def test_partial_chunks_do_not_trigger(self, service, aviso, paciente, med):
        _anchor(service, paciente, JAN5.isoformat())
        r1 = _ret(service, paciente, _shift(JAN5, 15), med, 3)
        r2 = _ret(service, paciente, _shift(JAN5, 105), med, 2)
        assert aviso.detect_for_retirada(r1.registro_id) == []
        assert aviso.detect_for_retirada(r2.registro_id) == []

    def test_accumulation_3_plus_3_triggers_on_second(self, service, aviso, paciente, med):
        _anchor(service, paciente, JAN5.isoformat())
        _ret(service, paciente, _shift(JAN5, 15), med, 3)
        r2 = _ret(service, paciente, _shift(JAN5, 105), med, 3)
        labels = aviso.detect_for_retirada(r2.registro_id)
        assert len(labels) == 1
        assert labels[0].n == 3

    def test_overshoot_still_triggers(self, service, aviso, paciente, med):
        _anchor(service, paciente, JAN5.isoformat())
        _ret(service, paciente, _shift(JAN5, 15), med, 4)
        r2 = _ret(service, paciente, _shift(JAN5, 135), med, 4)
        assert len(aviso.detect_for_retirada(r2.registro_id)) == 1

    def test_non_retirada_tipo_returns_empty(self, service, aviso, paciente, med):
        r = _anchor(service, paciente, JAN5.isoformat())
        assert aviso.detect_for_retirada(r.registro_id) == []

    def test_retirada_without_anchor_no_label(self, service, aviso, paciente, med):
        r = _ret(service, paciente, _shift(JAN5, 15), med, 6)
        assert aviso.detect_for_retirada(r.registro_id) == []

    def test_retirada_without_months_contributes_zero(self, service, aviso, paciente, med):
        _anchor(service, paciente, JAN5.isoformat())
        # five monthly retiradas, pre-feature (no months recorded)
        for i in range(5):
            _ret(service, paciente, _shift(JAN5, 15 + 30 * i), med, None)
        # sixth WITH months=1: ledger only counts 1 -> no trigger
        r6 = _ret(service, paciente, _shift(JAN5, 165), med, 1)
        assert aviso.detect_for_retirada(r6.registro_id) == []


class TestProcessSegmentation:
    def test_same_malote_retirada_belongs_to_previous_process(
        self, service, aviso, paciente, med
    ):
        _anchor(service, paciente, JAN5.isoformat())
        _ret(service, paciente, _shift(JAN5, 15), med, 2)
        # 2nd renovação and a retirada share malote 2026-03-02
        _anchor(service, paciente, date(2026, 3, 2).isoformat())
        r = _ret(service, paciente, date(2026, 3, 2).isoformat(), med, 4)
        # the retirada counts toward the OLD process: 2+4 = 6 -> trigger,
        # with the deadline anchored at the January renovação
        labels = aviso.detect_for_retirada(r.registro_id)
        assert len(labels) == 1
        # D1 = month(2026-01-05 + 6 months) = July/2026
        assert (labels[0].d1.month, labels[0].d1.year) == (7, 2026)

    def test_new_process_resets_ledger(self, service, aviso, paciente, med):
        _anchor(service, paciente, JAN5.isoformat())
        _ret(service, paciente, _shift(JAN5, 15), med, 3)
        _ret(service, paciente, _shift(JAN5, 105), med, 3)  # triggers
        _anchor(service, paciente, date(2026, 8, 3).isoformat())
        r = _ret(service, paciente, date(2026, 8, 15).isoformat(), med, 3)
        assert aviso.detect_for_retirada(r.registro_id) == []

    def test_later_retirada_after_earlier_trigger_no_label(
        self, service, aviso, paciente, med
    ):
        _anchor(service, paciente, JAN5.isoformat())
        _ret(service, paciente, _shift(JAN5, 15), med, 6)  # the last
        r2 = _ret(service, paciente, _shift(JAN5, 75), med, 1)  # missed renewal
        assert aviso.detect_for_retirada(r2.registro_id) == []

    def test_multi_med_registro_one_label_per_med(self, db, service, aviso, paciente):
        items = db.get_all_items()
        med1, med2 = items[0].id, items[1].id
        _anchor(service, paciente, JAN5.isoformat())
        r = service.save(
            tipo="retirada",
            paciente_name=paciente.name,
            malote_id=db.create_malote(_shift(JAN5, 15)).id,
            items=[(med1, 1, "", 0), (med2, 2, "", 0)],
            process_months=[(1, 6), (2, 6)],
        )
        labels = aviso.detect_for_retirada(r.registro_id)
        assert len(labels) == 2
        assert {lab.item_id for lab in labels} == {med1, med2}
        assert all(lab.paciente_name == "MARIA SANTOS" for lab in labels)
        assert all(lab.med_name for lab in labels)


class TestPersistence:
    def test_retirada_months_saved_without_return_date(self, db, service, paciente, med):
        r = _ret(service, paciente, _shift(JAN5, 15), med, 3)
        procs = db.get_processes_by_registro(r.registro_id)
        assert len(procs) == 1
        assert procs[0].months_supply == 3
        assert procs[0].expected_return_date is None

    def test_retirada_edit_updates_months(self, db, service, aviso, paciente, med):
        _anchor(service, paciente, JAN5.isoformat())
        r1 = _ret(service, paciente, _shift(JAN5, 15), med, 2)
        # edit: backfill months from 2 to 6 -> becomes the last retirada
        r2 = _ret(service, paciente, _shift(JAN5, 15), med, 6)
        assert r2.registro_id == r1.registro_id
        procs = db.get_processes_by_registro(r1.registro_id)
        assert procs[0].months_supply == 6
        assert len(aviso.detect_for_retirada(r1.registro_id)) == 1

    def test_retirada_without_months_writes_no_processes(self, db, service, paciente, med):
        r = _ret(service, paciente, _shift(JAN5, 15), med, None)
        assert db.get_processes_by_registro(r.registro_id) == []

    def test_change_tipo_preserves_months(self, db, service, paciente, med):

        _anchor(service, paciente, JAN5.isoformat())
        r = _ret(service, paciente, _shift(JAN5, 15), med, 3)
        service.change_tipo(r.registro_id, "renovacao")
        procs = db.get_processes_by_registro(r.registro_id)
        assert len(procs) == 1
        assert procs[0].months_supply == 3
        service.change_tipo(r.registro_id, "retirada")
        procs = db.get_processes_by_registro(r.registro_id)
        assert len(procs) == 1
        assert procs[0].months_supply == 3

    def test_delete_restore_keeps_months(self, db, service, aviso, paciente, med):
        _anchor(service, paciente, JAN5.isoformat())
        r = _ret(service, paciente, _shift(JAN5, 15), med, 6)
        snap = service.delete_with_snapshot(r.registro_id)
        assert snap is not None
        assert snap.process_months == [(1, 6)]
        new_id = service.restore_from_snapshot(snap)
        assert len(aviso.detect_for_retirada(new_id)) == 1


class TestDetectForMalote:
    def _setup_malote(self, db, service):
        """Anchor malote (Jan 5) + export malote (Jan 20)."""
        return (
            db.create_malote("2026-01-05").id,
            db.create_malote("2026-01-20").id,
        )

    def test_labels_only_for_last_retiradas_in_malote(self, db, service, aviso):
        items = db.get_all_items()
        anchor_id, malote_id = self._setup_malote(db, service)

        # patient A: 6-month recibo in the export malote -> label
        pa = db.create_paciente("AAA ULTIMO")
        service.save(tipo="renovacao", paciente_name=pa.name, malote_id=anchor_id, items=[])
        service.save(tipo="retirada", paciente_name=pa.name, malote_id=malote_id,
                     items=[(items[0].id, 1, "", 0)], process_months=[(1, 6)])

        # patient B: 3-month recibo -> no label
        pb = db.create_paciente("BBB MEIO")
        service.save(tipo="renovacao", paciente_name=pb.name, malote_id=anchor_id, items=[])
        service.save(tipo="retirada", paciente_name=pb.name, malote_id=malote_id,
                     items=[(items[1].id, 1, "", 0)], process_months=[(1, 3)])

        # patient C: trigger retirada happened in an EARLIER malote -> not in this one
        pc = db.create_paciente("CCC ANTERIOR")
        service.save(tipo="renovacao", paciente_name=pc.name, malote_id=anchor_id, items=[])
        service.save(tipo="retirada", paciente_name=pc.name, malote_id=anchor_id,
                     items=[(items[2].id, 1, "", 0)], process_months=[(1, 6)])
        service.save(tipo="retirada", paciente_name=pc.name, malote_id=malote_id,
                     items=[(items[2].id, 1, "", 0)], process_months=[(1, 1)])

        labels = aviso.detect_for_malote(malote_id)
        assert len(labels) == 1
        assert labels[0].paciente_name == "AAA ULTIMO"
        # patient C's Jan-5 retirada shares the malote with its renovação:
        # per the same-malote rule it belongs to the PREVIOUS (nonexistent)
        # process -> no label from the anchor malote either
        assert aviso.detect_for_malote(anchor_id) == []

    def test_sorted_by_patient_then_med(self, db, service, aviso):
        items = db.get_all_items()
        anchor_id, malote_id = self._setup_malote(db, service)
        pz = db.create_paciente("ZZZ ZEVIANO")
        pa = db.create_paciente("AAA ABREU")
        # pa: one med; pz: two meds in one registro -> 3 labels total
        for p, iids in ((pz, (items[0].id, items[2].id)), (pa, (items[1].id,))):
            service.save(tipo="renovacao", paciente_name=p.name, malote_id=anchor_id, items=[])
            service.save(tipo="retirada", paciente_name=p.name, malote_id=malote_id,
                         items=[(iid, 1, "", 0) for iid in iids],
                         process_months=[(1, 6)])
        labels = aviso.detect_for_malote(malote_id)
        assert [(lab.paciente_name, lab.med_name) for lab in labels] == sorted(
            (lab.paciente_name, lab.med_name) for lab in labels
        )
        assert len(labels) == 3

    def test_empty_malote_returns_empty(self, db, aviso):
        empty = db.create_malote("2026-02-02")
        assert aviso.detect_for_malote(empty.id) == []


class TestDeadlines:
    def test_d1_is_anchor_plus_six_months(self, service, aviso, paciente, med):
        _anchor(service, paciente, JAN5.isoformat())
        r = _ret(service, paciente, _shift(JAN5, 15), med, 6)
        labels = aviso.detect_for_retirada(r.registro_id)
        assert len(labels) == 1
        # D1 = month(2026-01-05 + 6 months) = July/2026
        assert (labels[0].d1.month, labels[0].d1.year) == (7, 2026)
        assert (labels[0].deadline.month, labels[0].deadline.year) == (7, 2026)

    def test_virada_de_mes_d1_shifts_one_month(self, service, aviso, paciente, med):
        """Anchor on day 28: auth crosses the month boundary -> D1 +1 month."""
        _anchor(service, paciente, date(2026, 1, 28).isoformat())
        r = _ret(service, paciente, date(2026, 2, 10).isoformat(), med, 6)
        labels = aviso.detect_for_retirada(r.registro_id)
        assert len(labels) == 1
        # D1 = month(2026-01-28 + 6 months) = July/2026
        assert (labels[0].d1.month, labels[0].d1.year) == (7, 2026)

    def test_late_pickups_still_use_same_d1(self, service, aviso, paciente, med):
        """Monthly retiradas drifting 34d apart: D1 is always anchor+6."""
        _anchor(service, paciente, JAN5.isoformat())
        r = None
        for d in (15, 49, 83, 117, 151, 185):  # 34-day intervals
            r = _ret(service, paciente, _shift(JAN5, d), med, 1)
        labels = aviso.detect_for_retirada(r.registro_id)
        assert len(labels) == 1
        assert (labels[0].d1.month, labels[0].d1.year) == (7, 2026)
        assert (labels[0].deadline.month, labels[0].deadline.year) == (7, 2026)
