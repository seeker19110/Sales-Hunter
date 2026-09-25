"""Review-driven edge cases for channel identity, recall and legacy bypass."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from s_n_sales.api.store_sqlite import SqliteOperatorStore
from s_n_sales.domain.json_value import canonical
from s_n_sales.publishing.contracts import LeaseLost
from s_n_sales.publishing.fake import FakeTransport
from s_n_sales.publishing.queue import PublicationQueue
from s_n_sales.publishing.recall import RecallService
from s_n_sales.publishing.worker import PublicationWorker
from s_n_sales.quality.repository import DealRepository
from s_n_sales.quality.urls import UrlPolicy
from test_grounded_flow import NOW, manual_request


class PublicationFollowupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)
        self.store = SqliteOperatorStore(self.path / "operator.db")
        self.addCleanup(self.store.close)
        self.repo = DealRepository(self.store, url_policy=UrlPolicy(frozenset({"example.com"})))
        self.queue = PublicationQueue(self.repo)
        self.transport = FakeTransport(self.path / "remote.db")
        self.addCleanup(self.transport.close)
        self.queue.set_pause("global", "*", paused=False, actor="admin", reason="fixture", now=NOW)

    def draft_and_scope(self, *, channel="fake:sales", title=None):
        request = manual_request()
        request["target_channel"] = channel
        if title is not None:
            request["offer"]["title"] = title
        package = self.repo.import_manual(canonical(request).encode(), actor="op", now=NOW)
        identifier = package.snapshot.candidate["publication_id"]
        scope = self.queue.approve_payload(
            identifier,
            expected_revision=1,
            expected_payload_sha256=package.payload["payload_sha256"],
            actor="op",
            now=NOW,
        )
        enqueue = {
            "publication_id": identifier,
            "expected_revision": scope["revision"],
            "expected_payload_sha256": package.payload["payload_sha256"],
        }
        return package, scope, enqueue

    def test_same_facts_can_have_two_channel_scoped_drafts_without_overwriting(self) -> None:
        package, _, _ = self.draft_and_scope(channel="fake:one")
        other = self.repo.save(
            package.facts,
            affiliate_url="https://example.com/aff",
            target_channel="fake:two",
            actor="op",
            now=NOW,
        )
        self.assertNotEqual(
            other.snapshot.candidate["publication_id"], package.snapshot.candidate["publication_id"]
        )
        self.assertEqual(
            other.snapshot.candidate["draft_sha256"], package.snapshot.candidate["draft_sha256"]
        )
        self.assertNotEqual(other.payload["payload_sha256"], package.payload["payload_sha256"])

    def test_late_worker_cannot_overwrite_recovered_unknown_state(self) -> None:
        _, _, request = self.draft_and_scope()
        intent = self.queue.enqueue_many([request], actor="op", now=NOW)[0]
        claim = self.queue.claim(worker_id="slow", now=NOW)
        assert claim is not None
        self.queue.start_send(claim, now=NOW)
        proof = self.transport.publish(
            intent["payload"], idempotency_key=intent["logical_key"], now=NOW
        )
        self.queue.recover_leases(now=NOW + timedelta(minutes=1))
        with self.assertRaises(LeaseLost):
            self.queue.confirmed(claim, proof, now=NOW + timedelta(minutes=1))
        result = self.queue.reconcile(
            intent["intent_id"], self.transport, actor="op", now=NOW + timedelta(minutes=1)
        )
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(self.transport.call_count(), 1)

    def test_recall_obeys_persistent_pause(self) -> None:
        _, _, request = self.draft_and_scope()
        intent = self.queue.enqueue_many([request], actor="op", now=NOW)[0]
        PublicationWorker(self.queue, self.transport, dry_run=False).run_once(now=NOW)
        service = RecallService(self.queue)
        service.request(intent["intent_id"], actor="op", reason="stale", now=NOW)
        self.queue.set_pause(
            "global", "*", paused=True, actor="admin", reason="all I/O stop", now=NOW
        )
        self.assertEqual(service.run_once(self.transport, now=NOW, dry_run=False)["status"], "idle")
        proof = self.transport.lookup(intent["logical_key"], now=NOW)
        assert proof is not None
        self.assertFalse(proof["withdrawn"])

    def test_ambiguous_withdrawal_requires_lookup_not_a_second_withdrawal(self) -> None:
        _, _, request = self.draft_and_scope()
        intent = self.queue.enqueue_many([request], actor="op", now=NOW)[0]
        PublicationWorker(self.queue, self.transport, dry_run=False).run_once(now=NOW)
        service = RecallService(self.queue)
        service.request(intent["intent_id"], actor="op", reason="stale", now=NOW)
        original = self.transport.withdraw
        calls = []

        def uncertain(key, *, now):
            calls.append(key)
            original(key, now=now)
            raise TimeoutError("ambiguous")

        self.transport.withdraw = uncertain
        self.assertEqual(
            service.run_once(self.transport, now=NOW, dry_run=False)["status"], "outcome_unknown"
        )
        self.assertEqual(service.run_once(self.transport, now=NOW, dry_run=False)["status"], "idle")
        resolved = service.reconcile(intent["intent_id"], self.transport, actor="op", now=NOW)
        self.assertEqual(resolved["status"], "confirmed")
        self.assertEqual(len(calls), 1)

    def test_queue_attempts_and_receipts_are_append_only(self) -> None:
        _, _, request = self.draft_and_scope()
        self.queue.enqueue_many([request], actor="op", now=NOW)
        PublicationWorker(self.queue, self.transport, dry_run=False).run_once(now=NOW)
        for table in (
            "payload_approvals",
            "publish_attempts",
            "publish_confirmations",
            "publish_events",
        ):
            with self.subTest(table=table), self.assertRaises(sqlite3.IntegrityError):
                self.store._conn.execute(f"DELETE FROM {table}")

    def test_legacy_direct_non_fake_client_is_not_a_durable_path_bypass(self) -> None:
        from s_n_sales.pipeline.publisher import Publisher, PublishError

        package, _, request = self.draft_and_scope()
        calls = []

        class ArbitraryClient:
            def publish_and_read_back(self, **kwargs):
                calls.append(kwargs)
                raise AssertionError("must never be called")

        approval = self.store.get_approval(request["publication_id"])
        assert approval is not None
        with self.assertRaises(PublishError):
            Publisher(client=ArbitraryClient(), dry_run=False, approval_source=self.store).publish(
                package.snapshot.candidate, approval, now=NOW
            )
        self.assertEqual(calls, [])
