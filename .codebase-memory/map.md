# CODEBASE MAP (passive context)
# Skeleton bodies mean: signatures kept, implementations stripped to '...'.

## src/database/rac_database.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC Database
SQLite database layer for Registros de Apoio ao CEAF
"""

import sqlite3
import operator
import contextlib
from typing import Optional
from datetime import date, datetime

from andaime.database import BaseDatabase, db_op
from andaime.paths import resolve_db_path
from andaime.error_handler import ErrorHandler, ErrorContext, ErrorLevel
from andaime.text import to_upper_normalized

from src.database.definitive_catalog import DEFINITIVE_CATALOG
from src.services.exceptions import DuplicateRecordError
from src.models import (
    Malote,
    Paciente,
    ItemCatalog,
    Registro,
    RegistroItem,
    RegistroExport,
    Process,
)


class RACDatabase(BaseDatabase):   [REF:32-957]
    SCHEMA_VERSION = 8

    def __init__(self, db_path: Optional[str] = None) -> None:   [REF:35-38]
        ...

    def _search_by_name(   [REF:40-48]
        self, table: str, name_column: str, query: str, limit: int
    ) -> list[dict]:
        ...

    def _create_schema(self) -> None:   [REF:50-54] → src/database/rac_database.py:56 _migrate_schema_if_needed → src/database/rac_database.py:73 _create_fresh_schema → src/database/rac_database.py:142 _seed_catalog_if_empty
        ...

    def _migrate_schema_if_needed(self) -> None:   [REF:56-71]
        ...

    def _create_fresh_schema(self) -> None:   [REF:73-132]
        ...

    def _log_initialization_success(self) -> None:   [REF:134-140] → src/database/rac_database.py:163 _get_catalog_count
        ...

    def _seed_catalog_if_empty(self) -> None:   [REF:142-161] → src/utils/unidade_parser.py:7 parse_unidade_from_name
        ...

    def _get_catalog_count(self) -> int:   [REF:163-164]
        ...

    # ========== MALOTE ==========

    @db_op("write")
    def create_malote(self, date: str, arrival_date: str | None = None) -> Malote:   [REF:169-182] → src/models.py:8 Malote
        ...

    @db_op("read")
    def get_malote_by_id(self, malote_id: int) -> Optional[Malote]:   [REF:185-187] → src/models.py:14 from_row
        ...

    @db_op("read")
    def get_recent_malotes(self, limit: int = 5) -> list[Malote]:   [REF:190-194] → src/models.py:14 from_row
        ...

    @db_op("read")
    def get_all_malotes(self) -> list[Malote]:   [REF:197-200] → src/models.py:14 from_row
        ...

    @db_op("read")
    def get_malote_dates(self) -> set:   [REF:203-208] → src/gui/widgets/crud_list.py:244 add
        ...

    @db_op("write")
    def update_malote(   [REF:211-221]
        self, malote_id: int, date: str | None = None, arrival_date: str | None = None
    ) -> bool:
        ...

    @db_op("write")
    def delete_malote(self, malote_id: int) -> bool:   [REF:224-225]
        ...

    # ========== PACIENTE ==========

    @db_op("write")
    def create_paciente(self, name: str) -> Paciente:   [REF:230-233] → src/models.py:23 Paciente
        ...

    @db_op("read")
    def get_paciente_by_id(self, paciente_id: int) -> Optional[Paciente]:   [REF:236-238] → src/models.py:14 from_row
        ...

    @db_op("read")
    def find_paciente_by_name(self, name: str) -> Optional[Paciente]:   [REF:241-246] → src/models.py:14 from_row
        ...

    @db_op("read")
    def search_pacientes(self, query: str, limit: int = 10) -> list[Paciente]:   [REF:249-252] → src/models.py:14 from_row → src/database/rac_database.py:40 _search_by_name
        ...

    @db_op("write")
    def update_paciente(self, paciente_id: int, name: str) -> bool:   [REF:255-258]
        ...

    @db_op("write")
    def delete_paciente(self, paciente_id: int) -> bool:   [REF:261-262]
        ...

    @db_op("write")
    def import_pacientes(self, names: list[str]) -> tuple[int, int]:   [REF:265-289]
        ...

    # ========== REGISTRO ==========

    @db_op("write")
    def create_registro(   [REF:294-318] → src/models.py:59 Registro
        self,
        tipo: str,
        paciente_id: int,
        malote_id: int,
        waiting_docs: bool = False,
    ) -> Registro:
        ...

    @db_op("read")
    def get_registro_by_id(self, registro_id: int) -> Optional[Registro]:   [REF:321-330] → src/models.py:14 from_row
        ...

    @db_op("read")
    def find_registro(   [REF:333-345] → src/models.py:14 from_row
        self, tipo: str, paciente_id: int, malote_id: int
    ) -> Optional[Registro]:
        ...

    @db_op("read")
    def get_registros_by_malote(self, malote_id: int) -> list[Registro]:   [REF:348-356] → src/models.py:14 from_row
        ...

    @db_op("read")
    def get_registros_by_malote_and_tipo(   [REF:359-369] → src/models.py:14 from_row
        self, malote_id: int, tipo: str
    ) -> list[Registro]:
        ...

    @db_op("write")
    def update_registro(self, registro_id: int, **fields) -> bool:   [REF:372-401] → src/services/exceptions.py:9 DuplicateRecordError
        ...

    @db_op("write")
    def delete_registro(self, registro_id: int) -> bool:   [REF:404-408]
        ...

    @db_op("read")
    def search_registros_by_paciente(   [REF:411-427] → src/models.py:14 from_row
        self, query: str, active_malote_id: int | None = None, limit: int = 20
    ) -> list[Registro]:
        ...

    @db_op("read")
    def get_registros_by_paciente(self, paciente_id: int) -> list[Registro]:   [REF:430-439] → src/models.py:14 from_row
        ...

    # ========== REGISTRO ITEMS ==========

    @db_op("write")
    def set_registro_items(   [REF:444-457]
        self, registro_id: int, items: list[tuple[int, int, str, int]]
    ) -> None:
        ...

    @db_op("write")
    def set_registro_items_with_process(   [REF:460-476]
        self, registro_id: int, items: list[tuple[int, int, int | None, str, int]]
    ) -> None:
        ...

    @db_op("read")
    def get_items_by_registro(self, registro_id: int) -> list[RegistroItem]:   [REF:479-487] → src/models.py:14 from_row
        ...

    @db_op("read")
    def get_items_by_paciente(self, paciente_id: int) -> list[ItemCatalog]:   [REF:490-499] → src/models.py:14 from_row
        ...

    @db_op("read")
    def get_last_usage_by_paciente(self, paciente_id: int) -> list[tuple[int, str]]:   [REF:502-519] → src/gui/widgets/crud_list.py:244 add
        ...

    # ========== PROCESSES ==========

    @db_op("write")
    def set_processes(   [REF:524-552]
        self,
        registro_id: int,
        processes: list[tuple[int, int, str | None]],
    ) -> list[Process]:
        ...

    @db_op("read")
    def get_processes_by_registro(self, registro_id: int) -> list[Process]:   [REF:555-559] → src/models.py:14 from_row
        ...

    @db_op("read")
    def get_malote_arrivals_between(self, start_iso: str, end_iso: str) -> list[str]:   [REF:562-580]
        ...

    @db_op("read")
    def count_return_dates_between(self, start_iso: str, end_iso: str) -> dict[str, int]:   [REF:583-592]
        ...

    @db_op("read")
    def get_earlier_malote(self, current_malote_id: int) -> Optional[Malote]:   [REF:595-603] → src/models.py:14 from_row → src/database/rac_database.py:185 get_malote_by_id
        ...

    # ========== ITEMS CATALOG ==========

    @db_op("read")
    def get_all_items(self) -> list[ItemCatalog]:   [REF:608-611] → src/models.py:14 from_row
        ...

    @db_op("read")
    def search_items(self, query: str, limit: int = 10) -> list[ItemCatalog]:   [REF:614-617] → src/models.py:14 from_row → src/database/rac_database.py:40 _search_by_name
        ...

    @db_op("write")
    def create_item(self, name: str, unidade: str = "un", quantidade: int = 0, cids: str = "") -> ItemCatalog:   [REF:620-623] → src/models.py:40 ItemCatalog
        ...

    @db_op("write")
    def update_item(self, item_id: int, name: str) -> bool:   [REF:626-629]
        ...

    @db_op("write")
    def update_item_cids(self, item_id: int, cids: str) -> bool:   [REF:632-633]
        ...

    @db_op("write")
    def update_item_quantidade(self, item_id: int, quantidade: int) -> bool:   [REF:636-637]
        ...

    @db_op("write")
    def update_item_unidade(self, item_id: int, unidade: str) -> bool:   [REF:640-641]
        ...

    @db_op("write")
    def delete_item(self, item_id: int) -> bool:   [REF:644-647]
        ...

    # ========== PACIENTE (listagem) ==========

    @db_op("read")
    def get_all_pacientes(self) -> list[Paciente]:   [REF:652-655] → src/models.py:14 from_row
        ...

    @db_op("read")
    def get_all_pacientes_with_last_registro(self) -> list[Paciente]:   [REF:658-673] → src/models.py:14 from_row
        ...

    # ========== EXPORT HELPERS ==========

    @db_op("read")
    def dump_all_tables(self) -> dict[str, list[dict]]:   [REF:678-689]
        ...

    @db_op("read")
    def get_registros_with_items_by_malote(   [REF:692-738] → src/models.py:128 ProcessExport → src/models.py:14 from_row
        self, malote_id: int
    ) -> list[RegistroExport]:
        ...

    # ========== STATISTICS ==========

    def _stats_where(   [REF:742-765]
        self,
        tipo: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        extra: str | None = None,
        extra_params: list | None = None,
    ) -> tuple[str, tuple]:
        ...

    @db_op("read")
    def get_stats_by_tipo(   [REF:768-795] → src/database/rac_database.py:742 _stats_where
        self,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        ...

    @db_op("read")
    def get_stats_totals(   [REF:798-811] → src/database/rac_database.py:742 _stats_where
        self,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        ...

    @db_op("read")
    def get_malote_date_range(self) -> tuple[str | None, str | None]:   [REF:814-822]
        ...

    @db_op("read")
    def get_stats_top_itens(   [REF:825-842] → src/database/rac_database.py:742 _stats_where
        self,
        tipo: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        ...

    @db_op("read")
    def get_stats_registros(   [REF:845-871] → src/models.py:14 from_row → src/database/rac_database.py:742 _stats_where
        self,
        tipo: str | None = None,
        item_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[Registro]:
        ...

    @db_op("read")
    def get_items_by_registros(   [REF:874-893] → src/models.py:14 from_row
        self, registro_ids: list[int]
    ) -> dict[int, list[RegistroItem]]:
        ...

    @db_op("read")
    def get_item_cids_by_registro(   [REF:896-918] → src/database/rac_database.py:742 _stats_where → src/gui/widgets/crud_list.py:244 add
        self,
        item_id: int,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[int, list[str]]:
        ...

    @db_op("read")
    def get_stats_item_totals(   [REF:921-957] → src/database/rac_database.py:742 _stats_where
        self,
        item_id: int,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        ...
```

## src/gui/main_window.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Window — QStackedWidget page navigation
"""

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QSizePolicy

from PySide6.QtCore import Signal, QTimer
from src.database.rac_database import RACDatabase
from src.state.rac_state_manager import RACStateManager
from andaime.config import ConfigManager

from src.gui.constants import TIPO_LABELS
from src.gui.pages.start_page import StartPage
from src.gui.pages.entry_page import EntryPage
from src.gui.pages.preview_page import PreviewPage
from src.gui.pages.medicamentos_page import MedicamentosPage
from src.gui.pages.pacientes_page import PacientesPage
from src.gui.pages.stats_page import StatsPage
from src.gui.pages.patient_page import PatientPage
from src.gui.pages.registro_list_page import RegistroListPage
from andaime.qt.status_line import StatusLine
from andaime.qt import ShortcutManager


class MainWindow(QMainWindow):   [REF:27-398]
    theme_changed = Signal()

    def __init__(self, app_instance):   [REF:30-65]
        ...

    def init_backend(self):   [REF:67-87] → src/gui/main_window.py:206 _setup_shortcuts → src/gui/styles.py:59 set_theme → src/state/rac_state_manager.py:17 RACStateManager
        ...

    def _toggle_shortcut_peek(self, show: bool):   [REF:89-93] → src/gui/main_window.py:228 _current_page
        ...

    @property
    def services(self):   [REF:96-110]
        ...

    def shutdown_backend(self):   [REF:112-119]
        ...

    def navigate_to(self, page_name: str, **kwargs):   [REF:121-154] → src/gui/main_window.py:156 _show_start_page → src/gui/main_window.py:188 _show_preview_page → src/gui/main_window.py:191 _show_medicamentos_page → src/gui/main_window.py:182 _show_entry_page → src/gui/main_window.py:203 _show_patient_page → src/gui/main_window.py:194 _show_pacientes_page → src/gui/main_window.py:200 _show_registro_list_page → src/gui/main_window.py:197 _show_stats_page
        ...

    def _show_start_page(self):   [REF:156-166] → src/gui/pages/start_page.py:56 StartPage
        ...

    def _clear_above_start(self):   [REF:168-174]
        ...

    def _push_page(self, page_class, *args, **kwargs):   [REF:176-180] → src/gui/main_window.py:168 _clear_above_start
        ...

    def _show_entry_page(   [REF:182-186] → src/gui/main_window.py:176 _push_page
        self, tipo: str, edit_id: int | None = None, return_to: str = "start",
        paciente_id: int | None = None, patient_return_to: str = "start",
    ):
        ...

    def _show_preview_page(self):   [REF:188-189] → src/gui/main_window.py:176 _push_page
        ...

    def _show_medicamentos_page(self):   [REF:191-192] → src/gui/main_window.py:176 _push_page
        ...

    def _show_pacientes_page(self, return_to: str = "start"):   [REF:194-195] → src/gui/main_window.py:176 _push_page
        ...

    def _show_stats_page(self):   [REF:197-198] → src/gui/main_window.py:176 _push_page
        ...

    def _show_registro_list_page(self, params: dict):   [REF:200-201] → src/gui/main_window.py:176 _push_page
        ...

    def _show_patient_page(self, paciente_id: int, highlight_registro: int | None = None, return_to: str | None = None):   [REF:203-204] → src/gui/main_window.py:176 _push_page
        ...

    def _setup_shortcuts(self):   [REF:206-226] → src/gui/main_window.py:303 _shortcut_tipo_by_key
        ...

    def _current_page(self):   [REF:228-229]
        ...

    def _on_page(self, page_class, fn):   [REF:231-234] → src/gui/main_window.py:228 _current_page
        ...

    def _shortcut_save(self):   [REF:236-237] → src/gui/main_window.py:231 _on_page
        ...

    def _shortcut_export(self):   [REF:239-240] → src/gui/main_window.py:231 _on_page
        ...

    def _shortcut_back(self):   [REF:242-249] → src/gui/main_window.py:121 navigate_to → src/gui/main_window.py:228 _current_page
        ...

    def _shortcut_malote_dialog(self):   [REF:251-254] → src/gui/widgets/malote.py:76 open_dialog → src/gui/main_window.py:228 _current_page
        ...

    def _shortcut_focus_search(self):   [REF:256-273] → src/gui/main_window.py:228 _current_page → src/gui/pages/entry_page.py:517 focus_next_field
        ...

    def _shortcut_add_item(self):   [REF:275-280] → src/gui/main_window.py:231 _on_page → src/gui/pages/entry_page.py:267 _add_item_row
        ...

    def _shortcut_toggle_docs(self):   [REF:282-283] → src/gui/main_window.py:231 _on_page
        ...

    def _shortcut_toggle_stay_on_page(self):   [REF:285-286] → src/gui/main_window.py:231 _on_page
        ...

    def _navigate_from_start(self, target: str):   [REF:288-289] → src/gui/main_window.py:231 _on_page
        ...

    def _shortcut_preview(self):   [REF:291-292] → src/gui/main_window.py:288 _navigate_from_start
        ...

    def _shortcut_medicamentos(self):   [REF:294-295] → src/gui/main_window.py:288 _navigate_from_start
        ...

    def _shortcut_pacientes(self):   [REF:297-298] → src/gui/main_window.py:288 _navigate_from_start
        ...

    def _shortcut_stats(self):   [REF:300-301] → src/gui/main_window.py:288 _navigate_from_start
        ...

    def _shortcut_tipo_by_key(self, tipo: str):   [REF:303-312] → src/gui/main_window.py:231 _on_page
        ...

    def show_status(self, text: str, kind: str = "info", path: str | None = None) -> None:   [REF:314-323]
        ...

    def _clear_status(self):   [REF:325-326]
        ...

    def closeEvent(self, event):   [REF:328-330] → src/gui/main_window.py:112 shutdown_backend
        ...

    _XLSX_SUFFIXES = (".xlsx", ".xlsm")

    def dragEnterEvent(self, event):   [REF:334-341]
        ...

    def dropEvent(self, event):   [REF:343-353] → src/gui/main_window.py:355 _open_import_dialog
        ...

    def _open_import_dialog(self, paths: list[str]) -> None:   [REF:355-398] → src/importers/excel_importer.py:257 ExcelImporter → src/database/rac_database.py:265 import_pacientes → src/gui/widgets/import_dialog.py:58 ImportPlanilhaDialog → src/gui/main_window.py:314 show_status
        ...
