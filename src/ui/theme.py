#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tema Unificado RAC
Sistema centralizado de cores e estilos
"""

import sys
import customtkinter as ctk


class AppTheme:
    COLOR_BG_PRIMARY = ("#e8e8e8", "#2d2d2d")
    COLOR_BG_SECONDARY = ("#d9d9d9", "#3a3a3a")
    COLOR_BG_TERTIARY = ("#ececec", "#262626")

    COLOR_FG_PRIMARY = ("#2d2d2d", "#e8e8e8")
    COLOR_FG_HEADER = ("#2d2d2d", "#e8e8e8")
    COLOR_FG_DISABLED = ("#999999", "#666666")

    COLOR_ACCENT = ("#4a90e2", "#4a7ba0")
    COLOR_ACCENT_HOVER = ("#3a7bc8", "#3a6a8f")
    COLOR_ACCENT_PRESSED = ("#2a66a8", "#2a5a7a")

    COLOR_SUCCESS = ("#4bbd61", "#4bbd61")
    COLOR_SUCCESS_HOVER = ("#2a853b", "#2a853b")

    COLOR_DANGER = ("#993234", "#993234")
    COLOR_DANGER_HOVER = ("#702223", "#702223")

    COLOR_WARNING = ("#ff8c00", "#ff6600")
    COLOR_INFO = ("#2196F3", "#64B5F6")

    COLOR_BORDER = ("#c0c0c0", "#404040")
    COLOR_BORDER_FOCUS = ("#4a90e2", "#4a7ba0")

    # Tipo colors
    COLOR_ENTRADA = ("#4bbd61", "#4bbd61")
    COLOR_ENTRADA_HOVER = ("#2a853b", "#2a853b")
    COLOR_RENOVACAO = ("#4a90e2", "#4a7ba0")
    COLOR_RENOVACAO_HOVER = ("#3a7bc8", "#3a6a8f")
    COLOR_RETIRADA = ("#ff8c00", "#e67300")
    COLOR_RETIRADA_HOVER = ("#cc7000", "#b35900")
    COLOR_URGENTE = ("#993234", "#cc3b3e")
    COLOR_URGENTE_HOVER = ("#702223", "#993234")

    # Autocomplete dropdown
    DROPDOWN_BG = ("#ececec", "#2d2d2d")
    DROPDOWN_FG = ("#2d2d2d", "#e8e8e8")
    DROPDOWN_SELECTED_BG = ("#4a90e2", "#4a7ba0")
    DROPDOWN_SELECTED_FG = ("#ffffff", "#ffffff")
    DROPDOWN_BORDER = ("#c0c0c0", "#404040")

    # Fonts
    _PLATFORM = sys.platform
    PLATFORM_FONT = (
        "Segoe UI"
        if _PLATFORM == "win32"
        else "Helvetica Neue" if _PLATFORM == "darwin" else "DejaVu Sans"
    )

    FONT_HEADER = (PLATFORM_FONT, 14, "bold")
    FONT_BODY = (PLATFORM_FONT, 13)
    FONT_SMALL = (PLATFORM_FONT, 12)
    FONT_BUTTON = (PLATFORM_FONT, 14, "bold")
    FONT_SMALL_BOLD = (PLATFORM_FONT, 12, "bold")
    FONT_TREEVIEW = (PLATFORM_FONT, 10)
    FONT_TREEVIEW_HEADER = (PLATFORM_FONT, 10, "bold")
    FONT_LARGE = (PLATFORM_FONT, 16, "bold")
    FONT_TITLE = (PLATFORM_FONT, 20, "bold")

    # Dimensions
    ENTRY_HEIGHT_STANDARD = 28
    BUTTON_HEIGHT_STANDARD = 36

    # Timing
    AUTOCOMPLETE_DEBOUNCE_DELAY = 150
    SEARCH_DEBOUNCE_DELAY = 200

    # Padding
    PADX_SMALL = 5
    PADX_MEDIUM = 10
    PADX_LARGE = 15
    PADY_SMALL = 5
    PADY_MEDIUM = 10

    TIPO_COLORS = {
        "entrada": (COLOR_ENTRADA, COLOR_ENTRADA_HOVER),
        "renovacao": (COLOR_RENOVACAO, COLOR_RENOVACAO_HOVER),
        "retirada": (COLOR_RETIRADA, COLOR_RETIRADA_HOVER),
        "urgente": (COLOR_URGENTE, COLOR_URGENTE_HOVER),
    }

    TIPO_LABELS = {
        "entrada": "Entrada",
        "renovacao": "Renovação",
        "retirada": "Retirada",
        "urgente": "Urgente",
    }

    @staticmethod
    def get_color(color_tuple: tuple) -> str:
        try:
            mode = ctk.get_appearance_mode()
            if mode == "Light":
                return color_tuple[0]  # type: ignore[no-any-return]
            else:
                return color_tuple[1]  # type: ignore[no-any-return]
        except Exception:
            return color_tuple[1]  # type: ignore[no-any-return]

    @staticmethod
    def is_dark_mode() -> bool:
        try:
            mode = ctk.get_appearance_mode()
            return mode != "Light"  # type: ignore[no-any-return]
        except Exception:
            return True
