#!/usr/bin/env python3
"""Reset the database — drops all registros, pacientes, malotes; keeps items_catalog."""

import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.rac_database import RACDatabase

db = RACDatabase()

def _op():
    cursor = db._get_cursor()
    cursor.execute("DELETE FROM registro_items")
    cursor.execute("DELETE FROM registros")
    cursor.execute("DELETE FROM pacientes")
    cursor.execute("DELETE FROM malotes")
    db._commit()
    cursor.close()
    return None

db._retry_on_transient_error(_op, operation_type="write")

print("Database cleaned — items_catalog preserved")
db.close()
