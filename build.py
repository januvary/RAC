#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build script for RAC desktop application (PySide6)
Usage: python3 build.py
"""

import PyInstaller.__main__
import os

here = os.path.dirname(os.path.abspath(__file__))

icon_path = os.path.join(here, "RAC.ico")

args = [
    os.path.join(here, "main.py"),
    "--name=RAC",
    "--noconfirm",
    "--windowed",
    f"--add-data={os.path.join(here, 'src')}:src",
    f"--add-data={os.path.join(here, 'data')}:data",
]

if os.path.exists(icon_path):
    args.append(f"--icon={icon_path}")

args += [
    "--hidden-import=PySide6",
    "--hidden-import=PySide6.QtWidgets",
    "--hidden-import=PySide6.QtCore",
    "--hidden-import=PySide6.QtGui",
    "--hidden-import=src",
    "--hidden-import=src.gui",
    "--hidden-import=src.gui.main_window",
    "--hidden-import=src.gui.components",
    "--hidden-import=src.gui.styles",
    "--hidden-import=src.gui.constants",
    "--hidden-import=src.gui.pages.start_page",
    "--hidden-import=src.gui.pages.entry_page",
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
    "--exclude-module=nicegui",
    "--exclude-module=uvicorn",
    "--exclude-module=starlette",
    "--exclude-module=webview",
    "--exclude-module=customtkinter",
    "--exclude-module=tkinter",
    "--exclude-module=_tkinter",
    "--exclude-module=pandas",
    "--exclude-module=pyarrow",
    "--exclude-module=numpy",
    "--exclude-module=uvloop",
    "--exclude-module=psycopg",
    "--exclude-module=psycopg2",
    "--exclude-module=cryptography",
    "--exclude-module=PIL",
    "--exclude-module=Pillow",
    "--exclude-module=lxml",
    "--exclude-module=sqlalchemy",
    "--exclude-module=aiohttp",
    "--exclude-module=pytest",
    "--exclude-module=py",
    "--exclude-module=docutils",
    "--exclude-module=pygments",
    "--exclude-module=fsspec",
    "--exclude-module=jinja2",
    "--exclude-module=mako",
    "--exclude-module=pyttsx3",
    "--exclude-module=pydoc_data",
    "--exclude-module=websockets",
    "--exclude-module=orjson",
    "--exclude-module=httptools",
    "--exclude-module=dns",
    "--exclude-module=anyio",
    "--exclude-module=httpcore",
    "--exclude-module=httpx",
    "--exclude-module=fastapi",
    "--exclude-module=PySide6.QtWebEngine",
    "--exclude-module=PySide6.QtNetwork",
    "--exclude-module=PySide6.QtXml",
    "--exclude-module=PySide6.QtSql",
    "--exclude-module=PySide6.QtOpenGL",
    "--exclude-module=PySide6.QtTest",
    "--exclude-module=PySide6.QtBluetooth",
    "--exclude-module=PySide6.QtNfc",
    "--exclude-module=PySide6.QtPositioning",
    "--exclude-module=PySide6.QtLocation",
    "--exclude-module=PySide6.QtMultimedia",
    "--exclude-module=PySide6.QtSensors",
    "--exclude-module=PySide6.QtSerialPort",
    "--exclude-module=PySide6.QtTextToSpeech",
    "--exclude-module=PySide6.QtWebSockets",
    "--exclude-module=PySide6.QtXmlPatterns",
]

PyInstaller.__main__.run(args)
