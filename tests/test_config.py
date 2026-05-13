import json
import tempfile
from pathlib import Path

import pytest

from andaime.config import ConfigManager
from src.utils.config import RACConfig


@pytest.fixture(autouse=True)
def _reset_singleton():
    yield
    ConfigManager._reset()


@pytest.fixture
def config_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def config_path(config_dir):
    return Path(config_dir) / "config.json"


@pytest.fixture
def config_manager(config_path, monkeypatch):
    monkeypatch.setattr("andaime.config.get_config_path", lambda: config_path)
    return ConfigManager()


class TestRACConfig:
    def test_defaults(self):
        cfg = RACConfig.get_defaults()
        assert cfg.stay_on_page is False
        assert cfg.theme == "dark"
        assert cfg.last_malote_id is None
        assert cfg.save_path == Path.home() / "Downloads"

    def test_validate_rejects_bad_theme(self):
        with pytest.raises(ValueError, match="theme"):
            RACConfig(theme="blue")

    def test_validate_rejects_bad_stay_on_page(self):
        with pytest.raises(ValueError, match="stay_on_page"):
            RACConfig(stay_on_page="yes")

    def test_validate_rejects_bad_last_malote_id(self):
        with pytest.raises(ValueError, match="last_malote_id"):
            RACConfig(last_malote_id="abc")

    def test_post_init_sets_default_save_path(self):
        cfg = RACConfig()
        assert cfg.save_path == Path.home() / "Downloads"

    def test_to_dict_roundtrip(self):
        cfg = RACConfig(theme="light", stay_on_page=True)
        d = cfg.to_dict()
        assert d["theme"] == "light"
        assert d["stay_on_page"] is True
        assert d["save_path"] == str(Path.home() / "Downloads")

    def test_save_path_string_converted_to_path(self):
        cfg = RACConfig(save_path="/tmp/test")
        assert isinstance(cfg.save_path, Path)


class TestConfigManagerDefaults:
    def test_creates_config_file_on_first_run(self, config_path, config_manager):
        assert config_path.exists()

    def test_get_default_theme(self, config_manager):
        assert config_manager.get("theme") == "dark"

    def test_get_default_stay_on_page(self, config_manager):
        assert config_manager.get("stay_on_page") is False

    def test_get_unknown_key_returns_default(self, config_manager):
        assert config_manager.get("nonexistent", "fallback") == "fallback"


class TestConfigManagerSetGet:
    def test_set_theme(self, config_manager):
        assert config_manager.set("theme", "light") is True
        assert config_manager.get("theme") == "light"

    def test_set_stay_on_page(self, config_manager):
        assert config_manager.set("stay_on_page", True) is True
        assert config_manager.get("stay_on_page") is True

    def test_set_last_malote_id(self, config_manager):
        assert config_manager.set("last_malote_id", 42) is True
        assert config_manager.get("last_malote_id") == 42

    def test_set_last_malote_id_none(self, config_manager):
        config_manager.set("last_malote_id", 42)
        assert config_manager.set("last_malote_id", None) is True
        assert config_manager.get("last_malote_id") is None

    def test_set_unknown_key_fails(self, config_manager):
        assert config_manager.set("unknown", "value") is False

    def test_set_invalid_theme_fails(self, config_manager):
        assert config_manager.set("theme", "blue") is False

    def test_set_invalid_stay_on_page_fails(self, config_manager):
        assert config_manager.set("stay_on_page", "yes") is False

    def test_set_invalid_last_malote_id_fails(self, config_manager):
        assert config_manager.set("last_malote_id", "abc") is False


class TestConfigManagerPersistence:
    def test_set_persists_to_file(self, config_path, config_manager):
        config_manager.set("theme", "light")
        with open(config_path) as f:
            data = json.load(f)
        assert data["theme"] == "light"

    def test_reload_reads_from_file(self, config_path, config_manager):
        config_manager.set("theme", "light")

        ConfigManager._reset()
        cm2 = ConfigManager()
        assert cm2.get("theme") == "light"


class TestConfigManagerCorruptFile:
    def test_invalid_json_uses_defaults(self, config_path, monkeypatch):
        monkeypatch.setattr("andaime.config.get_config_path", lambda: config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("{invalid json")

        cm = ConfigManager()
        assert cm.get("theme") == "dark"

    def test_invalid_values_uses_defaults(self, config_path, monkeypatch):
        monkeypatch.setattr("andaime.config.get_config_path", lambda: config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({"theme": "blue"}))

        cm = ConfigManager()
        assert cm.get("theme") == "dark"


class TestConfigManagerSingleton:
    def test_returns_same_instance(self, config_path, monkeypatch):
        monkeypatch.setattr("andaime.config.get_config_path", lambda: config_path)
        a = ConfigManager()
        b = ConfigManager()
        assert a is b

    def test_reset_clears_instance(self, config_path, monkeypatch):
        monkeypatch.setattr("andaime.config.get_config_path", lambda: config_path)
        a = ConfigManager()
        ConfigManager._reset()
        b = ConfigManager()
        assert a is not b


class TestConfigManagerGetAll:
    def test_get_all_returns_config(self, config_manager):
        cfg = config_manager.get_all()
        assert isinstance(cfg, RACConfig)
        assert cfg.theme == "dark"
