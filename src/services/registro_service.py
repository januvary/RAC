#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass

from src.database.rac_database import RACDatabase
from src.services.exceptions import ValidationError, DuplicateRecordError
from src.models import Registro

import sqlite3


@dataclass
class SaveResult:
    registro_id: int
    is_update: bool


@dataclass
class EditContext:
    registro: Registro
    items: list[tuple[int, int]]


class RegistroService:
    def __init__(self, db: RACDatabase) -> None:
        self._db = db

    def save(
        self,
        tipo: str,
        paciente_name: str,
        malote_id: int,
        items: list[tuple[int, int]],
        edit_id: int | None = None,
        waiting_docs: bool = False,
        paciente_id: int | None = None,
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
            self._db.update_registro(
                edit_id,
                tipo=tipo,
                paciente_id=resolved_id,
                malote_id=malote_id,
                waiting_docs=waiting_docs,
            )
            self._db.set_registro_items(edit_id, items)
            return SaveResult(registro_id=edit_id, is_update=True)

        existing = self._db.find_registro(tipo, resolved_id, malote_id)
        if existing and existing.id is not None:
            self._db.update_registro(
                existing.id,
                tipo=tipo,
                paciente_id=resolved_id,
                malote_id=malote_id,
                waiting_docs=waiting_docs,
            )
            self._db.set_registro_items(existing.id, items)
            return SaveResult(registro_id=existing.id, is_update=True)

        try:
            new_reg = self._db.create_registro(
                tipo, resolved_id, malote_id, waiting_docs=waiting_docs
            )
        except sqlite3.IntegrityError:
            existing = self._db.find_registro(tipo, resolved_id, malote_id)
            if existing and existing.id is not None:
                self._db.update_registro(
                    existing.id,
                    tipo=tipo,
                    paciente_id=resolved_id,
                    malote_id=malote_id,
                    waiting_docs=waiting_docs,
                )
                self._db.set_registro_items(existing.id, items)
                return SaveResult(registro_id=existing.id, is_update=True)
            raise DuplicateRecordError(
                f"Duplicate: tipo={tipo}, paciente_id={resolved_id}, malote_id={malote_id}"
            )
        if new_reg.id is None:
            raise RuntimeError("Failed to create registro")
        self._db.set_registro_items(new_reg.id, items)
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
        return EditContext(
            registro=reg,
            items=[(item.item_id, item.process_group) for item in items if item.item_id is not None],
        )