```

## src/models.py
```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Malote:   [REF:8-19]
    id: int | None = None
    date: str = ""
    arrival_date: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Malote:   [REF:14-19]
        ...


@dataclass
class Paciente:   [REF:23-36]
    id: int | None = None
    name: str = ""
    last_registro_date: str | None = None
    last_registro_tipo: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Paciente:   [REF:30-36]
        ...


@dataclass
class ItemCatalog:   [REF:40-55]
    id: int | None = None
    name: str = ""
    quantidade: int = 0
    unidade: str = "un"
    cids: str = ""

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> ItemCatalog:   [REF:48-55]
        ...


@dataclass
class Registro:   [REF:59-80]
    id: int | None = None
    tipo: str = ""
    paciente_id: int | None = None
    malote_id: int | None = None
    created_at: str = ""
    paciente_name: str | None = None
    malote_date: str | None = None
    waiting_docs: bool = False

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Registro:   [REF:70-80]
        ...


@dataclass
class Process:   [REF:84-99]
    id: int | None = None
    registro_id: int | None = None
    group_number: int = 1
    months_supply: int = 0
    expected_return_date: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Process:   [REF:92-99]
        ...


@dataclass
class RegistroItem:   [REF:103-124]
    id: int | None = None
    registro_id: int | None = None
    process_id: int | None = None
    item_id: int | None = None
    item_name: str | None = None
    process_group: int = 1
    cid: str = ""
    quantidade: int = 0

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> RegistroItem:   [REF:114-124]
        ...


@dataclass
class ProcessExport:   [REF:128-131]
    group_number: int = 1
    items: list[str] = field(default_factory=list)
    expected_return_date: str | None = None


@dataclass
class RegistroExport:   [REF:135-149]
    id: int | None = None
    tipo: str = ""
    paciente_id: int | None = None
    paciente_name: str | None = None
    processes: list[ProcessExport] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> RegistroExport:   [REF:143-149]
        ...
```

## src/gui/pages/entry_page.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry Page — record creation and editing
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QSizePolicy,
    QLineEdit,
)
from PySide6.QtCore import Qt, QTimer

if TYPE_CHECKING:
    from src.gui.main_window import MainWindow

from andaime.widgets import SearchableComboBox, CycleButton, static_search_fn
from andaime.error_handler import ErrorContext
from src.gui.widgets import (
    SectionLabel,
    TipoCombo,
    MaloteLabel,
    make_button,
    make_hbox,
    BasePage,
    delete_registro_with_undo,
    confirm_past_malote,
)
from src.gui.widgets.buttons import make_icon_button
from src.models import Registro
from src.services.registro_service import EditContext
from src.services.exceptions import ValidationError, DuplicateRecordError
from src.utils.text_utils import is_malote_past
from andaime.text import to_upper_normalized

from src.gui.styles import colors


@dataclass
class _RowData:   [REF:51-57]
    group_btn: CycleButton
    row_widget: QWidget
    combo: SearchableComboBox | None = None
    quantidade_input: QLineEdit | None = None
    cid_combo: SearchableComboBox | None = None
    pg: int = 1


class EntryPage(BasePage):   [REF:60-612]
    def __init__(   [REF:61-89] → src/gui/widgets/base_page.py:27 __init__ → src/state/rac_state_manager.py:44 set_current_tipo → src/gui/pages/entry_page.py:99 _build_ui
        self,
        main_window: MainWindow,
        tipo: str,
        edit_id: int | None = None,
        return_to: str = "start",
        paciente_id: int | None = None,
        patient_return_to: str = "start",
    ):
        ...

    @property
    def _is_editing(self) -> bool:   [REF:92-93]
        ...

    @property
    def _edit_registro(self) -> Registro | None:   [REF:96-97]
        ...

    def _build_ui(self):   [REF:99-120] → src/gui/pages/entry_page.py:122 _build_header → src/gui/pages/entry_page.py:173 _build_items_section → src/gui/pages/entry_page.py:205 _build_action_bar → src/gui/pages/entry_page.py:140 _build_patient_section
        ...

    def _build_header(self, layout: QVBoxLayout):   [REF:122-138] → src/state/rac_state_manager.py:30 set_active_malote → src/gui/widgets/malote.py:34 MaloteLabel → src/gui/widgets/inputs.py:37 TipoCombo
        ...

    def _build_patient_section(self, layout: QVBoxLayout):   [REF:140-163] → src/gui/widgets/base_page.py:194 make_hbox → src/gui/pages/entry_page.py:408 _rebuild_focusable_combos
        ...

    def _search_pacientes(self, query: str) -> dict[str, str]:   [REF:165-167]
        ...

    def _search_items(self, query: str) -> dict[str, str]:   [REF:169-171]
        ...

    def _build_items_section(self, layout: QVBoxLayout):   [REF:173-203] → src/gui/pages/entry_page.py:267 _add_item_row → src/gui/widgets/buttons.py:31 make_button
        ...

    def _build_action_bar(self, layout: QVBoxLayout):   [REF:205-254] → src/gui/widgets/buttons.py:31 make_button → src/gui/pages/entry_page.py:260 _update_registro_status → src/gui/styles.py:77 colors
        ...

    def set_shortcuts_visible(self, show: bool):   [REF:256-258] → src/gui/widgets/base_page.py:126 set_shortcuts_visible
        ...

    def _update_registro_status(self, editing: bool):   [REF:260-265] → src/gui/styles.py:77 colors
        ...

    def _add_item_row(self, item_id: int | None = None, process_group: int = 1, cid: str = "", quantidade: int = 0):   [REF:267-325] → src/gui/widgets/buttons.py:38 make_icon_button → src/gui/pages/entry_page.py:339 _populate_cid_combo → src/gui/widgets/base_page.py:194 make_hbox → src/gui/pages/entry_page.py:408 _rebuild_focusable_combos → src/gui/pages/entry_page.py:51 _RowData
        ...

    def _on_item_selected_in_row(self, rd: _RowData, data: str | None):   [REF:327-337] → src/gui/pages/entry_page.py:339 _populate_cid_combo
        ...

    def _populate_cid_combo(self, rd: _RowData, item_id: int, selected_cid: str):   [REF:339-357] → src/gui/pages/entry_page.py:364 _register_and_propagate_cid
        ...

    def _on_cid_changed_in_row(self, rd: _RowData, data: str | None):   [REF:359-362] → src/gui/pages/entry_page.py:364 _register_and_propagate_cid
        ...

    def _register_and_propagate_cid(self, rd: _RowData, cid: str):   [REF:364-376] → src/gui/pages/entry_page.py:378 _apply_cid_to_row_if_allowed
        ...

    def _apply_cid_to_row_if_allowed(self, rd: _RowData, cid: str):   [REF:378-390]
        ...

    def _on_group_changed(self, rd: _RowData, new_pg: int):   [REF:392-400] → src/gui/pages/entry_page.py:378 _apply_cid_to_row_if_allowed → src/gui/pages/entry_page.py:364 _register_and_propagate_cid
        ...

    def _remove_item(self, widget: QWidget):   [REF:402-406] → src/gui/pages/entry_page.py:408 _rebuild_focusable_combos
        ...

    def _rebuild_focusable_combos(self):   [REF:408-413]
        ...

    def _on_paciente_selected(self, data):   [REF:415-422] → src/gui/pages/entry_page.py:483 _load_items_for_context
        ...

    def _on_context_changed(self, *_):   [REF:424-429] → src/gui/pages/entry_page.py:441 _resolve_current_patient → src/gui/pages/entry_page.py:483 _load_items_for_context
        ...

    def _on_waiting_docs_toggled(self, checked: bool):   [REF:431-432]
        ...

    def _on_malote_changed(self):   [REF:434-439] → src/gui/widgets/dialogs.py:224 confirm_past_malote → src/utils/text_utils.py:23 is_malote_past → src/state/rac_state_manager.py:26 get_active_malote
        ...

    def _resolve_current_patient(self) -> int | None:   [REF:441-454]
        ...

    def _clear_item_rows(self):   [REF:456-465] → src/gui/pages/entry_page.py:408 _rebuild_focusable_combos
        ...

    def _collect_items(self) -> list[tuple[int, int, str, int]]:   [REF:467-481]
        ...

    def _load_items_for_context(self, paciente_id: int):   [REF:483-515] → src/gui/pages/entry_page.py:267 _add_item_row → src/gui/pages/entry_page.py:260 _update_registro_status → src/state/rac_state_manager.py:26 get_active_malote → src/gui/pages/entry_page.py:456 _clear_item_rows
        ...

    def focus_next_field(self):   [REF:517-526]
        ...

    def _combo_at(self, index: int) -> SearchableComboBox | None:   [REF:528-531]
        ...

    def _on_save(self):   [REF:533-579] → src/state/rac_state_manager.py:26 get_active_malote → src/gui/pages/entry_page.py:441 _resolve_current_patient → src/gui/pages/entry_page.py:467 _collect_items → src/services/registro_service.py:137 save
        ...

    def _reset_form(self):   [REF:581-593] → src/gui/pages/entry_page.py:267 _add_item_row → src/gui/pages/entry_page.py:260 _update_registro_status → src/gui/pages/entry_page.py:456 _clear_item_rows
        ...

    def _confirm_delete(self):   [REF:595-604] → src/gui/widgets/dialogs.py:262 delete_registro_with_undo
        ...

    def _navigate_back(self):   [REF:606-612]
        ...
```

## src/gui/widgets/crud_list.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrudList — reusable search + table widget for managing a simple named entity
(pacientes, medicamentos, etc.) via injected DB callbacks. Optionally renders
a secondary column (e.g. "Último registro") via a value accessor.
"""

import sqlite3
from typing import Callable

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QLabel,
    QMenu,
)
from PySide6.QtCore import Qt, QTimer

from src.gui.widgets.buttons import make_button
from src.gui.widgets.dialogs import confirm_delete_dialog, open_input_dialog
from src.gui.widgets.base_page import make_tab
from src.gui.styles import data_view_style_qss, filter_table_rows
from andaime.qt.table import table_batch_populate


class SortableTableWidgetItem(QTableWidgetItem):   [REF:31-45]
    """QTableWidgetItem that sorts by an explicit sort_key when provided,
    falling back to text comparison otherwise. Lets a column display a
    human-readable value (e.g. '01/06/2026 · Retirada') while sorting by an
    underlying value (e.g. the ISO date '2026-06-01')."""

    def __init__(self, text: str = "", sort_key: object = None) -> None:   [REF:37-39]
        ...

    def __lt__(self, other) -> bool:   [REF:41-45]
        ...


class CrudList:   [REF:48-371]
    def __init__(self, page, title, search_placeholder,   [REF:49-95] → src/gui/widgets/crud_list.py:97 _build
                 entity_label, entity_label_lower,
                 db_get_all, db_create, db_update, db_delete,
                 delete_in_use_msg, count_label: QLabel | None = None,
                 secondary_header: str | None = None,
                 secondary_value: Callable[[object], str] | None = None,
                 secondary_sort_key: Callable[[object], object] | None = None,
                 secondary_edit_callback: Callable[[int], None] | None = None,
                 tertiary_header: str | None = None,
                 tertiary_value: Callable[[object], str] | None = None,
                 tertiary_edit_callback: Callable[[int], None] | None = None,
                 quaternary_header: str | None = None,
                 quaternary_value: Callable[[object], str] | None = None,
                 quaternary_edit_callback: Callable[[int], None] | None = None,
                 sortable: bool = True,
                 on_activate: Callable[[object], None] | None = None,
                 extra_context_items: list[tuple[str, Callable[[int], None]]] | None = None,
                 secondary_tooltip: Callable[[object], str] | None = None):
        ...

    def _build(self, search_placeholder):   [REF:97-179] → src/gui/widgets/base_page.py:184 make_tab → src/gui/widgets/buttons.py:31 make_button → src/gui/widgets/base_page.py:74 register_keyboard_nav → src/gui/widgets/crud_list.py:181 load
        ...

    def load(self):   [REF:181-184] → src/gui/widgets/crud_list.py:186 _update_count → src/gui/widgets/crud_list.py:190 _populate
        ...

    def _update_count(self):   [REF:186-188]
        ...

    def _populate(self, items):   [REF:190-239] → src/gui/widgets/crud_list.py:31 SortableTableWidgetItem
        ...

    def filter(self, text: str):   [REF:241-242] → src/gui/styles.py:576 filter_table_rows
        ...

    def add(self):   [REF:244-259] → src/gui/widgets/base_page.py:139 _handle_error → src/gui/widgets/toast.py:45 _toast → src/gui/widgets/dialogs.py:106 open_input_dialog → src/gui/widgets/crud_list.py:181 load
        ...

    def _edit_row(self, row: int):   [REF:261-264] → src/gui/widgets/crud_list.py:329 _edit_item
        ...

    def _activate_row(self, row: int, col: int):   [REF:266-297] → src/gui/widgets/crud_list.py:329 _edit_item
        ...

    def _activate_current(self):   [REF:299-302] → src/gui/widgets/crud_list.py:266 _activate_row
        ...

    def _show_context_menu(self, pos):   [REF:304-327]
        ...

    def _edit_item(self, item: QTableWidgetItem):   [REF:329-346] → src/gui/widgets/base_page.py:139 _handle_error → src/gui/widgets/toast.py:45 _toast → src/gui/widgets/dialogs.py:106 open_input_dialog → src/gui/widgets/crud_list.py:181 load
        ...

    def edit_selected(self):   [REF:348-351] → src/gui/widgets/crud_list.py:261 _edit_row
        ...

    def delete_selected(self):   [REF:353-371] → src/gui/widgets/dialogs.py:48 confirm_delete_dialog → src/gui/widgets/toast.py:45 _toast → src/gui/widgets/crud_list.py:181 load
        ...
```

## src/gui/styles.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Global QSS stylesheet — native Qt feel with theme support.

As cores neutras são mapeadas a partir da paleta compartilhada
(``andaime.qt.theme``: rampa + níveis), mantendo o motor de tema
centralizado. Cores de identidade do RAC (azul de acento, vermelhos
destrutivos, sistema ``btnrole``, tipos de medicamento) continuam
definidas localmente neste módulo.
"""

from andaime.qt.theme import LIGHT as _SHARED_LIGHT, DARK as _SHARED_DARK

_current_theme: str = "light"


# RAC key -> chave correspondente na paleta compartilhada. Chaves com o mesmo
# nome não precisam de mapeamento (pass-through).
_RAC_TO_SHARED = {
    "bg_main": "window_bg",
    "bg_card": "panel_bg",
    "bg_card_alt": "panel_header_bg",
    "bg_input": "input_bg",
    "border": "panel_border",
    "text_primary": "text",
    "separator": "separador",
    "table_alt_bg": "window_bg",
    "toast_positive_fg": "status_success",
    "toast_warning_fg": "status_warning",
    "toast_negative_fg": "status_error",
}

# Chaves do RAC (text_dark era morta e foi removida).
_RAC_KEYS = (
    "bg_main", "bg_card", "bg_card_alt", "bg_hover", "bg_pressed",
    "bg_input", "border", "border_light", "text_primary", "text_secondary",
    "selection_bg", "selection_text", "separator", "gridline", "scrollbar",
    "scrollbar_hover", "table_alt_bg", "toast_positive_fg", "toast_positive_bg",
    "toast_warning_fg", "toast_warning_bg", "toast_negative_fg",
    "toast_negative_bg", "toast_info_fg", "toast_info_bg",
)


def _rac_palette(shared: dict) -> dict:   [REF:45-52]
    ...


LIGHT_COLORS = _rac_palette(_SHARED_LIGHT)
DARK_COLORS = _rac_palette(_SHARED_DARK)


def set_theme(theme: str) -> None:   [REF:59-61]
    ...


def get_theme() -> str:   [REF:64-65]
    ...


def toggle_theme() -> str:   [REF:68-74]
    ...


def colors() -> dict:   [REF:77-78]
    ...


def _blend_hex(hex_a: str, hex_b: str, ratio: float) -> str:   [REF:81-87]
    ...


def faded_tipo_color(hex_color: str) -> str:   [REF:90-93] → src/gui/styles.py:81 _blend_hex
    ...


def get_stylesheet(theme: str | None = None) -> str:   [REF:96-99] → src/gui/styles.py:179 _build_qss
    ...


def tipo_button_qss(text_color: str | None = None, c: dict | None = None) -> str:   [REF:102-124] → src/gui/styles.py:77 colors
    ...


