#!/usr/bin/env python3
"""
Create dummy unit folders with SQLite databases for testing the aggregator.

Usage:
    python create_dummy_data.py              # creates dummy_units/ in project root
    python create_dummy_data.py /path/to     # creates dummy_units/ in given path
"""

import json
import random
import sqlite3
import string
from datetime import date, timedelta
from pathlib import Path

UNITS = [
    {"slug": "OCIAN", "name": "USAFA OCIAN"},
    {"slug": "AMIGAOA", "name": "USAFA AMIGAOA"},
    {"slug": "ASA", "name": "USAFA ASA"},
]

# Sample catalog items (name, unidade, cids)
CATALOG_ITEMS = [
    ("adalimumabe 40 mg inj.", "un", '["K50.0","K50.1","L40.0"]'),
    ("adalimumabe biossimilar 40 mg inj.", "un", '["K50.0","K50.1","L40.0"]'),
    ("infliximabe 100 mg inj.", "un", '["K50.0","K50.1","M45"]'),
    ("etanercepte 50 mg inj.", "un", '["M05.0","M05.1","M45"]'),
    ("abatacepte 125 mg inj.", "un", '["M05.0","M06.0"]'),
    ("tocilizumabe 162 mg inj.", "un", '["M05.0","M06.0"]'),
    ("rituximabe 100 mg inj.", "un", '["M05.0","G35"]'),
    ("metotrexato 15 mg/ml inj.", "un", '["M05.0","M06.0","L40.0"]'),
    ("metotrexato 2,5 mg comp.", "un", '["M05.0","M06.0"]'),
    ("azatioprina 50 mg comp.", "un", '["M05.0","K50.0"]'),
    ("micofenolato mofetila 500 mg", "un", '["M05.0","N18.0"]'),
    ("ciclosporina 100 mg caps.", "un", '["M05.0","N18.0"]'),
    ("prednisona 20 mg comp.", "un", '["M05.0","L40.0"]'),
    ("prednisolona 1 mg/ml gotas", "ml", '["H20.1","L40.0"]'),
    ("ácido zoledrônico 5 mg inj.", "un", '["M80.0","M81.0"]'),
    ("denosumabe 60 mg inj.", "un", '["M80.0","M81.0"]'),
    ("teriparatida 750 mcg inj.", "un", '["M80.0","M81.0"]'),
    ("raloxifeno 60 mg comp.", "un", '["M80.0","M81.0"]'),
    ("ácido ursodeoxicolico 150 mg", "un", '["K74.3"]'),
    ("ácido ursodeoxicolico 300 mg", "un", '["K74.3"]'),
]

TIPOS = ["entrada", "renovacao", "solicitacao"]

MALOTE_DATES = [
    date(2026, 1, 12),
    date(2026, 1, 26),
    date(2026, 2, 9),
    date(2026, 2, 23),
    date(2026, 3, 9),
    date(2026, 3, 23),
    date(2026, 4, 6),
    date(2026, 4, 20),
    date(2026, 5, 4),
    date(2026, 5, 18),
    date(2026, 6, 1),
    date(2026, 6, 15),
    date(2026, 6, 29),
    date(2026, 7, 13),
    date(2026, 7, 27),
    date(2026, 8, 10),
    date(2026, 8, 24),
]

NAMES = [
    "Maria Silva", "Joao Santos", "Ana Oliveira", "Pedro Souza",
    "Lucia Ferreira", "Carlos Lima", "Fernanda Costa", "Roberto Almeida",
    "Patricia Ribeiro", "Marcos Araujo", "Juliana Pereira", "Antonio Gomes",
    "Mariana Rodrigues", "Francisco Barbosa", "Camila Martins", "Paulo Melo",
    "Adriana Vieira", "Ricardo Dias", "Sandra Mendes", "Eduardo Nunes",
    "Vanessa Cardoso", "Roberto Pinto", "Cristina Tavares", "Fernando Rocha",
    "Daniela Campos", "Gustavo Freitas", "Isabela Monteiro", "Leonardo Teixeira",
    "Renata Azevedo", "Thiago Carvalho", "Amanda Moreira", "Lucas Batista",
]


def rand_patient_name() -> str:
    return random.choice(NAMES)


