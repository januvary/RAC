#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel Exporter
Generates .xlsx spreadsheet from malote registros
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from datetime import datetime
from pathlib import Path

from src.utils.error_handler import ErrorHandler, ErrorContext, ErrorLevel
from src.utils.text_utils import to_upper_normalized

if TYPE_CHECKING:
    from src.database.rac_database import RACDatabase


class ExcelExporter:
    def __init__(self, db: RACDatabase) -> None:
        self._db = db

    def export_malote(self, malote_id: int) -> Optional[str]:
        try:
            import openpyxl
        except ImportError:
            ErrorHandler.log(
                "openpyxl não instalado",
                level=ErrorLevel.ERROR,
                context=ErrorContext.EXPORT,
            )
            return None

        registros = self._db.get_registros_with_items_by_malote(malote_id)
        if not registros:
            return None

        malote = self._db.get_malote_by_id(malote_id)
        if not malote:
            return None

        wb = openpyxl.Workbook()
        wb.remove(wb.active)

        tipo_tabs = {
            "entrada": "Entradas",
            "renovacao": "Renovações",
            "retirada": "Retiradas",
            "urgente": "Urgentes",
        }

        for tipo, tab_name in tipo_tabs.items():
            ws = wb.create_sheet(title=tab_name)

            ws.append(["Nome", "Medicamentos"])

            tipo_registros = [r for r in registros if r["tipo"] == tipo]
            tipo_registros.sort(key=lambda r: r.get("paciente_name", ""))

            for reg in tipo_registros:
                items_str = ", ".join(
                    to_upper_normalized(i) for i in reg.get("items", [])
                )
                ws.append([
                    to_upper_normalized(reg.get("paciente_name", "")),
                    items_str,
                ])

            ws.column_dimensions["A"].width = 35
            ws.column_dimensions["B"].width = 60

        try:
            date_str = malote.get("date", "unknown")
            try:
                dt = datetime.fromisoformat(date_str)
                date_display = dt.strftime("%Y-%m-%d")
            except ValueError:
                date_display = date_str

            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"Malote_{date_display}_{timestamp}.xlsx"

            from src.utils.config import ConfigManager
            config = ConfigManager()
            save_path = config.get("save_path", Path.home() / "Downloads")

            if isinstance(save_path, str):
                save_path = Path(save_path)

            save_path.mkdir(parents=True, exist_ok=True)
            full_path = save_path / filename

            wb.save(str(full_path))

            ErrorHandler.log(
                f"Planilha exportada: {full_path}",
                level=ErrorLevel.INFO,
                context=ErrorContext.EXPORT,
            )

            return str(full_path)

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                context=ErrorContext.EXPORT,
                recovery_hint="Verifique permissões de escrita no diretório de salvamento",
            )
            return None
