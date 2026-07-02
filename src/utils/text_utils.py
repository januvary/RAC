from __future__ import annotations

import re
from datetime import datetime, date as date_type
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.models import Malote


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


def format_item(name: str) -> str:
    paren = re.search(r"\(([^)]+)\)\s*$", name)
    if not paren:
        result = name
    else:
        brand = paren.group(1).strip().upper()
        digit = re.search(r"\d", name)
        if not digit:
            result = brand
        else:
            dosage = name[digit.start() : paren.start()].strip()
            result = f"{brand} {dosage}"
    return result.replace(" ", "\u00a0")
