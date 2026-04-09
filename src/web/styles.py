#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Global styles for RAC NiceGUI app
"""

GLOBAL_HEAD = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
body {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    background: #F1F5F9 !important;
    color: #1E293B !important;
}

/* ── Cards ── */
.rac-card {
    background: #FFFFFF !important;
    border-radius: 16px !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05) !important;
}

/* ── Tipo cards ── */
.rac-tipo-card {
    background: #FFFFFF !important;
    border-radius: 16px !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05) !important;
    cursor: pointer !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease !important;
}

.rac-tipo-card:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgb(0 0 0 / 0.08) !important;
    border-color: #CBD5E1 !important;
}

/* ── Section label ── */
.rac-section-label {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: #94A3B8 !important;
    padding-left: 4px !important;
    margin-bottom: 0 !important;
}

/* ── Quasar overrides ── */
.q-field--outlined .q-field__control {
    border-radius: 12px !important;
}

.q-btn {
    border-radius: 10px !important;
    text-transform: none !important;
    font-weight: 500 !important;
    letter-spacing: 0 !important;
}

.q-dialog .q-card {
    border-radius: 16px !important;
}

.q-menu {
    border-radius: 12px !important;
    box-shadow: 0 8px 30px rgb(0 0 0 / 0.1) !important;
}

.q-badge {
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 4px 12px !important;
}

.q-drawer {
    font-family: 'Inter', system-ui, sans-serif !important;
}

/* ── Item row ── */
.rac-item-row {
    background: #F8FAFC;
    border-radius: 12px;
    padding: 8px;
    border: 1px solid #F1F5F9;
}

/* ── Scrollbar ── */
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: #CBD5E1;
    border-radius: 3px;
}
</style>
"""


def inject_styles():
    from nicegui import ui
    ui.add_head_html(GLOBAL_HEAD)
