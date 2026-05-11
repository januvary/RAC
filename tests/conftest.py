import tempfile
from pathlib import Path

import pytest

import andaime
from andaime.error_handler import ErrorHandler
from src.utils.config import RACConfig
from andaime.config import ConfigManager


@pytest.fixture(autouse=True)
def _init_andaime(tmp_path):
    ErrorHandler._initialized = False
    ErrorHandler._logger = None
    ErrorHandler._show_dialog_callback = None
    andaime.init("RAC-TEST", "RACRegistros", root=tmp_path)
    ConfigManager.init(RACConfig)
    yield
    ConfigManager._reset()
    ErrorHandler._initialized = False
    ErrorHandler._logger = None
    ErrorHandler._show_dialog_callback = None
