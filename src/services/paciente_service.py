#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.database.rac_database import RACDatabase
from src.models import Paciente
from src.services.exceptions import ValidationError


class PacienteService:
    def __init__(self, db: RACDatabase) -> None:
        self._db = db

    def create(self, name: str) -> Paciente:
        return self._db.create_paciente(name)

    def rename(self, paciente_id: int, new_name: str) -> None:
        new_name = new_name.strip()
        if not new_name:
            raise ValidationError("Nome do paciente é obrigatório")
        paciente = self._db.get_paciente_by_id(paciente_id)
        if not paciente:
            raise ValidationError("Paciente não encontrado")
        self._db.update_paciente(paciente_id, new_name, cid=paciente.cid)

    def update_cid(self, paciente_id: int, cid: str) -> None:
        paciente = self._db.get_paciente_by_id(paciente_id)
        if not paciente:
            raise ValidationError("Paciente não encontrado")
        self._db.update_paciente(paciente_id, paciente.name, cid=cid)

    def delete(self, paciente_id: int) -> bool:
        return self._db.delete_paciente(paciente_id)
