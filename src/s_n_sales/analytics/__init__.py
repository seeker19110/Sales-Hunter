"""Analytics tối thiểu — event + metric, không mạng."""

from s_n_sales.analytics.events import AnalyticsEvent, EventType
from s_n_sales.analytics.metrics import MetricsStore, MetricsSummary
from s_n_sales.analytics.recall import should_recall_content

__all__ = [
    "AnalyticsEvent",
    "EventType",
    "MetricsStore",
    "MetricsSummary",
    "should_recall_content",
]
