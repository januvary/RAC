#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text Utilities
Utilitários para processamento de texto e normalização
"""

from __future__ import annotations

from datetime import datetime, date as date_type
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from src.models import Malote

_ACCENT_MAP: Dict[str, str] = {
    "Á": "A",
    "É": "E",
    "Í": "I",
    "Ó": "O",
    "Ú": "U",
    "á": "a",
    "é": "e",
    "í": "i",
    "ó": "o",
    "ú": "u",
    "À": "A",
    "È": "E",
    "Ì": "I",
    "Ò": "O",
    "Ù": "U",
    "à": "a",
    "è": "e",
    "ì": "i",
    "ò": "o",
    "ù": "u",
    "Â": "A",
    "Ê": "E",
    "Î": "I",
    "Ô": "O",
    "Û": "U",
    "â": "a",
    "ê": "e",
    "î": "i",
    "ô": "o",
    "û": "u",
    "Ã": "A",
    "Õ": "O",
    "Ñ": "N",
    "ã": "a",
    "õ": "o",
    "ñ": "n",
    "Ä": "A",
    "Ë": "E",
    "Ï": "I",
    "Ö": "O",
    "Ü": "U",
    "ä": "a",
    "ë": "e",
    "ï": "i",
    "ö": "o",
    "ü": "u",
    "Ç": "C",
    "ç": "c",
}

_TRANSLATE_TABLE = str.maketrans(_ACCENT_MAP)


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return text.translate(_TRANSLATE_TABLE).lower()


def to_upper_normalized(text: str) -> str:
    if not text:
        return ""
    return text.translate(_TRANSLATE_TABLE).upper()


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
