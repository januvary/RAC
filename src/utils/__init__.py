"""
Utils Module
Utilitários e configurações
"""

from .config import RACConfig, ConfigManager
from .error_handler import ErrorHandler, ErrorLevel, ErrorContext
from .paths import get_config_path, get_root_directory, resolve_db_path

__all__ = [
    "RACConfig",
    "ConfigManager",
    "ErrorHandler",
    "ErrorLevel",
    "ErrorContext",
    "get_config_path",
    "get_root_directory",
    "resolve_db_path",
]
