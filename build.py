#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build script for RAC desktop application (PySide6)
Usage: python3 build.py
"""

import PyInstaller.__main__
import os
import shutil
import glob
import tempfile

here = os.path.dirname(os.path.abspath(__file__))

icon_path = os.path.join(here, "RAC.ico")

clean_src = os.path.join(here, "build_tmp_src")
if os.path.exists(clean_src):
    shutil.rmtree(clean_src)
shutil.copytree(os.path.join(here, "src"), clean_src, ignore=shutil.ignore_patterns("__pycache__"))

args = [
    os.path.join(here, "main.py"),
    "--name=RAC",
    "--noconfirm",
    "--windowed",
    "--strip",
    f"--add-data={clean_src}:src",
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
    "--hidden-import=src.gui.pages.preview_page",
    "--hidden-import=src.database.rac_database",
    "--hidden-import=src.database.definitive_catalog",
    "--hidden-import=src.state.rac_state_manager",
    "--hidden-import=src.models",
    "--hidden-import=src.utils.config",
    "--hidden-import=src.utils.error_handler",
    "--hidden-import=src.utils.paths",
    "--hidden-import=src.utils.text_utils",
    "--hidden-import=src.utils.database_base",
    "--hidden-import=src.export.excel_exporter",
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
    "--exclude-module=PySide6.QtQuick",
    "--exclude-module=PySide6.QtQml",
    "--exclude-module=PySide6.QtPdf",
    "--exclude-module=PySide6.QtSvg",
    "--exclude-module=PySide6.QtVirtualKeyboard",
    "--exclude-module=PySide6.QtWaylandClient",
    "--exclude-module=PySide6.QtEglFSDeviceIntegration",
    "--exclude-module=PySide6.QtQmlModels",
    "--exclude-module=PySide6.QtQmlWorkerScript",
    "--exclude-module=PySide6.QtWlShellIntegration",
    "--exclude-module=PySide6.QtOpenGLWidgets",
    "--exclude-module=PySide6.QtConcurrent",
    "--exclude-module=PySide6.QtPrintSupport",
    "--exclude-module=PySide6.QtDesigner",
    "--exclude-module=PySide6.QtHelp",
    "--exclude-module=PySide6.QtUiTools",
    "--exclude-module=PySide6.QtAxContainer",
]

PyInstaller.__main__.run(args)

shutil.rmtree(clean_src, ignore_errors=True)

dist_internal = os.path.join(here, "dist", "RAC", "_internal")

qt_plugins = os.path.join(dist_internal, "PySide6", "Qt", "plugins")
if os.path.isdir(qt_plugins):
    remove_plugin_dirs = [
        "wayland-decoration-client",
        "wayland-graphics-integration-client",
        "wayland-shell-integration",
        "egldeviceintegrations",
        "generic",
        "platforminputcontexts",
        "iconengines",
        "xcbglintegrations",
    ]
    for d in remove_plugin_dirs:
        p = os.path.join(qt_plugins, d)
        if os.path.isdir(p):
            shutil.rmtree(p)

    img_dir = os.path.join(qt_plugins, "imageformats")
    if os.path.isdir(img_dir):
        keep = {"libqjpeg.so", "libqgif.so"}
        for f in os.listdir(img_dir):
            if f not in keep:
                os.remove(os.path.join(img_dir, f))

    platforms_dir = os.path.join(qt_plugins, "platforms")
    if os.path.isdir(platforms_dir):
        keep = {"libqxcb.so", "libqwayland.so", "libqoffscreen.so"}
        for f in os.listdir(platforms_dir):
            if f not in keep:
                os.remove(os.path.join(platforms_dir, f))

    themes_dir = os.path.join(qt_plugins, "platformthemes")
    if os.path.isdir(themes_dir):
        for f in os.listdir(themes_dir):
            if "gtk" in f.lower():
                os.remove(os.path.join(themes_dir, f))

qt_translations = os.path.join(dist_internal, "PySide6", "Qt", "translations")
if os.path.isdir(qt_translations):
    keep_prefixes = ("qtbase_pt", "qt_pt")
    for f in os.listdir(qt_translations):
        if not any(f.startswith(p) for p in keep_prefixes):
            os.remove(os.path.join(qt_translations, f))

qt_lib = os.path.join(dist_internal, "PySide6", "Qt", "lib")
if os.path.isdir(qt_lib):
    remove_libs = [
        "libQt6Quick*",
        "libQt6Qml*",
        "libQt6Pdf*",
        "libQt6Svg*",
        "libQt6VirtualKeyboard*",

        "libQt6WaylandClient*",
        "libQt6EglFS*",
        "libQt6WlShellIntegration*",
        "libQt6OpenGL*",
        "libQt6Network*",
    ]
    for pattern in remove_libs:
        for f in glob.glob(os.path.join(qt_lib, pattern)):
            os.remove(f)

pyside6_dir = os.path.join(dist_internal, "PySide6")
if os.path.isdir(pyside6_dir):
    remove_bindings = [
    ]
    for f in remove_bindings:
        p = os.path.join(pyside6_dir, f)
        if os.path.isfile(p):
            os.remove(p)

remove_shared_libs = [
    "libglycin-2.so*",
    "libgtk-3.so*",
    "libgdk-3.so*",
    "libatspi.so*",
    "libatk-bridge-2.0.so*",
    "libatk-1.0.so*",
    "libepoxy.so*",
    "libcairo-gobject.so*",
    "libcloudproviders.so*",
    "libXinerama.so*",
    "libXcomposite.so*",
    "libXdamage.so*",
]
for pattern in remove_shared_libs:
    for f in glob.glob(os.path.join(dist_internal, pattern)):
        os.remove(f)

remove_dynload = [
    "_codecs_jp*",
    "_codecs_kr*",
    "_codecs_cn*",
    "_codecs_tw*",
    "_codecs_hk*",
    "_codecs_iso2022*",
    "readline*",
]
dynload_dir = os.path.join(dist_internal, "python3.14", "lib-dynload")
for pattern in remove_dynload:
    for f in glob.glob(os.path.join(dynload_dir, pattern)):
        os.remove(f)

trimmed_icu = os.path.join(here, "build_icu", "libicudata.so.73")
icu_target = os.path.join(dist_internal, "PySide6", "Qt", "lib", "libicudata.so.73")
if os.path.isfile(trimmed_icu) and os.path.isfile(icu_target):
    shutil.copy2(trimmed_icu, icu_target)
    print("ICU data trimmed (31M -> 2.9M, keeping root + pt locales)")

print("\nBuild optimization complete!")
