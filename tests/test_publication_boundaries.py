"""Failure-injection tests across scope, queue, provider and recovery boundaries."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from s_n_sales.api.store_sqlite import SqliteOperatorStore
from s_n_sales.domain.json_value import canonical
from s_n_sales.publishing.contracts import DuplicateBusinessDeal, LeaseLost
from s_n_sales.publishing.fake import FakeTransport
from s_n_sales.publishing.queue import PublicationQueue
from s_n_sales.publishing.recall import RecallService
from s_n_sales.publishing.worker import PublicationWorker
from s_n_sales.quality.repository import DealRepository
from s_n_sales.quality.urls import UrlPolicy
from test_grounded_flow import NOW, manual_request


class PublicationBoundaryTests(unittest.TestCase):
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

    def test_scope_insert_failure_rolls_back_candidate_decision_and_history(self) -> None:
        request = manual_request()
        request["target_channel"] = "fake:sales"
        package = self.repo.import_manual(canonical(request).encode(), actor="op", now=NOW)
        identifier = package.snapshot.candidate["publication_id"]
        self.store._conn.execute(
            "CREATE TRIGGER scope_failure BEFORE INSERT ON payload_approvals "
            "BEGIN SELECT RAISE(ABORT,'injected_failure'); END"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.queue.approve_payload(
                identifier,
                expected_revision=1,
                expected_payload_sha256=package.payload["payload_sha256"],
                actor="op",
                now=NOW,
            )
        self.assertIsNone(self.store.get_approval(identifier))
        self.assertEqual(self.store.get_revision(identifier), 1)
        self.assertEqual(len(self.store.list_history(identifier)), 1)

    def test_unscoped_legacy_approval_cannot_enqueue(self) -> None:
        request = manual_request()
        request["target_channel"] = "fake:sales"
        package = self.repo.import_manual(canonical(request).encode(), actor="op", now=NOW)
        identifier = package.snapshot.candidate["publication_id"]
        self.store.approve(identifier, expected_revision=1, decided_by="op", now=NOW)
        with self.assertRaises(ValueError):
            self.queue.enqueue(
                identifier,
                expected_revision=2,
                expected_payload_sha256=package.payload["payload_sha256"],
                actor="op",
                now=NOW,
            )
        self.assertEqual(self.queue.list_intents(), [])

    def test_invalid_later_batch_item_rolls_back_entire_enqueue(self) -> None:
        _, _, first = self.draft_and_scope(channel="fake:one")
        _, _, second = self.draft_and_scope(channel="fake:two")
        second["expected_payload_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.queue.enqueue_many([first, second], actor="op", now=NOW)
        self.assertEqual(self.queue.list_intents(), [])
        self.assertEqual(self.transport.call_count(), 0)

    def test_same_scope_enqueue_is_idempotent_but_new_business_duplicate_is_blocked(self) -> None:
        _, _, first = self.draft_and_scope()
        initial = self.queue.enqueue_many([first], actor="op", now=NOW)[0]
        repeated = self.queue.enqueue_many([first], actor="op", now=NOW)[0]
        self.assertEqual(initial["intent_id"], repeated["intent_id"])
        _, _, second = self.draft_and_scope(title="Same product different title")
        with self.assertRaises(DuplicateBusinessDeal):
            self.queue.enqueue_many([second], actor="op", now=NOW)

    def test_unknown_blocks_business_duplicate_past_cooldown(self) -> None:
        _, _, first = self.draft_and_scope()
        self.queue.enqueue_many([first], actor="op", now=NOW)
        self.transport.faults = ["after_accept_timeout"]
        PublicationWorker(self.queue, self.transport, dry_run=False).run_once(now=NOW)
        _, _, second = self.draft_and_scope(title="Same product, another report")
        with self.assertRaises(DuplicateBusinessDeal):
            self.queue.enqueue_many([second], actor="op", now=NOW + timedelta(minutes=61))

    def test_confirmed_business_cooldown_is_durable(self) -> None:
        _, _, first = self.draft_and_scope()
        self.queue.enqueue_many([first], actor="op", now=NOW)
        PublicationWorker(self.queue, self.transport, dry_run=False).run_once(now=NOW)
        other_store = SqliteOperatorStore(self.path / "operator.db")
        self.addCleanup(other_store.close)
        other_queue = PublicationQueue(DealRepository(other_store, url_policy=self.repo.url_policy))
        _, _, second = self.draft_and_scope(title="Same variant new report")
        with self.assertRaises(DuplicateBusinessDeal):
            other_queue.enqueue_many([second], actor="op", now=NOW + timedelta(seconds=1))

    def test_expired_claim_is_fenced_from_new_worker(self) -> None:
        _, _, first = self.draft_and_scope()
        self.queue.enqueue_many([first], actor="op", now=NOW)
        old = self.queue.claim(worker_id="old", now=NOW)
        assert old is not None
        new = self.queue.claim(worker_id="new", now=NOW + timedelta(seconds=31))
        assert new is not None
        with self.assertRaises(LeaseLost):
            self.queue.start_send(old, now=NOW + timedelta(seconds=31))
        self.assertEqual(self.transport.call_count(), 0)
        self.queue.start_send(new, now=NOW + timedelta(seconds=31))

    def test_database_failure_after_accept_never_retries_as_not_sent(self) -> None:
        _, _, first = self.draft_and_scope()
        intent = self.queue.enqueue_many([first], actor="op", now=NOW)[0]
        self.store._conn.execute(
            "CREATE TRIGGER receipt_failure BEFORE INSERT ON publish_confirmations "
            "BEGIN SELECT RAISE(ABORT,'injected_db_failure'); END"
        )
        worker = PublicationWorker(self.queue, self.transport, dry_run=False)
        with self.assertRaises(sqlite3.IntegrityError):
            worker.run_once(now=NOW)
        self.assertEqual(self.queue.get(intent["intent_id"])["status"], "sending")
        self.queue.recover_leases(now=NOW + timedelta(minutes=1))
        self.assertEqual(worker.run_once(now=NOW + timedelta(minutes=1))["status"], "idle")
        self.assertEqual(self.transport.call_count(), 1)

    def test_freshness_and_retired_evidence_rechecked_before_send(self) -> None:
        package, _, first = self.draft_and_scope()
        self.queue.enqueue_many([first], actor="op", now=NOW)
        self.repo.vault.retire(package.facts["evidence_id"], actor="op", reason="revoked", now=NOW)
        result = PublicationWorker(self.queue, self.transport, dry_run=False).run_once(now=NOW)
        self.assertEqual(result["status"], "terminal_failed")
        self.assertEqual(self.transport.call_count(), 0)

    def test_old_evidence_becomes_terminal_without_send(self) -> None:
        _, _, first = self.draft_and_scope()
        self.queue.enqueue_many([first], actor="op", now=NOW)
        result = PublicationWorker(self.queue, self.transport, dry_run=False).run_once(
            now=NOW + timedelta(hours=3)
        )
        self.assertEqual(result["status"], "terminal_failed")
        self.assertEqual(self.transport.call_count(), 0)

    def test_manual_export_has_no_published_receipt_or_queue_success(self) -> None:
        package, scope, request = self.draft_and_scope(channel="manual_export")
        exported = self.queue.export_approved(
            package.snapshot.candidate["publication_id"],
            expected_revision=scope["revision"],
            expected_payload_sha256=package.payload["payload_sha256"],
            actor="op",
            now=NOW,
        )
        self.assertEqual(exported["status"], "exported_not_published")
        self.assertEqual(exported["payload"]["text"], package.payload["text"])
        with self.assertRaises(ValueError):
            self.queue.enqueue_many([request], actor="op", now=NOW)
        self.assertEqual(self.queue.list_intents(), [])
        self.assertEqual(self.store.list_receipts(), [])

    def test_recall_intent_is_not_confirmation_until_provider_readback(self) -> None:
        _, _, request = self.draft_and_scope()
        intent = self.queue.enqueue_many([request], actor="op", now=NOW)[0]
        PublicationWorker(self.queue, self.transport, dry_run=False).run_once(now=NOW)
        service = RecallService(self.queue)
        item = service.request(intent["intent_id"], actor="op", reason="expired", now=NOW)
        self.assertEqual(item["status"], "pending")
        proof = self.transport.lookup(intent["logical_key"], now=NOW)
        assert proof is not None
        self.assertFalse(proof["withdrawn"])
        self.assertEqual(service.run_once(self.transport, now=NOW)["status"], "dry_run")
        result = service.run_once(self.transport, now=NOW, dry_run=False)
        self.assertEqual(result["status"], "confirmed")
        self.assertTrue(result["receipt"]["withdrawn"])
        self.assertEqual(service.run_once(self.transport, now=NOW, dry_run=False)["status"], "idle")

    def test_confirmed_old_payload_is_preserved_if_draft_rejected_during_transport(self) -> None:
        _, _, request = self.draft_and_scope()
        intent = self.queue.enqueue_many([request], actor="op", now=NOW)[0]
        underlying = self.transport.publish

        def publish_and_reject(payload, *, idempotency_key, now):
            result = underlying(payload, idempotency_key=idempotency_key, now=now)
            self.store.reject(
                request["publication_id"],
                expected_revision=request["expected_revision"],
                decided_by="op",
                now=now,
            )
            return result

        self.transport.publish = publish_and_reject
        result = PublicationWorker(self.queue, self.transport, dry_run=False).run_once(now=NOW)
        self.assertEqual(result["status"], "confirmed")
        recall = RecallService(self.queue).get(intent["intent_id"])
        self.assertEqual(recall["status"], "pending")
        self.assertEqual(result["receipt"]["text"], intent["payload"]["text"])

    def test_queue_starts_paused_and_pause_survives_reopening(self) -> None:
        self.queue.set_pause("global", "*", paused=True, actor="admin", reason="stop", now=NOW)
        _, _, request = self.draft_and_scope()
        self.queue.enqueue_many([request], actor="op", now=NOW)
        other_store = SqliteOperatorStore(self.path / "operator.db")
        self.addCleanup(other_store.close)
        queue = PublicationQueue(DealRepository(other_store, url_policy=self.repo.url_policy))
        self.assertIsNone(queue.claim(worker_id="another", now=NOW))
        self.assertTrue(next(p for p in queue.pauses() if p["scope"] == "global")["paused"])