def combo_style_qss(   [REF:127-176]
    text_color: str,
    bg: str,
    bg_hover: str,
    dropdown_bg: str,
    selection_bg: str,
    selection_text: str,
    border: str = "none",
    font_size: str = "14px",
    font_weight: str = "400",
    padding: str = "9px 14px",
    min_height: str = "22px",
    max_height: str | None = None,
) -> str:
    ...


def _build_qss(c: dict) -> str:   [REF:179-486] → src/gui/styles.py:102 tipo_button_qss → src/gui/styles.py:127 combo_style_qss
    ...


def tab_style_qss(accent_color: str = "#3B82F6") -> str:   [REF:489-519] → src/gui/styles.py:77 colors
    ...


def data_view_style_qss(   [REF:522-573] → src/gui/styles.py:77 colors
    widget_type="QTableWidget",
    border="none",
    item_padding="8px 12px",
    include_selected=True,
    include_hover=False,
    header_bg_key="bg_card",
    header_padding="4px 8px",
    header_border_key="gridline",
    extra_header_hover="",
    outline="",
):
    ...


def filter_table_rows(table, text: str):   [REF:576-588]
    ...
```

## src/importers/excel_importer.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel Importer — reads patient names from .xlsx files.

Scans all tabs, detects the patient column from headers (PACIENTE(S),
NOME(S), NAME(S), ...) and extracts unique normalized names.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from andaime.error_handler import ErrorContext, ErrorHandler, ErrorLevel
from andaime.text import to_upper_normalized

_HEADER_SCAN_ROWS = 16
_CONTENT_SCAN_ROWS = 50
_MAX_EXTRACT_ROWS = 200_000
_TRAILING_BLANK_STOP = 8
_HIGH_PRIORITY = {"PACIENTE", "PACIENTES", "PATIENT", "PATIENTS"}
_LOW_PRIORITY = {"NOME", "NOMES", "NAME", "NAMES"}
_MED_PRIORITY = {"MEDICAMENTO", "MEDICAMENTOS", "MED", "MEDICACAO", "ITEM", "ITENS"}
_HEADER_NOISE = frozenset(_HIGH_PRIORITY | _LOW_PRIORITY)
_TOKEN_RE = re.compile(r"[A-Z0-9]+")

_COL_SPEC_RE = re.compile(r"^(\d+)\s*-\s*([A-Za-z]+)$")
_MALOTE_COL_SPEC_RE = re.compile(r"^(\d+)-([A-Za-z]+)-([A-Za-z]+)$")

# Tipo names found in tab titles (normalized without accents).
_TIPO_TITLES = {
    "ABERTURA": "entrada",
    "ENTRADA": "entrada",
    "ENTRADAS": "entrada",
    "RENOVACAO": "renovacao",
    "RENOVACOES": "renovacao",
    "RETIRADA": "retirada",
    "RETIRADAS": "retirada",
    "RESOLVER NA HORA": "urgente",
    "URGENTE": "urgente",
    "MEDICAMENTO EM CASA": "medcasa",
    "REMEDIO EM CASA": "medcasa",
    "MEDCASA": "medcasa",
}

# Tab names that map directly to a tipo when a title match is absent.
_TAB_TIPO = {
    "ABERTURA": "entrada",
    "ENTRADA": "entrada",
    "RENOVACAO": "renovacao",
    "RETIRADA": "retirada",
    "RESOLVER NA HORA": "urgente",
}

_MED_SPLIT_RE = re.compile(r"\s*;\s*|\s+/\s+|\s*-\s*")
_DATE_TOKENS_RE = re.compile(r"\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?")


def _header_tokens(text: str) -> set[str]:   [REF:61-62]
    ...


def _nonempty_cell_count(row: tuple) -> int:   [REF:65-66]
    ...


def parse_malote_date(text: str) -> date | None:   [REF:69-97]
    ...


def split_medications(text: str) -> list[str]:   [REF:100-107]
    ...


def parse_col_spec(text: str) -> dict[int, str]:   [REF:110-127] → src/importers/matcher.py:108 match
    ...


def format_col_spec(col_map: dict[int, str]) -> str:   [REF:130-132]
    ...


def parse_malote_spec(text: str) -> dict[int, tuple[str, str]]:   [REF:135-151] → src/importers/matcher.py:108 match
    ...


def _ensure_openpyxl():   [REF:154-165]
    ...


@dataclass
class SheetAnalysis:   [REF:169-180]
    name: str
    content_columns: list[str]
    header_row: int | None
    patient_col: str | None
    med_col: str | None = None
    tipo: str | None = None
    malote_date: date | None = None

    @property
    def is_malote_tab(self) -> bool:   [REF:179-180]
        ...


@dataclass
class ImportAnalysis:   [REF:184-228]
    sheets: list[SheetAnalysis]

    @property
    def all_content_columns(self) -> list[str]:   [REF:188-194]
        ...

    @property
    def detected_patient_col(self) -> str | None:   [REF:197-201]
        ...

    @property
    def default_col_spec(self) -> str:   [REF:204-210]
        ...

    @property
    def sheet_names(self) -> list[str]:   [REF:213-214]
        ...

    @property
    def has_malote(self) -> bool:   [REF:217-219]
        ...

    @property
    def default_malote_spec(self) -> str:   [REF:222-228]
        ...


@dataclass
class MaloteRow:   [REF:232-236]
    """One patient's meds for a single process row/group in a tab."""

    patient: str
    meds: list[str]


@dataclass
class MaloteTab:   [REF:240-247]
    """Extracted data for a single malote tab (tipo)."""

    tab_index: int
    sheet_name: str
    tipo: str
    date: date | None
    rows: list[MaloteRow] = field(default_factory=list)


@dataclass
class MaloteExtraction:   [REF:251-254]
    """Result of malote extraction across tabs."""

    tabs: list[MaloteTab] = field(default_factory=list)


class ExcelImporter:   [REF:257-511]
    """Open a workbook once, analyze it, then extract names from a chosen column."""

    def __init__(self, path: str) -> None:   [REF:260-266] → src/importers/excel_importer.py:154 _ensure_openpyxl
        ...

    def close(self) -> None:   [REF:268-269]
        ...

    def analyze(self) -> ImportAnalysis:   [REF:271-274] → src/importers/excel_importer.py:276 _analyze_sheet → src/importers/excel_importer.py:184 ImportAnalysis
        ...

    def _analyze_sheet(self, ws) -> SheetAnalysis:   [REF:276-381] → src/importers/excel_importer.py:169 SheetAnalysis → src/importers/excel_importer.py:383 _find_date_in_title → src/importers/excel_importer.py:61 _header_tokens → src/importers/excel_importer.py:65 _nonempty_cell_count
        ...

    def _find_date_in_title(self, upper_text: str) -> date | None:   [REF:383-388] → src/importers/excel_importer.py:69 parse_malote_date
        ...

    def _iter_data_rows(self, ws, start_row: int, ref_cols: tuple[int, ...]):   [REF:390-405]
        ...

    def extract_names(self, col_map: dict[int, str]) -> list[str]:   [REF:407-448] → src/importers/excel_importer.py:271 analyze → src/importers/excel_importer.py:390 _iter_data_rows → src/gui/widgets/crud_list.py:244 add
        ...

    def extract_malote(   [REF:450-511] → src/importers/excel_importer.py:271 analyze → src/importers/excel_importer.py:251 MaloteExtraction → src/importers/excel_importer.py:100 split_medications
        self, spec: dict[int, tuple[str, str]]
    ) -> MaloteExtraction:
        ...
```

## src/gui/widgets/base_page.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QLineEdit,
)
from PySide6.QtCore import Qt, QItemSelectionModel
from PySide6.QtGui import QKeyEvent
from typing import Callable

if TYPE_CHECKING:
    from src.gui.main_window import MainWindow

from src.gui.widgets.toast import ToastMixin
from src.gui.widgets.buttons import make_button
from src.gui.constants import SHORTCUT_LABELS


class BasePage(QWidget, ToastMixin):   [REF:26-181]
    def __init__(self, main_window: MainWindow):   [REF:27-32]
        ...

    # Type guards: state/config are only None during MainWindow initialization,
    # before any page is instantiated.
    def _state(self):   [REF:36-38]
        ...

    def _config(self):   [REF:40-42]
        ...

    def _require_db(self):   [REF:44-46]
        ...

    def _scaffold(self, expand_vertical: bool = False) -> QVBoxLayout:   [REF:48-72]
        ...

    def register_keyboard_nav(   [REF:74-79]
        self, widget: QWidget, search: QLineEdit, on_enter: Callable
    ):
        ...

    def clear_keyboard_nav(self):   [REF:81-82]
        ...

    def _move_row(self, widget, direction):   [REF:84-102]
        ...

    def eventFilter(self, obj, event):   [REF:104-124] → src/gui/widgets/base_page.py:84 _move_row
        ...

    def set_shortcuts_visible(self, show: bool):   [REF:126-137]
        ...

    def _handle_error(self, e, context=None):   [REF:139-144]
        ...

    def _add_back_button(   [REF:146-158] → src/gui/widgets/base_page.py:194 make_hbox → src/gui/widgets/buttons.py:31 make_button
        self, layout: QVBoxLayout, target: str = "start"
    ) -> QHBoxLayout:
        ...

    def _add_export_button(self, layout: QVBoxLayout, on_export, label: str = "Exportar Planilha"):   [REF:160-167] → src/gui/widgets/buttons.py:31 make_button
        ...

    def _export_active_malote(self):   [REF:169-181] → src/export/excel_exporter.py:98 ExcelExporter → src/gui/widgets/base_page.py:216 export_with_fallback → src/state/rac_state_manager.py:26 get_active_malote
        ...


def make_tab(margins=(16, 16, 16, 16), spacing=12):   [REF:184-191]
    ...


def make_hbox(margins=(0, 0, 0, 0), spacing=8):   [REF:194-200]
    ...


def _open_file_location(path: str):   [REF:203-213]
    ...


def export_with_fallback(page, export_fn, no_data_msg="Nenhum dado para exportar"):   [REF:216-253] → src/gui/widgets/toast.py:29 show_toast → src/gui/widgets/toast.py:45 _toast
    ...
```

## src/gui/widgets/buttons.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QPushButton, QSizePolicy, QStyle, QStyleOptionButton
from PySide6.QtCore import Qt, Signal, QRect, QSize
from PySide6.QtGui import QIcon, QPainter
from pathlib import Path

from src.gui.styles import tipo_button_qss, toggle_theme, get_stylesheet, get_theme, faded_tipo_color
from src.gui.constants import TIPO_LABELS, TIPO_SYMBOLS, TIPO_HEX


def _load_material_icon(name: str, white: bool = False, color: str | None = None) -> QIcon:   [REF:13-28]
    ...


def make_button(text: str, role: str, parent=None) -> QPushButton:   [REF:31-35]
    ...


def make_icon_button(text: str, role: str, width: int = 40, font_size: int = 14) -> QPushButton:   [REF:38-42] → src/gui/widgets/buttons.py:31 make_button
    ...


class IconButtonBase(QPushButton):   [REF:45-91]
    """QPushButton with manually positioned icon (left or right) and matching text alignment.

    This guarantees consistent icon-to-edge spacing regardless of the Qt style.
    """

    def __init__(self, text: str, icon_align: str = "left", parent=None):   [REF:51-54]
        ...

    def paintEvent(self, event):   [REF:56-91] → src/gui/widgets/_completer.py:95 paint
        ...


class TipoButton(IconButtonBase):   [REF:94-117]
    clicked_tipo = Signal(str)

    def __init__(self, tipo_key: str, parent=None):   [REF:97-109] → src/gui/widgets/buttons.py:111 _apply_style → src/gui/widgets/buttons.py:51 __init__
        ...

    def _apply_style(self):   [REF:111-114] → src/gui/widgets/buttons.py:13 _load_material_icon
        ...

    def refresh_style(self):   [REF:116-117] → src/gui/widgets/buttons.py:111 _apply_style
        ...


class ThemeToggleButton(QPushButton):   [REF:120-140]
    def __init__(self, parent=None):   [REF:121-127] → src/gui/widgets/buttons.py:139 _update_icon
        ...

    def _toggle(self):   [REF:129-137] → src/gui/widgets/buttons.py:139 _update_icon → src/gui/styles.py:68 toggle_theme
        ...

    def _update_icon(self):   [REF:139-140]
        ...
```

## src/gui/widgets/import_dialog.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Importar Planilha dialog — drop one or more .xlsx files.

Two modes, as tabs:
  - Malote: detects tipo+date per tab and imports paciente/med rows as registros.
  - Pacientes: imports patient names only.
