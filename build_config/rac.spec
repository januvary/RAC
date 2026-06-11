# -*- mode: python ; coding: utf-8 -*-

import os
import shutil

here = os.path.abspath(SPECPATH) if os.path.isdir(SPECPATH) else os.path.dirname(os.path.abspath(SPECPATH))
project_root = os.path.dirname(here)

src_dir = os.path.join(project_root, "src")
clean_src = os.path.join(here, "_build_src")

if os.path.exists(clean_src):
    shutil.rmtree(clean_src)
shutil.copytree(src_dir, clean_src, ignore=shutil.ignore_patterns("__pycache__"))

fonts_dir = os.path.join(here, "fonts")

datas = [
    (clean_src, "src"),
    (os.path.join(project_root, "..", "andaime", "andaime", "data"), os.path.join("andaime", "data")),
]

andaime_src = os.path.join(project_root, "..", "andaime", "andaime")
if os.path.isdir(andaime_src):
    datas.append((andaime_src, "andaime"))

if os.path.exists(fonts_dir):
    datas.append((fonts_dir, "fonts"))

icon_path = os.path.join(project_root, "RAC.ico")

excludes = [
    "tkinter", "_tkinter",
    "pandas", "pyarrow", "numpy",
    "uvloop", "psycopg", "psycopg2",
    "cryptography", "PIL", "Pillow", "lxml",
    "sqlalchemy", "aiohttp", "pytest", "py",
    "docutils", "pygments", "fsspec", "jinja2", "mako",
    "pyttsx3", "pydoc_data", "websockets", "orjson",
    "httptools", "dns", "anyio", "httpcore", "httpx", "fastapi",
    "PySide6.QtWebEngine", "PySide6.QtNetwork", "PySide6.QtXml",
    "PySide6.QtSql", "PySide6.QtOpenGL", "PySide6.QtTest",
    "PySide6.QtBluetooth", "PySide6.QtNfc", "PySide6.QtPositioning",
    "PySide6.QtLocation", "PySide6.QtMultimedia", "PySide6.QtSensors",
    "PySide6.QtSerialPort", "PySide6.QtTextToSpeech",
    "PySide6.QtWebSockets", "PySide6.QtXmlPatterns",
    "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtPdf",
    "PySide6.QtSvg", "PySide6.QtVirtualKeyboard",
    "PySide6.QtWaylandClient", "PySide6.QtEglFSDeviceIntegration",
    "PySide6.QtQmlModels", "PySide6.QtQmlWorkerScript",
    "PySide6.QtWlShellIntegration", "PySide6.QtOpenGLWidgets",
    "PySide6.QtConcurrent", "PySide6.QtPrintSupport",
    "PySide6.QtDesigner", "PySide6.QtHelp", "PySide6.QtUiTools",
    "PySide6.QtAxContainer",
]

a = Analysis(
    [os.path.join(project_root, "main.py")],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PySide6", "PySide6.QtWidgets", "PySide6.QtCore", "PySide6.QtGui",
        "src", "src.gui", "src.gui.main_window", "src.gui.components",
        "src.gui.styles", "src.gui.constants",
        "src.gui.pages.start_page", "src.gui.pages.entry_page",
        "src.gui.pages.preview_page",
        "src.database.rac_database", "src.database.definitive_catalog",
        "src.state.rac_state_manager", "src.models",
        "src.utils.config", "src.utils.text_utils", "src.utils.date_calculator",
        "src.export.excel_exporter",
        "andaime", "andaime.config", "andaime.database",
         "andaime.dates",
        "andaime.error_handler", "andaime.paths", "andaime.text",
        "holidays",
        "json", "sqlite3", "shutil", "traceback", "unicodedata",
        "dataclasses", "logging", "threading", "contextlib",
        "inspect", "dis", "tokenize", "token", "opcode",
        "importlib", "importlib.util", "importlib.machinery",
        "typing", "types", "functools", "enum", "operator",
        "weakref", "warnings", "collections", "collections.abc",
        "keyword", "heapq", "bisect", "abc", "io", "re",
        "linecache", "ntpath", "genericpath", "stat", "glob",
        "fnmatch", "pdb", "code", "codeop", "compile",
        "symtable", "ast", "reprlib", "pprint",
        "pkgutil", "zipimport", "runpy",
    ],
    hookspath=[os.path.join(here, "hooks")],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=True,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RAC",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path if os.path.exists(icon_path) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="RAC",
)
