#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Management
Centralized config handling with validation and defaults
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any

from src.utils.paths import get_config_path, get_root_directory
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel


@dataclass
class RACConfig:
    auto_return: bool = True
    theme: str = "dark"
    last_malote_id: Optional[int] = None
    save_path: Path = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.save_path is None:
            self.save_path = Path.home() / "Downloads"
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.auto_return, bool):
            raise ValueError(
                f"auto_return must be bool, got {type(self.auto_return).__name__}"
            )

        if self.theme not in ("dark", "light"):
            raise ValueError(f"theme must be 'dark' or 'light', got {self.theme}")

        if self.last_malote_id is not None and not isinstance(self.last_malote_id, int):
            raise ValueError(
                f"last_malote_id must be int or None, got {type(self.last_malote_id).__name__}"
            )

        if isinstance(self.save_path, str):
            self.save_path = Path(self.save_path)

    def to_dict(self) -> dict:
        return {
            "auto_return": self.auto_return,
            "theme": self.theme,
            "last_malote_id": self.last_malote_id,
            "save_path": str(self.save_path),
        }

    @staticmethod
    def get_defaults() -> "RACConfig":
        return RACConfig(
            auto_return=True,
            theme="dark",
            last_malote_id=None,
            save_path=Path.home() / "Downloads",
        )


class ConfigManager:
    _instance: Optional["ConfigManager"] = None
    _config: Optional[RACConfig] = None

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._config is None:
            self._load()

    @staticmethod
    def _load() -> RACConfig:
        config_file = get_config_path()

        if config_file.exists():
            try:
                with config_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                if "save_path" in data:
                    data["save_path"] = Path(data["save_path"])

                config = RACConfig(**data)
                ErrorHandler.log(
                    f"Configuração carregada: {config_file}",
                    level=ErrorLevel.INFO,
                    context=ErrorContext.CONFIGURATION,
                )
                ConfigManager._config = config
                return config

            except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
                ErrorHandler.log(
                    f"Configuração inválida: {e}. Usando padrão",
                    level=ErrorLevel.WARNING,
                    context=ErrorContext.CONFIGURATION,
                )
                ConfigManager._config = RACConfig.get_defaults()
                ConfigManager._save_to_file(ConfigManager._config)
                return ConfigManager._config
        else:
            config = RACConfig.get_defaults()
            ConfigManager._save_to_file(config)
            ConfigManager._config = config
            return config

    @staticmethod
    def _save_to_file(config: RACConfig) -> None:
        try:
            config_file = get_config_path()
            config_file.parent.mkdir(parents=True, exist_ok=True)

            with config_file.open("w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)

            ErrorHandler.log(
                f"Configuração salva: {config_file}",
                level=ErrorLevel.INFO,
                context=ErrorContext.CONFIGURATION,
            )
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                context=ErrorContext.CONFIGURATION,
                recovery_hint="Verifique permissões de escrita",
                show_dialog=False,
            )

    def get(self, key: str, default: Any = None) -> Any:
        if self._config is None:
            self._config = self._load()

        try:
            return getattr(self._config, key)
        except AttributeError:
            return default

    def set(self, key: str, value: Any) -> bool:
        if self._config is None:
            self._config = self._load()

        try:
            if key == "auto_return":
                if not isinstance(value, bool):
                    return False
            elif key == "theme":
                if value not in ("dark", "light"):
                    return False
            elif key == "last_malote_id":
                if value is not None and not isinstance(value, int):
                    return False
            elif key == "save_path":
                value = Path(value)
            else:
                return False

            setattr(self._config, key, value)
            self._save_to_file(self._config)
            return True

        except Exception as e:
            ErrorHandler.log(
                f"Falha ao atualizar config: {e}",
                level=ErrorLevel.ERROR,
                context=ErrorContext.CONFIGURATION,
            )
            return False

    def get_all(self) -> RACConfig:
        if self._config is None:
            self._config = self._load()
        return self._config

    def reload(self) -> None:
        self._config = None
        self._load()
