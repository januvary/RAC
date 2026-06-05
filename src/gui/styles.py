#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Global QSS stylesheet — native Qt feel with theme support
"""

_current_theme: str = "light"

LIGHT_COLORS = {
    "bg_main": "#F0EBE1",
    "bg_card": "#FFFAF0",
    "bg_card_alt": "#E1DAD0",
    "bg_hover": "#D2CBC0",
    "bg_pressed": "#C3BBB0",
    "bg_input": "#FFFCF5",
    "border": "#D6D3D1",
    "border_light": "#E7E5E4",
    "text_primary": "#44403C",
    "text_secondary": "#78716C",
    "text_dark": "#292524",
    "selection_bg": "#D6CFBF",
    "selection_text": "#292524",
    "separator": "#E7E5E4",
    "gridline": "#EDE8DE",
    "scrollbar": "#D6D3D1",
    "scrollbar_hover": "#A8A29E",
    "table_alt_bg": "#F5F0E6",
    "toast_positive_fg": "#059669",
    "toast_positive_bg": "#EDF7ED",
    "toast_warning_fg": "#D97706",
    "toast_warning_bg": "#FFF7E5",
    "toast_negative_fg": "#DC2626",
    "toast_negative_bg": "#FDF0F0",
    "toast_info_fg": "#2563EB",
    "toast_info_bg": "#EFF2FA",
}

DARK_COLORS = {
    "bg_main": "#111827",
    "bg_card": "#1F2937",
    "bg_card_alt": "#283040",
    "bg_hover": "#374151",
    "bg_pressed": "#4B5563",
    "bg_input": "#1F2937",
    "border": "#374151",
    "border_light": "#4B5563",
    "text_primary": "#F9FAFB",
    "text_secondary": "#9CA3AF",
    "text_dark": "#F9FAFB",
    "selection_bg": "#1E3A8A",
    "selection_text": "#F9FAFB",
    "separator": "#374151",
    "gridline": "#252D3A",
    "scrollbar": "#4B5563",
    "scrollbar_hover": "#6B7280",
    "table_alt_bg": "#283040",
    "toast_positive_fg": "#34D399",
    "toast_positive_bg": "#064E3B",
    "toast_warning_fg": "#FBBF24",
    "toast_warning_bg": "#78350F",
    "toast_negative_fg": "#F87171",
    "toast_negative_bg": "#7F1D1D",
    "toast_info_fg": "#60A5FA",
    "toast_info_bg": "#1E3A8A",
}


def set_theme(theme: str) -> None:
    global _current_theme
    _current_theme = theme


def get_theme() -> str:
    return _current_theme


def toggle_theme() -> str:
    global _current_theme
    _current_theme = "light" if _current_theme == "dark" else "dark"
    from andaime.config import ConfigManager

    ConfigManager().set("theme", _current_theme)
    return _current_theme


def colors() -> dict:
    return DARK_COLORS if _current_theme == "dark" else LIGHT_COLORS


def _blend_hex(hex_a: str, hex_b: str, ratio: float) -> str:
    ra, ga, ba = int(hex_a[1:3], 16), int(hex_a[3:5], 16), int(hex_a[5:7], 16)
    rb, gb, bb = int(hex_b[1:3], 16), int(hex_b[3:5], 16), int(hex_b[5:7], 16)
    r = int(ra * ratio + rb * (1 - ratio))
    g = int(ga * ratio + gb * (1 - ratio))
    b = int(ba * ratio + bb * (1 - ratio))
    return f"#{r:02x}{g:02x}{b:02x}"


def faded_tipo_color(hex_color: str) -> str:
    if _current_theme == "dark":
        return _blend_hex(hex_color, colors()["text_primary"], 0.85)
    return _blend_hex(hex_color, colors()["text_primary"], 0.55)


def get_stylesheet(theme: str | None = None) -> str:
    resolved = theme or _current_theme
    c = DARK_COLORS if resolved == "dark" else LIGHT_COLORS
    return _build_qss(c)


def tipo_button_qss(hex_color: str) -> str:
    c = colors()
    faded = faded_tipo_color(hex_color)
    return f"""
        QPushButton[tipobtn="true"] {{
            background-color: {c["bg_card"]};
            border: 1px solid {c["border_light"]};
            border-radius: 8px;
            padding: 20px 16px;
            font-size: 15px;
            font-weight: 500;
            color: {faded};
        }}
        QPushButton[tipobtn="true"]:hover {{
            background-color: {c["bg_card_alt"]};
            border-color: {c["border"]};
        }}
        QPushButton[tipobtn="true"]:pressed {{
            background-color: {c["bg_hover"]};
        }}
    """


def _build_qss(c: dict) -> str:
    return f"""
