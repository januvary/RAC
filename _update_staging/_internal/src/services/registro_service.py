#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.database.rac_database import RACDatabase
from src.services.exceptions import ValidationError, DuplicateRecordError
from src.models import Registro
from src.utils.date_calculator import calculate_return_dates

import sqlite3


@dataclass
class SaveResult:
    registro_id: int
    is_update: bool


@dataclass
class EditContext:
    registro: Registro
    items: list[tuple[int, int]]
    processes: list[tuple[int, int]]


class RegistroService:
    def __init__(self, db: RACDatabase) -> None:
        self._db = db

    def _update_existing(
        self,
        id: int,
        tipo: str,
        paciente_id: int,
        malote_id: int,
        items: list[tuple[int, int]],
        waiting_docs: bool,
        process_months: list[tuple[int, int]] | None = None,
    ) -> SaveResult:
        self._db.update_registro(
            id,
            tipo=tipo,
            paciente_id=paciente_id,
            malote_id=malote_id,
            waiting_docs=waiting_docs,
        )
        self._db.set_registro_items(id, items)
        if process_months is not None:
            self._save_processes(id, tipo, paciente_id, malote_id, waiting_docs, process_months)
        return SaveResult(registro_id=id, is_update=True)

    def _resolve_arrival_date(self, malote_id: int) -> date | None:
        from src.utils.date_calculator import calculate_arrival_date

        malote = self._db.get_malote_by_id(malote_id)
        if not malote:
            return None
        if malote.arrival_date:
            try:
                return date.fromisoformat(malote.arrival_date)
            except (ValueError, TypeError):
                pass
        if malote.date:
            try:
                send = date.fromisoformat(malote.date)
                return calculate_arrival_date(send)
            except (ValueError, TypeError):
                pass
        return None

    def _save_processes(
        self,
        registro_id: int,
        tipo: str,
        paciente_id: int,
        malote_id: int,
        waiting_docs: bool,
        process_months: list[tuple[int, int]],
    ) -> None:
        arrival_date = self._resolve_arrival_date(malote_id)
        returns = calculate_return_dates(
            tipo=tipo,
            arrival_date=arrival_date,
            process_groups=process_months,
            db=self._db,
            paciente_id=paciente_id,
            current_malote_id=malote_id,
            waiting_docs=waiting_docs,
        )
        processes_data = [
            (r.group_number, r.months_supply, r.expected_return_date.isoformat() if r.expected_return_date else None)
            for r in returns
        ]
        new_processes = self._db.set_processes(registro_id, processes_data)
        items = self._db.get_items_for_registro(registro_id)
        items_with_process: list[tuple[int, int, int | None]] = []
        process_by_group = {p.group_number: p.id for p in new_processes}
        for item in items:
            pid = process_by_group.get(item.process_group)
            iid = item.item_id if item.item_id is not None else 0
            items_with_process.append((iid, item.process_group, pid))
        self._db.set_registro_items_with_process(registro_id, items_with_process)

    def save(
        self,
        tipo: str,
        paciente_name: str,
        malote_id: int,
        items: list[tuple[int, int]],
        edit_id: int | None = None,
        waiting_docs: bool = False,
        paciente_id: int | None = None,
        process_months: list[tuple[int, int]] | None = None,
    ) -> SaveResult:
        """Save a registro. paciente_id takes priority if provided;
        otherwise paciente_name is used to find-or-create a patient."""
        if not tipo:
            raise ValidationError("Selecione um tipo")
        paciente_name = paciente_name.strip()
        if not paciente_name and paciente_id is None:
            raise ValidationError("Informe o nome do paciente")

        resolved_id = paciente_id
        if resolved_id is None:
            found = self._db.find_paciente_by_name(paciente_name)
            if found:
                resolved_id = found.id
            else:
                created = self._db.create_paciente(paciente_name)
                resolved_id = created.id

        if resolved_id is None:
            raise RuntimeError("Failed to resolve patient")

        if edit_id is not None:
            return self._update_existing(
                edit_id, tipo, resolved_id, malote_id, items, waiting_docs, process_months
            )

        existing = self._db.find_registro(tipo, resolved_id, malote_id)
        if existing and existing.id is not None:
            return self._update_existing(
                existing.id, tipo, resolved_id, malote_id, items, waiting_docs, process_months
            )

        try:
            new_reg = self._db.create_registro(
                tipo, resolved_id, malote_id, waiting_docs=waiting_docs
            )
        except sqlite3.IntegrityError:
            existing = self._db.find_registro(tipo, resolved_id, malote_id)
            if existing and existing.id is not None:
                return self._update_existing(
                    existing.id, tipo, resolved_id, malote_id, items, waiting_docs, process_months
                )
            raise DuplicateRecordError(
                f"Duplicate: tipo={tipo}, paciente_id={resolved_id}, malote_id={malote_id}"
            )
        if new_reg.id is None:
            raise RuntimeError("Failed to create registro")
        self._db.set_registro_items(new_reg.id, items)
        if process_months is not None:
            self._save_processes(
                new_reg.id, tipo, resolved_id, malote_id, waiting_docs, process_months
            )
        return SaveResult(registro_id=new_reg.id, is_update=False)

    def delete(self, registro_id: int) -> None:
        if registro_id is None or registro_id <= 0:
            raise ValidationError("ID do registro é obrigatório")
        deleted = self._db.delete_registro(registro_id)
        if not deleted:
            raise ValidationError("Registro não encontrado")

    def load_for_edit(self, registro_id: int) -> EditContext | None:
        reg = self._db.get_registro_by_id(registro_id)
        if not reg:
            return None
        items = self._db.get_items_for_registro(registro_id)
        processes = self._db.get_processes_for_registro(registro_id)
        return EditContext(
            registro=reg,
            items=[
                (item.item_id, item.process_group)
                for item in items
                if item.item_id is not None
            ],
            processes=[
                (p.group_number, p.months_supply)
                for p in processes
            ],
        )
