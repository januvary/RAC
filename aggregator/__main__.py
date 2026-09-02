#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aggregator entry point.

Usage:
    # One-shot: discover units, read all DBs, print stats
    python -m aggregator /path/to/SISTEMAS

    # Watch mode: poll for changes, print on every change
    python -m aggregator /path/to/SISTEMAS --watch

    # Generate panel HTML from aggregated data
    python -m aggregator /path/to/SISTEMAS --panel -o painel.html

    # Specify custom poll interval (seconds)
    python -m aggregator /path/to/SISTEMAS --watch --interval 2

    # Filter to specific units
    python -m aggregator /path/to/SISTEMAS --units OCIAN AMIGAOA
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from aggregator.reader import read_unit
from aggregator.watcher import UnitWatcher


def _print_summary(watcher: UnitWatcher) -> None:
    stats = watcher.aggregate()
    print(f"\n{'='*60}")
    print(f"  SISTEMAS — Agregador de Dados")
    print(f"  {stats.total_usafas} unidade(s)  ·  "
          f"{stats.total_registros} registro(s)  ·  "
          f"{stats.total_pacientes} paciente(s)")
    print(f"{'='*60}")

    for u in stats.usafas:
        tipos = "  ".join(
            f"{tipo}: {b.registros}"
            for tipo, b in sorted(u.by_tipo.items())
        )
        print(f"\n  [{u.usafa_id}] {u.usafa_name}")
        print(f"    registros={u.registros}  pacientes={u.pacientes}  "
              f"malotes={u.malotes}")
        if tipos:
            print(f"    {tipos}")
        if u.top_items:
            top3 = u.top_items[:3]
            items_str = ", ".join(
                f"{it['medicamento']}({it['registros']})"
                for it in top3
            )
            print(f"    top: {items_str}")

    print()


def _output_json(watcher: UnitWatcher) -> None:
    stats = watcher.aggregate()
    print(json.dumps(dataclasses.asdict(stats), ensure_ascii=False, indent=2))


def _output_panel(watcher: UnitWatcher, output: Path) -> None:
    """Generate panel HTML using the existing panel/render.py."""
    stats = watcher.aggregate()

    # Import here to avoid pulling in PySide6 at the top level.
    sys.path.insert(0, str(_PROJECT_ROOT))
    from panel.render import render_html

    html = render_html(stats)
    output.write_text(html, encoding="utf-8")
    print(f"Panel gerado: {output}")


def _discover_and_read(
    root: Path, unit_ids: list[str] | None
) -> UnitWatcher:
    watcher = UnitWatcher(root)
    watcher.discover()

    if unit_ids:
        # Filter to requested units.
        for uid in list(watcher.unit_ids):
            if uid not in unit_ids:
                del watcher._units[uid]

    # Initial read of all databases.
    watcher.poll()

    return watcher


def main() -> None:
    parser = argparse.ArgumentParser(
        description="RAC Agregador — lê bancos de unidades e agrega dados"
    )
    parser.add_argument(
        "root",
        type=Path,
        help="Pasta raiz contendo as pastas de cada unidade",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Modo contínuo: poll por mudanças e imprime ao detectar",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Intervalo de polling em segundos (padrão: 5)",
    )
    parser.add_argument(
        "--units",
        nargs="*",
        default=None,
        help="Filtrar para unidades específicas (ex: --units OCIAN AMIGAOA)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Saída em formato JSON",
    )
    parser.add_argument(
        "--panel",
        action="store_true",
        help="Gerar HTML do painel gerenciamento",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Arquivo de saída (para --panel ou --json)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Habilitar logging detalhado",
    )

    args = parser.parse_args()

    log_level = logging.WARNING if args.output_json else (logging.DEBUG if args.verbose else logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    root: Path = args.root.resolve()
    if not root.is_dir():
        print(f"Erro: pasta não encontrada: {root}", file=sys.stderr)
        sys.exit(1)

    watcher = _discover_and_read(root, args.units)

    if not watcher.unit_ids:
        print(f"Nenhuma unidade encontrada em {root}", file=sys.stderr)
        print("Esperado: <root>/<unit_folder>/data/registros.db", file=sys.stderr)
        sys.exit(1)

    if args.output_json:
        _output_json(watcher)
        return

    if args.panel:
        output = args.output or (_PROJECT_ROOT / "painel.html")
        _output_panel(watcher, output)
        return

    if args.watch:
        watcher._poll_interval = args.interval
        watcher._on_change = lambda uid: _print_summary(watcher)
        _print_summary(watcher)
        watcher.poll_forever()
    else:
        _print_summary(watcher)


if __name__ == "__main__":
    main()
