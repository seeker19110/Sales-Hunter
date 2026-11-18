"""Fake adapter: đọc fixture JSON local."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from s_n_sales.domain.json_value import json_object


def load_observation_fixture(path: Path) -> dict[str, Any]:
    try:
        return json_object(path.read_bytes())
    except ValueError as exc:
        raise ValueError(f"fixture phải là object JSON hợp lệ: {exc}") from exc
