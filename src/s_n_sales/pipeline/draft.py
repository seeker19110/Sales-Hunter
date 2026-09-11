"""Pipeline tối thiểu: observation dict → rank-result dict."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from s_n_sales.domain.ranking import RankInput, rank_observation


def observation_to_rank(
    observation: dict[str, Any], *, now: datetime | None = None
) -> dict[str, Any]:
    observed_raw = observation["observed_at"]
    if isinstance(observed_raw, str):
        observed_at = datetime.fromisoformat(observed_raw.replace("Z", "+00:00"))
    else:
        observed_at = observed_raw

    inp = RankInput(
        observation_id=observation["observation_id"],
        sale_price_minor=int(observation["sale_price_minor"]),
        list_price_minor=(
            int(observation["list_price_minor"])
            if observation.get("list_price_minor") is not None
            else None
        ),
        currency=observation.get("currency", "VND"),
        stock_status=observation.get("stock_status", "unknown"),
        observed_at=observed_at,
        now=now,
    )
    return rank_observation(inp)