Malote mode is selected automatically when a malote structure is detected.
"""

from __future__ import annotations

from PySide6.QtCore import QThread, QTimer, Signal, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.gui.styles import colors, tab_style_qss
from src.gui.widgets.buttons import make_button
from src.importers.excel_importer import (
    ExcelImporter,
    ImportAnalysis,
    MaloteExtraction,
    parse_malote_spec,
    parse_col_spec,
)
from src.importers.matcher import MedMatcher
from src.services.malote_import_service import MaloteImportService

_DEBOUNCE_MS = 250


class _ExtractWorker(QThread):   [REF:43-55]
    result = Signal(object)

    def __init__(self, job, parent=None):   [REF:46-48]
        ...

    def run(self) -> None:   [REF:50-55]
        ...


class ImportPlanilhaDialog(QDialog):   [REF:58-486]
    def __init__(self, parent, importers: list[ExcelImporter], db, on_import):   [REF:59-101] → src/gui/widgets/import_dialog.py:105 _build_ui → src/importers/matcher.py:72 MedMatcher → src/importers/excel_importer.py:271 analyze → src/database/rac_database.py:652 get_all_pacientes
        ...

    # ========== UI ==========

    def _build_ui(self) -> None:   [REF:105-134] → src/gui/widgets/import_dialog.py:489 _button_row → src/gui/widgets/import_dialog.py:281 _build_pacientes_tab → src/gui/styles.py:77 colors → src/gui/widgets/import_dialog.py:230 _build_malote_tab
        ...

    def _no_malote_widget(self, muted: str):   [REF:136-146]
        ...

    def _file_selector_row(self, c: dict) -> tuple[QHBoxLayout, QComboBox]:   [REF:148-168] → src/gui/widgets/_completer.py:16 themed_combo
        ...

    def _make_file_aware_edit(   [REF:170-190] → src/gui/widgets/crud_list.py:181 load
        self,
        combo: QComboBox,
        specs: list[str],
        edit: QLineEdit,
    ) -> None:
        ...

    def _scrollable_tab(self) -> tuple[QWidget, QVBoxLayout]:   [REF:192-221]
        ...

    def _pin_buttons(self, tab: QWidget, actions) -> list:   [REF:223-228] → src/gui/widgets/import_dialog.py:489 _button_row
        ...

    def _build_malote_tab(self, c: dict, muted: str) -> None:   [REF:230-279] → src/gui/widgets/import_dialog.py:223 _pin_buttons → src/gui/widgets/import_dialog.py:148 _file_selector_row → src/gui/widgets/import_dialog.py:192 _scrollable_tab → src/gui/widgets/import_dialog.py:320 _schedule_malote_preview → src/gui/widgets/import_dialog.py:170 _make_file_aware_edit
        ...

    def _build_pacientes_tab(self, c: dict, muted: str) -> None:   [REF:281-316] → src/gui/widgets/import_dialog.py:170 _make_file_aware_edit → src/gui/widgets/import_dialog.py:223 _pin_buttons → src/gui/widgets/import_dialog.py:419 _schedule_pac_preview → src/gui/widgets/import_dialog.py:148 _file_selector_row → src/gui/widgets/import_dialog.py:192 _scrollable_tab
        ...

    # ========== Malote mode ==========

    def _schedule_malote_preview(self) -> None:   [REF:320-321]
        ...

    def _run_malote_extract(self) -> None:   [REF:323-343] → src/gui/widgets/import_dialog.py:43 _ExtractWorker
        ...

    def _parse_malote_specs(self) -> list[dict]:   [REF:345-347] → src/importers/excel_importer.py:135 parse_malote_spec
        ...

    def _extract_all_malotes(self) -> MaloteExtraction:   [REF:349-363] → src/importers/excel_importer.py:251 MaloteExtraction → src/importers/excel_importer.py:450 extract_malote → src/gui/widgets/import_dialog.py:345 _parse_malote_specs
        ...

    def _on_malote_done(self, ext: MaloteExtraction, generation: int) -> None:   [REF:365-415] → src/gui/widgets/crud_list.py:244 add → src/importers/matcher.py:108 match
        ...

    # ========== Pacientes mode ==========

    def _schedule_pac_preview(self) -> None:   [REF:419-420]
        ...

    def _run_pac_extract(self) -> None:   [REF:422-442] → src/gui/widgets/import_dialog.py:43 _ExtractWorker
        ...

    def _extract_all_names(self) -> list[str]:   [REF:444-455] → src/importers/excel_importer.py:110 parse_col_spec → src/importers/excel_importer.py:407 extract_names → src/gui/widgets/crud_list.py:244 add
        ...

    def _on_pac_done(self, names: list[str], generation: int) -> None:   [REF:457-466]
        ...

    # ========== Actions ==========

    def _do_malote_import(self) -> None:   [REF:470-476] → src/services/malote_import_service.py:31 MaloteImportService → src/services/malote_import_service.py:36 import_tabs
        ...

    def _do_pac_import(self) -> None:   [REF:478-481]
        ...

    def closeEvent(self, event):   [REF:483-486]
        ...


def _button_row(actions: list[tuple[str, str]]):   [REF:489-495] → src/gui/widgets/buttons.py:31 make_button
    ...
```

## src/services/registro_service.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.database.rac_database import RACDatabase
from src.models import Registro, RegistroItem, RegistroExport
from src.services.exceptions import ValidationError, DuplicateRecordError
from src.utils.date_calculator import calculate_return_dates

import sqlite3


@dataclass
class SaveResult:   [REF:18-20]
    registro_id: int
    is_update: bool


@dataclass
class EditContext:   [REF:24-27]
    registro: Registro
    items: list[tuple[int, int, str, int]]
    processes: list[tuple[int, int]]


@dataclass
class ContextResult:   [REF:31-35]
    registro: Registro | None
    items: list[tuple[int, int, str, int]]
    processes: list[tuple[int, int]]
    suggested_items: list[tuple[int, int, str, int]]


@dataclass
class DeleteSnapshot:   [REF:39-45]
    tipo: str
    paciente_id: int
    malote_id: int
    waiting_docs: bool
    items: list[tuple[int, int, str, int]]
    process_months: list[tuple[int, int]]


class RegistroService:   [REF:48-351]
    def __init__(self, db: RACDatabase) -> None:   [REF:49-50]
        ...

    def get(self, registro_id: int) -> Registro | None:   [REF:52-53] → src/database/rac_database.py:321 get_registro_by_id
        ...

    def get_items(self, registro_id: int) -> list[RegistroItem]:   [REF:55-56] → src/database/rac_database.py:479 get_items_by_registro
        ...

    def get_by_paciente(self, paciente_id: int) -> list[Registro]:   [REF:58-59] → src/database/rac_database.py:430 get_registros_by_paciente
        ...

    def search_by_paciente(   [REF:61-64] → src/database/rac_database.py:411 search_registros_by_paciente
        self, query: str, malote_id: int | None = None, limit: int = 20
    ) -> list[Registro]:
        ...

    def get_with_items_by_malote(self, malote_id: int) -> list[RegistroExport]:   [REF:66-67] → src/database/rac_database.py:692 get_registros_with_items_by_malote
        ...

    def get_by_malote(self, malote_id: int) -> list[Registro]:   [REF:69-70] → src/database/rac_database.py:348 get_registros_by_malote
        ...

    def update(   [REF:72-95] → src/database/rac_database.py:444 set_registro_items → src/services/registro_service.py:102 _save_processes → src/services/registro_service.py:18 SaveResult → src/services/exceptions.py:13 ValidationError → src/database/rac_database.py:372 update_registro
        self,
        id: int,
        tipo: str,
        paciente_id: int,
        malote_id: int,
        items: list[tuple[int, int, str, int]],
        waiting_docs: bool,
        process_months: list[tuple[int, int]] | None = None,
    ) -> SaveResult:
        ...

    def _resolve_arrival_date(self, malote_id: int) -> date | None:   [REF:97-100] → src/database/rac_database.py:185 get_malote_by_id → src/utils/date_calculator.py:81 resolve_arrival_from_malote
        ...

    def _save_processes(   [REF:102-135] → src/database/rac_database.py:460 set_registro_items_with_process → src/database/rac_database.py:479 get_items_by_registro → src/services/registro_service.py:97 _resolve_arrival_date → src/database/rac_database.py:524 set_processes → src/utils/date_calculator.py:130 calculate_return_dates
        self,
        registro_id: int,
        tipo: str,
        malote_id: int,
        waiting_docs: bool,
        process_months: list[tuple[int, int]],
        items: list[tuple[int, int, str, int]] | None = None,
    ) -> None:
        ...

    def save(   [REF:137-200] → src/services/exceptions.py:9 DuplicateRecordError → src/services/registro_service.py:102 _save_processes → src/database/rac_database.py:444 set_registro_items → src/database/rac_database.py:241 find_paciente_by_name → src/services/registro_service.py:18 SaveResult → src/database/rac_database.py:230 create_paciente → src/services/exceptions.py:13 ValidationError → src/database/rac_database.py:333 find_registro → src/database/rac_database.py:294 create_registro
        self,
        tipo: str,
        paciente_name: str,
        malote_id: int,
        items: list[tuple[int, int, str, int]],
        edit_id: int | None = None,
        waiting_docs: bool = False,
        paciente_id: int | None = None,
        process_months: list[tuple[int, int]] | None = None,
    ) -> SaveResult:
        ...

    def delete(self, registro_id: int) -> None:   [REF:202-207] → src/services/exceptions.py:13 ValidationError → src/database/rac_database.py:404 delete_registro
        ...

    def load_for_edit(self, registro_id: int) -> EditContext | None:   [REF:209-226] → src/database/rac_database.py:555 get_processes_by_registro → src/database/rac_database.py:321 get_registro_by_id → src/services/registro_service.py:24 EditContext → src/database/rac_database.py:479 get_items_by_registro
        ...

    def load_for_context(   [REF:228-265] → src/services/registro_service.py:31 ContextResult → src/database/rac_database.py:479 get_items_by_registro → src/database/rac_database.py:555 get_processes_by_registro → src/database/rac_database.py:502 get_last_usage_by_paciente → src/database/rac_database.py:333 find_registro
        self, tipo: str, paciente_id: int, malote_id: int | None
    ) -> ContextResult:
        ...

    def change_tipo(self, registro_id: int, new_tipo: str) -> None:   [REF:267-282] → src/database/rac_database.py:479 get_items_by_registro → src/database/rac_database.py:321 get_registro_by_id → src/database/rac_database.py:555 get_processes_by_registro → src/services/exceptions.py:13 ValidationError
        ...

    def change_tipos(self, reg_ids: list[int], new_tipo: str) -> int:   [REF:284-296] → src/services/registro_service.py:267 change_tipo
        ...

    def move_to_malote(   [REF:298-320] → src/database/rac_database.py:479 get_items_by_registro → src/database/rac_database.py:555 get_processes_by_registro → src/database/rac_database.py:321 get_registro_by_id
        self, registro_ids: list[int], new_malote_id: int
    ) -> int:
        ...

    def delete_with_snapshot(self, registro_id: int) -> DeleteSnapshot | None:   [REF:322-339] → src/database/rac_database.py:479 get_items_by_registro → src/database/rac_database.py:555 get_processes_by_registro → src/database/rac_database.py:321 get_registro_by_id → src/services/registro_service.py:39 DeleteSnapshot → src/services/registro_service.py:202 delete
        ...

    def restore_from_snapshot(self, snapshot: DeleteSnapshot) -> int:   [REF:341-351] → src/services/registro_service.py:137 save
        ...
```

## src/gui/pages/start_page.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start Page — malote header, search, tipo buttons, export
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from contextlib import suppress

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QFrame,
    QLabel,
    QWidget,
)
from PySide6.QtCore import Qt

if TYPE_CHECKING:
    from src.gui.main_window import MainWindow

from andaime.widgets import SearchableComboBox
from src.gui.brasao import get_brasao_pixmap, get_rac_pixmap
from src.gui.widgets import (
    TipoButton,
    IconButtonBase,
    make_hbox,
    MaloteLabel,
    ThemeToggleButton,
    BasePage,
    export_with_fallback,
    confirm_past_malote,
    _load_material_icon,
)
from src.gui.constants import (
    TIPO_LABELS,
    TIPO_HEX,
    SHORTCUT_LABELS,
    TIPO_SHORTCUT_KEYS,
    TIPO_SYMBOLS,
    RIGHT_BUTTON_SYMBOLS,
)

from src.export.excel_exporter import ExcelExporter
from src.models import Malote
from src.utils.text_utils import format_malote_date, is_malote_past
from src.gui.styles import get_theme


from src import __version__


class StartPage(BasePage):   [REF:56-410]
    # Constants for easier customization
    BRASAO_HEIGHT = 42
    RAC_HEIGHT = 42
    SUBTITLE_FONT_SIZE = "10pt"
    USAFA_FONT_SIZE = "9pt"
    RAC_SPACING = 8
    SUBTITLE_SPACING = 8
    BRASAO_SPACING = 8
    
    def __init__(self, main_window: MainWindow):   [REF:66-74] → src/gui/widgets/base_page.py:27 __init__ → src/gui/pages/start_page.py:76 _build_ui
        ...

    def _build_ui(self):   [REF:76-96] → src/gui/pages/start_page.py:122 _build_brasao → src/gui/pages/start_page.py:174 _build_columns → src/gui/pages/start_page.py:98 _build_malote_header → src/gui/pages/start_page.py:112 _build_search
        ...

    def _build_malote_header(self, layout: QVBoxLayout):   [REF:98-110] → src/gui/widgets/base_page.py:194 make_hbox → src/gui/widgets/malote.py:34 MaloteLabel → src/gui/widgets/buttons.py:120 ThemeToggleButton
        ...

    def _build_search(self, layout: QVBoxLayout):   [REF:112-120]
        ...

    def _build_brasao(self, layout: QVBoxLayout):   [REF:122-149] → src/gui/pages/start_page.py:151 _build_subtitles → src/gui/pages/start_page.py:359 _update_brasao
        ...
    
    def _build_subtitles(self, layout: QVBoxLayout):   [REF:151-172] → src/gui/pages/start_page.py:393 _on_usafa_click
        ...

    def _build_columns(self, layout: QVBoxLayout):   [REF:174-246] → src/gui/widgets/buttons.py:13 _load_material_icon → src/gui/widgets/buttons.py:94 TipoButton → src/gui/widgets/buttons.py:45 IconButtonBase → src/gui/styles.py:90 faded_tipo_color
        ...

    def refresh(self):   [REF:248-253] → src/state/rac_state_manager.py:30 set_active_malote
        ...

    def _search_registros(self, query: str) -> dict[str, str]:   [REF:255-266] → src/utils/text_utils.py:13 format_malote_date → src/state/rac_state_manager.py:26 get_active_malote
        ...

    def _on_search_select(self, data):   [REF:268-276] → src/state/rac_state_manager.py:26 get_active_malote
        ...
    
    def _require_malote(self) -> bool:   [REF:278-282] → src/state/rac_state_manager.py:34 has_active_malote
        ...
    
    def _on_tipo_click(self, tipo_key: str):   [REF:284-293] → src/state/rac_state_manager.py:26 get_active_malote → src/utils/text_utils.py:23 is_malote_past → src/gui/widgets/dialogs.py:224 confirm_past_malote → src/gui/pages/start_page.py:278 _require_malote
        ...

    def _on_preview(self):   [REF:295-298] → src/gui/pages/start_page.py:278 _require_malote
        ...

    def _on_export(self):   [REF:300-311] → src/export/excel_exporter.py:98 ExcelExporter → src/gui/pages/start_page.py:278 _require_malote → src/gui/widgets/base_page.py:216 export_with_fallback → src/state/rac_state_manager.py:26 get_active_malote
        ...

    def _on_medicamentos(self):   [REF:313-314]
        ...

    def _on_pacientes(self):   [REF:316-317]
        ...

    def _on_stats(self):   [REF:319-320]
        ...

    @staticmethod
    def _flat_btn_style(c: dict, align: str, color: str | None = None) -> str:   [REF:323-333]
        ...

    def _on_theme_changed(self):   [REF:335-357] → src/gui/widgets/buttons.py:13 _load_material_icon → src/gui/styles.py:64 get_theme → src/gui/pages/start_page.py:359 _update_brasao → src/gui/styles.py:90 faded_tipo_color
        ...

    def _update_brasao(self):   [REF:359-377] → src/gui/brasao.py:65 get_rac_pixmap → src/gui/brasao.py:60 get_brasao_pixmap → src/gui/pages/start_page.py:379 _update_subtitle_colors
        ...
    
    def _update_subtitle_colors(self):   [REF:379-391]
        ...
    
    def _on_usafa_click(self, event):   [REF:393-399] → main.py:29 _show_usafa_dialog
        ...

    def set_shortcuts_visible(self, show: bool):   [REF:401-410] → src/gui/widgets/base_page.py:126 set_shortcuts_visible
        ...
```

## src/gui/widgets/dialogs.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QDialog,
    QPushButton,
)
from typing import Callable, Optional

from src.gui.widgets.buttons import make_button
from src.gui.widgets.labels import HeadingLabel
from src.gui.widgets._completer import themed_combo
from src.gui.styles import colors
from src.gui.widgets.toast import show_toast
from src.services.registro_service import RegistroService
from src.models import Malote
from src.utils.text_utils import format_malote_date
from andaime.error_handler import ErrorContext, ErrorHandler


def scaffold_dialog(parent, title, spacing=12, min_width=340):   [REF:27-34]
    ...


def make_dialog_button_row(actions: list[tuple[str, str]]) -> tuple[QHBoxLayout, list[QPushButton]]:   [REF:37-45] → src/gui/widgets/buttons.py:31 make_button
    ...


def confirm_delete_dialog(   [REF:48-71] → src/gui/styles.py:77 colors → src/gui/widgets/dialogs.py:37 make_dialog_button_row → src/gui/widgets/dialogs.py:27 scaffold_dialog
    parent: QWidget,
    title: str,
    message: str,
    destructive_label: str = "Excluir",
) -> bool:
    ...


def open_select_dialog(   [REF:74-103] → src/gui/widgets/_completer.py:16 themed_combo → src/gui/widgets/dialogs.py:37 make_dialog_button_row → src/gui/widgets/dialogs.py:27 scaffold_dialog
    parent: QWidget,
    title: str,
    placeholder: str,
    options: list[str],
    initial: str | None = None,
    confirm_label: str = "Confirmar",
) -> str | None:
    ...


def open_input_dialog(   [REF:106-135] → src/gui/widgets/dialogs.py:37 make_dialog_button_row → src/gui/widgets/dialogs.py:27 scaffold_dialog
    parent: QWidget,
    title: str,
    placeholder: str,
    initial: str = "",
    confirm_label: str = "Confirmar",
) -> str | None:
    ...


def open_estoque_dialog(   [REF:138-221] → src/gui/widgets/dialogs.py:27 scaffold_dialog → src/gui/widgets/dialogs.py:37 make_dialog_button_row
    parent: QWidget,
    title: str,
    initial_value: int,
) -> int | None:
    ...


def confirm_past_malote(   [REF:224-259] → src/gui/styles.py:77 colors → src/gui/widgets/dialogs.py:37 make_dialog_button_row → src/gui/widgets/dialogs.py:27 scaffold_dialog
    parent: QWidget,
    malote: Malote,
    on_change: Optional[Callable[[], None]] = None,
) -> bool:
    ...


def delete_registro_with_undo(page, db, reg_id: int, on_refresh, on_error=None):   [REF:262-278] → src/gui/widgets/toast.py:29 show_toast → src/gui/widgets/dialogs.py:48 confirm_delete_dialog → src/services/registro_service.py:48 RegistroService
    ...
```

## src/gui/pages/stats_page.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QSizePolicy,
    QHeaderView,
    QTreeWidgetItem,
    QLineEdit,
)
from datetime import datetime

if TYPE_CHECKING:
    from src.gui.main_window import MainWindow

from PySide6.QtCore import Qt, QTimer

from src.gui.widgets import (
    make_button,
    BasePage,
    SortableTableWidgetItem,
    make_dialog_button_row,
    export_with_fallback,
)
from src.gui.widgets.dialogs import scaffold_dialog
from src.gui.widgets._malote_tree import (
    make_malote_tree,
    populate_malote_tree,
    wire_tree_keyboard,
)
from src.gui.constants import TIPO_LABELS, TIPO_HEX
from src.gui.styles import colors, filter_table_rows, data_view_style_qss, faded_tipo_color
from src.export.excel_exporter import ExcelExporter
from andaime.qt.table import table_batch_populate

_CANCELLED = object()


class _TipoCard(QWidget):   [REF:46-87]
    def __init__(self, tipo_key: str, value: str, label: str | None = None, label_color: str | None = None):   [REF:47-75] → src/gui/styles.py:77 colors
        ...

    def set_value(self, value: str):   [REF:77-78]
        ...

    def set_on_click(self, callback):   [REF:80-82]
        ...

    def mouseReleaseEvent(self, event):   [REF:84-87]
        ...


class StatsPage(BasePage):   [REF:90-338]
    def __init__(self, main_window: MainWindow):   [REF:91-96] → src/gui/widgets/base_page.py:27 __init__ → src/gui/pages/stats_page.py:98 _build_ui → src/gui/pages/stats_page.py:261 _load_stats
        ...

    def _build_ui(self):   [REF:98-112] → src/gui/pages/stats_page.py:114 _build_header → src/gui/pages/stats_page.py:226 _build_medications_table → src/gui/widgets/buttons.py:31 make_button → src/gui/pages/stats_page.py:180 _build_tipo_cards
        ...

    def _build_header(self, layout: QVBoxLayout):   [REF:114-150] → src/gui/styles.py:77 colors → src/gui/widgets/buttons.py:31 make_button
        ...

    def _pick_date(self, side: str):   [REF:152-166] → src/gui/pages/stats_page.py:261 _load_stats → src/gui/pages/stats_page.py:348 _show_date_picker → src/gui/pages/stats_page.py:168 _update_date_buttons
        ...

    def _update_date_buttons(self):   [REF:168-178]
        ...

    def _build_tipo_cards(self, layout: QVBoxLayout):   [REF:180-207] → src/gui/pages/stats_page.py:80 set_on_click → src/gui/pages/stats_page.py:46 _TipoCard
        ...

    def _open_tipo_list(self, tipo_key: str):   [REF:209-216]
        ...

    def _open_all_registros(self):   [REF:218-224]
        ...

    def _build_medications_table(self, layout: QVBoxLayout):   [REF:226-259]
        ...

    def _load_stats(self):   [REF:261-279] → src/database/rac_database.py:768 get_stats_by_tipo → src/database/rac_database.py:798 get_stats_totals → src/gui/pages/stats_page.py:281 _fill_meds_table → src/database/rac_database.py:825 get_stats_top_itens
        ...

    def _fill_meds_table(self, rows: list[dict]):   [REF:281-301] → src/gui/widgets/crud_list.py:31 SortableTableWidgetItem
        ...

    def _filter_meds_table(self, text: str):   [REF:303-304] → src/gui/styles.py:576 filter_table_rows
        ...

    def _on_med_double_clicked(self, row: int, _col: int):   [REF:306-314]
        ...

    def _on_med_enter(self):   [REF:316-319] → src/gui/pages/stats_page.py:306 _on_med_double_clicked
        ...

    def _open_item_list(self, item_id: int, item_name: str):   [REF:321-329]
        ...

    def _on_export(self):   [REF:331-338] → src/export/excel_exporter.py:98 ExcelExporter → src/gui/widgets/base_page.py:216 export_with_fallback
        ...






_RESET_SENTINEL = object()


def _show_date_picker(parent_page: StatsPage, side: str) -> object:   [REF:348-396] → src/gui/widgets/_malote_tree.py:117 wire_tree_keyboard → src/gui/widgets/dialogs.py:27 scaffold_dialog → src/gui/widgets/_malote_tree.py:102 make_malote_tree → src/gui/widgets/dialogs.py:37 make_dialog_button_row → src/gui/widgets/_malote_tree.py:15 populate_malote_tree
    ...
```

## src/importers/matcher.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medication matching — maps free-text med names from imported sheets to the
app's items_catalog. Pure logic, no DB/Qt: fed by a list of (name, id) pairs.
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Iterable

_CANON_RE = re.compile(r"[^a-z0-9]+")
_PAREN_RE = re.compile(r"\(([^)]+)\)")
_DOSE_RE = re.compile(r"\d+(?:[.,]\d*)?")


def _canon(text: str) -> str:   [REF:20-24]
    ...


def _letters(text: str) -> str:   [REF:27-29]
    ...


def _dose_tokens(text: str) -> frozenset[str]:   [REF:32-34]
    ...


# Active-ingredient abbreviations / common typos seen in real sheets.
# Keys stored lowercase to match canonical sheet letters.
_INGREDIENT_ALIASES: dict[str, str] = {
    "ator": "ATORVASTATINA",
    "ciclosp": "CICLOSPORINA",
    "ciclocsp": "CICLOSPORINA",
    "micof": "MICOFENOLATO",
    "micofmofetila": "MICOFENOLATODEMOFETILA",
    "micofenolatomofetila": "MICOFENOLATODEMOFETILA",
"mesal": "MESALAZINA",
    "mes": "MESALAZINA",
    "shf": "sacarato de hidroxido ferrico 100 mg inj.",
    "ciclopsorina": "CICLOSPORINA",
    "azatiopriona": "AZATIOPRINA",
    "dapaglifloizina": "DAPAGLIFLOZINA",
    "dapgliflozina": "DAPAGLIFLOZINA",
    "etn": "ETANERCEPTE",
    "tac": "TACROLIMO",
    "micofenolatosodio": "MICOFENOLATODESODIO",
    "fludrocortisona": "FLUDROCORTISONA",
    "kit": "kit infusao infliximabe",
}

# Special whole-name phrases -> specific catalog items. Keys lowercase.
_PHRASE_ALIASES: dict[str, str] = {
    "insulinaglargina": "insulina analoga de acao prolongada 100 ui/ml",
    "insulinalispro": "insulina analoga de acao rapida 100 ui/ml",
}

# Form words that hint at a liquid/solution catalog form.
LIQUID_HINTS = ("ML", "SOL", "SOLUCAO", "GOTAS", "XAROPE", "SPRAY", "NASAL")
# Form words that hint at a solid form.
SOLID_HINTS = ("CAP", "COMP", "COMPRIMIDO", "POMADA", "CREME", "SACHE", "CPSULA")


class MedMatcher:   [REF:72-279]
    """Match sheet med names to catalog items by id."""

    def __init__(self, catalog: Iterable[tuple[str, int]]) -> None:   [REF:75-94] → src/importers/matcher.py:27 _letters → src/importers/matcher.py:20 _canon
        ...

    def _candidates_by_letters(self, sheet_letters: str) -> list[int]:   [REF:96-106] → src/gui/widgets/crud_list.py:244 add
        ...

    def match(self, sheet_name: str) -> tuple[int | None, str | None]:   [REF:108-173] → src/importers/matcher.py:27 _letters → src/importers/matcher.py:275 _name_of → src/importers/matcher.py:263 _fuzzy_best → src/importers/matcher.py:96 _candidates_by_letters → src/importers/matcher.py:187 _pick_brand_candidate → src/importers/matcher.py:252 _strip_dose_form → src/importers/matcher.py:211 _pick_best_for_candidates → src/importers/matcher.py:175 _try_aliased → src/importers/matcher.py:20 _canon → src/importers/matcher.py:32 _dose_tokens
        ...

    def _try_aliased(   [REF:175-185] → src/importers/matcher.py:96 _candidates_by_letters → src/importers/matcher.py:20 _canon → src/importers/matcher.py:211 _pick_best_for_candidates
        self,
        aliased: str,
        sheet_doses: frozenset[str],
        sheet_name: str,
    ) -> int | None:
        ...

    def _pick_brand_candidate(   [REF:187-209] → src/importers/matcher.py:32 _dose_tokens
        self,
        candidates: list[int],
        sheet_doses: frozenset[str],
    ) -> int | None:
        ...

    def _pick_best_for_candidates(   [REF:211-250] → src/importers/matcher.py:27 _letters → src/importers/matcher.py:275 _name_of → src/importers/matcher.py:20 _canon → src/importers/matcher.py:32 _dose_tokens
        self,
        candidates: list[int],
        sheet_name: str,
        sheet_doses: frozenset[str],
        min_ratio: float = 0.5,
    ) -> int | None:
        ...

    def _strip_dose_form(self, name: str) -> str:   [REF:252-261]
        ...

    def _fuzzy_best(   [REF:263-273] → src/importers/matcher.py:211 _pick_best_for_candidates
        self,
        query: str,
        candidates: list[int] | None = None,
        sheet_doses: frozenset[str] | None = None,
        min_ratio: float = 0.55,
    ) -> int | None:
        ...

    def _name_of(self, cid: int) -> str:   [REF:275-279]
        ...
```

## src/gui/pages/preview_page.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Preview Page — tabbed table view of malote registros
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QHeaderView,
    QMenu,
)
from PySide6.QtCore import Qt

if TYPE_CHECKING:
    from src.gui.main_window import MainWindow

from src.gui.widgets import (
    MaloteLabel,
    BasePage,
    make_button,
    open_input_dialog,
    delete_registro_with_undo,
    confirm_delete_dialog,
    make_tab,
)
from src.gui.constants import TIPO_HEX, TIPO_LABELS
from src.gui.styles import faded_tipo_color, tab_style_qss, filter_table_rows, data_view_style_qss

from src.utils.text_utils import format_malote_date, format_item
from src.services.exceptions import DuplicateRecordError
from src.services.registro_service import DeleteSnapshot
from andaime.qt.table import table_batch_populate


class PreviewPage(BasePage):   [REF:43-401]
    def __init__(self, main_window: MainWindow):   [REF:44-46] → src/gui/widgets/base_page.py:27 __init__ → src/gui/pages/preview_page.py:48 _build_ui
        ...

    def _build_ui(self):   [REF:48-54] → src/gui/pages/preview_page.py:56 _build_header → src/gui/pages/preview_page.py:63 _build_tabs
        ...

    def _build_header(self, layout: QVBoxLayout):   [REF:56-61] → src/gui/widgets/malote.py:34 MaloteLabel
        ...

    def _build_tabs(self, layout: QVBoxLayout, insert_index: int | None = None):   [REF:63-175] → src/gui/widgets/base_page.py:184 make_tab → src/gui/pages/preview_page.py:177 _on_tab_changed → src/utils/text_utils.py:50 format_item → src/gui/widgets/buttons.py:31 make_button → src/state/rac_state_manager.py:26 get_active_malote
        ...

    def _on_tab_changed(self, idx):   [REF:177-181]
        ...

    def refresh(self):   [REF:183-208] → src/gui/pages/preview_page.py:63 _build_tabs
        ...

    def _on_row_double_clicked(self, table: QTableWidget, row: int):   [REF:210-221]
        ...

    def _on_enter(self, table: QTableWidget):   [REF:223-226] → src/gui/pages/preview_page.py:210 _on_row_double_clicked
        ...

    def _get_selected_ids(self, table: QTableWidget) -> list[int]:   [REF:228-236]
        ...

    def _show_row_menu(self, table: QTableWidget, current_tipo: str, pos):   [REF:238-304] → src/gui/pages/preview_page.py:228 _get_selected_ids → src/state/rac_state_manager.py:26 get_active_malote → src/utils/text_utils.py:13 format_malote_date
        ...

    def _change_tipo(self, reg_ids: list[int], new_tipo: str):   [REF:306-322] → src/services/registro_service.py:267 change_tipo → src/gui/pages/preview_page.py:183 refresh
        ...

    def _move_to_malote(self, reg_ids: list[int], new_malote_id: int):   [REF:324-335] → src/gui/pages/preview_page.py:183 refresh → src/services/registro_service.py:298 move_to_malote
        ...

    def _edit_paciente_name(self, reg_id: int):   [REF:337-354] → src/gui/widgets/dialogs.py:106 open_input_dialog → src/gui/pages/preview_page.py:183 refresh
        ...

    def _confirm_delete(self, reg_ids: list[int]):   [REF:356-392] → src/gui/widgets/dialogs.py:48 confirm_delete_dialog → src/services/registro_service.py:322 delete_with_snapshot → src/gui/pages/preview_page.py:183 refresh → src/gui/widgets/dialogs.py:262 delete_registro_with_undo
        ...

    def _view_patient(self, reg_id: int):   [REF:394-397]
        ...

    def set_shortcuts_visible(self, show: bool):   [REF:399-401] → src/gui/widgets/base_page.py:126 set_shortcuts_visible
        ...
```

## src/gui/widgets/_completer.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QComboBox,
    QWidget,
    QStyledItemDelegate,
)
from PySide6.QtGui import QPainter, QFontMetrics, QColor
from PySide6.QtWidgets import QStyleOptionViewItem, QStyle
from PySide6.QtCore import Qt, QRect, QSize

from src.gui.styles import colors


def themed_combo() -> "_ThemedPopupComboBox":   [REF:16-25] → src/gui/widgets/_completer.py:33 _ThemedPopupComboBox → src/gui/styles.py:77 colors
    ...


class _NoScrollComboBox(QComboBox):   [REF:28-30]
    def wheelEvent(self, event):   [REF:29-30]
        ...


class _ThemedPopupComboBox(_NoScrollComboBox):   [REF:33-43]
    """QComboBox whose popup gets the app's themed background/selection look."""

    _popup_bg: str = ""

    def showPopup(self):   [REF:38-43] → src/gui/styles.py:77 colors
        ...


