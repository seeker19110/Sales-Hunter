"""Event analytics — schema nhẹ, deterministic."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

EventType = Literal[
    "click",
    "conversion",
    "ingest_no_sale",
    "ingest_source_unavailable",
    "content_recalled",
]


@dataclass(frozen=True, slots=True)
class AnalyticsEvent:
    event_type: EventType
    occurred_at: datetime
    publication_id: str | None = None
    observation_id: str | None = None
    channel: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("occurred_at phải có timezone")
        allowed = {
            "click",
            "conversion",
            "ingest_no_sale",
            "ingest_source_unavailable",
            "content_recalled",
        }
        if self.event_type not in allowed:
            raise ValueError(f"event_type không hợp lệ: {self.event_type}")

    def to_dict(self) -> dict[str, Any]:
        at = self.occurred_at.astimezone(UTC)
        return {
            "event_type": self.event_type,
            "occurred_at": at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "publication_id": self.publication_id,
            "observation_id": self.observation_id,
            "channel": self.channel,
            "metadata": dict(self.metadata) if self.metadata else None,
        }
