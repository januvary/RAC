from src.database.rac_database import RACDatabase
from src.sync.snapshot import export_snapshot


def _make_db(tmp_path):
    return RACDatabase(db_path=str(tmp_path / "t.db"))


class TestExportSnapshot:
    def test_empty_db(self, tmp_path):
        db = _make_db(tmp_path)
        try:
            snap = export_snapshot(db, "ocian", "USAFA OCIAN")
            assert snap["usafa_id"] == "ocian"
            assert snap["usafa_name"] == "USAFA OCIAN"
            assert snap["schema_version"] == db.SCHEMA_VERSION
            assert snap["summary"]["totals"]["registros"] == 0
            assert snap["summary"]["totals"]["pacientes"] == 0
            assert snap["summary"]["by_tipo"] == {}
            assert snap["summary"]["top_items"] == []
            assert set(snap["tables"]) == {
                "malotes",
                "pacientes",
                "items_catalog",
                "registros",
                "processes",
                "registro_items",
            }
        finally:
            db.close(skip_backup=True)

    def test_seeded_db(self, tmp_path):
        db = _make_db(tmp_path)
        try:
            malote = db.create_malote("2026-04-12")
            paciente = db.create_paciente("João Silva")
            db.create_registro("entrada", paciente.id, malote.id)

            snap = export_snapshot(db, "ocian", "USAFA OCIAN")
            summary = snap["summary"]
            assert summary["totals"]["registros"] == 1
            assert summary["totals"]["pacientes"] == 1
            assert summary["by_tipo"]["entrada"]["registros"] == 1
            assert summary["by_tipo"]["entrada"]["pacientes"] == 1
            assert len(snap["tables"]["malotes"]) == 1
        finally:
            db.close(skip_backup=True)