class _CenteredComboBox(_ThemedPopupComboBox):   [REF:46-81]
    _hide_current: bool = False

    def setHideCurrentItem(self, hide: bool):   [REF:49-50]
        ...

    def showPopup(self):   [REF:52-56] → src/gui/widgets/_completer.py:38 showPopup
        ...

    def paintEvent(self, event):   [REF:58-81] → src/gui/widgets/_completer.py:95 paint
        ...


class _BaseComboDelegate(QStyledItemDelegate):   [REF:84-121]
    align = Qt.AlignmentFlag.AlignCenter
    padding_left: int = 0

    def _pen_color_unselected(self, option: QStyleOptionViewItem, index) -> QColor:   [REF:88-89]
        ...

    def _selected_fill_and_pen(self, option: QStyleOptionViewItem):   [REF:91-93] → src/gui/styles.py:77 colors
        ...

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):   [REF:95-121] → src/services/registro_service.py:137 save → src/gui/widgets/_completer.py:91 _selected_fill_and_pen
        ...


class _ThemedComboDelegate(_BaseComboDelegate):   [REF:124-126]
    def _pen_color_unselected(self, option, index):   [REF:125-126]
        ...


class _LeftComboDelegate(_ThemedComboDelegate):   [REF:129-137]
    """Left-aligned themed rows, ~2px shorter for native popup feel."""

    align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
    padding_left = 10

    def sizeHint(self, option, index):   [REF:135-137]
        ...
```

## src/gui/pages/patient_page.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMenu,
)
from PySide6.QtCore import Qt

if TYPE_CHECKING:
    from src.gui.main_window import MainWindow

from src.gui.widgets import (
    TipoButton,
    BasePage,
    delete_registro_with_undo,
    open_input_dialog,
    make_button,
    make_hbox,
)
from src.gui.constants import TIPO_LABELS, TIPO_HEX
from src.gui.styles import (
    colors,
    data_view_style_qss,
    faded_tipo_color,
)
from src.utils.text_utils import format_malote_date, format_registro_meds
from src.models import Malote
from andaime.qt.table import table_batch_populate


def _remove_layout_item(item):   [REF:39-48]
    ...


class PatientPage(BasePage):   [REF:51-305]
    def __init__(self, main_window: MainWindow, paciente_id: int, highlight_registro: int | None = None, return_to: str = "start"):   [REF:52-57] → src/gui/widgets/base_page.py:27 __init__ → src/gui/pages/patient_page.py:59 _build_ui
        ...

    def _build_ui(self):   [REF:59-65] → src/gui/pages/patient_page.py:67 _build_header → src/gui/pages/patient_page.py:89 _build_table → src/gui/pages/patient_page.py:170 _build_tipo_buttons
        ...

    def _build_header(self, layout: QVBoxLayout):   [REF:67-87] → src/gui/widgets/base_page.py:194 make_hbox → src/gui/styles.py:77 colors → src/gui/widgets/buttons.py:31 make_button
        ...

    def _build_table(self, layout: QVBoxLayout):   [REF:89-168] → src/utils/text_utils.py:32 format_registro_meds → src/utils/text_utils.py:13 format_malote_date
        ...

    def _build_tipo_buttons(self, layout: QVBoxLayout):   [REF:170-197] → src/gui/widgets/labels.py:24 SectionLabel → src/gui/widgets/buttons.py:94 TipoButton → src/gui/styles.py:77 colors → src/gui/styles.py:90 faded_tipo_color
        ...

    def refresh(self):   [REF:199-213] → src/gui/pages/patient_page.py:215 _container_layout → src/gui/pages/patient_page.py:67 _build_header → src/gui/pages/patient_page.py:89 _build_table → src/gui/pages/patient_page.py:170 _build_tipo_buttons → src/gui/pages/patient_page.py:39 _remove_layout_item
        ...

    def _container_layout(self) -> QVBoxLayout | None:   [REF:215-228]
        ...

    def _get_reg_id(self, row: int) -> int | None:   [REF:230-234]
        ...

    def _on_row_double_clicked(self, row: int, _col: int):   [REF:236-245] → src/gui/pages/patient_page.py:230 _get_reg_id
        ...

    def _show_row_menu(self, pos):   [REF:247-266] → src/gui/pages/patient_page.py:230 _get_reg_id
        ...

    def _edit_registro(self, reg_id: int):   [REF:268-274]
        ...

    def _delete_registro(self, reg_id: int):   [REF:276-277] → src/gui/widgets/dialogs.py:262 delete_registro_with_undo
        ...

    def _on_new_registro(self, tipo: str):   [REF:279-286] → src/state/rac_state_manager.py:34 has_active_malote
        ...

    def _edit_name(self):   [REF:288-302] → src/gui/widgets/dialogs.py:106 open_input_dialog → src/gui/pages/patient_page.py:199 refresh
        ...

    def set_shortcuts_visible(self, show: bool):   [REF:304-305] → src/gui/widgets/base_page.py:126 set_shortcuts_visible
        ...
```

