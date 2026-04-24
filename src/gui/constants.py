#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared constants for RAC PySide6 app
"""

from src.constants import TIPO_LABELS, TIPO_TITLES  # noqa: F401

TIPO_HEX = {
    "entrada": "#10B981",
    "renovacao": "#3B82F6",
    "retirada": "#F59E0B",
    "urgente": "#EF4444",
}

TIPO_SYMBOLS = {
    "entrada": "\u25b2",
    "renovacao": "\u21bb",
    "retirada": "\u25bc",
    "urgente": "!",
}

SHORTCUT_LABELS: dict[str, tuple[str, str]] = {
    "save": ("Ctrl+S", "Salvar"),
    "export": ("Ctrl+E", "Exportar Planilha"),
    "back": ("Esc", "Voltar"),
    "preview": ("Ctrl+G", "Visualizar Malote"),
    "lists": ("Ctrl+T", "Gerenciar Listas"),
    "add_item": ("Ctrl+F", "+ Adicionar Item"),
    "toggle_docs": ("Ctrl+W", "Esperando documentos"),
    "toggle_stay": ("Ctrl+Q", "Ficar nesta tela"),
}

TIPO_SHORTCUT_KEYS: dict[str, str] = {
    "entrada": "Ctrl+1",
    "renovacao": "Ctrl+2",
    "retirada": "Ctrl+3",
    "urgente": "Ctrl+4",
}
