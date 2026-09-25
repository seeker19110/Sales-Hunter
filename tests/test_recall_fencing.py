"""Withdrawal confirmation must own the active lease or reconcile an unknown outcome."""

from __future__ import annotations

import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from s_n_sales.api.store_sqlite import SqliteOperatorStore
from s_n_sales.domain.json_value import canonical, iso
from s_n_sales.publishing.fake import FakeTransport
from s_n_sales.publishing.queue import PublicationQueue
from s_n_sales.publishing.recall import RecallService
from s_n_sales.publishing.worker import PublicationWorker
from s_n_sales.quality.repository import DealRepository
from s_n_sales.quality.urls import UrlPolicy
from test_grounded_flow import NOW, manual_request


class RecallFencingTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name)
        self.store = SqliteOperatorStore(path / "operator.db")
        self.addCleanup(self.store.close)
        self.transport = FakeTransport(path / "remote.db")
        self.addCleanup(self.transport.close)
        repo = DealRepository(self.store, url_policy=UrlPolicy(frozenset({"example.com"})))
        queue = PublicationQueue(repo)
        queue.set_pause("global", "*", paused=False, actor="op", reason="fixture", now=NOW)
        request = manual_request()
        request["target_channel"] = "fake:sales"
        saved = repo.import_manual(canonical(request).encode(), actor="op", now=NOW)
        publication_id = saved.snapshot.candidate["publication_id"]
        payload_hash = saved.payload["payload_sha256"]
        scope = queue.approve_payload(
            publication_id,
            expected_revision=saved.snapshot.revision,
            expected_payload_sha256=payload_hash,
            actor="op",
            now=NOW,
        )
        self.intent = queue.enqueue(
            publication_id,
            expected_revision=scope["revision"],
            expected_payload_sha256=payload_hash,
            actor="op",
            now=NOW,
        )
        self.assertEqual(
            PublicationWorker(queue, self.transport, dry_run=False).run_once(now=NOW)["status"],
            "confirmed",
        )
        self.service = RecallService(queue)
        self.identifier = self.intent["intent_id"]
        self.service.request(self.identifier, actor="op", reason="fixture recall", now=NOW)
        self.proof = self.transport.withdraw(self.intent["logical_key"], now=NOW)

    def claim_with_token(self, token: str) -> None:
        with self.store.transaction() as connection:
            connection.execute(
                "UPDATE recall_intents SET status='withdrawing',lease_token=?,worker_id='worker',"
                "lease_until=? WHERE intent_id=?",
                (token, iso(NOW + timedelta(seconds=30)), self.identifier),
            )

    def test_old_token_cannot_confirm_new_lease(self) -> None:
        self.claim_with_token("new-owner")
        self.service._confirm(
            self.identifier, self.proof, actor="old-worker", now=NOW, expected_token="old-owner"
        )
        current = self.service.get(self.identifier)
        self.assertEqual(current["status"], "withdrawing")
        self.assertEqual(current["lease_token"], "new-owner")
        self.assertIsNone(current["receipt"])

    def test_expired_token_cannot_confirm_without_reconciliation(self) -> None:
        self.claim_with_token("owner")
        self.service._confirm(
            self.identifier,
            self.proof,
            actor="worker",
            now=NOW + timedelta(seconds=30),
            expected_token="owner",
        )
        self.assertEqual(self.service.get(self.identifier)["status"], "withdrawing")
        self.service.run_once(self.transport, now=NOW + timedelta(seconds=31), dry_run=False)
        self.assertEqual(self.service.get(self.identifier)["status"], "outcome_unknown")
        result = self.service.reconcile(
            self.identifier, self.transport, actor="op", now=NOW + timedelta(seconds=31)
        )
        self.assertEqual(result["status"], "confirmed")

    def test_unleased_confirmation_does_not_bypass_pending_state(self) -> None:
        self.service._confirm(self.identifier, self.proof, actor="op", now=NOW)
        self.assertEqual(self.service.get(self.identifier)["status"], "pending")


if __name__ == "__main__":
    unittest.main()