## src/utils/date_calculator.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC-specific malote date calculations.

Send:  next Monday, adjusted backwards for holidays/weekends.
Arrival:  Thursday of the week following the original Monday,
          adjusted forward for holidays/weekends.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING

from src.constants import TIPOS_WITH_MONTHS

from andaime.dates import DateCalculator

if TYPE_CHECKING:
    from src.database.rac_database import RACDatabase


def calculate_send_date(from_date: date) -> date:   [REF:25-30]
    ...


def calculate_arrival_date(send_date: date) -> date:   [REF:33-39]
    ...


def next_send_date(existing_dates: set[date] | None = None) -> date:   [REF:42-58] → src/utils/date_calculator.py:25 calculate_send_date
    ...


@dataclass
class ProcessReturnInfo:   [REF:62-65]
    group_number: int
    months_supply: int
    expected_return_date: date | None


def get_candidate_days_after_arrival(arrival: date) -> list[date]:   [REF:68-78]
    ...


def resolve_arrival_from_malote(malote) -> date | None:   [REF:81-92] → src/utils/date_calculator.py:33 calculate_arrival_date
    ...


def _spread_across_candidates(   [REF:95-122] → src/database/rac_database.py:583 count_return_dates_between
    groups: list[int],
    candidates: list[date],
    *,
    db: RACDatabase | None = None,
) -> dict[int, date]:
    ...


def _theoretical_arrival_near(target: date) -> date:   [REF:125-127] → src/utils/date_calculator.py:33 calculate_arrival_date → src/utils/date_calculator.py:25 calculate_send_date
    ...


def calculate_return_dates(   [REF:130-177] → src/utils/date_calculator.py:62 ProcessReturnInfo → src/utils/date_calculator.py:68 get_candidate_days_after_arrival → src/utils/date_calculator.py:250 _calculate_retirada_returns → src/utils/date_calculator.py:95 _spread_across_candidates → src/utils/date_calculator.py:81 resolve_arrival_from_malote → src/database/rac_database.py:595 get_earlier_malote
    tipo: str,
    arrival_date: date | None,
    process_groups: list[tuple[int, int]],
    *,
    db: RACDatabase | None = None,
    current_malote_id: int | None = None,
    waiting_docs: bool = False,
) -> list[ProcessReturnInfo]:
    ...


def _next_malote_arrival_after(d: date) -> date:   [REF:180-187] → src/utils/date_calculator.py:33 calculate_arrival_date → src/utils/date_calculator.py:25 calculate_send_date
    ...


def _get_malote_arrivals_near(   [REF:190-222] → src/utils/date_calculator.py:180 _next_malote_arrival_after → src/database/rac_database.py:562 get_malote_arrivals_between → src/gui/widgets/crud_list.py:244 add
    runs_out: date,
    *,
    db: RACDatabase | None = None,
) -> list[date]:
    ...


def find_nearest_arrival_after(   [REF:225-247] → src/utils/date_calculator.py:190 _get_malote_arrivals_near → src/database/rac_database.py:583 count_return_dates_between
    runs_out: date,
    *,
    db: RACDatabase | None = None,
    top: int = 4,
) -> list[tuple[date, int]]:
    ...


def _calculate_retirada_returns(   [REF:250-274] → src/utils/date_calculator.py:68 get_candidate_days_after_arrival → src/utils/date_calculator.py:62 ProcessReturnInfo → src/utils/date_calculator.py:95 _spread_across_candidates → src/utils/date_calculator.py:225 find_nearest_arrival_after → src/utils/date_calculator.py:125 _theoretical_arrival_near
    process_groups: list[tuple[int, int]],
    current_arrival: date,
    *,
    db: RACDatabase | None = None,
) -> list[ProcessReturnInfo]:
    ...
```

## src/export/excel_exporter.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel Exporter
Generates .xlsx spreadsheet from malote registros
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional
from datetime import datetime
from pathlib import Path

from andaime.error_handler import ErrorHandler, ErrorContext, ErrorLevel

from src.constants import TIPO_LABELS, TIPO_TITLES
from src.utils.text_utils import format_item

if TYPE_CHECKING:
    from src.database.rac_database import RACDatabase


class SavePathError(Exception):   [REF:24-25]
    pass


def _ensure_openpyxl():   [REF:28-39]
    ...


def _make_excel_styles():   [REF:42-62]
    ...


def _apply_page_setup(ws):   [REF:65-74]
    ...


def _style_title_row(ws, row_num, styles, font_key="title1_font", height=30, fill=None):   [REF:77-84]
    ...


def _style_data_rows(ws, start_row, styles):   [REF:87-95]
    ...


class ExcelExporter:   [REF:98-480]
    def __init__(self, db: RACDatabase) -> None:   [REF:99-102]
        ...

    def _get_usafa_name(self) -> str:   [REF:104-106]
        ...

    def _save_workbook(   [REF:108-145] → src/export/excel_exporter.py:24 SavePathError → src/services/registro_service.py:137 save
        self, wb, base_filename, date_label="", log_label="Planilha exportada"
    ):
        ...

    def export_malote(self, malote_id: int) -> Optional[str]:   [REF:147-208] → src/export/excel_exporter.py:65 _apply_page_setup → src/export/excel_exporter.py:42 _make_excel_styles → src/export/excel_exporter.py:104 _get_usafa_name → src/database/rac_database.py:185 get_malote_by_id → src/utils/text_utils.py:50 format_item → src/database/rac_database.py:692 get_registros_with_items_by_malote → src/export/excel_exporter.py:87 _style_data_rows → src/export/excel_exporter.py:108 _save_workbook → src/export/excel_exporter.py:77 _style_title_row → src/export/excel_exporter.py:28 _ensure_openpyxl
        ...

    def export_stats(   [REF:210-302] → src/export/excel_exporter.py:77 _style_title_row → src/export/excel_exporter.py:28 _ensure_openpyxl → src/database/rac_database.py:798 get_stats_totals → src/export/excel_exporter.py:65 _apply_page_setup → src/database/rac_database.py:814 get_malote_date_range → src/export/excel_exporter.py:42 _make_excel_styles → src/export/excel_exporter.py:104 _get_usafa_name → src/export/excel_exporter.py:87 _style_data_rows → src/export/excel_exporter.py:108 _save_workbook → src/database/rac_database.py:768 get_stats_by_tipo → src/database/rac_database.py:825 get_stats_top_itens
        self,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> Optional[str]:
        ...

    def export_pacientes(self) -> Optional[str]:   [REF:304-347] → src/export/excel_exporter.py:77 _style_title_row → src/export/excel_exporter.py:28 _ensure_openpyxl → src/export/excel_exporter.py:65 _apply_page_setup → src/export/excel_exporter.py:104 _get_usafa_name → src/export/excel_exporter.py:42 _make_excel_styles → src/export/excel_exporter.py:87 _style_data_rows → src/export/excel_exporter.py:108 _save_workbook → src/database/rac_database.py:658 get_all_pacientes_with_last_registro
        ...

    def export_catalog(self) -> Optional[str]:   [REF:349-396] → src/export/excel_exporter.py:77 _style_title_row → src/export/excel_exporter.py:28 _ensure_openpyxl → src/export/excel_exporter.py:65 _apply_page_setup → src/database/rac_database.py:608 get_all_items → src/export/excel_exporter.py:42 _make_excel_styles → src/export/excel_exporter.py:87 _style_data_rows → src/export/excel_exporter.py:108 _save_workbook
        ...

    def export_registro_list(   [REF:398-480] → src/export/excel_exporter.py:77 _style_title_row → src/export/excel_exporter.py:28 _ensure_openpyxl → src/export/excel_exporter.py:65 _apply_page_setup → src/export/excel_exporter.py:42 _make_excel_styles → src/export/excel_exporter.py:87 _style_data_rows → src/export/excel_exporter.py:108 _save_workbook
        self,
        title: str,
        headers: list[str],
        rows: list[list[str]],
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> Optional[str]:
        ...
```

## src/state/rac_state_manager.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAC State Manager
Centralized state management with observer pattern
"""

from __future__ import annotations

import threading
import copy
from typing import Optional

from src.models import Malote


class RACStateManager:   [REF:17-56]
    def __init__(self) -> None:   [REF:18-22]
        ...

    # ========== MALOTE ==========

    def get_active_malote(self) -> Optional[Malote]:   [REF:26-28]
        ...

    def set_active_malote(self, malote: Optional[Malote]) -> None:   [REF:30-32]
        ...

    def has_active_malote(self) -> bool:   [REF:34-36]
        ...

    # ========== TIPO ==========

    def get_current_tipo(self) -> str:   [REF:40-42]
        ...

    def set_current_tipo(self, tipo: str) -> None:   [REF:44-46]
        ...

    # ========== CONFIG ==========

    def get_stay_on_page(self) -> bool:   [REF:50-52]
        ...

    def set_stay_on_page(self, value: bool) -> None:   [REF:54-56]
        ...
```

## src/gui/widgets/malote.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from contextlib import suppress
import json
from pathlib import Path

from PySide6.QtWidgets import (
    QLabel,
    QSizePolicy,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QDialog,
    QMenu,
    QTreeWidget,
    QTreeWidgetItem,
)
from PySide6.QtCore import Qt, Signal

from src.gui.widgets.buttons import make_button
from src.gui.widgets.labels import HeadingLabel
from src.gui.widgets.base_page import make_hbox
from src.gui.widgets.toast import show_toast
from src.gui.widgets.dialogs import confirm_delete_dialog, make_dialog_button_row, open_input_dialog, scaffold_dialog
from src.gui.styles import colors

def _activate_malote_if_changed(mw, malote):   [REF:28-31] → src/state/rac_state_manager.py:26 get_active_malote → src/state/rac_state_manager.py:30 set_active_malote
    ...


class MaloteLabel(QWidget):   [REF:34-87]
    malote_changed = Signal()

    def __init__(self, main_window, parent=None):   [REF:37-71] → src/gui/widgets/base_page.py:194 make_hbox → src/gui/widgets/malote.py:79 refresh
        ...

    def mousePressEvent(self, event):   [REF:73-74] → src/gui/widgets/malote.py:90 _show_malote_dialog
        ...

    def open_dialog(self):   [REF:76-77] → src/gui/widgets/malote.py:90 _show_malote_dialog
        ...

    def refresh(self):   [REF:79-84] → src/state/rac_state_manager.py:26 get_active_malote → src/utils/text_utils.py:13 format_malote_date
        ...

    def set_shortcut_hint_visible(self, show: bool):   [REF:86-87]
        ...


def _show_malote_dialog(label: MaloteLabel):   [REF:90-255] → src/state/rac_state_manager.py:26 get_active_malote → src/gui/widgets/malote.py:28 _activate_malote_if_changed → src/state/rac_state_manager.py:30 set_active_malote → src/gui/widgets/toast.py:29 show_toast → src/gui/widgets/dialogs.py:48 confirm_delete_dialog → src/gui/widgets/buttons.py:31 make_button → src/services/registro_service.py:69 get_by_malote → src/gui/widgets/malote.py:475 _show_date_dialog → src/gui/widgets/malote.py:79 refresh → src/gui/widgets/malote.py:419 _show_new_malote_dialog → src/utils/text_utils.py:13 format_malote_date
    ...


def _show_holidays_dialog(parent):   [REF:258-392] → src/gui/widgets/crud_list.py:244 add → src/gui/widgets/dialogs.py:106 open_input_dialog → src/gui/widgets/toast.py:29 show_toast → src/gui/widgets/dialogs.py:48 confirm_delete_dialog → src/gui/widgets/buttons.py:31 make_button → src/gui/widgets/dialogs.py:27 scaffold_dialog → src/gui/widgets/malote.py:411 _save_pontos → src/gui/styles.py:77 colors → src/gui/widgets/malote.py:395 _remove_ponto
    ...


def _remove_ponto(dt, pontos_path: Path):   [REF:395-408] → src/gui/widgets/malote.py:411 _save_pontos → src/gui/widgets/crud_list.py:181 load
    ...


def _save_pontos(pontos_path: Path, pontos_data: dict):   [REF:411-416]
    ...


def _show_new_malote_dialog(label: MaloteLabel):   [REF:419-472] → src/gui/widgets/malote.py:28 _activate_malote_if_changed → src/gui/widgets/toast.py:29 show_toast → src/gui/widgets/dialogs.py:27 scaffold_dialog → src/gui/widgets/malote.py:79 refresh → src/utils/date_calculator.py:33 calculate_arrival_date → src/gui/widgets/dialogs.py:37 make_dialog_button_row → src/utils/date_calculator.py:42 next_send_date
    ...


def _show_date_dialog(label: MaloteLabel, malote, field: str, on_done):   [REF:475-556] → src/state/rac_state_manager.py:26 get_active_malote → src/state/rac_state_manager.py:30 set_active_malote → src/gui/widgets/toast.py:29 show_toast → src/gui/widgets/dialogs.py:27 scaffold_dialog → src/gui/widgets/malote.py:79 refresh → src/gui/widgets/dialogs.py:37 make_dialog_button_row
    ...
```

## src/services/paciente_service.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.database.rac_database import RACDatabase
from src.models import Paciente
from src.services.exceptions import ValidationError


class PacienteService:   [REF:9-43]
    def __init__(self, db: RACDatabase) -> None:   [REF:10-11]
        ...

    def create(self, name: str) -> Paciente:   [REF:13-14] → src/database/rac_database.py:230 create_paciente
        ...

    def get(self, paciente_id: int) -> Paciente | None:   [REF:16-17] → src/database/rac_database.py:236 get_paciente_by_id
        ...

    def find_by_name(self, name: str) -> Paciente | None:   [REF:19-20] → src/database/rac_database.py:241 find_paciente_by_name
        ...

    def search(self, query: str, limit: int = 10) -> list[Paciente]:   [REF:22-23] → src/database/rac_database.py:249 search_pacientes
        ...

    def all(self) -> list[Paciente]:   [REF:25-26] → src/database/rac_database.py:652 get_all_pacientes
        ...

    def all_with_last_registro(self) -> list[Paciente]:   [REF:28-29] → src/database/rac_database.py:658 get_all_pacientes_with_last_registro
        ...

    def update(   [REF:31-40] → src/services/exceptions.py:13 ValidationError → src/database/rac_database.py:236 get_paciente_by_id → src/database/rac_database.py:255 update_paciente
        self, paciente_id: int, *, name: str | None = None
    ) -> None:
        ...

    def delete(self, paciente_id: int) -> bool:   [REF:42-43] → src/database/rac_database.py:261 delete_paciente
        ...
```

## src/gui/widgets/toast.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QLabel, QWidget, QHBoxLayout

from src.gui.styles import colors


class _ToastWidget(QWidget):   [REF:9-26]
    def __init__(self, message: str, kind: str, parent=None):   [REF:10-26] → src/gui/styles.py:77 colors
        ...


def show_toast(   [REF:29-41] → src/gui/main_window.py:314 show_status
    message: str,
    kind: str,
    parent: QWidget,
    path: str | None = None,
) -> None:
    ...


class ToastMixin:   [REF:44-46]
    def _toast(self, message: str, kind: str = "info"):   [REF:45-46]
        ...
```

## src/gui/widgets/labels.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QSizePolicy,
    QWidget,
)
from src.gui.constants import TIPO_HEX, TIPO_SYMBOLS, TIPO_LABELS
from src.gui.styles import colors
from src.gui.widgets.base_page import make_hbox
from src.gui.widgets.buttons import _load_material_icon


class Separator(QFrame):   [REF:16-21]
    def __init__(self, parent=None):   [REF:17-21]
        ...


class SectionLabel(QLabel):   [REF:24-28]
    def __init__(self, text: str, parent=None):   [REF:25-28]
        ...


class HeadingLabel(QLabel):   [REF:31-35]
    def __init__(self, text: str, parent=None):   [REF:32-35]
        ...


class TipoLabel(QWidget):   [REF:38-66]
    def __init__(self, tipo_key: str, parent=None):   [REF:39-66] → src/gui/widgets/base_page.py:194 make_hbox → src/gui/styles.py:77 colors
        ...
```

## src/gui/widgets/list_page.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ListPage — reusable read-only list page: heading, search bar and a sortable
table. Parameterized by columns and row data; double-clicking (or pressing
Enter on) a row invokes on_activate with the row's user data. No CRUD buttons
and no context menu.
"""

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import (
    QTableWidget,
    QHeaderView,
    QLineEdit,
    QSizePolicy,
    QLabel,
)
from PySide6.QtCore import Qt, QTimer

from src.gui.widgets.base_page import BasePage
from src.gui.widgets.crud_list import SortableTableWidgetItem
from src.gui.widgets.labels import HeadingLabel
from src.gui.styles import (
    data_view_style_qss,
    filter_table_rows,
    colors,
)
from andaime.qt.table import table_batch_populate


@dataclass
class ListColumn:   [REF:34-39]
    header: str
    resize_mode: QHeaderView.ResizeMode = QHeaderView.ResizeMode.Stretch
    align: Qt.AlignmentFlag = (
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
    )


