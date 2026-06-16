#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared constants for RAC PySide6 app
"""

from src.constants import TIPO_LABELS, TIPO_TITLES, TIPOS_WITH_MONTHS  # noqa: F401

TIPO_HEX = {
    "entrada": "#10B981",
    "renovacao": "#3B82F6",
    "retirada": "#D97706",
    "urgente": "#EF4444",
    "medcasa": "#06B6D4",
}

TIPO_SYMBOLS = {
    "entrada": "\u25b2",
    "renovacao": "\u21bb",
    "retirada": "\u25bc",
    "urgente": "!",
    "medcasa": "\u2302",
}

SHORTCUT_LABELS: dict[str, tuple[str, str]] = {
    "save": ("Ctrl+S", "Salvar"),
    "export": ("Ctrl+E", "Exportar Planilha"),
    "back": ("Esc", "Voltar"),
    "preview": ("Ctrl+G", "Visualizar Malote"),
    "lists": ("Ctrl+T", "Gerenciar Listas"),
    "stats": ("Ctrl+Y", "Estatisticas"),
    "add_item": ("Ctrl+F", "+ Adicionar Item"),
    "toggle_docs": ("Ctrl+W", "Esperando documentos"),
    "toggle_stay": ("Ctrl+Q", "Ficar nesta tela"),
}

TIPO_SHORTCUT_KEYS: dict[str, str] = {
    "entrada": "Ctrl+1",
    "renovacao": "Ctrl+2",
    "retirada": "Ctrl+3",
    "urgente": "Ctrl+4",
    "medcasa": "Ctrl+5",
}
