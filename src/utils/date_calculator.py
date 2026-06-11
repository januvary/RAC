#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC-specific malote date calculations.

Send:  next Monday, adjusted backwards for holidays/weekends.
Arrival:  Thursday of the week following the original Monday,
          adjusted forward for holidays/weekends.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING

from andaime.dates import DateCalculator

if TYPE_CHECKING:
    from src.database.rac_database import RACDatabase


def calculate_send_date(from_date: date) -> date:
    days_ahead = (7 - from_date.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_monday = from_date + timedelta(days=days_ahead)
    return DateCalculator.skip_to_previous_business_day(next_monday)


def calculate_arrival_date(send_date: date) -> date:
    if send_date.weekday() == 0:
        intended_monday = send_date
    else:
        intended_monday = send_date + timedelta(days=7 - send_date.weekday())
    target = intended_monday + timedelta(days=10)
    return DateCalculator.skip_to_next_business_day(target)


def next_send_date(existing_dates: set[date] | None = None) -> date:
    candidate = calculate_send_date(date.today())
    if not existing_dates:
        return candidate
    while candidate in existing_dates:
        candidate = calculate_send_date(candidate)
    return candidate


@dataclass
class ProcessReturnInfo:
    group_number: int
    months_supply: int
    expected_return_date: date | None


def _get_candidate_days_after_arrival(arrival: date) -> list[date]:
    candidates: list[date] = []
    d = arrival + timedelta(days=1)
    end = arrival + timedelta(days=8)
    while d <= end:
        if DateCalculator.is_business_day(d):
            candidates.append(d)
        d += timedelta(days=1)
    if not candidates:
        candidates.append(DateCalculator.skip_to_next_business_day(end))
    return candidates


def resolve_arrival_from_malote(malote) -> date | None:
    if malote.arrival_date:
        try:
            return date.fromisoformat(malote.arrival_date)
        except (ValueError, TypeError):
            pass
    if malote.date:
        try:
            return calculate_arrival_date(date.fromisoformat(malote.date))
        except (ValueError, TypeError):
            pass
    return None


def _spread_across_candidates(
    groups: list[int],
    candidates: list[date],
    *,
    db: RACDatabase | None = None,
) -> dict[int, date]:
    result: dict[int, date] = {}
    if not groups or not candidates:
        return result

    load_map: dict[str, int] = {}
    if db:
        iso_candidates = [c.isoformat() for c in candidates]
        if iso_candidates:
            load_map = db.count_return_dates_between(
                min(iso_candidates), max(iso_candidates)
            )

    assigned_loads: dict[date, int] = {}
    for c in candidates:
        assigned_loads[c] = load_map.get(c.isoformat(), 0)

    for g in sorted(groups):
        best = min(candidates, key=lambda c: assigned_loads.get(c, 0))
        result[g] = best
        assigned_loads[best] = assigned_loads.get(best, 0) + 1

    return result


def _theoretical_arrival_near(target: date) -> date:
    send = calculate_send_date(target)
    return calculate_arrival_date(send)


def calculate_return_dates(
    tipo: str,
    arrival_date: date | None,
    process_groups: list[tuple[int, int]],
    *,
    db: RACDatabase | None = None,
    current_malote_id: int | None = None,
    waiting_docs: bool = False,
) -> list[ProcessReturnInfo]:
    if waiting_docs or not process_groups or arrival_date is None:
        return [
            ProcessReturnInfo(g, m, None)
            for g, m in process_groups
        ]

    if tipo == "urgente":
        effective_arrival = arrival_date
        if db and current_malote_id:
            earlier = db.get_earlier_malote(current_malote_id)
            if earlier and earlier.arrival_date:
                try:
                    effective_arrival = date.fromisoformat(earlier.arrival_date)
                except (ValueError, TypeError):
                    pass
        next_bd = DateCalculator.skip_to_next_business_day(effective_arrival + timedelta(days=1))
        return [
            ProcessReturnInfo(g, m, next_bd)
            for g, m in process_groups
        ]

    if tipo == "retirada":
        return _calculate_retirada_returns(
            process_groups, arrival_date, db=db,
        )

    candidates = _get_candidate_days_after_arrival(arrival_date)
    spread = _spread_across_candidates([g for g, _ in process_groups], candidates, db=db)
    return [
        ProcessReturnInfo(g, m, spread.get(g, candidates[0] if candidates else None))
        for g, m in process_groups
    ]


def _get_malote_arrivals_near(
    runs_out: date,
    *,
    db: RACDatabase | None = None,
) -> list[date]:
    search_start = runs_out - timedelta(days=45)
    search_end = runs_out + timedelta(days=45)
    candidates: list[date] = []

    if db:
        arrivals = db.get_malote_arrivals_between(
            search_start.isoformat(), search_end.isoformat()
        )
        for a in arrivals:
            try:
                candidates.append(date.fromisoformat(a))
            except (ValueError, TypeError):
                pass

    if not candidates:
        for offset in (-2, -1, 0, 1, 2):
            arrival = _theoretical_arrival_near(runs_out + timedelta(days=offset * 30))
            if search_start <= arrival <= search_end:
                candidates.append(arrival)
        if not candidates:
            candidates.append(_theoretical_arrival_near(runs_out))

    return candidates


def _find_nearest_arrival_before(
    runs_out: date,
    *,
    db: RACDatabase | None = None,
    top: int = 4,
) -> list[tuple[date, int]]:
    candidates = _get_malote_arrivals_near(runs_out, db=db)
    if not candidates:
        return []

    load_map: dict[str, int] = {}
    if db:
        iso_dates = [c.isoformat() for c in candidates]
        load_map = db.count_return_dates_between(min(iso_dates), max(iso_dates))

    def sort_key(c: date) -> tuple[int, int]:
        dist = abs((runs_out - c).days)
        after = 1 if c > runs_out else 0
        load = load_map.get(c.isoformat(), 0)
        return (after, dist, load)

    candidates.sort(key=sort_key)
    return [(c, load_map.get(c.isoformat(), 0)) for c in candidates[:top]]


def _calculate_retirada_returns(
    process_groups: list[tuple[int, int]],
    current_arrival: date,
    *,
    db: RACDatabase | None = None,
) -> list[ProcessReturnInfo]:
    zero_groups = [g for g, m in process_groups if m == 0]
    nonzero_groups = [(g, m) for g, m in process_groups if m > 0]

    candidates = _get_candidate_days_after_arrival(current_arrival)
    spread = _spread_across_candidates(zero_groups, candidates, db=db)

    results: dict[int, ProcessReturnInfo] = {}
    for g in zero_groups:
        results[g] = ProcessReturnInfo(g, 0, spread.get(g, candidates[0] if candidates else None))

    for group_number, months_supply in nonzero_groups:
        runs_out = date.today() + timedelta(days=months_supply * 30)
        nearest = _find_nearest_arrival_before(runs_out, db=db)
        best = nearest[0][0] if nearest else _theoretical_arrival_near(runs_out)
        results[group_number] = ProcessReturnInfo(group_number, months_supply, best)

    return [results[g] for g, _ in process_groups]
