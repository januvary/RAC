#!/usr/bin/env python3
"""Generate 50 registros of each tipo for testing."""

import sys, os, random
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import andaime
from pathlib import Path
andaime.init("RAC", "RACRegistros", root=Path(__file__).parent)

from src.database.rac_database import RACDatabase

FIRST_NAMES = [
    "Ana", "Bruno", "Carlos", "Diana", "Eduardo", "Fernanda", "Gabriel",
    "Helena", "Igor", "Julia", "Kevin", "Lucas", "Mariana", "Nicolas",
    "Olivia", "Paulo", "Rafaela", "Sergio", "Tatiana", "Vanessa",
    "Amanda", "Beatriz", "Caio", "Daniela", "Eliseu", "Flavia",
    "Gustavo", "Isabela", "Jorge", "Karina", "Leandro", "Monica",
    "Natalia", "Otavio", "Patricia", "Quentin", "Renata", "Samuel",
    "Talita", "Ulisses", "Valentina", "Wesley", "Ximena", "Yuri",
    "Zuleica", "Alberto", "Bianca", "Cristiano", "Debora", "Emerson",
    "Adriana", "Benicio", "Catarina", "Diego", "Elena", "Fabiano",
    "Giovanna", "Henrique", "Ingrid", "Juliano", "Larissa", "Marco",
    "Noemia", "Oscar", "Penelope", "Ricardo", "Sandra", "Thiago",
    "Ursula", "Vitor", "Wagner", "Xavier", "Yasmin", "Zander",
    "Alice", "Breno", "Clarice", "Davi", "Elisa", "Felipe",
    "Graziela", "Hugo", "Iris", "Joao", "Katia", "Luis",
    "Marcia", "Nelson", "Orlanda", "Pedro", "Regina", "Simone",
    "Tomas", "Uriel", "Vera", "William", "Xena", "Yvete", "Zilda",
]

LAST_NAMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Lima", "Costa", "Ferreira",
    "Rodrigues", "Almeida", "Nascimento", "Pereira", "Araujo", "Barbosa",
    "Moraes", "Ribeiro", "Martins", "Gomes", "Carvalho", "Rocha", "Dias",
    "Mendes", "Nunes", "Vieira", "Monteiro", "Freitas", "Barros", "Batista",
    "Correia", "Duarte", "Fonseca", "Goncalves", "Machado", "Moreira",
    "Cardoso", "Ramos", "Teixeira", "Vasconcelos", "Cavalcanti", "Lopes",
    "Andrade",
]

db = RACDatabase()

malote = db.create_malote(date.today().isoformat())
assert malote.id is not None
print(f"Malote: {malote.id}")

all_items = db.get_all_items()
item_ids = [i.id for i in all_items if i.id is not None]

paciente_ids = []
used_names = set()
for fn in FIRST_NAMES:
    for ln in LAST_NAMES:
        name = f"{fn} {ln}"
        if name not in used_names and len(paciente_ids) < 110:
            used_names.add(name)
            p = db.create_paciente(name)
            assert p.id is not None
            paciente_ids.append(p.id)

random.shuffle(paciente_ids)
print(f"Created {len(paciente_ids)} pacientes")

tipos = ["entrada", "renovacao", "retirada", "urgente"]
per_patient_tipo: dict[tuple[int, str], int] = {}
count = 0
for tipo in tipos:
    for i in range(50):
        random.shuffle(paciente_ids)
        pid = None
        for candidate in paciente_ids:
            if per_patient_tipo.get((candidate, tipo), 0) < 1:
                pid = candidate
                break
        if pid is None:
            break
        per_patient_tipo[(pid, tipo)] = per_patient_tipo.get((pid, tipo), 0) + 1
        reg = db.create_registro(tipo, pid, malote.id)
        assert reg.id is not None
        n_items = random.randint(1, 5)
        chosen = random.sample(item_ids, min(n_items, len(item_ids)))
        db.set_registro_items(reg.id, chosen)
        count += 1

print(f"Created {count} registros")
db.close()
print("Done")
