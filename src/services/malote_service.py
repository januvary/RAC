#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.database.rac_database import RACDatabase
from src.models import Malote
from src.services.exceptions import ValidationError


class MaloteService:
    def __init__(self, db: RACDatabase) -> None:
        self._db = db

    def create(self, date: str, arrival_date: str | None = None) -> Malote:
        return self._db.create_malote(date, arrival_date=arrival_date)

    def update_send_date(self, malote_id: int, new_date: str) -> None:
        arrival_iso = self._derive_arrival(new_date)
        self._db.update_malote(malote_id, date=new_date, arrival_date=arrival_iso)
        self._recalculate_affected_registros(malote_id)

    def update_arrival_date(self, malote_id: int, arrival_date: str) -> None:
        self._db.update_malote(malote_id, arrival_date=arrival_date)
        self._recalculate_affected_registros(malote_id)

    def delete(self, malote_id: int) -> bool:
        return self._db.delete_malote(malote_id)

    def _derive_arrival(self, iso_date: str) -> str | None:
        from datetime import date as date_cls
        from src.utils.date_calculator import calculate_arrival_date
        try:
            send_dt = date_cls.fromisoformat(iso_date)
            return calculate_arrival_date(send_dt).isoformat()
        except (ValueError, TypeError):
            return None

    def _recalculate_affected_registros(self, malote_id: int) -> None:
        from src.services.registro_service import RegistroService

        registros = self._db.get_registros_by_malote(malote_id)
        svc = RegistroService(self._db)
        for reg in registros:
            if reg.id is None:
                continue
            items = self._db.get_items_for_registro(reg.id)
            item_tuples = [
                (i.item_id, i.process_group)
                for i in items
                if i.item_id is not None
            ]
            processes = self._db.get_processes_for_registro(reg.id)
            process_months = [
                (p.group_number, p.months_supply) for p in processes
            ]
            if not item_tuples:
                continue
            svc.update_existing(
                reg.id,
                reg.tipo,
                reg.paciente_id,
                reg.malote_id,
                item_tuples,
                reg.waiting_docs,
                process_months,
            )
