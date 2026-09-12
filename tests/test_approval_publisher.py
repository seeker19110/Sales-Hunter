from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from s_n_sales.pipeline.approval import (
    ApprovalError,
    assert_approval_matches_draft,
    decide_approval,
)
from s_n_sales.pipeline.draft import observation_to_rank
from s_n_sales.pipeline.publication import build_publication_candidate
from s_n_sales.pipeline.publisher import FakePlatformClient, Publisher, PublishError

ROOT = Path(__file__).resolve().parents[1]


class ApprovalPublisherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 9, 11, 5, 0, tzinfo=UTC)
        obs = json.loads(
            (ROOT / "schemas/examples/valid/offer-observation.v1.json").read_text(encoding="utf-8")
        )
        rank = observation_to_rank(obs, now=self.now)
        self.candidate = build_publication_candidate(
            obs,
            rank,
            content="Deal demo approved path",
            affiliate_url="https://example.com/aff/item-demo-001",
            target_channel="telegram:s-n-sales-demo",
        )

    def test_decide_approval_approved(self) -> None:
        record = decide_approval(
            self.candidate,
            status="approved",
            decided_by="operator@example.com",
            decided_at=self.now,
        )
        self.assertEqual(record["status"], "approved")
        self.assertEqual(record["draft_sha256"], self.candidate["draft_sha256"])
        schema = json.loads((ROOT / "schemas/approval-record.v1.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(record)

    def test_changed_draft_invalidates_approval(self) -> None:
        approval = decide_approval(
            self.candidate,
            status="approved",
            decided_by="op",
            decided_at=self.now,
        )
        changed = dict(self.candidate)
        changed["content"] = "changed content"
        changed["draft_sha256"] = "a" * 64
        with self.assertRaises(ApprovalError):
            assert_approval_matches_draft(approval, changed)

    def test_dry_run_blocks_publish(self) -> None:
        approval = decide_approval(
            self.candidate,
            status="approved",
            decided_by="op",
            decided_at=self.now,
        )
        pub = Publisher(dry_run=True)
        with self.assertRaises(PublishError) as ctx:
            pub.publish(self.candidate, approval, now=self.now)
        self.assertIn("dry_run", str(ctx.exception))

    def test_kill_switch_blocks(self) -> None:
        approval = decide_approval(
            self.candidate,
            status="approved",
            decided_by="op",
            decided_at=self.now,
        )
        pub = Publisher(dry_run=False, client=FakePlatformClient())
        with self.assertRaises(PublishError):
            pub.publish(self.candidate, approval, now=self.now, system_kill_switch=True)

    def test_publish_idempotent_with_fake_client(self) -> None:
        approval = decide_approval(
            self.candidate,
            status="approved",
            decided_by="op",
            decided_at=self.now,
        )
        client = FakePlatformClient()
        pub = Publisher(dry_run=False, client=client)
        r1 = pub.publish(self.candidate, approval, now=self.now)
        r2 = pub.publish(self.candidate, approval, now=self.now)
        self.assertEqual(r1["idempotency_key"], r2["idempotency_key"])
        self.assertEqual(r1["platform_post_id"], r2["platform_post_id"])
        self.assertEqual(r1["status"], "published")
        schema = json.loads((ROOT / "schemas/publish-receipt.v1.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(r1)

    def test_rejected_cannot_publish(self) -> None:
        approval = decide_approval(
            self.candidate,
            status="rejected",
            decided_by="op",
            decided_at=self.now,
            reason="bad claim",
        )
        pub = Publisher(dry_run=False, client=FakePlatformClient())
        with self.assertRaises(ApprovalError):
            pub.publish(self.candidate, approval, now=self.now)


if __name__ == "__main__":
    unittest.main()
