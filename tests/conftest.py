import pytest

from andaime import App

from src.database.rac_database import RACDatabase
from src.utils.config import RACConfig


@pytest.fixture(autouse=True)
def _init_andaime(tmp_path):
    App.reset()
    App("RAC-TEST", "RACRegistros", config_cls=RACConfig, db_cls=RACDatabase, root=tmp_path)
    yield
    App.reset()
