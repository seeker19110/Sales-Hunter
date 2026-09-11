"""Ranking deterministic — score + reasons, version hóa công thức."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from s_n_sales.domain.money import Money

RANK_VERSION = "rank-v1.0.0"


@dataclass(frozen=True, slots=True)
class RankInput:
    observation_id: str
    sale_price_minor: int
    list_price_minor: int | None
    currency: str
    stock_status: str
    observed_at: datetime
    now: datetime | None = None


def rank_observation(inp: RankInput) -> dict[str, Any]:
    """Trả dict khớp schema rank-result.v1 (không ghi file)."""
    now = inp.now or datetime.now(timezone.utc)
    if inp.observed_at.tzinfo is None:
        observed = inp.observed_at.replace(tzinfo=timezone.utc)
    else:
        observed = inp.observed_at

    sale = Money(inp.sale_price_minor, inp.currency)
    list_price = (
        Money(inp.list_price_minor, inp.currency) if inp.list_price_minor is not None else None
    )
    ratio = sale.discount_ratio(list_price)

    age_seconds = max(0.0, (now - observed).total_seconds())
    reasons: list[dict[str, Any]] = []
    score = 0.0

    if ratio is not None and ratio > 0:
        depth = min(1.0, ratio)
        w = 0.45
        score += depth * w
        reasons.append(
            {
                "code": "discount_depth",
                "message": f"Mức giảm {ratio:.0%} so với list price.",
                "weight": w,
            }
        )
    else:
        reasons.append(
            {
                "code": "no_discount",
                "message": "Không có mức giảm tính được từ list/sale.",
                "weight": 0.0,
            }
        )

    # Freshness: trong 1h = full, tuyến tính về 0 ở 24h
    freshness = max(0.0, 1.0 - age_seconds / 86400.0)
    w_f = 0.35
    score += freshness * w_f
    reasons.append(
        {
            "code": "freshness",
            "message": f"Tuổi observation ~{int(age_seconds)}s.",
            "weight": w_f,
        }
    )

    stock_bonus = 0.2 if inp.stock_status == "in_stock" else 0.0
    if stock_bonus:
        score += stock_bonus
        reasons.append(
            {
                "code": "in_stock",
                "message": "Còn hàng.",
                "weight": stock_bonus,
            }
        )
    else:
        reasons.append(
            {
                "code": "stock_other",
                "message": f"stock_status={inp.stock_status}.",
                "weight": 0.0,
            }
        )

    return {
        "schema_version": "rank-result.v1",
        "rank_id": f"rank-{inp.observation_id}",
        "observation_id": inp.observation_id,
        "score": round(score, 6),
        "rank_version": RANK_VERSION,
        "ranked_at": now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reasons": reasons,
        "features": {
            "discount_ratio": ratio,
            "age_seconds": age_seconds,
            "stock_status": inp.stock_status,
        },
    }
