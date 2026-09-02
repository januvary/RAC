#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit watcher — discovers unit data folders, polls for database changes,
and maintains current aggregate state.

Each unit is identified by a folder under the root that contains
``data/registros.db``.  The watcher tracks file mtime + size and
re-reads only databases that changed since the last poll.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Callable

from aggregator.models import AggregateStats, UsafaStats
from aggregator.reader import aggregate, read_unit

log = logging.getLogger(__name__)


class UnitWatcher:
    """Watches a set of unit data folders for database changes.

    Usage::

        watcher = UnitWatcher(Path("\\\\server\\SISTEMAS"))
        watcher.discover()

        # In a loop or timer:
        watcher.poll()
        stats = watcher.aggregate()

    ``discover()`` scans the root for folders containing
    ``data/registros.db``.  Call it again later to pick up new units.
    """

    def __init__(
        self,
        root: Path,
        *,
        poll_interval: float = 5.0,
        on_change: Callable[[str], None] | None = None,
    ) -> None:
        self._root = root
        self._poll_interval = poll_interval
        self._on_change = on_change

        # unit_id → UnitState
        self._units: dict[str, _UnitState] = {}

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover(self) -> list[str]:
        """Scan root for unit folders and (re-)register them.

        A unit folder is any immediate child of ``root`` that contains
        ``data/registros.db``.

        Returns the list of newly discovered unit IDs.
        """
        new_units: list[str] = []
        if not self._root.is_dir():
            return new_units

        for child in sorted(self._root.iterdir()):
            if not child.is_dir():
                continue
            db_path = child / "data" / "registros.db"
            if not db_path.exists():
                continue
            uid = child.name
            if uid not in self._units:
                self._units[uid] = _UnitState(folder=child, db_path=db_path)
                new_units.append(uid)
                log.info("Discovered unit: %s (%s)", uid, child)

        return new_units

    @property
    def unit_ids(self) -> list[str]:
        return list(self._units.keys())

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    def poll(self) -> list[str]:
        """Check all known units for database changes.

        Returns the list of unit IDs whose databases changed (and were
        re-read).  Also picks up newly appeared databases for units
        discovered earlier.
        """
        changed: list[str] = []

        for uid, state in self._units.items():
            # If the DB didn't exist at discover time but does now, pick it up.
            if not state.db_path.exists():
                continue

            try:
                stat = state.db_path.stat()
            except OSError:
                continue

            current_mtime = stat.st_mtime
            current_size = stat.st_size

            if current_mtime == state.last_mtime and current_size == state.last_size:
                continue

            # Changed — re-read.
            stats = read_unit(
                state.folder,
                usafa_id=state.usafa_id,
                usafa_name=state.usafa_name,
            )
            if stats is not None:
                state.last_mtime = current_mtime
                state.last_size = current_size
                state.stats = stats
                state.usafa_id = stats.usafa_id
                state.usafa_name = stats.usafa_name
                changed.append(uid)
                log.debug("Unit %s changed, re-read %d registros", uid, stats.registros)
                if self._on_change:
                    self._on_change(uid)

        return changed

    def poll_forever(self) -> None:
        """Blocking poll loop.  Ctrl+C to stop."""
        log.info(
            "Watching %d unit(s) every %.1fs.  Ctrl+C to stop.",
            len(self._units),
            self._poll_interval,
        )
        try:
            while True:
                self.poll()
                time.sleep(self._poll_interval)
        except KeyboardInterrupt:
            log.info("Stopped.")

    # ------------------------------------------------------------------
    # State access
    # ------------------------------------------------------------------

    def get_unit(self, unit_id: str) -> UsafaStats | None:
        state = self._units.get(unit_id)
        return state.stats if state else None

    def get_all_units(self) -> list[UsafaStats]:
        return [
            state.stats
            for state in self._units.values()
            if state.stats is not None
        ]

    def aggregate(self) -> AggregateStats:
        return aggregate(self.get_all_units())


class _UnitState:
    """Internal tracking state for one unit."""

    __slots__ = (
        "folder",
        "db_path",
        "last_mtime",
        "last_size",
        "usafa_id",
        "usafa_name",
        "stats",
    )

    def __init__(self, folder: Path, db_path: Path) -> None:
        self.folder = folder
        self.db_path = db_path
        self.last_mtime: float = 0.0
        self.last_size: int = -1
        self.usafa_id: str | None = None
        self.usafa_name: str | None = None
        self.stats: UsafaStats | None = None
