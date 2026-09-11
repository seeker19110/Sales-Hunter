"""Fake adapter: đọc fixture JSON local."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_observation_fixture(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("fixture phải là object JSON")
    return data
