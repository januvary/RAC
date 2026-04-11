#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Global QSS stylesheet — native Qt feel
"""

STYLESHEET = """
/* ── Global ── */
QMainWindow {
    background-color: #FAFAFA;
}
QWidget#central {
    background-color: #FAFAFA;
}

/* ── Section headings ── */
QLabel[heading="true"] {
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    padding: 0px;
    margin: 0px;
}
QLabel[heading="section"] {
    font-size: 11px;
    font-weight: 600;
    color: #6B7280;
    padding: 0px;
    margin: 0px;
}

/* ── Separator ── */
QFrame[separator="true"] {
    background-color: #E5E7EB;
    max-height: 1px;
    border: none;
}

/* ── Buttons ── */
QPushButton {
    background-color: transparent;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 500;
    color: #374151;
    min-height: 18px;
}
QPushButton:hover {
    background-color: #F3F4F6;
    border-color: #9CA3AF;
}
QPushButton:pressed {
    background-color: #E5E7EB;
}

QPushButton[btnrole="primary"] {
    background-color: #3B82F6;
    border-color: #3B82F6;
    color: white;
}
QPushButton[btnrole="primary"]:hover {
    background-color: #2563EB;
    border-color: #2563EB;
}
QPushButton[btnrole="primary"]:pressed {
    background-color: #1D4ED8;
}

QPushButton[btnrole="positive"] {
    background-color: #10B981;
    border-color: #10B981;
    color: white;
}
QPushButton[btnrole="positive"]:hover {
    background-color: #059669;
    border-color: #059669;
}
QPushButton[btnrole="positive"]:pressed {
    background-color: #047857;
}

QPushButton[btnrole="negative"] {
    background-color: transparent;
    border-color: #FCA5A5;
    color: #DC2626;
}
QPushButton[btnrole="negative"]:hover {
    background-color: #FEF2F2;
    border-color: #F87171;
}
QPushButton[btnrole="negative"]:pressed {
    background-color: #FEE2E2;
}

QPushButton[btnrole="flat"] {
    background-color: transparent;
    border: none;
    color: #6B7280;
}
QPushButton[btnrole="flat"]:hover {
    background-color: #F3F4F6;
    color: #374151;
}
QPushButton[btnrole="flat"]:pressed {
    background-color: #E5E7EB;
}

QPushButton[btnrole="destructive"] {
    background-color: #EF4444;
    border-color: #EF4444;
    color: white;
}
QPushButton[btnrole="destructive"]:hover {
    background-color: #DC2626;
    border-color: #DC2626;
}

/* ── Inputs / ComboBox ── */
QLineEdit, QComboBox {
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    padding: 7px 12px;
    background: white;
    font-size: 13px;
    min-height: 18px;
    selection-background-color: #BFDBFE;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #3B82F6;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #9CA3AF;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    border: 1px solid #E5E7EB;
    border-radius: 6px;
    background-color: white;
    selection-background-color: #EFF6FF;
    selection-color: #1F2937;
    outline: none;
    padding: 2px;
}
QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    min-height: 22px;
}

/* ── Tipo Button ── */
QPushButton[tipobtn="true"] {
    background-color: white;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 16px 12px;
    font-size: 13px;
    font-weight: 500;
    color: #374151;
}
QPushButton[tipobtn="true"]:hover {
    background-color: #F9FAFB;
    border-color: #D1D5DB;
}
QPushButton[tipobtn="true"]:pressed {
    background-color: #F3F4F6;
}

/* ── Item Row ── */
QFrame[itemrow="true"] {
    background-color: white;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
}

/* ── Dialog ── */
QDialog {
    background-color: white;
}

/* ── Scrollbar ── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #D1D5DB;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #9CA3AF;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* ── List Widget ── */
QListWidget {
    border: 1px solid #E5E7EB;
    border-radius: 6px;
    background: white;
    outline: none;
    padding: 2px;
}
QListWidget::item {
    padding: 8px 12px;
    border-radius: 4px;
}
QListWidget::item:hover {
    background-color: #F3F4F6;
}
QListWidget::item:selected {
    background-color: #EFF6FF;
    color: #1F2937;
}

/* ── Status Bar ── */
QStatusBar {
    background-color: white;
    border-top: 1px solid #E5E7EB;
    color: #6B7280;
    font-size: 12px;
    padding: 4px 12px;
}

/* ── Check Box ── */
QCheckBox {
    spacing: 6px;
    color: #374151;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #D1D5DB;
    background: white;
}
QCheckBox::indicator:checked {
    background-color: #3B82F6;
    border-color: #3B82F6;
}

/* ── Remove Button ── */
QPushButton[btnrole="remove"] {
    background-color: transparent;
    border: none;
    color: #9CA3AF;
    padding: 4px 8px;
    font-size: 16px;
    border-radius: 4px;
}
QPushButton[btnrole="remove"]:hover {
    background-color: #FEF2F2;
    color: #EF4444;
}
"""
