#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build script for RAC desktop application
Usage: python3 build.py
"""

import PyInstaller.__main__
import os

here = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    os.path.join(here, "main.py"),
    "--name=RAC",
    "--noconfirm",
    "--console",
    f"--add-data={os.path.join(here, 'src')}:src",
    f"--add-data={os.path.join(here, 'data')}:data",
    f"--icon={os.path.join(here, 'RAC.ico')}" if os.path.exists(os.path.join(here, 'RAC.ico')) else "",
    "--hidden-import=nicegui",
    "--hidden-import=nicegui.elements",
    "--hidden-import=nicegui.elements.button",
    "--hidden-import=nicegui.elements.label",
    "--hidden-import=nicegui.elements.card",
    "--hidden-import=nicegui.elements.input",
    "--hidden-import=nicegui.elements.select",
    "--hidden-import=nicegui.elements.dialog",
    "--hidden-import=nicegui.elements.icon",
    "--hidden-import=nicegui.elements.badge",
    "--hidden-import=nicegui.elements.switch",
    "--hidden-import=nicegui.elements.scroll_area",
    "--hidden-import=nicegui.elements.list",
    "--hidden-import=nicegui.elements.item",
    "--hidden-import=nicegui.elements.row",
    "--hidden-import=nicegui.elements.column",
    "--hidden-import=nicegui.elements.colors",
    "--hidden-import=starlette",
    "--hidden-import=starlette.requests",
    "--hidden-import=starlette.routing",
    "--hidden-import=uvicorn",
    "--hidden-import=uvicorn.lifespan.on",
    "--hidden-import=webview",
    "--hidden-import=openpyxl",
    "--hidden-import=src",
    "--hidden-import=src.web",
    "--hidden-import=src.web.app",
    "--hidden-import=src.web.pages.start_page",
    "--hidden-import=src.web.pages.entry_page",
    "--hidden-import=src.database.rac_database",
    "--hidden-import=src.database.definitive_catalog",
    "--hidden-import=src.state.rac_state_manager",
    "--hidden-import=src.state.state_events",
    "--hidden-import=src.utils.config",
    "--hidden-import=src.utils.error_handler",
    "--hidden-import=src.utils.paths",
    "--hidden-import=src.utils.text_utils",
    "--hidden-import=src.utils.database_base",
    "--hidden-import=src.export.excel_exporter",
    "--collect-all=nicegui",
    "--collect-all=customtkinter",
])
