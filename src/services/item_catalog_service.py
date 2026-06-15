#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.database.rac_database import RACDatabase
from src.models import ItemCatalog


class ItemCatalogService:
    def __init__(self, db: RACDatabase) -> None:
        self._db = db

    def create(self, name: str, unidade: str = "un") -> ItemCatalog:
        return self._db.create_item(name, unidade)

    def all(self) -> list[ItemCatalog]:
        return self._db.get_all_items()

    def update(self, item_id: int, name: str) -> bool:
        return self._db.update_item(item_id, name)

    def delete(self, item_id: int) -> bool:
        return self._db.delete_item(item_id)
