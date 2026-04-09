#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC NiceGUI Application Setup
"""

from typing import Optional

from src.database.rac_database import RACDatabase
from src.state.rac_state_manager import RACStateManager
from src.utils.config import ConfigManager
from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel


db: Optional[RACDatabase] = None
state: Optional[RACStateManager] = None
config: Optional[ConfigManager] = None


TIPO_COLORS = {
    "entrada": "positive",
    "renovacao": "info",
    "retirada": "warning",
    "urgente": "negative",
}

TIPO_HEX = {
    "entrada": "#059669",
    "renovacao": "#2563EB",
    "retirada": "#D97706",
    "urgente": "#DC2626",
}

TIPO_LABELS = {
    "entrada": "Entrada",
    "renovacao": "Renovação",
    "retirada": "Retirada",
    "urgente": "Urgente",
}

TIPO_ICONS = {
    "entrada": "login",
    "renovacao": "autorenew",
    "retirada": "logout",
    "urgente": "priority_high",
}

PRIMARY_COLOR = "#4F46E5"


async def init_app():
    global db, state, config
    config = ConfigManager()
    config.apply_theme()
    db = RACDatabase()
    state = RACStateManager()

    auto_return = config.get("auto_return", True)
    state.set_auto_return(auto_return)

    last_malote_id = config.get("last_malote_id")
    if last_malote_id:
        malote = db.get_malote_by_id(last_malote_id)
        if malote:
            state.set_active_malote(malote)

    ErrorHandler.log(
        "RAC web app inicializado",
        level=ErrorLevel.INFO,
        context=ErrorContext.UI,
    )


async def shutdown_app():
    if state and config:
        malote = state.get_active_malote()
        if malote:
            config.set("last_malote_id", malote["id"])
        config.set("auto_return", state.get_auto_return())

    if db:
        db.close()


def get_db() -> RACDatabase:
    assert db is not None, "Database not initialized"
    return db


def get_state() -> RACStateManager:
    assert state is not None, "State manager not initialized"
    return state


def get_config() -> ConfigManager:
    assert config is not None, "Config not initialized"
    return config
