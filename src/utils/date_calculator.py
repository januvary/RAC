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


def _theoretical_malote_for_month(year: int, month: int) -> date:
    first_of_month = date(year, month, 1)
    return calculate_send_date(first_of_month)


def _theoretical_arrival_for_month(year: int, month: int) -> date:
    send = _theoretical_malote_for_month(year, month)
    return calculate_arrival_date(send)


def _add_months(d: date, months: int) -> date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, 28)
    return date(year, month, day)


def calculate_return_dates(
    tipo: str,
    arrival_date: date | None,
    process_groups: list[tuple[int, int]],
    *,
    db: RACDatabase | None = None,
    paciente_id: int | None = None,
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
            process_groups, arrival_date, db=db, paciente_id=paciente_id,
        )

    candidates = _get_candidate_days_after_arrival(arrival_date)
    spread = _spread_across_candidates([g for g, _ in process_groups], candidates, db=db)
    return [
        ProcessReturnInfo(g, m, spread.get(g, candidates[0] if candidates else None))
        for g, m in process_groups
    ]


def _score_arrival(candidate: date, runs_out: date) -> float:
    days_before = (runs_out - candidate).days
    if days_before < 0 or days_before > 14:
        return -1.0
    if days_before <= 7:
        return days_before / 7.0
    return (14 - days_before) / 7.0


@dataclass
class ScoredCandidate:
    date: date
    score: float
    proximity: float
    load: int


def _find_best_malote_in_window(
    runs_out: date,
    *,
    db: RACDatabase | None = None,
) -> date | None:
    ranked = _rank_candidates(runs_out, db=db)
    return ranked[0].date if ranked else None


def _rank_candidates(
    runs_out: date,
    *,
    db: RACDatabase | None = None,
    top: int = 4,
) -> list[ScoredCandidate]:
    window_start = runs_out - timedelta(days=14)
    window_end = runs_out
    candidates: list[date] = []

    if db:
        arrivals = db.get_malote_arrivals_between(
            window_start.isoformat(), window_end.isoformat()
        )
        for a in arrivals:
            try:
                candidates.append(date.fromisoformat(a))
            except (ValueError, TypeError):
                pass

    if not candidates:
        d = window_start
        while d <= window_end:
            if DateCalculator.is_business_day(d):
                candidates.append(d)
            d += timedelta(days=1)

    if not candidates:
        candidates.append(DateCalculator.skip_to_next_business_day(window_start))

    load_map: dict[str, int] = {}
    if db:
        load_map = db.count_return_dates_between(
            window_start.isoformat(), window_end.isoformat()
        )

    max_load = max(load_map.values()) if load_map else 0
    if max_load == 0:
        max_load = 1

    scored: list[ScoredCandidate] = []
    for c in candidates:
        proximity = _score_arrival(c, runs_out)
        if proximity < 0:
            continue
        load = load_map.get(c.isoformat(), 0)
        load_factor = 1.0 - (load / (max_load + 1)) * 0.5
        s = proximity * load_factor
        scored.append(ScoredCandidate(date=c, score=s, proximity=proximity, load=load))

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top]


def _calculate_retirada_returns(
    process_groups: list[tuple[int, int]],
    current_arrival: date,
    *,
    db: RACDatabase | None = None,
    paciente_id: int | None = None,
) -> list[ProcessReturnInfo]:
    zero_groups = [g for g, m in process_groups if m == 0]
    nonzero_groups = [(g, m) for g, m in process_groups if m > 0]

    candidates = _get_candidate_days_after_arrival(current_arrival)
    spread = _spread_across_candidates(zero_groups, candidates, db=db)

    results: dict[int, ProcessReturnInfo] = {}
    for g in zero_groups:
        results[g] = ProcessReturnInfo(g, 0, spread.get(g, candidates[0] if candidates else None))

    for group_number, months_supply in nonzero_groups:
        reference_arrival = current_arrival
        if db and paciente_id:
            last_arrival = db.get_last_retirada_arrival_for_patient(paciente_id, group_number)
            if last_arrival:
                try:
                    reference_arrival = date.fromisoformat(last_arrival)
                except (ValueError, TypeError):
                    pass

        runs_out = reference_arrival + timedelta(days=months_supply * 30)
        best = _find_best_malote_in_window(runs_out, db=db)
        results[group_number] = ProcessReturnInfo(group_number, months_supply, best)

    return [results[g] for g, _ in process_groups]