/* -- Global -- */
* {{
    font-family: "Geist", sans-serif;
}}
QMainWindow {{
    background-color: {c["bg_main"]};
}}
QWidget#central {{
    background-color: {c["bg_main"]};
}}

/* -- Section headings -- */
QLabel[heading="true"] {{
    font-size: 16px;
    font-weight: 600;
    color: {c["text_primary"]};
    padding: 0px;
    margin: 0px;
}}
QLabel[heading="section"] {{
    font-size: 12px;
    font-weight: 600;
    color: {c["text_secondary"]};
    padding: 0px;
    margin: 0px;
}}

/* -- Separator -- */
QFrame[separator="true"] {{
    background-color: {c["separator"]};
    max-height: 1px;
    border: none;
}}

/* -- Buttons -- */
QPushButton {{
    background-color: transparent;
    border: 1px solid {c["bg_main"]};
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 14px;
    font-weight: 500;
    color: {c["text_primary"]};
    min-height: 22px;
}}
QPushButton:hover {{
    background-color: {c["bg_hover"]};
    border-color: {c["bg_main"]};
}}
QPushButton:pressed {{
    background-color: {c["bg_pressed"]};
}}

QPushButton[btnrole="primary"] {{
    background-color: {c["bg_card"]};
    border: 1px solid {c["border_light"]};
    border-radius: 6px;
    color: {c["text_primary"]};
}}
QPushButton[btnrole="primary"]:hover {{
    background-color: {c["bg_card_alt"]};
    border-color: {c["border"]};
}}
QPushButton[btnrole="primary"]:pressed {{
    background-color: {c["bg_hover"]};
}}

QPushButton[btnrole="positive"] {{
    background-color: {c["bg_card"]};
    border: 1px solid {c["border_light"]};
    border-radius: 6px;
    color: {c["text_primary"]};
}}
QPushButton[btnrole="positive"]:hover {{
    background-color: {c["bg_card_alt"]};
    border-color: {c["border"]};
}}
QPushButton[btnrole="positive"]:pressed {{
    background-color: {c["bg_hover"]};
}}

QPushButton[btnrole="negative"] {{
    background-color: transparent;
    border-color: #FCA5A5;
    color: #DC2626;
}}
QPushButton[btnrole="negative"]:hover {{
    background-color: #FEF2F2;
    border-color: #F87171;
}}
QPushButton[btnrole="negative"]:pressed {{
    background-color: #FEE2E2;
}}

QPushButton[btnrole="flat"] {{
    background-color: transparent;
    border: none;
    padding: 4px 12px;
    color: {c["text_secondary"]};
}}
QPushButton[btnrole="flat"]:hover {{
    background-color: {c["bg_hover"]};
    color: {c["text_primary"]};
}}
QPushButton[btnrole="flat"]:pressed {{
    background-color: {c["bg_pressed"]};
}}

QPushButton[btnrole="destructive"] {{
    background-color: #EF4444;
    border-color: #EF4444;
    color: white;
}}
QPushButton[btnrole="destructive"]:hover {{
    background-color: #DC2626;
    border-color: #DC2626;
}}

/* -- Inputs / ComboBox -- */
QLineEdit, QComboBox {{
    border: 1px solid {c["border"]};
    border-radius: 6px;
    padding: 9px 14px;
    background: {c["bg_input"]};
    color: {c["text_primary"]};
    font-size: 14px;
    min-height: 22px;
    selection-background-color: {c["selection_bg"]};
    selection-color: {c["selection_text"]};
}}

QLineEdit:focus, QComboBox:focus {{
    border-color: #3B82F6;
}}

QComboBox::drop-down {{
    border: none;
    width: 0px;
}}
QComboBox::down-arrow {{
    image: none;
    width: 0px;
    border: none;
}}

QComboBox QAbstractItemView {{
    border: 1px solid {c["border_light"]};
    border-radius: 6px;
    background-color: {c["bg_card"]};
    color: {c["text_primary"]};
    selection-background-color: {c["selection_bg"]};
    selection-color: {c["selection_text"]};
    outline: none;
    padding: 2px;
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 10px;
    min-height: 22px;
    color: {c["text_primary"]};
}}