def create_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS malotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            arrival_date TEXT
        );
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS items_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            quantidade INTEGER NOT NULL DEFAULT 0,
            unidade TEXT NOT NULL DEFAULT 'un',
            cids TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
            malote_id INTEGER NOT NULL REFERENCES malotes(id),
            created_at TEXT NOT NULL,
            waiting_docs INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS processes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registro_id INTEGER NOT NULL REFERENCES registros(id) ON DELETE CASCADE,
            group_number INTEGER NOT NULL DEFAULT 1,
            months_supply INTEGER NOT NULL DEFAULT 0,
            expected_return_date TEXT
        );
        CREATE TABLE IF NOT EXISTS registro_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registro_id INTEGER NOT NULL REFERENCES registros(id) ON DELETE CASCADE,
            process_id INTEGER REFERENCES processes(id),
            item_id INTEGER NOT NULL REFERENCES items_catalog(id),
            process_group INTEGER NOT NULL DEFAULT 1,
            cid TEXT NOT NULL DEFAULT '',
            quantidade INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_registros_malote ON registros(malote_id);
        CREATE INDEX IF NOT EXISTS idx_registros_paciente ON registros(paciente_id);
        CREATE INDEX IF NOT EXISTS idx_registros_tipo ON registros(tipo);
        CREATE INDEX IF NOT EXISTS idx_pacientes_nome ON pacientes(name COLLATE NOCASE);
        CREATE INDEX IF NOT EXISTS idx_registro_items_registro ON registro_items(registro_id);
        CREATE INDEX IF NOT EXISTS idx_registro_items_item ON registro_items(item_id);
        CREATE INDEX IF NOT EXISTS idx_processes_registro ON processes(registro_id);
    """)
    conn.commit()


def seed_catalog(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    for name, unidade, cids in CATALOG_ITEMS:
        cur.execute(
            "INSERT OR IGNORE INTO items_catalog (name, unidade, cids) VALUES (?, ?, ?)",
            (name, unidade, cids),
        )
    conn.commit()


def seed_malotes(conn: sqlite3.Connection) -> list[int]:
    cur = conn.cursor()
    ids = []
    for d in MALOTE_DATES:
        arrival = (d + timedelta(days=random.randint(1, 3))).isoformat()
        cur.execute(
            "INSERT INTO malotes (date, arrival_date) VALUES (?, ?)",
            (d.isoformat(), arrival),
        )
        ids.append(cur.lastrowid)
    conn.commit()
    return ids


def seed_pacientes(conn: sqlite3.Connection, n: int) -> list[int]:
    cur = conn.cursor()
    ids = []
    used = set()
    for _ in range(n):
        name = rand_patient_name()
        while name in used:
            name = rand_patient_name()
        used.add(name)
        cur.execute("INSERT INTO pacientes (name) VALUES (?)", (name,))
        ids.append(cur.lastrowid)
    conn.commit()
    return ids


def seed_registros(conn: sqlite3.Connection, malote_ids: list[int], paciente_ids: list[int]) -> None:
    cur = conn.cursor()
    item_ids = [row[0] for row in cur.execute("SELECT id FROM items_catalog").fetchall()]

    for malote_id in malote_ids:
        # 3-8 registros per malote
        n_registros = random.randint(3, 8)
        used_patients = set()
        for _ in range(n_registros):
            paciente_id = random.choice(paciente_ids)
            while paciente_id in used_patients:
                paciente_id = random.choice(paciente_ids)
            used_patients.add(paciente_id)

            tipo = random.choice(TIPOS)
            created_at = f"{MALOTE_DATES[malote_ids.index(malote_id)].isoformat()}T{random.randint(8,17):02d}:{random.randint(0,59):02d}:00"
            waiting_docs = random.choices([0, 1], weights=[0.8, 0.2])[0]

            cur.execute(
                "INSERT INTO registros (tipo, paciente_id, malote_id, created_at, waiting_docs) "
                "VALUES (?, ?, ?, ?, ?)",
                (tipo, paciente_id, malote_id, created_at, waiting_docs),
            )
            registro_id = cur.lastrowid

            # 1-3 items per registro
            n_items = random.randint(1, 3)
            selected_items = random.sample(item_ids, min(n_items, len(item_ids)))
            for i, item_id in enumerate(selected_items):
                months = random.choice([1, 2, 3, 6])
                cur.execute(
                    "INSERT INTO processes (registro_id, group_number, months_supply) "
                    "VALUES (?, ?, ?)",
                    (registro_id, 1, months),
                )
                process_id = cur.lastrowid
                cur.execute(
                    "INSERT INTO registro_items "
                    "(registro_id, process_id, item_id, process_group, cid, quantidade) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (registro_id, process_id, item_id, 1, "", random.randint(1, 3)),
                )

    conn.commit()


def create_unit(path: Path, unit_name: str, n_patients: int = 0) -> None:
    data_dir = path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # config.json
    config = {"name": unit_name}
    (data_dir / "config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False))

    # registros.db
    db_path = data_dir / "registros.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    create_schema(conn)
    seed_catalog(conn)
    malote_ids = seed_malotes(conn)

    if n_patients == 0:
        n_patients = random.randint(10, 20)
    paciente_ids = seed_pacientes(conn, n_patients)
    seed_registros(conn, malote_ids, paciente_ids)

    conn.close()
    print(f"  Created: {path} ({n_patients} patients)")


def main() -> None:
    import sys
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    root = base / "dummy_units"
    root.mkdir(parents=True, exist_ok=True)

    print(f"Creating dummy units in {root}/")
    for unit in UNITS:
        unit_path = root / unit["slug"]
        n = random.randint(12, 25)
        create_unit(unit_path, unit["name"], n)

    print(f"\nDone. {len(UNITS)} units created.")


if __name__ == "__main__":
    main()
