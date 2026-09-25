"""Audit regressions: actual protected values, not two caller-controlled hashes."""

from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from s_n_sales.api.store import OperatorStore
from s_n_sales.api.store_sqlite import SqliteOperatorStore
from s_n_sales.pipeline.approval import (
    ApprovalError,
    assert_approval_matches_draft,
    decide_approval,
)
from s_n_sales.pipeline.multi_channel import publish_multi_channel
from s_n_sales.pipeline.publication import build_publication_candidate, compute_draft_sha256
from s_n_sales.pipeline.publisher import FakePlatformClient, Publisher, PublishError

ROOT = Path(__file__).resolve().parents[1]


class IntegrityBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 9, 25, 7, tzinfo=timezone(timedelta(hours=7)))
        observation = json.loads(
            (ROOT / "schemas/examples/valid/offer-observation.v1.json").read_text(encoding="utf-8")
        )
        self.candidate = build_publication_candidate(
            observation,
            {},
            content="Nội dung đã xem",
            affiliate_url="https://example.com/affiliate",
            target_channel="manual_export",
        )
        self.store = OperatorStore()
        self.store.upsert_candidate(self.candidate)
        self.approval = self.store.approve(
            self.candidate["publication_id"],
            decided_by="reviewer",
            now=self.now,
            expected_revision=self.store.get_revision(self.candidate["publication_id"]),
        )

    def changed_candidates(self) -> list[dict[str, Any]]:
        changes = []
        for field, value in (
            ("content", "Chưa được duyệt"),
            ("affiliate_url", "https://example.com/other"),
            ("affiliate_disclosure", "Disclosure bị thay"),
            ("observation_id", "other-observation"),
        ):
            candidate = deepcopy(self.candidate)
            candidate[field] = value
            changes.append(candidate)
        candidate = deepcopy(self.candidate)
        candidate["claim_snapshot"]["sale_price_minor"] += 1
        changes.append(candidate)
        return changes

    def test_approve_recomputes_every_protected_field(self) -> None:
        for candidate in self.changed_candidates():
            with self.subTest(candidate=candidate), self.assertRaises(ApprovalError):
                decide_approval(
                    candidate, status="approved", decided_by="reviewer", decided_at=self.now
                )

    def test_publish_recomputes_every_protected_field_before_side_effect(self) -> None:
        client = FakePlatformClient()
        publisher = Publisher(client=client, dry_run=False, approval_source=self.store)
        for candidate in self.changed_candidates():
            with self.subTest(candidate=candidate), self.assertRaises(ApprovalError):
                publisher.publish(candidate, self.approval, now=self.now)
        self.assertEqual(client.posts, {})

    def test_both_store_ingest_paths_reject_tampered_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for store in (OperatorStore(), SqliteOperatorStore(Path(directory) / "store.db")):
                try:
                    for candidate in self.changed_candidates():
                        with (
                            self.subTest(store=type(store).__name__, candidate=candidate),
                            self.assertRaises(ValueError),
                        ):
                            store.upsert_candidate(candidate)
                    self.assertEqual(store.list_candidates(), [])
                finally:
                    store.close()

    def test_approval_requires_complete_schema_and_nonblank_actor(self) -> None:
        client = FakePlatformClient()
        for field in ("schema_version", "approval_id", "decided_at", "decided_by"):
            approval = dict(self.approval)
            del approval[field]
            with self.subTest(field=field), self.assertRaises(ApprovalError):
                Publisher(client=client, dry_run=False, approval_source=self.store).publish(
                    self.candidate, approval, now=self.now
                )
        approval = dict(self.approval, decided_by=" \t ")
        with self.assertRaises(ApprovalError):
            assert_approval_matches_draft(approval, self.candidate)
        self.assertEqual(client.posts, {})

    def test_bad_approval_time_and_extra_fields_are_rejected(self) -> None:
        for changes in (
            {"decided_at": "yesterday"},
            {"decided_at": "2026-09-25T00:00:00"},
            {"admin": True},
        ):
            with self.subTest(changes=changes), self.assertRaises(ApprovalError):
                assert_approval_matches_draft(dict(self.approval, **changes), self.candidate)

    def test_multi_channel_preflight_rejects_invalid_later_channel(self) -> None:
        client = FakePlatformClient()
        with self.assertRaises(PublishError):
            publish_multi_channel(
                self.candidate,
                self.approval,
                ["manual_export", " "],
                publisher=Publisher(client=client, dry_run=False, approval_source=self.store),
                now=self.now,
            )
        self.assertEqual(client.posts, {})

    def test_multi_channel_preflight_rejects_duplicate_channels(self) -> None:
        client = FakePlatformClient()
        with self.assertRaises(PublishError):
            publish_multi_channel(
                self.candidate,
                self.approval,
                ["manual_export", "manual_export"],
                publisher=Publisher(client=client, dry_run=False, approval_source=self.store),
                now=self.now,
            )
        self.assertEqual(client.posts, {})

    def test_multi_channel_integrity_is_global_even_when_channels_disabled(self) -> None:
        with self.assertRaises(ApprovalError):
            publish_multi_channel(
                self.changed_candidates()[0],
                self.approval,
                ["manual_export"],
                publisher=Publisher(),
                now=self.now,
                disabled_channels={"manual_export"},
            )

    def test_receipt_and_fake_timestamp_are_actual_utc(self) -> None:
        receipt = Publisher(
            client=FakePlatformClient(), dry_run=False, approval_source=self.store
        ).publish(self.candidate, self.approval, now=self.now)
        for field in ("read_back_at", "published_at"):
            self.assertEqual(receipt[field], "2026-09-25T00:00:00Z")
        self.assertEqual(self.approval["decided_at"], "2026-09-25T00:00:00Z")

    def test_stale_hash_is_rejected_even_with_cached_receipt(self) -> None:
        publisher = Publisher(
            client=FakePlatformClient(), dry_run=False, approval_source=self.store
        )
        publisher.publish(self.candidate, self.approval, now=self.now)
        with self.assertRaises(ApprovalError):
            publisher.publish(self.changed_candidates()[0], self.approval, now=self.now)

    def test_receipt_uses_frozen_candidate_across_client_call(self) -> None:
        candidate = self.candidate

        class MutatingClient(FakePlatformClient):
            def publish_and_read_back(self, **kwargs: Any) -> dict[str, str]:
                candidate["publication_id"] = "mutated-during-network"
                return super().publish_and_read_back(**kwargs)

        expected = candidate["publication_id"]
        receipt = Publisher(
            client=MutatingClient(), dry_run=False, approval_source=self.store
        ).publish(candidate, self.approval, now=self.now)
        self.assertEqual(receipt["publication_id"], expected)

    def test_publish_requires_configured_trusted_approval_source(self) -> None:
        client = FakePlatformClient()
        with self.assertRaises(ApprovalError):
            Publisher(client=client, dry_run=False).publish(
                self.candidate, self.approval, now=self.now
            )
        self.assertEqual(client.posts, {})

    def test_self_declared_schema_valid_approval_is_not_trusted(self) -> None:
        forged = dict(self.approval, approval_id="self-declared", decided_by="admin")
        client = FakePlatformClient()
        with self.assertRaises(ApprovalError):
            Publisher(client=client, dry_run=False, approval_source=self.store).publish(
                self.candidate, forged, now=self.now
            )
        self.assertEqual(client.posts, {})

    def test_current_rejection_blocks_old_approval_and_cached_receipt(self) -> None:
        publisher = Publisher(
            client=FakePlatformClient(), dry_run=False, approval_source=self.store
        )
        publisher.publish(self.candidate, self.approval, now=self.now)
        self.store.reject(
            self.candidate["publication_id"],
            decided_by="reviewer",
            now=self.now,
            expected_revision=self.store.get_revision(self.candidate["publication_id"]),
        )
        with self.assertRaises(ApprovalError):
            publisher.publish(self.candidate, self.approval, now=self.now)

    def test_rejected_approval_is_rechecked_after_sqlite_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "approval.db"
            store = SqliteOperatorStore(path)
            store.upsert_candidate(self.candidate)
            approval = store.approve(
                self.candidate["publication_id"],
                decided_by="reviewer",
                now=self.now,
                expected_revision=store.get_revision(self.candidate["publication_id"]),
            )
            store.reject(
                self.candidate["publication_id"],
                decided_by="reviewer",
                now=self.now,
                expected_revision=store.get_revision(self.candidate["publication_id"]),
            )
            store.close()
            store = SqliteOperatorStore(path)
            client = FakePlatformClient()
            try:
                with self.assertRaises(ApprovalError):
                    Publisher(client=client, dry_run=False, approval_source=store).publish(
                        self.candidate, approval, now=self.now
                    )
                self.assertEqual(client.posts, {})
            finally:
                store.close()

    def test_old_approval_cannot_publish_after_authoritative_draft_edit(self) -> None:
        edited = dict(self.candidate, content="A newer draft requires review")
        edited["draft_sha256"] = compute_draft_sha256(
            content=edited["content"],
            affiliate_url=edited["affiliate_url"],
            affiliate_disclosure=edited["affiliate_disclosure"],
            observation_id=edited["observation_id"],
            claim_snapshot=edited["claim_snapshot"],
        )
        edited["approval"] = {"status": "pending", "draft_sha256": edited["draft_sha256"]}
        self.store.upsert_candidate(
            edited, expected_revision=self.store.get_revision(edited["publication_id"])
        )
        client = FakePlatformClient()
        with self.assertRaises(ApprovalError):
            Publisher(client=client, dry_run=False, approval_source=self.store).publish(
                self.candidate, self.approval, now=self.now
            )
        self.assertEqual(client.posts, {})

    def test_valid_channel_agnostic_hash_is_still_accepted(self) -> None:
        changed = dict(self.candidate, target_channel="second-channel")
        assert_approval_matches_draft(self.approval, changed)
        self.assertEqual(self.now.astimezone(UTC).hour, 0)


if __name__ == "__main__":
    unittest.main()