/* -- Tipo Button -- */
QPushButton[tipobtn="true"] {{
    background-color: {c["bg_card"]};
    border: 1px solid {c["border_light"]};
    border-radius: 8px;
    padding: 20px 16px;
    font-size: 15px;
    font-weight: 500;
    color: {c["text_primary"]};
}}
QPushButton[tipobtn="true"]:hover {{
    background-color: {c["bg_card_alt"]};
    border-color: {c["border"]};
}}
QPushButton[tipobtn="true"]:pressed {{
    background-color: {c["bg_hover"]};
}}

/* -- Dialog -- */
QDialog {{
    background-color: {c["bg_card"]};
    color: {c["text_primary"]};
}}

/* -- Scrollbar -- */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {c["scrollbar"]};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c["scrollbar_hover"]};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* -- List Widget -- */
QListWidget {{
    border: 1px solid {c["border_light"]};
    border-radius: 6px;
    background: {c["bg_card"]};
    color: {c["text_primary"]};
    outline: none;
    padding: 2px;
}}
QListWidget::item {{
    padding: 8px 12px;
    border-radius: 4px;
}}
QListWidget::item:hover {{
    background-color: {c["bg_hover"]};
}}
QListWidget::item:selected {{
    background-color: {c["selection_bg"]};
    color: {c["selection_text"]};
}}

/* -- Status Bar -- */
QStatusBar {{
    background-color: {c["bg_card"]};
    border-top: 1px solid {c["border_light"]};
    color: {c["text_secondary"]};
    font-size: 12px;
    padding: 4px 12px;
}}

/* -- Check Box -- */
QCheckBox {{
    spacing: 6px;
    color: {c["text_primary"]};
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid {c["border"]};
    background: {c["bg_input"]};
}}
QCheckBox::indicator:checked {{
    background-color: #3B82F6;
    border-color: #3B82F6;
}}

/* -- Remove Button -- */
QPushButton[btnrole="remove"] {{
    background-color: transparent;
    border: none;
    color: {c["text_secondary"]};
    padding: 0px;
    font-size: 16px;
    border-radius: 4px;
}}
QPushButton[btnrole="remove"]:hover {{
    background-color: #FEF2F2;
    color: #EF4444;
}}

/* -- Tree Widget -- */
QTreeWidget {{
    border: 1px solid {c["border_light"]};
    border-radius: 6px;
    background: {c["bg_card"]};
    color: {c["text_primary"]};
    outline: none;
    padding: 2px;
}}
QTreeWidget::item {{
    padding: 6px 12px;
    border-radius: 4px;
}}
QTreeWidget::item:hover {{
    background-color: {c["bg_hover"]};
}}
QTreeWidget::item:selected {{
    background-color: {c["selection_bg"]};
    color: {c["selection_text"]};
}}
QTreeWidget::branch {{
    background-color: {c["bg_card"]};
}}

/* -- Completer Popup -- */
QListView {{
    background-color: {c["bg_card"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border_light"]};
    border-radius: 6px;
    selection-background-color: {c["selection_bg"]};
    selection-color: {c["selection_text"]};
    outline: none;
    padding: 2px;
}}

/* -- Table alternating rows -- */
QTableWidget {{
    alternate-background-color: {c["table_alt_bg"]};
}}

/* -- Malote Label -- */
QLabel[malotelabel="true"] {{
    color: {c["text_primary"]};
    font-size: 22px;
    font-weight: 400;
}}

/* -- Theme Toggle Button -- */
QPushButton[btnrole="theme-toggle"] {{
    border: none;
    font-size: 16px;
    padding: 0;
}}

/* -- Toast -- */
QLabel[toastkind] {{
    border-radius: 7px;
    padding: 9px 17px;
    font-weight: 500;
    font-size: 15px;
}}
QLabel[toastkind="positive"] {{
    background-color: {c["toast_positive_bg"]};
    color: {c["toast_positive_fg"]};
    border: 1px solid {c["toast_positive_fg"]}33;
}}
QLabel[toastkind="warning"] {{
    background-color: {c["toast_warning_bg"]};
    color: {c["toast_warning_fg"]};
    border: 1px solid {c["toast_warning_fg"]}33;
}}
QLabel[toastkind="negative"] {{
    background-color: {c["toast_negative_bg"]};
    color: {c["toast_negative_fg"]};
    border: 1px solid {c["toast_negative_fg"]}33;
}}
QLabel[toastkind="info"] {{
    background-color: {c["toast_info_bg"]};
    color: {c["toast_info_fg"]};
    border: 1px solid {c["toast_info_fg"]}33;
}}
"""
