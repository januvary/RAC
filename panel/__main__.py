#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Management panel entry point.

Usage:
    python -m panel                                        # local plaintext painel.html
    RAC_PANEL_PASSWORD='...' python -m panel --locked      # encrypted index.html
    RAC_PANEL_PASSWORD='...' python -m panel --publish     # encrypt + push to gh-pages

Reads unit databases directly via the aggregator reader.  The root folder
(the parent of all unit folders) is auto-detected from the project root,
or can be specified with --root.
"""

from __future__ import annotations

import argparse
import base64
import dataclasses
import getpass
import json
import os
import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from panel.render import render_html, render_locked_html  # noqa: E402
from aggregator.reader import read_unit, aggregate  # noqa: E402


def _get_password() -> str:
    pw = os.environ.get("RAC_PANEL_PASSWORD") or os.environ.get("PANEL_PASSWORD")
    if pw:
        return pw
    return getpass.getpass("Senha do painel: ")


def _build_from_local(root: Path | None = None):
    """Read all unit databases under *root* and return AggregateStats.

    If *root* is None, uses the project root (the folder containing this
    project's data/ directory as a single-unit fallback).
    """
    if root is None:
        root = _PROJECT_ROOT

    units = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        db_path = child / "data" / "registros.db"
        if not db_path.exists():
            continue
        stats = read_unit(child)
        if stats is not None:
            units.append(stats)

    # Fallback: if no sub-unit folders found, try reading the root itself
    # (single-unit mode, e.g. running from a unit's own folder).
    if not units:
        db_path = root / "data" / "registros.db"
        if db_path.exists():
            stats = read_unit(root)
            if stats is not None:
                units.append(stats)

    return aggregate(units)


def _publish_to_github_pages(html: str, repo: str = "januvary/RAC") -> str:
    content_b64 = base64.b64encode(html.encode("utf-8")).decode("ascii")

    def gh_post(endpoint: str, body_json: str) -> dict:
        result = subprocess.run(
            ["gh", "api", "-X", "POST", endpoint, "--input", "-"],
            input=body_json,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)

    blob_sha = gh_post(
        f"repos/{repo}/git/blobs",
        json.dumps({"content": content_b64, "encoding": "base64"}),
    )["sha"]
    tree_sha = gh_post(
        f"repos/{repo}/git/trees",
        json.dumps(
            {
                "tree": [
                    {
                        "path": "index.html",
                        "mode": "100644",
                        "type": "blob",
                        "sha": blob_sha,
                    }
                ]
            }
        ),
    )["sha"]
    commit_sha = gh_post(
        f"repos/{repo}/git/commits",
        json.dumps({"tree": tree_sha, "message": "Panel: update", "parents": []}),
    )["sha"]

    update = subprocess.run(
        [
            "gh",
            "api",
            "-X",
            "PATCH",
            "--input",
            "-",
            f"repos/{repo}/git/refs/heads/gh-pages",
        ],
        input=json.dumps({"sha": commit_sha, "force": True}),
        capture_output=True,
        text=True,
    )
    if update.returncode != 0:
        subprocess.run(
            [
                "gh",
                "api",
                "-X",
                "POST",
                "--input",
                "-",
                f"repos/{repo}/git/refs",
            ],
            input=json.dumps({"ref": "refs/heads/gh-pages", "sha": commit_sha}),
            capture_output=True,
            text=True,
            check=True,
        )
    return f"https://{repo.split('/')[0]}.github.io/{repo.split('/')[1]}/"


def main() -> None:
    parser = argparse.ArgumentParser(description="RAC management panel builder")
    parser.add_argument(
        "--locked",
        action="store_true",
        help="Encrypt with password (for public hosting)",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Push encrypted page to GitHub Pages",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Pasta raiz contendo as pastas de cada unidade",
    )
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output file")
    args = parser.parse_args()

    aggregate_stats = _build_from_local(args.root)

    encrypt = args.locked or args.publish
    if encrypt:
        password = _get_password()
        payload = json.dumps(
            dataclasses.asdict(aggregate_stats), ensure_ascii=False
        ).encode("utf-8")
        from panel.crypto import encrypt_payload

        blob = encrypt_payload(payload, password)
        html = render_locked_html(blob)
        filename = "index.html"
    else:
        html = render_html(aggregate_stats)
        filename = "painel.html"

    target = args.output or (_PROJECT_ROOT / filename)
    target.write_text(html, encoding="utf-8")
    print(f"Painel gerado: {target}")

    if args.publish:
        url = _publish_to_github_pages(html)
        print(f"Publicado: {url}")


if __name__ == "__main__":
    main()
