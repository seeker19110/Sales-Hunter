from __future__ import annotations

import json
import tempfile
import threading
import unittest
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from s_n_sales.api.app import make_server
from s_n_sales.api.store import OperatorStore
from s_n_sales.api.store_sqlite import SqliteOperatorStore
from s_n_sales.pipeline.draft import observation_to_rank
from s_n_sales.pipeline.manual_draft_flow import run_manual_to_publication_candidate
from s_n_sales.pipeline.publication import build_publication_candidate
from s_n_sales.pipeline.publisher import FakePlatformClient, Publisher, PublishError

ROOT = Path(__file__).resolve().parents[1]


class OperatorApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = OperatorStore()
        self.server = make_server(self.store, host="127.0.0.1", port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.port}"

        now = datetime(2026, 9, 11, 6, 0, tzinfo=UTC)
        obs = json.loads(
            (ROOT / "schemas/examples/valid/offer-observation.v1.json").read_text(encoding="utf-8")
        )
        rank = observation_to_rank(obs, now=now)
        self.candidate = build_publication_candidate(
            obs,
            rank,
            content="API staging demo",
            affiliate_url="https://example.com/aff/item-demo-001",
            target_channel="telegram:sales-hunter-demo",
        )

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def _json(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        req_headers = {"Content-Type": "application/json"} if body is not None else {}
        if headers:
            req_headers.update(headers)
        req = Request(
            self.base + path,
            data=data,
            method=method,
            headers=req_headers,
        )
        try:
            with urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_healthz(self) -> None:
        status, body = self._json("GET", "/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["service"], "sales-hunter-operator")

    def test_upsert_list_approve(self) -> None:
        status, saved = self._json("POST", "/api/v1/candidates", self.candidate)
        self.assertEqual(status, 201)
        pub_id = saved["publication_id"]

        status, listing = self._json("GET", "/api/v1/candidates")
        self.assertEqual(status, 200)
        self.assertEqual(len(listing["items"]), 1)

        status, got = self._json("GET", f"/api/v1/candidates/{pub_id}")
        self.assertEqual(status, 200)
        self.assertEqual(got["draft_sha256"], self.candidate["draft_sha256"])

        status, approval = self._json(
            "POST",
            f"/api/v1/candidates/{pub_id}/approve",
            {"decided_by": "operator@example.com"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(approval["status"], "approved")
        self.assertEqual(approval["draft_sha256"], self.candidate["draft_sha256"])

        status, stored = self._json("GET", f"/api/v1/candidates/{pub_id}/approval")
        self.assertEqual(status, 200)
        self.assertEqual(stored["approval_id"], approval["approval_id"])

    def test_reject(self) -> None:
        self._json("POST", "/api/v1/candidates", self.candidate)
        pub_id = self.candidate["publication_id"]
        status, approval = self._json(
            "POST",
            f"/api/v1/candidates/{pub_id}/reject",
            {"decided_by": "op", "reason": "stale price"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(approval["status"], "rejected")


class OperatorAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.token = "secret-token-xyz"
        self.store = OperatorStore()
        self.server = make_server(
            self.store,
            host="127.0.0.1",
            port=0,
            auth_token=self.token,
        )
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def test_healthz_allowed_without_auth(self) -> None:
        req = Request(self.base + "/healthz")
        with urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)

    def test_api_denied_without_auth(self) -> None:
        req = Request(self.base + "/api/v1/candidates")
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req, timeout=5)
        self.assertEqual(ctx.exception.code, 401)

    def test_api_denied_with_wrong_token(self) -> None:
        req = Request(
            self.base + "/api/v1/candidates",
            headers={"Authorization": "Bearer wrong-token"},
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req, timeout=5)
        self.assertEqual(ctx.exception.code, 401)

    def test_api_allowed_with_bearer_token(self) -> None:
        req = Request(
            self.base + "/api/v1/candidates",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        with urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)

    def test_api_allowed_with_query_token(self) -> None:
        req = Request(self.base + f"/api/v1/candidates?token={self.token}")
        with urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)


class OperatorDashboardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = OperatorStore()
        self.server = make_server(self.store, host="127.0.0.1", port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.port}"

        now = datetime(2026, 9, 11, 6, 0, tzinfo=UTC)
        obs = json.loads(
            (ROOT / "schemas/examples/valid/offer-observation.v1.json").read_text(encoding="utf-8")
        )
        rank = observation_to_rank(obs, now=now)
        self.candidate = build_publication_candidate(
            obs,
            rank,
            content="Dashboard preview test item",
            affiliate_url="https://example.com/aff/dash-item-001",
            target_channel="telegram:sales-hunter-dash",
        )
        self.store.upsert_candidate(self.candidate)

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def test_dashboard_html_list(self) -> None:
        req = Request(self.base + "/dashboard")
        with urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/html", resp.headers.get("Content-Type", ""))
            html = resp.read().decode("utf-8")
            self.assertIn("Sales-Hunter", html)
            self.assertIn(self.candidate["publication_id"], html)
            self.assertIn("pending", html)

    def test_dashboard_candidate_detail(self) -> None:
        pub_id = self.candidate["publication_id"]
        req = Request(f"{self.base}/dashboard/candidates/{pub_id}")
        with urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            html = resp.read().decode("utf-8")
            self.assertIn(pub_id, html)
            self.assertIn("Dashboard preview test item", html)
            self.assertIn("https://example.com/aff/dash-item-001", html)
            self.assertIn(self.candidate["draft_sha256"], html)
            self.assertIn("Approve", html)
            self.assertIn("Reject", html)

    def test_dashboard_form_approve(self) -> None:
        pub_id = self.candidate["publication_id"]
        form_data = urlencode(
            {
                "decided_by": "operator@test.com",
                "reason": "Verified deal quality",
            }
        ).encode("utf-8")
        req = Request(
            f"{self.base}/dashboard/candidates/{pub_id}/approve",
            data=form_data,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(req, timeout=5) as resp:
            self.assertIn(resp.status, (200, 303))

        approval = self.store.get_approval(pub_id)
        self.assertIsNotNone(approval)
        assert approval is not None
        self.assertEqual(approval["status"], "approved")
        self.assertEqual(approval["decided_by"], "operator@test.com")

    def test_dashboard_form_reject(self) -> None:
        pub_id = self.candidate["publication_id"]
        form_data = urlencode(
            {
                "decided_by": "operator@test.com",
                "reason": "Not enough discount",
            }
        ).encode("utf-8")
        req = Request(
            f"{self.base}/dashboard/candidates/{pub_id}/reject",
            data=form_data,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(req, timeout=5) as resp:
            self.assertIn(resp.status, (200, 303))

        approval = self.store.get_approval(pub_id)
        self.assertIsNotNone(approval)
        assert approval is not None
        self.assertEqual(approval["status"], "rejected")


class OperatorSqliteIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "test_api_sqlite.db"
        self.store = SqliteOperatorStore(db_path=db_path)
        self.server = make_server(self.store, host="127.0.0.1", port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.store.close()
        self.temp_dir.cleanup()

    def test_sqlite_store_via_api_and_receipts(self) -> None:
        obs = json.loads(
            (ROOT / "schemas/examples/valid/offer-observation.v1.json").read_text(encoding="utf-8")
        )
        now = datetime(2026, 9, 11, 6, 0, tzinfo=UTC)
        rank = observation_to_rank(obs, now=now)
        candidate = build_publication_candidate(
            obs,
            rank,
            content="SQLite API integration test",
            affiliate_url="https://example.com/aff/sqlite-api-001",
            target_channel="telegram:sales-hunter-demo",
        )
        req = Request(
            self.base + "/api/v1/candidates",
            data=json.dumps(candidate).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 201)

        req_list = Request(self.base + "/api/v1/candidates")
        with urlopen(req_list, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(len(data["items"]), 1)


class OperatorEndToEndPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "e2e_operator.db"
        self.store = SqliteOperatorStore(db_path=db_path)
        self.token = "e2e-secret-token"
        self.server = make_server(
            self.store,
            host="127.0.0.1",
            port=0,
            auth_token=self.token,
        )
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.port}"
        self.fixture = ROOT / "schemas/examples/valid/offer-observation.v1.json"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.store.close()
        self.temp_dir.cleanup()

    def test_end_to_end_observation_to_ui_to_publish(self) -> None:
        now = datetime(2026, 9, 11, 8, 0, tzinfo=UTC)

        # 1. Pipeline: load observation and build candidate
        candidate = run_manual_to_publication_candidate(
            self.fixture,
            content="Deal công nghệ hot — tai nghe không dây giảm giá sốc!",
            affiliate_url="https://example.com/aff/e2e-deal-001",
            target_channel="telegram:sales-hunter-channel",
            now=now,
        )
        pub_id = candidate["publication_id"]
        draft_sha = candidate["draft_sha256"]

        # 2. Ingest into Operator Store via API (with Bearer token)
        ingest_req = Request(
            self.base + "/api/v1/candidates",
            data=json.dumps(candidate).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
            method="POST",
        )
        with urlopen(ingest_req, timeout=5) as resp:
            self.assertEqual(resp.status, 201)

        # 3. Verify deal appears in Web Dashboard HTML
        dash_req = Request(f"{self.base}/dashboard?token={self.token}")
        with urlopen(dash_req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            html_content = resp.read().decode("utf-8")
            self.assertIn(pub_id, html_content)
            self.assertIn("Chờ duyệt", html_content)

        # 4. Operator approves deal via Web Form submission
        approve_form = urlencode(
            {
                "token": self.token,
                "decided_by": "lead-operator@donghanhcungban.org",
                "reason": "Verified price claim and affiliate disclosure",
            }
        ).encode("utf-8")
        approve_req = Request(
            f"{self.base}/dashboard/candidates/{pub_id}/approve",
            data=approve_form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urlopen(approve_req, timeout=5) as resp:
            self.assertIn(resp.status, (200, 303))

        # 5. Read back approval record from SQLite store and assert invariants
        approval = self.store.get_approval(pub_id)
        self.assertIsNotNone(approval)
        assert approval is not None
        self.assertEqual(approval["status"], "approved")
        self.assertEqual(approval["draft_sha256"], draft_sha)
        self.assertEqual(approval["decided_by"], "lead-operator@donghanhcungban.org")

        # 6. Verify dry-run safety invariant: publish with dry_run=True blocks external publish
        pub_dry = Publisher(dry_run=True)
        with self.assertRaises(PublishError):
            pub_dry.publish(candidate, approval, now=now)

        # 7. Execute idempotent publish with FakePlatformClient (dry_run=False in staging test)
        client = FakePlatformClient()
        publisher = Publisher(client=client, dry_run=False, approval_source=self.store)
        receipt = publisher.publish(candidate, approval, now=now)
        self.assertEqual(receipt["status"], "published")
        self.assertEqual(receipt["publication_id"], pub_id)

        # 8. Save receipt and verify via Receipts API
        self.store.save_receipt(receipt)
        receipts_req = Request(
            f"{self.base}/api/v1/receipts",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        with urlopen(receipts_req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            receipts_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(len(receipts_data["items"]), 1)
            self.assertEqual(receipts_data["items"][0]["receipt_id"], receipt["receipt_id"])


if __name__ == "__main__":
    unittest.main()
