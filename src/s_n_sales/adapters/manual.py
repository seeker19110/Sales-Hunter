"""Manual observation adapter — file/JSON local, không mạng.

source_method phải là \"manual\". Không giả dữ liệu live API.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from s_n_sales.pipeline.draft import ObservationValidationError, validate_observation


class ManualAdapterError(ValueError):
    """Lỗi tải hoặc kiểm tra observation manual."""


def load_manual_observation(
    path: Path,
    *,
    require_source_method_manual: bool = True,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Đọc observation JSON từ đĩa; bắt buộc source_method=manual (mặc định)."""
    if not path.is_file():
        raise ManualAdapterError(f"không tìm thấy file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManualAdapterError(f"JSON không hợp lệ: {exc}") from exc
    if not isinstance(data, dict):
        raise ManualAdapterError("observation phải là object JSON")

    if require_source_method_manual and data.get("source_method") != "manual":
        raise ManualAdapterError(
            "manual adapter chỉ nhận source_method=manual "
            f"(nhận được {data.get('source_method')!r})"
        )

    clock = now if now is not None else datetime.now(UTC)
    try:
        validate_observation(data, now=clock)
    except ObservationValidationError as exc:
        raise ManualAdapterError(str(exc)) from exc
    return data
