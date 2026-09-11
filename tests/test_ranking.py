from __future__ import annotations

import unittest
from datetime import UTC, datetime

from s_n_sales.domain.ranking import RANK_VERSION, RankInput, rank_observation
from s_n_sales.pipeline.draft import observation_to_rank


class RankingTests(unittest.TestCase):
    def test_deterministic_same_input(self) -> None:
        now = datetime(2026, 9, 11, 4, 0, tzinfo=UTC)
        observed = datetime(2026, 9, 11, 3, 0, tzinfo=UTC)
        inp = RankInput(
            observation_id="obs-1",
            sale_price_minor=150_000,
            list_price_minor=200_000,
            currency="VND",
            stock_status="in_stock",
            observed_at=observed,
            now=now,
        )
        a = rank_observation(inp)
        b = rank_observation(inp)
        self.assertEqual(a, b)
        self.assertEqual(a["rank_version"], RANK_VERSION)
        self.assertGreaterEqual(len(a["reasons"]), 1)
        self.assertGreater(a["score"], 0.5)

    def test_pipeline_from_fixture_shape(self) -> None:
        obs = {
            "observation_id": "obs-demo-001",
            "sale_price_minor": 150_000,
            "list_price_minor": 200_000,
            "currency": "VND",
            "stock_status": "unknown",
            "observed_at": "2026-09-11T03:00:00Z",
        }
        now = datetime(2026, 9, 11, 3, 30, tzinfo=UTC)
        result = observation_to_rank(obs, now=now)
        self.assertEqual(result["schema_version"], "rank-result.v1")
        self.assertEqual(result["observation_id"], "obs-demo-001")


if __name__ == "__main__":
    unittest.main()
