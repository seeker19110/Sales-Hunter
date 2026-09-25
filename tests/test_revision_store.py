"""SH-006/008/009: imports cannot manufacture authority or bypass contracts."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from s_n_sales.api.store import OperatorStore
from s_n_sales.api.store_sqlite import SqliteOperatorStore
from s_n_sales.pipeline.publication import build_publication_candidate, compute_draft_sha256

ROOT = Path(__file__).resolve().parents[1]


def draft() -> dict[str, Any]:
    observation = json.loads(
        (ROOT / "schemas/examples/valid/offer-observation.v1.json").read_text(encoding="utf-8")
    )
    return build_publication_candidate(
        observation,
        {},
        content="Nội dung thử nghiệm",
        affiliate_url="https://example.com/aff",
        target_channel="manual_export",
    )


def rehash(candidate: dict[str, Any]) -> dict[str, Any]:
    candidate["draft_sha256"] = compute_draft_sha256(
        content=candidate["content"],
        affiliate_url=candidate["affiliate_url"],
        affiliate_disclosure=candidate["affiliate_disclosure"],
        claim_snapshot=candidate["claim_snapshot"],
        observation_id=candidate["observation_id"],
    )
    candidate["approval"]["draft_sha256"] = candidate["draft_sha256"]
    return candidate


class ImportAuthorityTests(unittest.TestCase):
    def check_rejected(self, candidate: dict[str, Any]) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for store in (OperatorStore(), SqliteOperatorStore(Path(directory) / "operator.db")):
                try:
                    with self.subTest(store=type(store).__name__), self.assertRaises(ValueError):
                        store.upsert_candidate(candidate)
                    self.assertEqual(store.list_candidates(), [])
                finally:
                    store.close()

    def test_import_cannot_self_approve(self) -> None:
        candidate = draft()
        candidate["approval"].update(
            status="approved", decided_by="caller-admin", decided_at="2026-09-25T00:00:00Z"
        )
        self.check_rejected(candidate)

    def test_import_requires_full_claim_contract_not_only_matching_hash(self) -> None:
        candidate = draft()
        del candidate["claim_snapshot"]["currency"]
        self.check_rejected(rehash(candidate))

    def test_import_rejects_unknown_server_fields(self) -> None:
        candidate = draft()
        candidate["role"] = "admin"
        self.check_rejected(candidate)

    def test_import_rejects_float_or_boolean_money(self) -> None:
        for value in (True, 1.0, -1):
            candidate = draft()
            candidate["claim_snapshot"]["sale_price_minor"] = value
            with self.subTest(value=value):
                self.check_rejected(rehash(candidate))


class RevisionTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "operator.db"
        self.store = SqliteOperatorStore(self.path)
        self.candidate = draft()
        self.pub_id = self.candidate["publication_id"]
        self.store.upsert_candidate(self.candidate)

    def tearDown(self) -> None:
        self.store.close()
        self.directory.cleanup()

    def test_decision_requires_the_revision_seen(self) -> None:
        from s_n_sales.api.contracts import RevisionConflict, RevisionRequired

        with self.assertRaises(RevisionRequired):
            self.store.approve(self.pub_id, decided_by="op")
        invalid_values: list[Any] = [True, 0, -1, "1"]
        for invalid in invalid_values:
            with self.subTest(invalid=invalid), self.assertRaises(RevisionRequired):
                self.store.approve(self.pub_id, decided_by="op", expected_revision=invalid)
        self.store.approve(self.pub_id, decided_by="op", expected_revision=1)
        with self.assertRaises(RevisionConflict):
            self.store.reject(self.pub_id, decided_by="op", expected_revision=1)
        approval = self.store.get_approval(self.pub_id)
        assert approval is not None
        self.assertEqual(approval["status"], "approved")

    def test_history_survives_restart_and_cannot_be_rewritten(self) -> None:
        import sqlite3

        self.store.approve(self.pub_id, decided_by="a", expected_revision=1)
        self.store.reject(self.pub_id, decided_by="b", expected_revision=2)
        self.store.approve(self.pub_id, decided_by="c", expected_revision=3)
        self.store.close()
        self.store = SqliteOperatorStore(self.path)
        history = self.store.list_history(self.pub_id)
        self.assertEqual(
            [item["kind"] for item in history], ["created", "approved", "rejected", "approved"]
        )
        self.assertEqual([item["revision"] for item in history], [1, 2, 3, 4])
        self.assertEqual([item["actor"] for item in history[1:]], ["a", "b", "c"])
        for table in ("candidate_revisions", "candidate_events"):
            with self.assertRaises(sqlite3.IntegrityError):
                self.store._conn.execute(f"DELETE FROM {table}")
        self.assertEqual(len(self.store.list_history(self.pub_id)), 4)

    def test_edit_invalidates_authority_atomically_and_aba_does_not_reuse_revision(self) -> None:
        from s_n_sales.api.contracts import RevisionConflict

        self.store.approve(self.pub_id, decided_by="a", expected_revision=1)
        edited = rehash(dict(self.candidate, content="Version B", approval={"status": "pending"}))
        self.store.upsert_candidate(edited, expected_revision=2, actor="editor")
        self.assertIsNone(self.store.get_approval(self.pub_id))
        self.store.upsert_candidate(self.candidate, expected_revision=3, actor="editor")
        self.assertEqual(self.store.get_revision(self.pub_id), 4)
        with self.assertRaises(RevisionConflict):
            self.store.approve(self.pub_id, decided_by="a", expected_revision=1)
        candidate = self.store.get_candidate(self.pub_id)
        assert candidate is not None
        self.assertEqual(candidate["approval"]["status"], "pending")

    def test_pending_reimport_cannot_revoke_a_decision(self) -> None:
        approved = self.store.approve(self.pub_id, decided_by="a", expected_revision=1)
        saved = self.store.upsert_candidate(self.candidate, expected_revision=2)
        self.assertEqual(saved["approval"]["status"], "approved")
        self.assertEqual(self.store.get_approval(self.pub_id), approved)
        self.assertEqual(self.store.get_revision(self.pub_id), 2)

    def test_two_connections_cannot_both_change_the_same_revision(self) -> None:
        import threading
        from concurrent.futures import ThreadPoolExecutor

        from s_n_sales.api.contracts import RevisionConflict

        other = SqliteOperatorStore(self.path)
        barrier = threading.Barrier(2)

        def decide(store: SqliteOperatorStore, status: str) -> str:
            barrier.wait(timeout=5)
            try:
                getattr(store, status)(self.pub_id, decided_by=status, expected_revision=1)
                return "committed"
            except RevisionConflict:
                return "conflict"

        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [
                    pool.submit(decide, self.store, "approve"),
                    pool.submit(decide, other, "reject"),
                ]
                results = [future.result(timeout=10) for future in futures]
            self.assertCountEqual(results, ["committed", "conflict"])
            self.assertEqual(self.store.get_revision(self.pub_id), 2)
            self.assertEqual(len(self.store.list_history(self.pub_id)), 2)
        finally:
            other.close()

    def test_state_snapshot_is_not_aliased_to_storage(self) -> None:
        snapshot = self.store.get_snapshot(self.pub_id)
        assert snapshot is not None
        snapshot.candidate["content"] = "tampered by reader"
        fresh = self.store.get_snapshot(self.pub_id)
        assert fresh is not None
        self.assertEqual(fresh.candidate["content"], self.candidate["content"])

    def test_failed_history_write_rolls_back_projection_and_authority(self) -> None:
        import sqlite3

        self.store._conn.execute(
            "CREATE TRIGGER injected_failure BEFORE INSERT ON candidate_events "
            "BEGIN SELECT RAISE(ABORT, 'injected_crash'); END"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.approve(self.pub_id, decided_by="a", expected_revision=1)
        self.assertEqual(self.store.get_revision(self.pub_id), 1)
        self.assertIsNone(self.store.get_approval(self.pub_id))
        self.assertEqual(len(self.store.list_history(self.pub_id)), 1)

    def test_receipt_rejects_legacy_success_shape_without_platform_readback(self) -> None:
        with self.assertRaises(ValueError):
            self.store.save_receipt(
                {
                    "receipt_id": "r",
                    "status": "success",
                    "idempotency_key": "k",
                    "target_channel": "manual_export",
                    "published_at": "2026-09-25T00:00:00Z",
                    "mode": "dry_run",
                    "external_post_id": "unverified",
                }
            )
        self.assertEqual(self.store.list_receipts(), [])

    def test_manifest_is_not_rewritten_on_restart(self) -> None:
        manifest = self.store.migration_manifest()
        self.store.close()
        self.store = SqliteOperatorStore(self.path)
        self.assertEqual(self.store.migration_manifest(), manifest)


class RevisionHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        import threading

        from s_n_sales.api.app import make_server

        self.store = OperatorStore()
        self.candidate = draft()
        self.pub_id = self.candidate["publication_id"]
        self.store.upsert_candidate(self.candidate)
        self.server = make_server(self.store, allow_unauthenticated_local=True)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.store.close()

    def request(
        self, method: str, path: str, body: bytes | None = None, **headers: str
    ) -> tuple[int, dict[str, str], bytes]:
        from http.client import HTTPConnection

        connection = HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=3)
        try:
            connection.request(
                method, path, body=body, headers={"Content-Type": "application/json", **headers}
            )
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_api_missing_revision_is_428_not_silent_approval(self) -> None:
        status, _, _ = self.request("POST", f"/api/v1/candidates/{self.pub_id}/approve", b"{}")
        self.assertEqual(status, 428)
        self.assertIsNone(self.store.get_approval(self.pub_id))

    def test_api_etag_and_stale_revision_conflict(self) -> None:
        status, headers, _ = self.request("GET", f"/api/v1/candidates/{self.pub_id}")
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("ETag"), '"1"')
        status, _, _ = self.request(
            "POST", f"/api/v1/candidates/{self.pub_id}/approve", b"{}", **{"If-Match": '"1"'}
        )
        self.assertEqual(status, 200)
        status, _, _ = self.request(
            "POST", f"/api/v1/candidates/{self.pub_id}/reject", b"{}", **{"If-Match": '"1"'}
        )
        self.assertEqual(status, 409)
        approval = self.store.get_approval(self.pub_id)
        assert approval is not None
        self.assertEqual(approval["status"], "approved")

    def test_dashboard_contains_viewed_revision_and_rejects_stale_form(self) -> None:
        import re
        from urllib.parse import urlencode

        status, _, page = self.request("GET", f"/dashboard/candidates/{self.pub_id}")
        self.assertEqual(status, 200)
        match = re.search(rb'name="expected_revision" value="([0-9]+)"', page)
        self.assertIsNotNone(match)
        self.store.approve(self.pub_id, decided_by="another", expected_revision=1)
        form = urlencode({"expected_revision": "1"}).encode()
        status, _, _ = self.request(
            "POST",
            f"/dashboard/candidates/{self.pub_id}/reject",
            form,
            **{"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status, 409)

    def test_invalid_utf8_returns_structured_error(self) -> None:
        status, _, body = self.request("POST", "/api/v1/candidates", b"\xff")
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body)["error"], "invalid_json")

    def test_cross_origin_and_host_are_rejected(self) -> None:
        status, _, _ = self.request("GET", "/dashboard", Host="attacker.example")
        self.assertEqual(status, 400)
        status, _, _ = self.request(
            "POST",
            "/dashboard/login",
            b"token=x",
            **{
                "Origin": "https://attacker.example",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
