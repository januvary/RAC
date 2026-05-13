#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC-specific malote date calculations.

Send:  next Monday, adjusted backwards for holidays/weekends.
Arrival:  Thursday of the week following the original Monday,
          adjusted forward for holidays/weekends.
"""

from datetime import date, timedelta

from andaime.dates import DateCalculator


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
