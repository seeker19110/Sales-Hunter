"""Regression tests for the 2026-10-09 line-by-line audit findings."""

from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from s_n_sales.adapters.manual import ManualAdapterError, load_manual_observation
from s_n_sales.api.app import _render_dashboard_detail, make_server
from s_n_sales.api.store import OperatorStore
from s_n_sales.api.store_sqlite import SqliteOperatorStore
from s_n_sales.domain.json_value import canonical, iso, json_object
from s_n_sales.pipeline.draft import observation_to_rank
from s_n_sales.pipeline.publication import build_publication_candidate
from s_n_sales.pipeline.publisher import FakePlatformClient, Publisher
from s_n_sales.publishing.contracts import QueuePolicy
from s_n_sales.publishing.fake import FakeTransport
from s_n_sales.publishing.queue import PublicationQueue
from s_n_sales.publishing.recall import RecallService
from s_n_sales.publishing.worker import PublicationWorker
from s_n_sales.quality.repository import DealRepository
from s_n_sales.quality.urls import UrlPolicy
from test_grounded_flow import NOW, manual_request
from test_operator_auth_security import seeded_store

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "schemas/examples/valid/offer-observation.v1.json"


def _candidate(publication_id: str | None = None, content: str = "Audit candidate") -> dict:
    observation = json.loads(FIXTURE.read_text(encoding="utf-8"))
    rank = observation_to_rank(observation, now=datetime(2026, 9, 11, 6, tzinfo=UTC))
    return build_publication_candidate(
        observation,
        rank,
        content=content,
        affiliate_url="https://example.com/aff/audit",
        target_channel="telegram:audit",
        publication_id=publication_id,
    )


class _OperatorServerCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store, self.publication_id = seeded_store()
        self.addCleanup(self.store.close)
        self.server = make_server(self.store, auth_token="audit-secret")
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 5)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.port = self.server.server_address[1]

    def request(
        self, method: str, path: str, *, body: bytes | None = None, headers: dict | None = None
    ) -> tuple[int, dict[str, str], str]:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read().decode("utf-8")
        finally:
            connection.close()

    def api_headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer audit-secret", "Content-Type": "application/json"}

    def session_cookie(self) -> str:
        status, headers, _ = self.request(
            "POST",
            "/dashboard/login",
            body=urlencode({"token": "audit-secret"}).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status, 303)
        return headers["Set-Cookie"].split(";", 1)[0]


