"""Read-only migration rehearsal on an online SQLite backup, never on the source."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any

from s_n_sales.api.store_sqlite import SqliteOperatorStore


def preview_migration(path: str | Path) -> dict[str, Any]:
    source_path = Path(path).resolve(strict=True)
    deadline = time.monotonic() + 30

    def progress(status: int, remaining: int, total: int) -> None:
        del status, remaining, total
        if time.monotonic() > deadline:
            raise TimeoutError("migration_preview_backup_timeout")

    source = sqlite3.connect(source_path.as_uri() + "?mode=ro", uri=True, isolation_level=None)
    working = SqliteOperatorStore(":memory:")
    try:
        source.backup(working._conn, pages=256, progress=progress, sleep=0.01)
        try:
            working._init_schema()
            result: dict[str, Any] = {"valid": True, "manifest": working.migration_manifest()}
        except (ValueError, sqlite3.Error) as exc:
            result = {"valid": False, "error_code": type(exc).__name__}
        return result
    finally:
        source.close()
        working.close()
