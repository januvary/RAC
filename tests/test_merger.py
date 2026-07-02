from src.sync.merger import AggregateStats, UsafaStats, merge_snapshots
from src.sync.types import Snapshot


def _snap(
    usafa_id: str,
    usafa_name: str,
    reg: int,
    pac: int,
    by_tipo: dict[str, int],
    top_items: list[dict],
    malotes: int = 1,
) -> Snapshot:
    return {
        "usafa_id": usafa_id,
        "usafa_name": usafa_name,
        "exported_at": "2026-06-25T10:00:00",
        "schema_version": 5,
        "tables": {"malotes": [{} for _ in range(malotes)]},
        "summary": {
            "by_tipo": {
                t: {"registros": c, "pacientes": 0, "items": 0}
                for t, c in by_tipo.items()
            },
            "totals": {"registros": reg, "pacientes": pac},
            "top_items": top_items,
        },
    }


class TestMergeSnapshots:
    def test_empty(self):
        agg = merge_snapshots([])
        assert agg.total_usafas == 0
        assert agg.total_registros == 0
        assert agg.top_items == []
        assert isinstance(agg, AggregateStats)

    def test_single(self):
        agg = merge_snapshots(
            [
                _snap(
                    "ocian",
                    "USAFA OCIAN",
                    10,
                    4,
                    {"entrada": 10},
                    [{"medicamento": "A", "registros": 10}],
                    malotes=3,
                )
            ]
        )
        assert agg.total_usafas == 1
        assert agg.total_registros == 10
        assert agg.total_pacientes == 4
        assert agg.by_tipo == {"entrada": 10}
        assert agg.top_items == [{"medicamento": "A", "registros": 10}]
        assert isinstance(agg.usafas[0], UsafaStats)
        assert agg.usafas[0].malotes == 3

    def test_multi_aggregates(self):
        a = _snap(
            "ocian",
            "OCIAN",
            5,
            2,
            {"entrada": 3, "retirada": 2},
            [
                {"medicamento": "A", "registros": 3},
                {"medicamento": "B", "registros": 2},
            ],
        )
        b = _snap(
            "outra",
            "OUTRA",
            7,
            3,
            {"entrada": 4, "retirada": 3},
            [
                {"medicamento": "A", "registros": 4},
                {"medicamento": "C", "registros": 3},
            ],
        )
        agg = merge_snapshots([a, b])
        assert agg.total_usafas == 2
        assert agg.total_registros == 12
        assert agg.total_pacientes == 5
        assert agg.by_tipo == {"entrada": 7, "retirada": 5}
        assert agg.top_items == [
            {"medicamento": "A", "registros": 7},
            {"medicamento": "C", "registros": 3},
            {"medicamento": "B", "registros": 2},
        ]

    def test_per_usafa_tipo_counts_preserved(self):
        agg = merge_snapshots(
            [
                _snap("a", "A", 2, 1, {"entrada": 2}, []),
                _snap("b", "B", 3, 1, {"retirada": 3}, []),
            ]
        )
        a = next(u for u in agg.usafas if u.usafa_id == "a")
        b = next(u for u in agg.usafas if u.usafa_id == "b")
        assert a.by_tipo == {"entrada": 2}
        assert b.by_tipo == {"retirada": 3}
