"""Canonical JSON and aware UTC helpers for versioned application records."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any


def canonical(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def utc(value: datetime | str) -> datetime:
    if not isinstance(value, (str, datetime)):
        raise ValueError("datetime_required")
    parsed = (
        datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    )
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone_required")
    return parsed.astimezone(UTC)


def iso(value: datetime | str) -> str:
    return utc(value).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError("nonfinite_json")


def json_object(raw: bytes, *, max_bytes: int = 1024 * 1024) -> dict[str, Any]:
    if not raw or len(raw) > max_bytes:
        raise ValueError("json_size_limit")
    try:
        obj = json.loads(raw.decode("utf-8"), parse_constant=_constant, object_pairs_hook=_pairs)
    except (UnicodeError, RecursionError) as exc:
        raise ValueError("invalid_json") from exc
    if not isinstance(obj, dict):
        raise ValueError("json_object_required")
    return obj
