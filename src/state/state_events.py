#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
State Events
Event types and observer interface for state management
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any


class StateEventType(Enum):
    MALOTE_CHANGED = "malote_changed"
    REGISTRO_SAVED = "registro_saved"
    REGISTRO_DELETED = "registro_deleted"
    TIPO_SELECTED = "tipo_selected"
    SEARCH_UPDATED = "search_updated"
    CONFIG_CHANGED = "config_changed"


@dataclass
class StateEvent:
    event_type: StateEventType
    data: Dict[str, Any]


class StateObserver:
    def on_state_changed(self, event: StateEvent) -> None:
        pass
