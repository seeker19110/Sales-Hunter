"""Ghi event và tổng hợp metric — tách no_sale vs source_unavailable."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from s_n_sales.analytics.events import AnalyticsEvent


@dataclass(frozen=True, slots=True)
class MetricsSummary:
    clicks: int
    conversions: int
    ingest_no_sale: int
    ingest_source_unavailable: int
    content_recalled: int
    conversion_rate: float | None  # conversions/clicks if clicks > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "clicks": self.clicks,
            "conversions": self.conversions,
            "ingest_no_sale": self.ingest_no_sale,
            "ingest_source_unavailable": self.ingest_source_unavailable,
            "content_recalled": self.content_recalled,
            "conversion_rate": self.conversion_rate,
        }


@dataclass
class MetricsStore:
    _events: list[AnalyticsEvent] = field(default_factory=list)

    def record(self, event: AnalyticsEvent) -> None:
        self._events.append(event)

    def all_events(self) -> list[AnalyticsEvent]:
        return list(self._events)

    def summarize(self) -> MetricsSummary:
        clicks = conversions = no_sale = unavailable = recalled = 0
        for e in self._events:
            if e.event_type == "click":
                clicks += 1
            elif e.event_type == "conversion":
                conversions += 1
            elif e.event_type == "ingest_no_sale":
                no_sale += 1
            elif e.event_type == "ingest_source_unavailable":
                unavailable += 1
            elif e.event_type == "content_recalled":
                recalled += 1
        rate = (conversions / clicks) if clicks > 0 else None
        return MetricsSummary(
            clicks=clicks,
            conversions=conversions,
            ingest_no_sale=no_sale,
            ingest_source_unavailable=unavailable,
            content_recalled=recalled,
            conversion_rate=rate,
        )
