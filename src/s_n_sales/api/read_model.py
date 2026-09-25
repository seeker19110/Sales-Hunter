"""Typed, read-only price presentation shared by operator list and detail."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

UNKNOWN = "Chưa xác minh"


def _minor(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _money_label(value: int | None, currency: object) -> str:
    # The v1 contract supports VND only. Never assume another currency's exponent.
    if value is None or currency != "VND":
        return UNKNOWN
    return f"{value:,}".replace(",", ".") + " VND"


def _discount_label(sale: int | None, listed: int | None, currency: object) -> str:
    if currency != "VND" or sale is None or listed is None or listed == 0 or sale > listed:
        return UNKNOWN
    # Integer arithmetic, rounded half-up to two decimal percentage points.
    hundredths, remainder = divmod((listed - sale) * 10000, listed)
    hundredths += int(remainder * 2 >= listed)
    whole, fraction = divmod(hundredths, 100)
    suffix = f",{fraction:02d}".rstrip("0") if fraction else ""
    return f"{whole}{suffix}%"


@dataclass(frozen=True)
class CandidatePriceView:
    platform: str
    sale: str
    listed: str
    discount: str

    @classmethod
    def from_candidate(cls, candidate: dict[str, Any]) -> CandidatePriceView:
        raw = candidate.get("claim_snapshot")
        claim = raw if isinstance(raw, dict) else {}
        platform = {"shopee": "Shopee", "tiktok_shop": "TikTok Shop"}.get(
            str(claim.get("platform", "")), UNKNOWN
        )
        currency = claim.get("currency")
        sale = _minor(claim.get("sale_price_minor"))
        listed = _minor(claim.get("list_price_minor"))
        return cls(
            platform=platform,
            sale=_money_label(sale, currency),
            listed=_money_label(listed, currency),
            discount=_discount_label(sale, listed, currency),
        )
