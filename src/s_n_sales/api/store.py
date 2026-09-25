"""In-memory operator store using the same transactional rules as persistent SQLite."""

from __future__ import annotations

from s_n_sales.api.store_sqlite import SqliteOperatorStore


class OperatorStore(SqliteOperatorStore):
    def __init__(self) -> None:
        super().__init__(":memory:")
