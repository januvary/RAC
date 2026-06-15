#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CID input field with auto-formatting (uppercase, dot insertion, multi-value).
"""

from PySide6.QtWidgets import QLineEdit


class CidInput(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("CID")
        self.setFixedWidth(170)
        self._formatting = False
        self._deleting = False
        self._prev_len = 0
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text: str):
        if self._formatting:
            self._prev_len = len(text)
            return
        self._deleting = len(text) < self._prev_len
        self._prev_len = len(text)
        self._formatting = True
        cursor = self.cursorPosition()
        formatted = self._format_all(text.upper())
        if formatted != text:
            new_cursor = cursor + (len(formatted) - len(text))
            self.setText(formatted)
            self.setCursorPosition(max(0, min(new_cursor, len(formatted))))
        self._formatting = False

    def _format_all(self, raw: str) -> str:
        cids = []
        current = ""
        trailing_sep = False
        i = 0
        while i < len(raw):
            ch = raw[i]
            if ch in (";", ",", " "):
                if current:
                    cids.append(self._format_single(current))
                    current = ""
                trailing_sep = True
                i += 1
                continue
            trailing_sep = False
            current += ch
            i += 1
        if current:
            cids.append(self._format_single(current))
            trailing_sep = False
        result = "; ".join(cids)
        if trailing_sep and not self._deleting:
            result += "; "
        return result

    def _format_single(self, cid: str) -> str:
        cleaned = ""
        for ch in cid:
            if ch.isalpha():
                if not cleaned:
                    cleaned += ch.upper()
            elif ch.isdigit():
                cleaned += ch
            elif ch == "." and len(cleaned) >= 3 and "." not in cleaned:
                cleaned += ch
        if not self._deleting and len(cleaned) >= 3 and "." not in cleaned:
            cleaned = cleaned[:3] + "." + cleaned[3:]
        if len(cleaned) > 7:
            cleaned = cleaned[:7]
        return cleaned

    def focusOutEvent(self, event):
        self._deleting = False
        self._formatting = True
        formatted = self._format_all(self.text().upper())
        self.setText(formatted)
        self._formatting = False
        super().focusOutEvent(event)
