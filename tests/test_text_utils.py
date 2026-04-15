from src.utils.text_utils import (
    normalize_text,
    to_upper_normalized,
    parse_date,
    format_malote_date,
)
from src.models import Malote


class TestNormalizeText:
    def test_removes_accents(self):
        assert normalize_text("João Açúcar") == "joao acucar"

    def test_handles_empty(self):
        assert normalize_text("") == ""

    def test_no_accents(self):
        assert normalize_text("Maria Santos") == "maria santos"

    def test_uppercase_accents(self):
        assert normalize_text("ÁÉÍÓÚ") == "aeiou"

    def test_cedilla(self):
        assert normalize_text("Coração") == "coracao"

    def test_tilde(self):
        assert normalize_text("Pão Órfã") == "pao orfa"

    def test_grave_accents(self):
        assert normalize_text("Àèìòù") == "aeiou"

    def test_n_tilde(self):
        assert normalize_text("Nuñez") == "nunez"


class TestToUpperNormalized:
    def test_removes_accents_and_uppercases(self):
        assert to_upper_normalized("João Açúcar") == "JOAO ACUCAR"

    def test_handles_empty(self):
        assert to_upper_normalized("") == ""


class TestParseDate:
    def test_dd_mm(self):
        result = parse_date("12/04")
        assert result == "2026-04-12"

    def test_dd_mm_yyyy(self):
        assert parse_date("12/04/2025") == "2025-04-12"

    def test_dd_mm_yy(self):
        assert parse_date("12/04/25") == "2025-04-12"

    def test_dash_separator(self):
        assert parse_date("12-04-2025") == "2025-04-12"

    def test_dot_separator(self):
        assert parse_date("12.04.2025") == "2025-04-12"

    def test_empty_returns_none(self):
        assert parse_date("") is None

    def test_none_returns_none(self):
        assert parse_date(None) is None

    def test_invalid_date_returns_none(self):
        assert parse_date("32/13") is None

    def test_no_separator_returns_none(self):
        assert parse_date("12042025") is None

    def test_strips_whitespace(self):
        assert parse_date("  12/04  ") == "2026-04-12"


class TestFormatMaloteDate:
    def test_valid_date(self):
        m = Malote(id=1, date="2026-04-12")
        assert format_malote_date(m) == "12/04/2026"

    def test_none_returns_question_mark(self):
        assert format_malote_date(None) == "?"

    def test_invalid_date_returns_raw(self):
        m = Malote(id=1, date="not-a-date")
        assert format_malote_date(m) == "not-a-date"

    def test_empty_date_returns_question_mark(self):
        m = Malote(id=1, date="")
        assert format_malote_date(m) == "?"
