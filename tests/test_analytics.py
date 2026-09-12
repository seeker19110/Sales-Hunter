from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from s_n_sales.analytics.events import AnalyticsEvent
from s_n_sales.analytics.metrics import MetricsStore
from s_n_sales.analytics.recall import should_recall_content


class AnalyticsTests(unittest.TestCase):
    def test_record_and_summarize_separates_no_sale_vs_unavailable(self) -> None:
        store = MetricsStore()
        t = datetime(2026, 9, 11, 7, 0, tzinfo=UTC)
        store.record(AnalyticsEvent("click", t, publication_id="pub-1"))
        store.record(AnalyticsEvent("click", t, publication_id="pub-1"))
        store.record(AnalyticsEvent("conversion", t, publication_id="pub-1"))
        store.record(AnalyticsEvent("ingest_no_sale", t, observation_id="obs-1"))
        store.record(AnalyticsEvent("ingest_source_unavailable", t, observation_id="obs-2"))
        store.record(AnalyticsEvent("content_recalled", t, publication_id="pub-old"))

        s = store.summarize()
        self.assertEqual(s.clicks, 2)
        self.assertEqual(s.conversions, 1)
        self.assertEqual(s.ingest_no_sale, 1)
        self.assertEqual(s.ingest_source_unavailable, 1)
        self.assertEqual(s.content_recalled, 1)
        self.assertAlmostEqual(s.conversion_rate or 0.0, 0.5)
        self.assertEqual(s.ingest_no_sale + s.ingest_source_unavailable, 2)

    def test_event_requires_timezone(self) -> None:
        with self.assertRaises(ValueError):
            AnalyticsEvent("click", datetime(2026, 9, 11, 7, 0))

    def test_recall_when_stale(self) -> None:
        observed = datetime(2026, 9, 10, 0, 0, tzinfo=UTC)
        now = datetime(2026, 9, 11, 1, 0, tzinfo=UTC)
        self.assertTrue(should_recall_content(observed_at=observed, now=now))
        self.assertFalse(
            should_recall_content(
                observed_at=observed,
                now=observed + timedelta(hours=1),
                max_age=timedelta(hours=24),
            )
        )


if __name__ == "__main__":
    unittest.main()
