"""Luồng manual: file observation → rank → publication-candidate (draft-only)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from s_n_sales.adapters.kill_switch import KillSwitch
from s_n_sales.adapters.manual import load_manual_observation
from s_n_sales.pipeline.draft import observation_to_rank
from s_n_sales.pipeline.publication import build_publication_candidate

ADAPTER_NAME = "manual"


def run_manual_to_publication_candidate(
    observation_path: Path,
    *,
    content: str,
    affiliate_url: str,
    target_channel: str,
    now: datetime,
    kill_switch: KillSwitch | None = None,
    disclosure: str | None = None,
) -> dict[str, Any]:
    """E2E draft-only từ file manual. Side effect: none."""
    switch = kill_switch or KillSwitch()
    switch.assert_enabled(ADAPTER_NAME)

    observation = load_manual_observation(observation_path, now=now)
    rank_result = observation_to_rank(observation, now=now)
    return build_publication_candidate(
        observation,
        rank_result,
        content=content,
        affiliate_url=affiliate_url,
        target_channel=target_channel,
        disclosure=disclosure,
    )