@dataclass
class ListRow:   [REF:43-46]
    cells: list[str]
    data: object = None
    sort_keys: list | None = None


class ListPage(BasePage):   [REF:49-206]
    def __init__(   [REF:50-75] → src/gui/widgets/base_page.py:27 __init__ → src/gui/widgets/list_page.py:77 _build_ui
        self,
        main_window,
        *,
        title: str,
        search_placeholder: str,
        columns: list[ListColumn],
        rows: list[ListRow],
        on_activate: Callable[[object], None],
        back_target: str = "start",
        default_sort: tuple[int, Qt.SortOrder] | None = None,
        on_export: Callable | None = None,
        export_label: str = "Exportar Registros",
        title_parts: list[tuple[str, Qt.AlignmentFlag]] | None = None,
    ):
        ...

    def _build_ui(   [REF:77-172] → src/gui/widgets/list_page.py:174 _populate → src/gui/styles.py:77 colors → src/gui/widgets/labels.py:31 HeadingLabel
        self,
        title: str,
        search_placeholder: str,
        columns: list[ListColumn],
        rows: list[ListRow],
        back_target: str,
        default_sort: tuple[int, Qt.SortOrder] | None,
        on_export: Callable | None,
        export_label: str,
        title_parts: list[tuple[str, Qt.AlignmentFlag]] | None,
    ):
        ...

    def _populate(self, columns: list[ListColumn], rows: list[ListRow]):   [REF:174-188] → src/gui/widgets/crud_list.py:31 SortableTableWidgetItem
        ...

    def _activate_row(self, row: int):   [REF:190-198]
        ...

    def _activate_current(self):   [REF:200-203] → src/gui/widgets/list_page.py:190 _activate_row
        ...

    def _on_search(self, text: str):   [REF:205-206] → src/gui/styles.py:576 filter_table_rows
        ...
```

## src/gui/brasao.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Brasão da Prefeitura e RAC logo (Qt). Os PNGs claro/escuro são pré-renderizados
por ``tools/generate_brasao.py`` evitando QtSvg em runtime e garantindo visual 
idêntico entre fonte e build empacotado. O resultado é cacheado por (altura, modo_escuro)."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


def _resolver_caminho(nome: str, pasta: str = "img") -> Path:   [REF:16-25]
    ...


def _get_pixmap_cached(   [REF:28-53] → src/gui/brasao.py:16 _resolver_caminho
    cache: dict, height: int, dark_mode: bool, nome: str
) -> QPixmap | None:
    ...


_pixmap_cache: dict[tuple[int, bool], QPixmap | None] = {}
_rac_cache: dict[tuple[int, bool], QPixmap | None] = {}


def get_brasao_pixmap(height: int = 41, dark_mode: bool = True) -> QPixmap | None:   [REF:60-62] → src/gui/brasao.py:28 _get_pixmap_cached
    ...


def get_rac_pixmap(height: int = 30, dark_mode: bool = True) -> QPixmap | None:   [REF:65-67] → src/gui/brasao.py:28 _get_pixmap_cached
    ...
```

## src/services/malote_service.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.database.rac_database import RACDatabase
from src.models import Malote


class MaloteService:   [REF:8-76]
    def __init__(self, db: RACDatabase) -> None:   [REF:9-10]
        ...

    def create(self, date: str, arrival_date: str | None = None) -> Malote:   [REF:12-13] → src/database/rac_database.py:169 create_malote
        ...

    def get(self, malote_id: int) -> Malote | None:   [REF:15-16] → src/database/rac_database.py:185 get_malote_by_id
        ...

    def all(self) -> list[Malote]:   [REF:18-19] → src/database/rac_database.py:197 get_all_malotes
        ...

    def get_dates(self) -> set[str]:   [REF:21-22] → src/database/rac_database.py:203 get_malote_dates
        ...

    def update(   [REF:24-34] → src/database/rac_database.py:211 update_malote → src/services/malote_service.py:48 _recalculate_affected_registros → src/services/malote_service.py:39 _derive_arrival
        self, malote_id: int, *, date: str | None = None, arrival_date: str | None = None
    ) -> None:
        ...

    def delete(self, malote_id: int) -> bool:   [REF:36-37] → src/database/rac_database.py:224 delete_malote
        ...

    def _derive_arrival(self, iso_date: str) -> str | None:   [REF:39-46]
        ...

    def _recalculate_affected_registros(self, malote_id: int) -> None:   [REF:48-76] → src/database/rac_database.py:479 get_items_by_registro → src/database/rac_database.py:555 get_processes_by_registro → src/services/registro_service.py:48 RegistroService → src/database/rac_database.py:348 get_registros_by_malote
        ...
```

## src/gui/widgets/inputs.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QSizePolicy,
    QWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette

from src.gui.widgets._completer import (
    _CenteredComboBox,
    _BaseComboDelegate,
)
from src.gui.widgets.base_page import make_hbox
from src.gui.constants import TIPO_LABELS, TIPO_SYMBOLS, TIPO_HEX
from src.gui.widgets.buttons import _load_material_icon
from src.gui.styles import colors, faded_tipo_color, combo_style_qss


class _TipoComboDelegate(_BaseComboDelegate):   [REF:21-34]
    def _selected_fill_and_pen(self, option):   [REF:22-26]
        ...

    def _pen_color_unselected(self, option, index):   [REF:28-34]
        ...


class TipoCombo(QWidget):   [REF:37-108]
    tipo_changed = Signal(str)

    def __init__(self, current_tipo: str, parent=None):   [REF:40-70] → src/gui/widgets/base_page.py:194 make_hbox → src/gui/widgets/buttons.py:13 _load_material_icon → src/gui/widgets/inputs.py:87 _update_display → src/gui/widgets/_completer.py:49 setHideCurrentItem → src/gui/widgets/_completer.py:46 _CenteredComboBox
        ...

    def current_tipo(self) -> str:   [REF:72-73]
        ...

    def set_tipo(self, tipo_key: str):   [REF:75-78]
        ...

    def _on_index_changed(self, idx):   [REF:80-85] → src/gui/widgets/inputs.py:87 _update_display
        ...

    def _update_display(self, tipo_key: str):   [REF:87-108] → src/gui/widgets/buttons.py:13 _load_material_icon → src/gui/styles.py:77 colors → src/gui/styles.py:90 faded_tipo_color
        ...
```

## src/utils/text_utils.py
```python
from __future__ import annotations

import re
from datetime import date as date_type
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.models import Malote, RegistroItem

from andaime.dates import format_date


def format_malote_date(malote: Optional[Malote]) -> str:   [REF:13-20]
    ...


def is_malote_past(malote: Optional[Malote]) -> bool:   [REF:23-29]
    ...


def format_registro_meds(items: list[RegistroItem]) -> str:   [REF:32-47] → src/utils/text_utils.py:50 format_item
    ...


def format_item(name: str) -> str:   [REF:50-62] → src/services/paciente_service.py:22 search
    ...
```

## src/services/malote_import_service.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Malote import — persists extracted malote tabs into the database.

Given a matcher + set of MaloteTab extractions, it creates/reuses malotes,
finds-or-creates pacientes, skips existing registros and links items.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from src.database.rac_database import RACDatabase
from src.importers.excel_importer import MaloteRow, MaloteTab
from src.importers.matcher import MedMatcher
from src.models import Malote


@dataclass
class MaloteImportSummary:   [REF:22-28]
    malotes: int = 0
    registros_new: int = 0
    registros_skipped: int = 0
    pacientes_new: int = 0
    items_linked: int = 0
    unmatched: list[str] = field(default_factory=list)


class MaloteImportService:   [REF:31-117]
    def __init__(self, db: RACDatabase, matcher: MedMatcher) -> None:   [REF:32-34]
        ...

    def import_tabs(self, tabs: list[MaloteTab]) -> MaloteImportSummary:   [REF:36-42] → src/services/malote_import_service.py:22 MaloteImportSummary → src/services/malote_import_service.py:44 _import_tab
        ...

    def _import_tab(self, tab: MaloteTab, summary: MaloteImportSummary) -> None:   [REF:44-87] → src/services/malote_import_service.py:102 _ensure_paciente → src/database/rac_database.py:444 set_registro_items → src/database/rac_database.py:333 find_registro → src/services/malote_import_service.py:89 _ensure_malote → src/importers/matcher.py:108 match → src/database/rac_database.py:294 create_registro
        ...

    def _ensure_malote(self, malote_date: date) -> Malote:   [REF:89-100] → src/database/rac_database.py:169 create_malote
        ...

    def _ensure_paciente(   [REF:102-117] → src/database/rac_database.py:241 find_paciente_by_name → src/database/rac_database.py:230 create_paciente
        self, cache: dict[str, int], name: str, summary: MaloteImportSummary
    ) -> int | None:
        ...
```

## src/gui/pages/medicamentos_page.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medicamentos Page — manage the medication (item catalog) list
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from src.gui.widgets import (
    BasePage, CrudList, HeadingLabel, export_with_fallback, open_input_dialog, open_select_dialog, open_estoque_dialog,
)
from src.export.excel_exporter import ExcelExporter

if TYPE_CHECKING:
    from src.gui.main_window import MainWindow


def _format_cids(item) -> str:   [REF:21-28]
    ...


def _full_cids(item) -> str:   [REF:31-37]
    ...


class MedicamentosPage(BasePage):   [REF:40-169]
    def __init__(self, main_window: MainWindow):   [REF:41-43] → src/gui/widgets/base_page.py:27 __init__ → src/gui/pages/medicamentos_page.py:45 _build_ui
        ...

    def _build_ui(self):   [REF:45-88] → src/gui/widgets/crud_list.py:48 CrudList → src/gui/widgets/labels.py:31 HeadingLabel
        ...

    def _edit_cids(self, item_id: int):   [REF:90-114] → src/gui/widgets/dialogs.py:106 open_input_dialog
        ...

    def _on_export(self):   [REF:116-122] → src/export/excel_exporter.py:98 ExcelExporter → src/gui/widgets/base_page.py:216 export_with_fallback
        ...

    def _edit_estoque(self, item_id: int):   [REF:124-143] → src/gui/widgets/dialogs.py:138 open_estoque_dialog
        ...

    def _edit_unidade(self, item_id: int):   [REF:145-169] → src/gui/widgets/dialogs.py:74 open_select_dialog
        ...
```

## main.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path

from PySide6.QtCore import Qt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import andaime
from andaime.error_handler import ErrorHandler, ErrorContext, ErrorLevel
from andaime.qt.fonts import FontSpec, apply_font
from src.utils.config import RACConfig
from src.database.rac_database import RACDatabase


def _get_app_icon_path():   [REF:19-20]
    ...


def _apply_pending_update():   [REF:23-26]
    ...


def _show_usafa_dialog(config, splash=None, parent=None):   [REF:29-90] → src/gui/widgets/buttons.py:31 make_button → src/gui/styles.py:77 colors → src/gui/widgets/labels.py:31 HeadingLabel
    ...


def _prompt_usafa_name(config, splash=None):   [REF:93-101] → main.py:29 _show_usafa_dialog
    ...


def _start_update_check(window):   [REF:104-151] → src/gui/widgets/buttons.py:31 make_button → src/gui/styles.py:77 colors
    ...


def main():   [REF:154-211] → main.py:104 _start_update_check → main.py:19 _get_app_icon_path → src/gui/main_window.py:67 init_backend → main.py:23 _apply_pending_update → main.py:93 _prompt_usafa_name → src/gui/main_window.py:27 MainWindow → src/gui/styles.py:59 set_theme → src/gui/main_window.py:121 navigate_to
    # Set AppUserModelID + register icon in registry BEFORE QApplication.
    ...


if __name__ == "__main__":
    main()
```

## src/services/item_catalog_service.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.database.rac_database import RACDatabase
from src.models import ItemCatalog


class ItemCatalogService:   [REF:8-31]
    def __init__(self, db: RACDatabase) -> None:   [REF:9-10]
        ...

    def create(self, name: str, unidade: str = "un", quantidade: int = 0) -> ItemCatalog:   [REF:12-13] → src/database/rac_database.py:620 create_item
        ...

    def all(self) -> list[ItemCatalog]:   [REF:15-16] → src/database/rac_database.py:608 get_all_items
        ...

    def update(self, item_id: int, name: str) -> bool:   [REF:18-19] → src/database/rac_database.py:626 update_item
        ...

    def update_cids(self, item_id: int, cids: str) -> bool:   [REF:21-22] → src/database/rac_database.py:632 update_item_cids
        ...

    def update_quantidade(self, item_id: int, quantidade: int) -> bool:   [REF:24-25] → src/database/rac_database.py:636 update_item_quantidade
        ...

    def update_unidade(self, item_id: int, unidade: str) -> bool:   [REF:27-28] → src/database/rac_database.py:640 update_item_unidade
        ...

    def delete(self, item_id: int) -> bool:   [REF:30-31] → src/database/rac_database.py:644 delete_item
        ...
```

## src/sync/collection.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collection snapshot provider — pulls encrypted snapshots from a GitHub
collection branch and decrypts them with the admin private key.

Used by the GitHub Action (and local testing) to aggregate all USAFAs.
Only depends on ``cryptography`` + stdlib — no andaime, no PySide6, no DB.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from src.sync.asymmetric import decrypt_with_private_key
from src.sync.types import Snapshot

_API_BASE = "https://api.github.com/repos"


def _github_get_json(url: str, token: str | None) -> Any:   [REF:25-34]
    ...


def _github_get_text(url: str, token: str | None) -> str:   [REF:37-46]
    ...


class CollectionSnapshotProvider:   [REF:49-91]
    """Pull + decrypt snapshots from a GitHub collection branch."""

    def __init__(   [REF:52-64]
        self,
        repo: str,
        branch: str,
        private_key_pem: str,
        token: str | None = None,
    ) -> None:
        ...

    def snapshots(self) -> list[Snapshot]:   [REF:66-79] → src/sync/asymmetric.py:98 decrypt_with_private_key → src/sync/collection.py:81 _list_files
        ...

    def _list_files(self) -> list[dict]:   [REF:81-91] → src/sync/collection.py:25 _github_get_json
        ...
```

## src/utils/config.py
```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class RACConfig:   [REF:7-68]
    stay_on_page: bool = False
    theme: str = "dark"
    last_malote_id: Optional[int] = None
    save_path: Optional[Path] = None
    usafa_id: Optional[str] = None
    usafa_name: Optional[str] = None

    def __post_init__(self) -> None:   [REF:15-20] → src/utils/config.py:22 validate
        ...

    def validate(self) -> None:   [REF:22-40]
        ...

    def to_dict(self) -> dict:   [REF:42-53]
        ...

    @staticmethod
    def get_defaults() -> "RACConfig":   [REF:56-62] → src/utils/config.py:7 RACConfig
        ...

    @staticmethod
    def migrate_data(data: dict) -> dict:   [REF:65-68]
        ...
```

## src/sync/asymmetric.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Asymmetric encryption for the collection layer.

Each RAC instance encrypts its snapshot to the admin's X25519 public key.
Only the admin (GitHub Action, holding the private key) can decrypt.

This is the ``age`` design: hybrid encryption using X25519 ECDH + HKDF +
AES-GCM. The public key ships in the RAC installer (it is not a secret).
The private key lives only as a GitHub Secret.

Only depends on ``cryptography`` + stdlib — no andaime, no PySide6, no DB.
"""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

_INFO = b"rac-collection-v1"
_KEY_LEN = 32
_NONCE_LEN = 12


def generate_keypair() -> tuple[str, str]:   [REF:34-50]
    ...


def _load_private_key(pem: str) -> X25519PrivateKey:   [REF:53-56]
    ...


def _load_public_key(pem: str) -> X25519PublicKey:   [REF:59-62]
    ...


def encrypt_to_public_key(plaintext: bytes, recipient_public_pem: str) -> dict:   [REF:65-95] → src/sync/asymmetric.py:59 _load_public_key
    ...


def decrypt_with_private_key(blob: dict, private_pem: str) -> bytes:   [REF:98-122] → src/sync/asymmetric.py:53 _load_private_key
    ...
```

## src/gui/pages/pacientes_page.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pacientes Page — manage the patient list
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from src.gui.widgets import BasePage, CrudList, HeadingLabel, export_with_fallback
from src.export.excel_exporter import ExcelExporter
from src.models import Paciente

if TYPE_CHECKING:
    from src.gui.main_window import MainWindow


def _format_last_registro(p: Paciente) -> str:   [REF:20-27]
    ...


class PacientesPage(BasePage):   [REF:30-82]
    def __init__(self, main_window: MainWindow, return_to: str = "start"):   [REF:31-34] → src/gui/widgets/base_page.py:27 __init__ → src/gui/pages/pacientes_page.py:36 _build_ui
        ...

    def _build_ui(self):   [REF:36-71] → src/gui/widgets/crud_list.py:48 CrudList → src/gui/widgets/labels.py:31 HeadingLabel
        ...

    def _on_export(self):   [REF:73-79] → src/export/excel_exporter.py:98 ExcelExporter → src/gui/widgets/base_page.py:216 export_with_fallback
        ...

    def _view_paciente(self, paciente_id: int):   [REF:81-82]
        ...
