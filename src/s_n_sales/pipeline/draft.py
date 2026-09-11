"""Pipeline an toàn: observation thô → validate → rank-result."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker

from s_n_sales.domain.ranking import RankInput, rank_observation


class ObservationValidationError(ValueError):
    """Observation không đạt JSON Schema hoặc invariant domain."""


@lru_cache(maxsize=1)
def _observation_validator() -> Draft202012Validator:
    root = Path(__file__).resolve().parents[3]
    schema_path = root / "schemas" / "offer-observation.v1.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _parse_aware_datetime(value: object, *, field: str) -> datetime:
    if not isinstance(value, str):
        raise ObservationValidationError(f"{field} phải là ISO 8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ObservationValidationError(f"{field} không phải ISO 8601 hợp lệ") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ObservationValidationError(f"{field} phải có timezone")
    return parsed.astimezone(UTC)


def _require_https(value: object, *, field: str) -> None:
    if not isinstance(value, str) or urlparse(value).scheme != "https":
        raise ObservationValidationError(f"{field} phải dùng HTTPS")


def _validated_rank_input(observation: dict[str, Any], now: datetime) -> RankInput:
    errors = sorted(
        _observation_validator().iter_errors(observation), key=lambda error: list(error.path)
    )
    if errors:
        raise ObservationValidationError(f"observation không khớp schema: {errors[0].message}")

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now phải có timezone")

    list_price_minor = observation["list_price_minor"]
    sale_price_minor = observation["sale_price_minor"]
    if list_price_minor is not None and sale_price_minor > list_price_minor:
        raise ObservationValidationError("sale_price_minor không được lớn hơn list_price_minor")

    _require_https(observation["product_url"], field="product_url")
    evidence = observation["evidence"]
    _require_https(evidence["source_url"], field="evidence.source_url")

    return RankInput(
        observation_id=observation["observation_id"],
        sale_price_minor=sale_price_minor,
        list_price_minor=list_price_minor,
        currency=observation["currency"],
        stock_status=observation["stock_status"],
        observed_at=_parse_aware_datetime(observation["observed_at"], field="observed_at"),
        now=now.astimezone(UTC),
    )


def observation_to_rank(observation: dict[str, Any], *, now: datetime) -> dict[str, Any]:
    """Validate observation external rồi trả rank-result xác định, không side effect."""
    return rank_observation(_validated_rank_input(observation, now))
