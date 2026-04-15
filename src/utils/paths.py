#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Path Management Utilities
Centralized path resolution for all modules
"""

import os
import sys
from pathlib import Path

from .error_handler import ErrorHandler, ErrorContext, ErrorLevel

APP_FOLDERS = {"RACRegistros"}


def get_root_directory() -> Path:
    if getattr(sys, "frozen", False):
        exe_dir = Path(os.path.dirname(sys.executable))
        if exe_dir.name in APP_FOLDERS:
            return exe_dir.parent
        return exe_dir

    return Path(__file__).parent.parent.parent


def resolve_db_path(db_filename: str, create_dir: bool = True) -> str:
    root_dir = get_root_directory()

    db_in_data_dir = root_dir / "data" / db_filename
    db_in_root = root_dir / db_filename

    if db_in_data_dir.exists():
        return str(db_in_data_dir)

    if db_in_root.exists():
        return str(db_in_root)

    chosen_path = db_in_data_dir

    if create_dir:
        chosen_path.parent.mkdir(parents=True, exist_ok=True)
        ErrorHandler.log(
            f"Criando diretório: {chosen_path.parent}",
            level=ErrorLevel.INFO,
            context=ErrorContext.FILE_IO,
        )

    return str(chosen_path)


def get_config_path() -> Path:
    root_dir = get_root_directory()

    data_config = root_dir / "data" / "config.json"
    if data_config.exists():
        return data_config

    root_config = root_dir / "config.json"
    if root_config.exists():
        return root_config

    return data_config
