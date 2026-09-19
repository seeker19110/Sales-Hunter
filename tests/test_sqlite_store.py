from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from s_n_sales.api.store_sqlite import SqliteOperatorStore
from s_n_sales.pipeline.draft import observation_to_rank
from s_n_sales.pipeline.publication import build_publication_candidate

ROOT = Path(__file__).resolve().parents[1]


class SqliteStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_operator.db"
        self.store = SqliteOperatorStore(db_path=self.db_path)

        now = datetime(2026, 9, 11, 6, 0, tzinfo=UTC)
        obs = json.loads(
            (ROOT / "schemas/examples/valid/offer-observation.v1.json").read_text(encoding="utf-8")
        )
        rank = observation_to_rank(obs, now=now)
        self.candidate = build_publication_candidate(
            obs,
            rank,
            content="SQLite store test content",
            affiliate_url="https://example.com/aff/sqlite-test-001",
            target_channel="telegram:sales-hunter-demo",
        )

    def tearDown(self) -> None:
        self.store.close()
        self.temp_dir.cleanup()

    def test_upsert_and_get_candidate(self) -> None:
        saved = self.store.upsert_candidate(self.candidate)
        self.assertEqual(saved["publication_id"], self.candidate["publication_id"])
        self.assertEqual(saved["draft_sha256"], self.candidate["draft_sha256"])

        got = self.store.get_candidate(self.candidate["publication_id"])
        self.assertIsNotNone(got)
        assert got is not None
        self.assertEqual(got["publication_id"], self.candidate["publication_id"])
        self.assertEqual(got["draft_sha256"], self.candidate["draft_sha256"])
        self.assertEqual(got["claim_snapshot"], self.candidate["claim_snapshot"])

    def test_get_nonexistent_candidate_returns_none(self) -> None:
        self.assertIsNone(self.store.get_candidate("nonexistent-id"))

    def test_list_candidates_with_status_filter(self) -> None:
        self.store.upsert_candidate(self.candidate)
        items = self.store.list_candidates()
        self.assertEqual(len(items), 1)

        pending_items = self.store.list_candidates(status="pending")
        self.assertEqual(len(pending_items), 1)

        approved_items = self.store.list_candidates(status="approved")
        self.assertEqual(len(approved_items), 0)

    def test_approve_candidate(self) -> None:
        self.store.upsert_candidate(self.candidate)
        pub_id = self.candidate["publication_id"]
        clock = datetime(2026, 9, 12, 10, 0, tzinfo=UTC)

        approval = self.store.approve(
            pub_id,
            decided_by="operator@example.com",
            reason="Verified good deal",
            now=clock,
        )

        self.assertEqual(approval["status"], "approved")
        self.assertEqual(approval["draft_sha256"], self.candidate["draft_sha256"])
        self.assertEqual(approval["decided_by"], "operator@example.com")
        self.assertEqual(approval["reason"], "Verified good deal")

        # Candidate status in store should now be approved
        updated_cand = self.store.get_candidate(pub_id)
        assert updated_cand is not None
        self.assertEqual(updated_cand["approval"]["status"], "approved")

        # Approval record can be retrieved
        stored_approval = self.store.get_approval(pub_id)
        self.assertIsNotNone(stored_approval)
        assert stored_approval is not None
        self.assertEqual(stored_approval["approval_id"], approval["approval_id"])

    def test_reject_candidate(self) -> None:
        self.store.upsert_candidate(self.candidate)
        pub_id = self.candidate["publication_id"]

        rejection = self.store.reject(
            pub_id,
            decided_by="operator@example.com",
            reason="Price not verified",
        )
        self.assertEqual(rejection["status"], "rejected")

        updated_cand = self.store.get_candidate(pub_id)
        assert updated_cand is not None
        self.assertEqual(updated_cand["approval"]["status"], "rejected")

    def test_approve_nonexistent_raises_key_error(self) -> None:
        with self.assertRaises(KeyError):
            self.store.approve("missing-id", decided_by="op")

    def test_reject_nonexistent_raises_key_error(self) -> None:
        with self.assertRaises(KeyError):
            self.store.reject("missing-id", decided_by="op")

    def test_persistence_across_instances(self) -> None:
        # Save and approve on first store instance
        self.store.upsert_candidate(self.candidate)
        pub_id = self.candidate["publication_id"]
        self.store.approve(pub_id, decided_by="op1")
        self.store.close()

        # Open the exact same SQLite file with a fresh store instance
        store2 = SqliteOperatorStore(db_path=self.db_path)
        try:
            cand2 = store2.get_candidate(pub_id)
            self.assertIsNotNone(cand2)
            assert cand2 is not None
            self.assertEqual(cand2["approval"]["status"], "approved")

            approval2 = store2.get_approval(pub_id)
            self.assertIsNotNone(approval2)
            assert approval2 is not None
            self.assertEqual(approval2["decided_by"], "op1")
        finally:
            store2.close()

    def test_receipt_storage_and_idempotency(self) -> None:
        receipt = {
            "schema_version": "publish-receipt.v1",
            "receipt_id": "rcpt-001",
            "publication_id": self.candidate["publication_id"],
            "target_channel": "telegram:sales-hunter-demo",
            "idempotency_key": "obs-001:telegram:draft-hash-001",
            "published_at": "2026-09-12T10:00:00Z",
            "external_post_id": "post-999",
            "status": "success",
            "mode": "dry_run",
        }
        self.store.save_receipt(receipt)

        receipts = self.store.list_receipts()
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["receipt_id"], "rcpt-001")

        # Duplicate idempotency_key is rejected
        duplicate_receipt = dict(receipt, receipt_id="rcpt-002")
        with self.assertRaises(ValueError):
            self.store.save_receipt(duplicate_receipt)


if __name__ == "__main__":
    unittest.main()
