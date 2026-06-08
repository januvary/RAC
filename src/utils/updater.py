#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from src import __version__

REPO = "januvary/RAC"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
STAGING_DIR = "_update_staging"


def _get_auth_headers() -> dict:
    headers = {"User-Agent": "RAC-Updater", "Accept": "application/vnd.github+json"}
    try:
        token = subprocess.check_output(
            ["gh", "auth", "token"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
    except Exception:
        pass
    return headers


def _app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent


def _internal_dir() -> Path:
    app = _app_dir()
    candidate = app / "_internal"
    if candidate.is_dir():
        return candidate
    return app


def staging_path() -> Path:
    return _app_dir() / STAGING_DIR


def apply_pending_update() -> bool:
    staging = staging_path()
    if not staging.is_dir():
        return False

    internal = _internal_dir()
    staging_internal = staging / "_internal"

    src = staging_internal if staging_internal.is_dir() else staging

    try:
        for item in internal.iterdir():
            if item.name == STAGING_DIR:
                continue
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink(missing_ok=True)

        for item in src.iterdir():
            dest = internal / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        shutil.rmtree(staging, ignore_errors=True)
        return True
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        return False


def _parse_version(tag: str) -> tuple:
    return tuple(int(x) for x in tag.lstrip("v").split("."))


def is_newer(remote_tag: str) -> bool:
    try:
        return _parse_version(remote_tag) > _parse_version(__version__)
    except (ValueError, IndexError):
        return False


class UpdateCheckWorker(QThread):
    update_available = Signal(str, str, str)
    update_downloaded = Signal(str)
    update_failed = Signal(str)
    no_update = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._download_dir = None

    def run(self):
        try:
            import urllib.request

            headers = _get_auth_headers()
            req = urllib.request.Request(API_URL, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            tag = data.get("tag_name", "")
            if not tag or not is_newer(tag):
                self.no_update.emit()
                return

            notes = data.get("body", "") or f"Release {tag}"
            asset_url = None
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                if name.endswith(".zip"):
                    asset_url = asset.get("browser_download_url")
                    break

            if not asset_url:
                self.update_failed.emit("No downloadable asset found.")
                return

            self.update_available.emit(tag, notes, asset_url)

            tmp = tempfile.mkdtemp(prefix="rac_update_")
            zip_path = Path(tmp) / "update.zip"

            zip_req = urllib.request.Request(
                asset_url, headers=_get_auth_headers()
            )
            with urllib.request.urlopen(zip_req, timeout=120) as resp:
                with open(zip_path, "wb") as f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)

            staging = staging_path()
            if staging.is_dir():
                shutil.rmtree(staging)

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(staging)

            shutil.rmtree(tmp, ignore_errors=True)

            nested = staging / "RAC"
            if nested.is_dir():
                for item in nested.iterdir():
                    dest = staging / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)
                shutil.rmtree(nested)

            self.update_downloaded.emit(tag)

        except Exception as e:
            self.update_failed.emit(str(e))
