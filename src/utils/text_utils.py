#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text Utilities
Utilitários para processamento de texto e normalização
"""

from __future__ import annotations

import unicodedata
from datetime import datetime, date as date_type
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.models import Malote


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if unicodedata.category(c) != "Mn"
    )


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return _strip_accents(text).lower()


def to_upper_normalized(text: str) -> str:
    if not text:
        return ""
    return _strip_accents(text).upper()


def parse_date(text: Optional[str]) -> Optional[str]:
    text = (text or "").strip()
    if not text:
        return None
    today = date_type.today()
    for sep in ("/", "-", "."):
        if sep in text:
            parts = text.split(sep)
            break
    else:
        return None
    try:
        if len(parts) == 2:
            day, month = int(parts[0]), int(parts[1])
            year = today.year
        elif len(parts) == 3:
            day, month = int(parts[0]), int(parts[1])
            yp = int(parts[2])
            year = 2000 + yp if yp < 100 else yp
        else:
            return None
        return date_type(year, month, day).isoformat()
    except (ValueError, IndexError):
        return None


def format_malote_date(malote: Optional[Malote]) -> str:
    if not malote:
        return "?"
    try:
        dt = datetime.fromisoformat(malote.date)
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return malote.date or "?"
