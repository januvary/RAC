
from datetime import date, timedelta

from src.utils.date_calculator import (
    _next_malote_arrival_after,
    add_months,
    month_idx,
)


class TestAddMonths:
    def test_same_month_zero(self):
        assert add_months(date(2026, 3, 15), 0) == date(2026, 3, 15)

    def test_simple_add(self):
        assert add_months(date(2026, 1, 15), 5) == date(2026, 6, 15)

    def test_crosses_year(self):
        assert add_months(date(2026, 11, 10), 3) == date(2027, 2, 10)

    def test_day_clamps_to_shorter_month(self):
        assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)

    def test_day_clamps_leap_february(self):
        assert add_months(date(2026, 1, 31), 13) == date(2027, 2, 28)
        assert add_months(date(2023, 1, 31), 13) == date(2024, 2, 29)

    def test_into_leap_february(self):
        assert add_months(date(2023, 12, 31), 2) == date(2024, 2, 29)

    def test_year_rollover_from_december(self):
        assert add_months(date(2026, 12, 31), 1) == date(2027, 1, 31)

    def test_multiple_years(self):
        assert add_months(date(2026, 5, 17), 26) == date(2028, 7, 17)


class TestMonthIdx:
    def test_january_is_zero_month_of_year(self):
        assert month_idx(date(2026, 1, 1)) == 2026 * 12

    def test_months_apart(self):
        assert month_idx(date(2026, 6, 1)) - month_idx(date(2026, 1, 1)) == 5

    def test_across_year_boundary(self):
        assert month_idx(date(2027, 1, 1)) - month_idx(date(2026, 12, 1)) == 1

    def test_day_ignored(self):
        assert month_idx(date(2026, 3, 1)) == month_idx(date(2026, 3, 31))


class TestNextMaloteArrivalAfter:
    def test_returns_arrival_on_or_after_target(self):
        result = _next_malote_arrival_after(date(2026, 10, 30))
        assert result >= date(2026, 10, 30)

    def test_no_infinite_loop_when_monday_is_holiday(self):
        """Regression: Finados 02/11/2026 (Monday) made calculate_send_date
        return a date before its input, so ref = send + 1 oscillated forever
        for any d in the Nov 6..12 window."""
        for d in (
            date(2026, 11, 6),
            date(2026, 11, 9),
            date(2026, 11, 12),
        ):
            assert _next_malote_arrival_after(d) >= d

    def test_result_is_increasing_across_successive_days(self):
        prev = None
        for i in range(40):
            d = date(2026, 10, 1) + timedelta(days=i)
            r = _next_malote_arrival_after(d)
            if prev is not None:
                assert r >= prev
            prev = r
