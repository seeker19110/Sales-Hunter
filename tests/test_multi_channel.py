from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime
from pathlib import Path

from s_n_sales.api.store import OperatorStore
from s_n_sales.pipeline.draft import observation_to_rank
from s_n_sales.pipeline.multi_channel import publish_multi_channel
from s_n_sales.pipeline.publication import build_publication_candidate
from s_n_sales.pipeline.publisher import FakePlatformClient, Publisher

ROOT = Path(__file__).resolve().parents[1]


class MultiChannelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 9, 11, 8, 0, tzinfo=UTC)
        obs = json.loads(
            (ROOT / "schemas/examples/valid/offer-observation.v1.json").read_text(encoding="utf-8")
        )
        rank = observation_to_rank(obs, now=self.now)
        self.candidate = build_publication_candidate(
            obs,
            rank,
            content="Multi-channel demo",
            affiliate_url="https://example.com/aff/item-demo-001",
            target_channel="telegram:demo",
        )
        self.store = OperatorStore()
        self.store.upsert_candidate(self.candidate)
        self.approval = self.store.approve(
            self.candidate["publication_id"], decided_by="op", now=self.now
        )

    def test_dry_run_reports_error_per_channel(self) -> None:
        pub = Publisher(dry_run=True)
        results = publish_multi_channel(
            self.candidate,
            self.approval,
            ["telegram:a", "telegram:b"],
            publisher=pub,
            now=self.now,
        )
        self.assertIn("dry_run", results["telegram:a"]["error"])
        self.assertIn("dry_run", results["telegram:b"]["error"])

    def test_fake_client_two_channels_distinct_posts(self) -> None:
        pub = Publisher(dry_run=False, client=FakePlatformClient(), approval_source=self.store)
        results = publish_multi_channel(
            self.candidate,
            self.approval,
            ["telegram:a", "telegram:b"],
            publisher=pub,
            now=self.now,
        )
        self.assertEqual(results["telegram:a"]["status"], "published")
        self.assertEqual(results["telegram:b"]["status"], "published")
        self.assertNotEqual(
            results["telegram:a"]["platform_post_id"],
            results["telegram:b"]["platform_post_id"],
        )
        self.assertNotEqual(
            results["telegram:a"]["idempotency_key"],
            results["telegram:b"]["idempotency_key"],
        )

    def test_disabled_channel(self) -> None:
        pub = Publisher(dry_run=False, client=FakePlatformClient(), approval_source=self.store)
        results = publish_multi_channel(
            self.candidate,
            self.approval,
            ["telegram:a", "telegram:b"],
            publisher=pub,
            now=self.now,
            disabled_channels={"telegram:b"},
        )
        self.assertEqual(results["telegram:b"]["error"], "kill_switch")
        self.assertEqual(results["telegram:a"]["status"], "published")

    def test_draft_sha256_remains_valid_across_channels(self) -> None:
        pub = Publisher(dry_run=False, client=FakePlatformClient(), approval_source=self.store)
        channels = ["telegram:channel_1", "tiktok_shop:channel_2"]
        results = publish_multi_channel(
            self.candidate,
            self.approval,
            channels,
            publisher=pub,
            now=self.now,
        )
        self.assertEqual(results["telegram:channel_1"]["status"], "published")
        self.assertEqual(results["tiktok_shop:channel_2"]["status"], "published")
        self.assertEqual(self.candidate["draft_sha256"], self.approval["draft_sha256"])


if __name__ == "__main__":
    unittest.main()
