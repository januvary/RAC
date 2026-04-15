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
from src.constants import TIPO_LABELS, TIPO_TITLES

if TYPE_CHECKING:
    from src.database.rac_database import RACDatabase


class SavePathError(Exception):
    pass


class ExcelExporter:
    def __init__(self, db: RACDatabase) -> None:
        self._db = db

    def export_malote(self, malote_id: int) -> Optional[str]:
        try:
            import openpyxl  # type: ignore[import-untyped]
            from openpyxl.styles import (  # type: ignore[import-untyped]
                Alignment,
                Border,
                Font,
                Side,
            )
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

        date_str = malote.date or "unknown"
        try:
            dt = datetime.fromisoformat(date_str)
            date_display = dt.strftime("%d/%m")
        except ValueError:
            date_display = date_str

        wb = openpyxl.Workbook()
        active_sheet = wb.active
        if active_sheet is not None:
            wb.remove(active_sheet)

        for tipo, tab_name in TIPO_LABELS.items():
            ws = wb.create_sheet(title=tab_name)

            subtitle = f"{TIPO_TITLES[tipo]} - {date_display}"

            ws["A1"] = "USAFA OCIAN"
            ws.merge_cells("A1:B1")
            ws["A2"] = subtitle
            ws.merge_cells("A2:B2")

            tipo_registros = [r for r in registros if r.tipo == tipo]
            tipo_registros.sort(key=lambda r: r.paciente_name or "")

            for reg in tipo_registros:
                items_str = "\n".join(reg.items)
                ws.append(
                    [
                        reg.paciente_name or "",
                        items_str,
                    ]
                )

            max_a = 10
            max_b = 10
            for row in ws.iter_rows(min_row=3, max_row=ws.max_row):
                a_val = str(row[0].value or "")
                max_a = max(max_a, len(a_val))
                b_val = row[1].value
                if b_val:
                    longest_line = max(len(line) for line in str(b_val).split("\n"))
                    max_b = max(max_b, longest_line)

            ws.column_dimensions["A"].width = min(max_a + 4, 50)
            ws.column_dimensions["B"].width = min(max_b + 4, 80)

            main_font = Font(name="Arial", size=11)
            title1_font = Font(name="Arial", size=20)
            title2_font = Font(name="Arial", size=16)
            center = Alignment(horizontal="center", vertical="center")
            center_wrap = Alignment(
                horizontal="center", vertical="center", wrap_text=True
            )
            thin_border = Border(
                left=Side(style="thin"),
                right=Side(style="thin"),
                top=Side(style="thin"),
                bottom=Side(style="thin"),
            )

            for cell in ws[1]:
                cell.font = title1_font
                cell.alignment = center
                cell.border = thin_border
            for cell in ws[2]:
                cell.font = title2_font
                cell.alignment = center
                cell.border = thin_border

            for row in ws.iter_rows(min_row=3, max_row=ws.max_row):
                for cell in row:
                    cell.font = main_font
                    if cell.value and "\n" in str(cell.value):
                        cell.alignment = center_wrap
                    else:
                        cell.alignment = center
                    if cell.value is not None:
                        cell.border = thin_border

            ws.page_setup.paperSize = ws.PAPERSIZE_A4
            ws.page_setup.orientation = "portrait"
            ws.page_setup.fitToWidth = 1
            ws.page_setup.fitToHeight = 0
            ws.sheet_properties.pageSetUpPr.fitToPage = True

            ws.page_setup.pageOrder = "downThenOver"
            ws.sheet_view.showGridLines = False

            ws.print_options.horizontalCentered = True
            ws.print_options.verticalCentered = False

        try:
            timestamp = datetime.now().strftime("%H%M%S")
            safe_date = date_display.replace("/", "-")
            filename = f"Malote_{safe_date}_{timestamp}.xlsx"

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
            raise SavePathError(str(e)) from e
