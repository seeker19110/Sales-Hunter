"""Publish multi-channel — mỗi kênh một idempotency_key, dry-run mặc định."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from s_n_sales.pipeline.publisher import Publisher, PublishError


def publish_multi_channel(
    publication_candidate: dict[str, Any],
    approval: dict[str, Any],
    channels: list[str],
    *,
    publisher: Publisher,
    now: datetime,
    system_kill_switch: bool = False,
    disabled_channels: frozenset[str] | set[str] | None = None,
) -> dict[str, dict[str, Any] | dict[str, str]]:
    """Thử publish lần lượt từng kênh.

    Trả map channel -> receipt dict hoặc {"error": "..."}.
    Không dừng toàn bộ nếu một kênh lỗi (best-effort per channel).
    """
    if not channels:
        raise PublishError("channels không được rỗng")
    disabled = frozenset(disabled_channels or ())
    results: dict[str, dict[str, Any] | dict[str, str]] = {}

    for channel in channels:
        if channel in disabled or system_kill_switch:
            results[channel] = {"error": "kill_switch"}
            continue
        candidate = deepcopy(publication_candidate)
        candidate["target_channel"] = channel
        base_hash = candidate.get("draft_sha256", "")
        obs = candidate.get("observation_id", "")
        candidate["idempotency_key"] = f"{obs}:{channel}:{base_hash}"
        try:
            receipt = publisher.publish(
                candidate,
                approval,
                now=now,
                system_kill_switch=False,
                channel_kill_switch=False,
            )
            results[channel] = receipt
        except PublishError as exc:
            results[channel] = {"error": str(exc)}

    return results