```

## src/services/exceptions.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class RACError(Exception):   [REF:5-6]
    pass


class DuplicateRecordError(RACError):   [REF:9-10]
    pass


class ValidationError(RACError):   [REF:13-14]
    pass
```

## src/gui/pages/registro_list_page.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Registro List Page — read-only list of registros reached from the stats page,
filtered by tipo, by medication, or unfiltered. Double-clicking a row opens
the patient page for that registro's patient.
"""

from PySide6.QtWidgets import QHeaderView
from PySide6.QtCore import Qt

from src.gui.widgets import ListPage, ListColumn, ListRow
from src.gui.constants import TIPO_LABELS
from src.models import Malote, Registro
from src.utils.text_utils import format_malote_date, format_registro_meds
from src.export.excel_exporter import ExcelExporter
from src.gui.widgets import export_with_fallback

_CENTER = Qt.AlignmentFlag.AlignCenter
_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter


class RegistroListPage(ListPage):   [REF:23-161]
    def __init__(   [REF:24-100] → src/database/rac_database.py:921 get_stats_item_totals → src/gui/pages/registro_list_page.py:116 _registro_rows → src/gui/widgets/list_page.py:50 __init__ → src/gui/pages/registro_list_page.py:132 _item_rows → src/database/rac_database.py:845 get_stats_registros → src/gui/widgets/list_page.py:34 ListColumn
        self,
        main_window,
        kind: str,
        tipo: str | None = None,
        item_id: int | None = None,
        item_name: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ):
        ...

    def _on_export(self):   [REF:102-113] → src/export/excel_exporter.py:98 ExcelExporter → src/gui/widgets/base_page.py:216 export_with_fallback
        ...

    @staticmethod
    def _registro_rows(db, registros: list[Registro]) -> list[ListRow]:   [REF:116-129] → src/database/rac_database.py:874 get_items_by_registros
        ...

    @staticmethod
    def _item_rows(   [REF:132-152] → src/database/rac_database.py:896 get_item_cids_by_registro
        db,
        registros: list[Registro],
        item_id: int,
        date_from: str | None,
        date_to: str | None,
    ) -> list[ListRow]:
        ...

    def _open_patient(self, data):   [REF:154-161]
        ...
```

## panel/render.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render an AggregateStats into a self-contained HTML dashboard.

Output is a single static file (no server, no external assets): the merged
data is baked in as HTML, styled with inline CSS, with a tiny inline JS hook
for the medications search filter. Open it directly in any browser.
"""

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any

from src.constants import TIPO_HEX, TIPO_LABELS
from src.sync.merger import AggregateStats

_CSS = """
  :root {
    --bg: #18181B;
    --card: #27272A;
    --border: #3F3F46;
    --text: #F4F4F5;
    --muted: #A1A1AA;
    --alt: #2D2D31;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: "Geist", -apple-system, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 32px;
    max-width: 960px;
  }
  h1 { font-size: 22px; font-weight: 600; margin: 0 0 4px; }
  .sub { color: var(--muted); font-size: 13px; margin-bottom: 26px; }
  .row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 22px; }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 18px;
    min-width: 124px;
  }
  .card .v { font-size: 24px; font-weight: 700; }
  .card .l {
    font-size: 11px; font-weight: 600; color: var(--muted);
    margin-top: 2px; text-transform: uppercase; letter-spacing: .04em;
  }
  .section {
    font-size: 12px; font-weight: 600; color: var(--muted);
    text-transform: uppercase; letter-spacing: .05em; margin: 6px 0 10px;
  }
  .wrap {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 8px; margin-bottom: 24px; overflow: hidden;
  }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 9px 14px; border-bottom: 1px solid var(--border); }
  th {
    color: var(--muted); font-size: 11px; font-weight: 600;
    text-transform: uppercase; letter-spacing: .04em;
  }
  td.num, th.num { text-align: right; }
  tbody tr:nth-child(even) { background: var(--alt); }
  .pad { padding: 10px 14px 0; }
  input {
    width: 100%; padding: 9px 12px;
    border-radius: 6px; border: 1px solid var(--border);
    background: var(--bg); color: var(--text); font-size: 13px;
  }
  .empty td { text-align: center; color: var(--muted); }
  .lock { max-width: 340px; margin: 80px auto; text-align: center; }
  .lock input { text-align: center; margin-bottom: 12px; }
  .lock button {
    padding: 9px 24px; border-radius: 6px; border: 1px solid var(--border);
    background: var(--card); color: var(--text); font-size: 14px; cursor: pointer;
  }
  .lock .err { color: #F87171; font-size: 13px; margin-top: 10px; min-height: 18px; }
"""

_PAGE = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gestao - RAC</title>
<style>{_CSS}</style>
</head>
<body>
__BODY__
<script>
var s = document.getElementById('meds-search');
if (s) s.addEventListener('input', function () {{
  var q = s.value.toLowerCase();
  document.querySelectorAll('#meds-table tbody tr').forEach(function (tr) {{
    tr.style.display = tr.textContent.toLowerCase().indexOf(q) !== -1 ? '' : 'none';
  }});
}});
</script>
</body>
</html>"""


def _card(value: str, label: str, accent: str | None = None) -> str:   [REF:108-115]
    ...


def _format_synced(iso: str) -> str:   [REF:118-122]
    ...


def _usafa_table(agg: AggregateStats) -> str:   [REF:125-144]
    ...


def _meds_table(agg: AggregateStats) -> str:   [REF:147-166]
    ...


def render_html(agg: AggregateStats) -> str:   [REF:169-206]
    ...


def render_locked_html(enc_blob: dict) -> str:   [REF:209-347]
    ...
```

## panel/__main__.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Management panel entry point.

Usage:
    python -m panel                                        # local plaintext painel.html
    RAC_PANEL_PASSWORD='...' python -m panel --locked      # encrypted index.html
    RAC_PANEL_PASSWORD='...' python -m panel --publish     # encrypt + push to gh-pages
    python -m panel --from-collection --publish            # from collection branch (Action)

The --from-collection mode skips the local DB entirely (no andaime/PySide6),
reading encrypted snapshots from a GitHub branch instead. This is what the
GitHub Action uses.
"""

from __future__ import annotations

import argparse
import base64
import dataclasses
import getpass
import json
import os
import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from panel.render import render_html, render_locked_html  # noqa: E402
from src.sync.merger import merge_snapshots  # noqa: E402


def _get_password() -> str:   [REF:37-41]
    ...


def _build_from_local():   [REF:44-64] → src/sync/merger.py:37 merge_snapshots → src/sync/provider.py:25 LocalSnapshotProvider → src/database/rac_database.py:32 RACDatabase
    ...


def _build_from_collection():   [REF:67-75] → src/sync/merger.py:37 merge_snapshots → src/sync/collection.py:49 CollectionSnapshotProvider
    ...


def _publish_to_github_pages(html: str, repo: str = "januvary/RAC") -> str:   [REF:78-145] → src/gui/widgets/import_dialog.py:50 run
    ...


def main() -> None:   [REF:148-194] → panel/__main__.py:67 _build_from_collection → panel/crypto.py:48 encrypt_payload → panel/render.py:169 render_html → panel/__main__.py:78 _publish_to_github_pages → panel/__main__.py:37 _get_password → panel/__main__.py:44 _build_from_local → panel/render.py:209 render_locked_html
    ...


if __name__ == "__main__":
    main()
```

## src/sync/merger.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Snapshot merger — combine per-USAFA snapshots into aggregate stats for the
management panel. Pure logic: no I/O, no Qt, fully testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.sync.types import Snapshot


@dataclass
class UsafaStats:   [REF:17-24]
    usafa_id: str
    usafa_name: str
    exported_at: str
    registros: int
    pacientes: int
    malotes: int
    by_tipo: dict[str, int] = field(default_factory=dict)


@dataclass
class AggregateStats:   [REF:28-34]
    usafas: list[UsafaStats] = field(default_factory=list)
    total_registros: int = 0
    total_pacientes: int = 0
    total_usafas: int = 0
    by_tipo: dict[str, int] = field(default_factory=dict)
    top_items: list[dict[str, Any]] = field(default_factory=list)


def merge_snapshots(snapshots: list[Snapshot]) -> AggregateStats:   [REF:37-90] → src/sync/merger.py:28 AggregateStats
    ...
```

## src/sync/provider.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Snapshot providers — the seam between the management panel and its data source.

A provider yields the list of per-USAFA snapshots the panel renders.
``LocalSnapshotProvider`` exports the current instance's database (used today,
while only one USAFA exists). A future ``GitHubSnapshotProvider`` will pull and
decrypt snapshots published by every USAFA over the wire.
"""

from __future__ import annotations

from typing import Protocol

from src.database.rac_database import RACDatabase
from src.sync.snapshot import export_snapshot
from src.sync.types import Snapshot


class SnapshotProvider(Protocol):   [REF:21-22]
    ...


class LocalSnapshotProvider:   [REF:22-22]
    def __init__(self, db: RACDatabase, usafa_id: str, usafa_name: str) -> None:   [REF:25-32]
        ...

    def snapshots(self) -> list[Snapshot]:   [REF:26-29]
        ...
```

## panel/crypto.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Password-based encryption for the panel's published payload.

The aggregate is encrypted with a key derived from a password (PBKDF2-HMAC-SHA256)
and AES-GCM. The browser decrypts it via Web Crypto using the same parameters,
so Python encrypts and JS decrypts with zero shared library code.

Output format (all fields base64 except iterations):
    iterations : int    (PBKDF2 iteration count)
    salt       : str    (16 bytes, base64)
    nonce      : str    (12 bytes, base64 — AES-GCM IV)
    ciphertext : str    (plaintext + 16-byte GCM auth tag appended, base64)

Note: ``cryptography``'s AESGCM.encrypt emits ciphertext WITH the tag appended,
which is exactly what Web Crypto's AES-GCM decrypt expects. The two sides are
wire-compatible.
"""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

DEFAULT_ITERATIONS = 600_000
_KEY_LEN = 32
_SALT_LEN = 16
_NONCE_LEN = 12


def derive_key(   [REF:36-45]
    password: str, salt: bytes, iterations: int = DEFAULT_ITERATIONS
) -> bytes:
    ...


def encrypt_payload(   [REF:48-60] → panel/crypto.py:36 derive_key
    plaintext: bytes, password: str, iterations: int = DEFAULT_ITERATIONS
) -> dict:
    ...


def decrypt_payload(blob: dict, password: str) -> bytes:   [REF:63-69] → panel/crypto.py:36 derive_key
    ...
```

## tools/generate_rac_icons.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate pre-rendered PNG icons for RAC from Material Symbols SVGs.

Tipo icons are tinted to their respective color. Right-column shortcut icons
are rendered in black (light theme) and white (dark theme).
"""

import subprocess
import sys
from pathlib import Path

ICON_DIR = Path(__file__).resolve().parent.parent / "src" / "gui" / "img" / "material-icons"

TIPO_COLORS = {
    "arrow_upward": "#10B981",
    "autorenew": "#3B82F6",
    "arrow_downward": "#D97706",
    "frame_source": "#EF4444",
    "home": "#06B6D4",
}

RIGHT_ICONS = [
    "view_list",
    "file_export",
    "pill",
    "person",
    "leaderboard",
]


TPL_FILL = ['#000000', '#ffffff', '#e3e3e3']


def svg_recolored(svg_path: Path, color: str) -> str:   [REF:35-42]
    ...


def render_to_png(svg_text: str, output: Path, size: int = 24) -> None:   [REF:45-59] → src/gui/widgets/import_dialog.py:50 run
    ...


def main():   [REF:62-84] → tools/generate_rac_icons.py:45 render_to_png
    ...


if __name__ == "__main__":
    main()
```

## src/gui/widgets/_malote_tree.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import operator
from typing import Callable, Any

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Qt, QObject
from PySide6.QtGui import QKeyEvent

from src.gui.styles import colors


def populate_malote_tree(   [REF:15-99]
    tree: QTreeWidget,
    malotes: list[Any],
    *,
    format_display: Callable[[Any, datetime], str] | None = None,
    decorate_item: Callable[[QTreeWidgetItem, Any, datetime], None] | None = None,
    get_user_data: Callable[[Any, datetime], Any] | None = None,
    prepend_items: list[QTreeWidgetItem] | None = None,
) -> None:
    ...


def make_malote_tree() -> QTreeWidget:   [REF:102-114] → src/gui/styles.py:77 colors
    ...


def wire_tree_keyboard(tree: QTreeWidget, on_activate) -> None:   [REF:117-128] → src/gui/widgets/base_page.py:104 eventFilter
    ...
```

## src/sync/snapshot.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Snapshot export — serialize a RAC database into a JSON-serializable dict,
tagged with the originating USAFA identity.

The snapshot is the unit of data exchanged with the management panel. It is
self-describing: it carries the raw table rows (for drill-down /
reconstruction) and a precomputed summary that the panel renders directly.
"""

from __future__ import annotations

from datetime import datetime

from src.database.rac_database import RACDatabase
from src.sync.types import Snapshot, SnapshotSummary, TipoSummaryRow


def build_summary(db: RACDatabase) -> SnapshotSummary:   [REF:20-40] → src/database/rac_database.py:798 get_stats_totals → src/database/rac_database.py:768 get_stats_by_tipo → src/database/rac_database.py:825 get_stats_top_itens
    ...


def export_snapshot(db: RACDatabase, usafa_id: str, usafa_name: str) -> Snapshot:   [REF:43-51] → src/sync/snapshot.py:20 build_summary → src/database/rac_database.py:678 dump_all_tables
    ...
```

## src/sync/types.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Snapshot type definitions — pure TypedDicts with no runtime dependencies.

Kept separate from ``snapshot.py`` (which imports the database) so that
``merger.py`` and the GitHub Action can consume snapshots without pulling in
PySide6, andaime, or the database layer.
"""

from __future__ import annotations

from typing import Any, TypedDict


class TipoSummaryRow(TypedDict):   [REF:16-19]
    registros: int
    pacientes: int
    items: int


class SnapshotSummary(TypedDict):   [REF:22-25]
    by_tipo: dict[str, TipoSummaryRow]
    totals: dict[str, int]
    top_items: list[dict[str, Any]]


class Snapshot(TypedDict):   [REF:28-34]
    usafa_id: str
    usafa_name: str
    exported_at: str
    schema_version: int
    tables: dict[str, list[dict[str, Any]]]
    summary: SnapshotSummary
```

## src/utils/unidade_parser.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parse medication dosage forms and map to standard units
"""

def parse_unidade_from_name(name: str) -> str:   [REF:7-75]
    ...


# Test function
if __name__ == "__main__":
    test_cases = [
        ("abatacepte 125 mg inj.", "un"),
        ("atorvastatina 20 mg", "comp"),
        ("atorvastatina 20 mg/ml", "frs"),
        ("dapagliflozina 10 mg", "comp"),
        ("codeina 3 mg/ml sol. oral", "frs"),
        ("codeina 30 mg", "comp"),
        ("etossuximida 50 mg/ml xarope", "frs"),
        ("calcipotriol 50 mcg pomada", "un"),
        ("calcitriol 0,25 mcg capsula", "comp"),
        ("lanreotida 120 mg inj.", "un"),
        ("pentoxifilina 400 mg/ml inj.", "un"),
        ("codeina 30 mg/ml inj.", "un"),
        ("formoterol 12 mcg aerossol", "frs"),
        ("pilocarpina 20 mg/ml sol. oftalmica", "frs"),
        ("clobetasol 0,5 mg/g creme", "un"),
        ("mesalazina 400 mg", "comp"),
        ("calcitonina 200 ui spray nasal", "frs"),
        ("ibuprofeno 600 mg", "comp"),
        ("dipropionato de beclometasona 100 mcg", "comp"),
    ]
    
    print("Testing parse_unidade_from_name:")
    print("-" * 50)
    for name, expected in test_cases:
        result = parse_unidade_from_name(name)
        status = "✓" if result == expected else "✗"
        print(f"{status} {name:<50} → {result} (expected: {expected})")
```

## cleanup_db.py
```python
#!/usr/bin/env python3
"""Reset the database — drops all registros, pacientes, malotes; keeps items_catalog."""

import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.rac_database import RACDatabase

db = RACDatabase()

def _op():   [REF:12-20]
    ...

db._retry_on_transient_error(_op, operation_type="write")

print("Database cleaned — items_catalog preserved")
db.close()
```

## tools/generate_brasao.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera os PNGs do brasão e RAC a partir dos SVGs, usando andaime.brasao."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from andaime.brasao import render_brasao_silhouette, recolor_brasao
from andaime.qt.theme import LIGHT as _SHARED_LIGHT, DARK as _SHARED_DARK


def main():   [REF:14-50] → src/services/registro_service.py:137 save
    ...


if __name__ == "__main__":
    main()
```

<!-- 52/52 files, ~33743 tokens -->