class OperatorHttpBoundaryTests(_OperatorServerCase):
    def test_invalid_dashboard_filter_returns_400_instead_of_dropping_connection(self) -> None:
        status, headers, _ = self.request(
            "GET", "/dashboard?status=bogus", headers={"Cookie": self.session_cookie()}
        )
        self.assertEqual(status, 400)
        self.assertTrue(headers["Content-Type"].startswith("text/html"))

    def test_unexpected_store_errors_get_stable_json_without_details(self) -> None:
        def broken(_: str) -> None:
            raise RuntimeError("internal detail that must not leak")

        self.store.get_snapshot = broken  # type: ignore[method-assign]
        status, _, text = self.request(
            "GET", f"/api/v1/candidates/{self.publication_id}", headers=self.api_headers()
        )
        self.assertEqual((status, json.loads(text)), (500, {"error": "internal_error"}))
        self.assertNotIn("internal detail", text)

    def test_duplicate_json_keys_are_rejected_before_any_decision(self) -> None:
        status, _, text = self.request(
            "POST",
            f"/api/v1/candidates/{self.publication_id}/approve",
            body=b'{"expected_revision": 99, "expected_revision": 1}',
            headers=self.api_headers(),
        )
        self.assertEqual((status, json.loads(text)), (400, {"error": "invalid_json"}))
        self.assertIsNone(self.store.get_approval(self.publication_id))

    def test_history_of_unknown_candidate_is_404(self) -> None:
        status, _, text = self.request(
            "GET", "/api/v1/candidates/missing/history", headers=self.api_headers()
        )
        self.assertEqual((status, json.loads(text)), (404, {"error": "candidate_not_found"}))

    def test_detail_form_actions_url_encode_publication_id(self) -> None:
        candidate = _candidate(publication_id="pub/with?reserved#chars")
        page = _render_dashboard_detail(candidate, "csrf", 1)
        self.assertIn('action="/dashboard/candidates/pub%2Fwith%3Freserved%23chars/approve"', page)
        self.assertIn('action="/dashboard/candidates/pub%2Fwith%3Freserved%23chars/reject"', page)
        self.assertNotIn('action="/dashboard/candidates/pub/with', page)

    def test_dashboard_decision_round_trips_reserved_publication_id(self) -> None:
        candidate = _candidate(publication_id="pub/with?reserved", content="Reserved id")
        self.store.upsert_candidate(candidate)
        cookie = self.session_cookie()
        status, _, page = self.request(
            "GET", "/dashboard/candidates/pub%2Fwith%3Freserved", headers={"Cookie": cookie}
        )
        self.assertEqual(status, 200)
        csrf = page.split('name="csrf_token" value="', 1)[1].split('"', 1)[0]
        status, headers, _ = self.request(
            "POST",
            "/dashboard/candidates/pub%2Fwith%3Freserved/approve",
            body=urlencode({"csrf_token": csrf, "expected_revision": "1"}).encode(),
            headers={"Cookie": cookie, "Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status, 303)
        self.assertEqual(headers["Location"], "/dashboard/candidates/pub%2Fwith%3Freserved")
        approval = self.store.get_approval("pub/with?reserved")
        self.assertIsNotNone(approval)
        assert approval is not None
        self.assertEqual(approval["status"], "approved")


class StrictJsonTests(unittest.TestCase):
    def test_json_object_has_stable_error_codes(self) -> None:
        for raw, code in (
            (b"{", "invalid_json"),
            (b'{"a": 1, "a": 2}', "duplicate_json_key"),
            (b'{"a": NaN}', "nonfinite_json"),
            (b"[]", "json_object_required"),
        ):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, f"^{code}$"):
                json_object(raw)

    def test_manual_adapter_rejects_duplicate_keys(self) -> None:
        text = FIXTURE.read_text(encoding="utf-8")
        observation = json.loads(text)
        observation["source_method"] = "manual"
        body = json.dumps(observation)
        # The second, conflicting value would silently win with a lenient parser.
        duplicated = body[:-1] + ', "sale_price_minor": 1}'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "observation.json"
            path.write_text(duplicated, encoding="utf-8")
            with self.assertRaisesRegex(ManualAdapterError, "duplicate_json_key"):
                load_manual_observation(path, now=datetime(2026, 9, 11, 6, tzinfo=UTC))


class StoreOrderingTests(unittest.TestCase):
    def test_created_at_sorts_chronologically_across_fractional_seconds(self) -> None:
        store = OperatorStore()
        self.addCleanup(store.close)
        whole = datetime(2026, 9, 25, 0, 0, 0, tzinfo=UTC)
        first = _candidate(content="Created at a whole second")
        later = _candidate(content="Created half a second later")
        store.upsert_candidate(first, now=whole)
        store.upsert_candidate(later, now=whole + timedelta(microseconds=500000))
        listed = [item["publication_id"] for item in store.list_candidates()]
        self.assertEqual(listed, [later["publication_id"], first["publication_id"]])


class PublisherCacheTests(unittest.TestCase):
    def test_cached_receipt_cannot_be_mutated_by_caller(self) -> None:
        store = OperatorStore()
        self.addCleanup(store.close)
        candidate = _candidate()
        store.upsert_candidate(candidate)
        store.approve(candidate["publication_id"], decided_by="reviewer", expected_revision=1)
        snapshot = store.get_snapshot(candidate["publication_id"])
        assert snapshot is not None and snapshot.approval is not None
        publisher = Publisher(client=FakePlatformClient(), dry_run=False, approval_source=store)
        first = publisher.publish(snapshot.candidate, snapshot.approval, now=NOW)
        first["platform_post_url"] = "https://attacker.invalid/"
        again = publisher.publish(snapshot.candidate, snapshot.approval, now=NOW)
        self.assertTrue(again["platform_post_url"].startswith("https://example.com/posts/"))


class _ProxyTransport:
    proof_kind = "fake"
    capability_version = "local-simulator-v1"
    definitive_absence = True

    def __init__(self, inner: FakeTransport) -> None:
        self.inner = inner
        self.before_publish: Any = None
        self.lookup_error: BaseException | None = None

    def publish(self, payload: dict, *, idempotency_key: str, now: datetime) -> dict:
        if self.before_publish is not None:
            self.before_publish(now)
        return self.inner.publish(payload, idempotency_key=idempotency_key, now=now)

    def lookup(self, idempotency_key: str, *, now: datetime) -> dict | None:
        if self.lookup_error is not None:
            raise self.lookup_error
        return self.inner.lookup(idempotency_key, now=now)

    def withdraw(self, idempotency_key: str, *, now: datetime) -> dict:
        return self.inner.withdraw(idempotency_key, now=now)


class _DurableCase(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name)
        self.store = SqliteOperatorStore(path / "operator.db")
        self.addCleanup(self.store.close)
        fake = FakeTransport(path / "remote.db")
        self.addCleanup(fake.close)
        self.transport = _ProxyTransport(fake)
        repo = DealRepository(self.store, url_policy=UrlPolicy(frozenset({"example.com"})))
        self.queue = PublicationQueue(repo)
        self.queue.set_pause("global", "*", paused=False, actor="op", reason="fixture", now=NOW)
        request = manual_request()
        request["target_channel"] = "fake:sales"
        saved = repo.import_manual(canonical(request).encode(), actor="op", now=NOW)
        publication_id = saved.snapshot.candidate["publication_id"]
        payload_hash = saved.payload["payload_sha256"]
        scope = self.queue.approve_payload(
            publication_id,
            expected_revision=saved.snapshot.revision,
            expected_payload_sha256=payload_hash,
            actor="op",
            now=NOW,
        )
        self.intent = self.queue.enqueue(
            publication_id,
            expected_revision=scope["revision"],
            expected_payload_sha256=payload_hash,
            actor="op",
            now=NOW,
        )


class DurableWorkerFencingTests(_DurableCase):
    def test_lease_lost_after_acceptance_is_reported_not_raised(self) -> None:
        self.transport.before_publish = lambda now: self.queue.recover_leases(
            now=now + timedelta(minutes=5)
        )
        result = PublicationWorker(self.queue, self.transport, dry_run=False).run_once(now=NOW)
        self.assertEqual(result, {"status": "lease_lost", "intent_id": self.intent["intent_id"]})
        # The accepted post is recoverable by reconciliation, never silently resent.
        self.assertEqual(self.queue.get(self.intent["intent_id"])["status"], "outcome_unknown")
        reconciled = self.queue.reconcile(
            self.intent["intent_id"], self.transport, actor="op", now=NOW
        )
        self.assertEqual(reconciled["status"], "confirmed")
        self.assertEqual(self.transport.inner.post_count(), 1)

    def test_recall_reconcile_keeps_unknown_when_lookup_times_out(self) -> None:
        worker = PublicationWorker(self.queue, self.transport, dry_run=False)
        self.assertEqual(worker.run_once(now=NOW)["status"], "confirmed")
        service = RecallService(self.queue)
        identifier = self.intent["intent_id"]
        service.request(identifier, actor="op", reason="audit", now=NOW)
        with self.store.transaction() as connection:
            connection.execute(
                "UPDATE recall_intents SET status='outcome_unknown' WHERE intent_id=?",
                (identifier,),
            )
        self.transport.lookup_error = TimeoutError("ambiguous network timeout")
        result = service.reconcile(identifier, self.transport, actor="op", now=NOW)
        self.assertEqual(result["status"], "outcome_unknown")
        self.assertIsNone(result["receipt"])

    def test_recall_scan_is_not_capped_at_one_page_of_confirmed_intents(self) -> None:
        worker = PublicationWorker(self.queue, self.transport, dry_run=False)
        self.assertEqual(worker.run_once(now=NOW)["status"], "confirmed")
        calls: list[int] = []
        original = self.queue.list_intents

        def capped(*, limit: int = 100, status: str | None = None) -> list[dict]:
            calls.append(limit)
            return [] if limit <= 1000 else original(limit=limit, status=status)

        self.queue.list_intents = capped  # type: ignore[method-assign]
        service = RecallService(self.queue)
        # Stale facts make every confirmed publication need a recall.
        self.assertEqual(service.scan(now=NOW + timedelta(days=2)), 1)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()


class LoginThrottleTests(_OperatorServerCase):
    def login_status(self, token: str) -> tuple[int, dict[str, str]]:
        status, headers, _ = self.request(
            "POST",
            "/dashboard/login",
            body=urlencode({"token": token}).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return status, headers

    def test_repeated_wrong_tokens_are_throttled_even_for_the_right_token(self) -> None:
        for _ in range(10):
            self.assertEqual(self.login_status("wrong")[0], 401)
        status, headers = self.login_status("audit-secret")
        self.assertEqual(status, 429)
        self.assertIn("Retry-After", headers)
        self.assertNotIn("Set-Cookie", headers)

    def test_a_few_typos_do_not_block_the_operator(self) -> None:
        for _ in range(3):
            self.assertEqual(self.login_status("typo")[0], 401)
        self.assertEqual(self.login_status("audit-secret")[0], 303)

    def test_login_page_is_mobile_ready(self) -> None:
        status, _, page = self.request("GET", "/dashboard/login")
        self.assertEqual(status, 200)
        self.assertIn('name="viewport"', page)
        self.assertIn("<title>", page)


class EncapsulationTests(unittest.TestCase):
    def test_modules_outside_the_store_do_not_touch_its_private_state(self) -> None:
        offenders = []
        for path in sorted((ROOT / "src/s_n_sales").rglob("*.py")):
            if path.parent.name == "api":
                continue  # The store and its migration helper own the connection.
            text = path.read_text(encoding="utf-8")
            for marker in ("store._lock", "store._conn", "store._decide_in_transaction"):
                if marker in text:
                    offenders.append(f"{path.relative_to(ROOT)}: {marker}")
        self.assertEqual(offenders, [])


class ProvenanceNormalizationTests(unittest.TestCase):
    def test_manual_import_records_the_normalized_actor(self) -> None:
        store = SqliteOperatorStore(":memory:")
        self.addCleanup(store.close)
        repo = DealRepository(store, url_policy=UrlPolicy(frozenset({"example.com"})))
        saved = repo.import_manual(canonical(manual_request()).encode(), actor="  op  ", now=NOW)
        self.assertEqual(saved.facts["captured_by"], "op")


class RecallLeasePolicyTests(_DurableCase):
    def test_withdrawal_lease_follows_queue_policy(self) -> None:
        worker = PublicationWorker(self.queue, self.transport, dry_run=False)
        self.assertEqual(worker.run_once(now=NOW)["status"], "confirmed")
        self.queue.policy = QueuePolicy(lease_seconds=120)
        service = RecallService(self.queue)
        identifier = self.intent["intent_id"]
        service.request(identifier, actor="op", reason="audit", now=NOW)
        seen: list[str] = []
        inner_withdraw = self.transport.withdraw

        def observing(key: str, *, now: datetime) -> dict:
            seen.append(service.get(identifier)["lease_until"])
            return inner_withdraw(key, now=now)

        self.transport.withdraw = observing  # type: ignore[method-assign]
        self.assertEqual(
            service.run_once(self.transport, now=NOW, dry_run=False)["status"], "confirmed"
        )
        self.assertEqual(seen, [iso(NOW + timedelta(seconds=120))])
