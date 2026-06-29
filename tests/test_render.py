from src.sync.merger import AggregateStats, UsafaStats
from panel.render import render_html


def test_empty():
    html = render_html(AggregateStats())
    assert "<h1>Gestao" in html
    assert "USAFAs" in html
    assert "Sem dados" in html


def test_populated():
    agg = AggregateStats(
        usafas=[
            UsafaStats(
                "ocian",
                "USAFA OCIAN",
                "2026-06-25T10:00:00",
                5,
                2,
                1,
                {"entrada": 5},
            )
        ],
        total_registros=5,
        total_pacientes=2,
        total_usafas=1,
        by_tipo={"entrada": 5},
        top_items=[{"medicamento": "BETA", "registros": 3}],
    )
    html = render_html(agg)
    assert "USAFA OCIAN" in html
    assert "BETA" in html
    assert "Entrada" in html
    assert "25/06/2026 10:00" in html
    assert html.count("<table") == 2
    assert html.count('id="meds-search"') == 1


def test_escapes_unsafe_content():
    agg = AggregateStats(
        total_usafas=1,
        top_items=[{"medicamento": "<script>x</script>", "registros": 1}],
        usafas=[UsafaStats("a", "<b>Name</b>", "2026-01-01T00:00:00", 1, 1, 1, {})],
    )
    html = render_html(agg)
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html
