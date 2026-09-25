"""Durable intent acceptance: no blind retry of an ambiguous provider outcome."""

from __future__ import annotations

import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path

from s_n_sales.api.store_sqlite import SqliteOperatorStore
from s_n_sales.domain.json_value import canonical
from s_n_sales.quality.repository import DealRepository
from s_n_sales.quality.urls import UrlPolicy
from test_grounded_flow import NOW, manual_request


class DurablePublicationTests(unittest.TestCase):
    def setUp(self) -> None:
        from s_n_sales.publishing.fake import FakeTransport
        from s_n_sales.publishing.queue import PublicationQueue

        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name)
        self.store = SqliteOperatorStore(self.path / "operator.db")
        self.policy = UrlPolicy(frozenset({"example.com"}))
        self.repo = DealRepository(self.store, url_policy=self.policy)
        self.queue = PublicationQueue(self.repo)
        self.queue.set_pause("global", "*", paused=False, actor="admin", reason="fixture", now=NOW)
        request = manual_request()
        request["target_channel"] = "fake:sales"
        self.package = self.repo.import_manual(canonical(request).encode(), actor="op", now=NOW)
        self.pub_id = self.package.snapshot.candidate["publication_id"]
        self.transport = FakeTransport(self.path / "remote.db")

    def tearDown(self) -> None:
        self.transport.close()
        self.store.close()
        self.directory.cleanup()

    def enqueue(self):
        scope = self.queue.approve_payload(
            self.pub_id,
            expected_revision=1,
            expected_payload_sha256=self.package.payload["payload_sha256"],
            actor="op",
            now=NOW,
        )
        return self.queue.enqueue(
            self.pub_id,
            expected_revision=scope["revision"],
            expected_payload_sha256=self.package.payload["payload_sha256"],
            actor="op",
            now=NOW,
        )

    def test_default_dry_run_never_calls_transport_or_claims(self) -> None:
        from s_n_sales.publishing.worker import PublicationWorker

        intent = self.enqueue()
        worker = PublicationWorker(self.queue, self.transport)
        self.assertEqual(worker.run_once(now=NOW)["status"], "dry_run")
        self.assertEqual(self.transport.call_count(), 0)
        self.assertEqual(self.queue.get(intent["intent_id"])["status"], "ready")

    def test_confirmed_receipt_survives_restart_without_a_second_send(self) -> None:
        from s_n_sales.publishing.queue import PublicationQueue
        from s_n_sales.publishing.worker import PublicationWorker

        intent = self.enqueue()
        self.assertEqual(
            PublicationWorker(self.queue, self.transport, dry_run=False).run_once(now=NOW)[
                "status"
            ],
            "confirmed",
        )
        self.store.close()
        self.store = SqliteOperatorStore(self.path / "operator.db")
        self.repo = DealRepository(self.store, url_policy=self.policy)
        self.queue = PublicationQueue(self.repo)
        worker = PublicationWorker(self.queue, self.transport, dry_run=False)
        self.assertEqual(worker.run_once(now=NOW)["status"], "idle")
        stored = self.queue.get(intent["intent_id"])
        self.assertEqual(
            stored["receipt"]["payload_sha256"], self.package.payload["payload_sha256"]
        )
        self.assertEqual(stored["receipt"]["proof_kind"], "fake")
        self.assertEqual(self.transport.post_count(), 1)

    def test_ambiguous_timeout_reconciles_without_retrying_publish(self) -> None:
        from s_n_sales.publishing.worker import PublicationWorker

        intent = self.enqueue()
        self.transport.faults = ["after_accept_timeout"]
        worker = PublicationWorker(self.queue, self.transport, dry_run=False)
        self.assertEqual(worker.run_once(now=NOW)["status"], "outcome_unknown")
        self.assertEqual(worker.run_once(now=NOW + timedelta(minutes=2))["status"], "idle")
        result = self.queue.reconcile(
            intent["intent_id"], self.transport, actor="op", now=NOW + timedelta(minutes=2)
        )
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(self.transport.call_count(), 1)
        self.assertEqual(self.transport.post_count(), 1)

    def test_crash_after_remote_accept_becomes_unknown_when_lease_expires(self) -> None:
        from s_n_sales.publishing.fake import SimulatedCrash
        from s_n_sales.publishing.worker import PublicationWorker

        intent = self.enqueue()
        self.transport.faults = ["crash_after_accept"]
        worker = PublicationWorker(self.queue, self.transport, dry_run=False)
        with self.assertRaises(SimulatedCrash):
            worker.run_once(now=NOW)
        self.queue.recover_leases(now=NOW + timedelta(minutes=2))
        self.assertEqual(self.queue.get(intent["intent_id"])["status"], "outcome_unknown")
        self.assertEqual(worker.run_once(now=NOW + timedelta(minutes=2))["status"], "idle")
        self.assertEqual(self.transport.post_count(), 1)

    def test_pause_persists_and_is_rechecked_after_claim(self) -> None:
        from s_n_sales.publishing.contracts import Paused

        self.enqueue()
        claim = self.queue.claim(worker_id="worker-a", now=NOW)
        assert claim is not None
        self.queue.set_pause(
            "channel", "fake:sales", paused=True, actor="admin", reason="stop", now=NOW
        )
        with self.assertRaises(Paused):
            self.queue.start_send(claim, now=NOW)
        self.assertEqual(self.transport.call_count(), 0)

    def test_known_not_sent_failure_has_bounded_retry_and_backoff(self) -> None:
        from s_n_sales.publishing.worker import PublicationWorker

        intent = self.enqueue()
        self.transport.faults = ["before_send"] * 10
        worker = PublicationWorker(self.queue, self.transport, dry_run=False)
        self.assertEqual(worker.run_once(now=NOW)["status"], "retryable_failed")
        self.assertEqual(worker.run_once(now=NOW)["status"], "idle")
        worker.run_once(now=NOW + timedelta(minutes=1))
        worker.run_once(now=NOW + timedelta(minutes=2))
        saved = self.queue.get(intent["intent_id"])
        self.assertEqual(saved["status"], "terminal_failed")
        self.assertEqual(saved["attempts"], 3)
        self.assertEqual(self.transport.post_count(), 0)

    def test_payload_review_requires_exact_preview_hash_and_revision(self) -> None:
        with self.assertRaises(ValueError):
            self.queue.approve_payload(
                self.pub_id,
                expected_revision=1,
                expected_payload_sha256="a" * 64,
                actor="op",
                now=NOW,
            )
        self.assertIsNone(self.store.get_approval(self.pub_id))
        self.assertEqual(self.store.get_revision(self.pub_id), 1)

    def test_rejected_or_edited_candidate_never_reaches_transport(self) -> None:
        from s_n_sales.publishing.worker import PublicationWorker

        intent = self.enqueue()
        self.store.reject(
            self.pub_id, expected_revision=self.store.get_revision(self.pub_id), decided_by="op"
        )
        result = PublicationWorker(self.queue, self.transport, dry_run=False).run_once(now=NOW)
        self.assertEqual(result["status"], "terminal_failed")
        self.assertEqual(self.transport.call_count(), 0)
        self.assertEqual(
            self.queue.get(intent["intent_id"])["error_code"], "authority_or_eligibility_changed"
        )

    def test_mismatched_readback_is_unknown_not_confirmed(self) -> None:
        from s_n_sales.publishing.worker import PublicationWorker

        self.enqueue()
        self.transport.faults = ["bad_readback"]
        result = PublicationWorker(self.queue, self.transport, dry_run=False).run_once(now=NOW)
        self.assertEqual(result["status"], "outcome_unknown")

    def test_two_workers_cannot_claim_same_intent(self) -> None:
        from s_n_sales.publishing.queue import PublicationQueue

        self.enqueue()
        other_store = SqliteOperatorStore(self.path / "operator.db")
        other_queue = PublicationQueue(DealRepository(other_store, url_policy=self.policy))
        barrier = threading.Barrier(2)

        def claim(queue, identifier):
            barrier.wait(timeout=5)
            return queue.claim(worker_id=identifier, now=NOW)

        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = [
                    pool.submit(claim, self.queue, "a"),
                    pool.submit(claim, other_queue, "b"),
                ]
                claims = [result.result(timeout=10) for result in results]
            self.assertEqual(sum(claim is not None for claim in claims), 1)
        finally:
            other_store.close()
