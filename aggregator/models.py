#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aggregator data models — per-unit and aggregate statistics.

These replace the snapshot-based types from src.sync.merger.
The rendering layer (panel/render.py) consumes AggregateStats directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TipoBreakdown:
    registros: int = 0
    pacientes: int = 0
    items: int = 0


@dataclass
class UsafaStats:
    usafa_id: str
    usafa_name: str
    exported_at: str
    registros: int = 0
    pacientes: int = 0
    malotes: int = 0
    by_tipo: dict[str, TipoBreakdown] = field(default_factory=dict)
    top_items: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AggregateStats:
    usafas: list[UsafaStats] = field(default_factory=list)
    total_registros: int = 0
    total_pacientes: int = 0
    total_usafas: int = 0
    by_tipo: dict[str, int] = field(default_factory=dict)
    top_items: list[dict[str, Any]] = field(default_factory=list)
