#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text Utilities
Utilitários para processamento de texto e normalização
"""

from typing import Dict

_ACCENT_MAP: Dict[str, str] = {
    "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
    "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
    "Â": "A", "Ê": "E", "Î": "I", "Ô": "O", "Û": "U",
    "â": "a", "ê": "e", "î": "i", "ô": "o", "û": "u",
    "Ã": "A", "Õ": "O",
    "ã": "a", "õ": "o",
    "Ä": "A", "Ë": "E", "Ï": "I", "Ö": "O", "Ü": "U",
    "ä": "a", "ë": "e", "ï": "i", "ö": "o", "ü": "u",
    "Ç": "C", "ç": "c",
}


def normalize_text(text: str) -> str:
    if not text:
        return ""

    normalized = text
    for accented_char, unaccented_char in _ACCENT_MAP.items():
        normalized = normalized.replace(accented_char, unaccented_char)

    return normalized.lower()


def to_upper_normalized(text: str) -> str:
    if not text:
        return ""

    normalized = text
    for accented_char, unaccented_char in _ACCENT_MAP.items():
        normalized = normalized.replace(accented_char, unaccented_char)

    return normalized.upper()
