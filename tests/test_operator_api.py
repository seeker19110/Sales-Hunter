from __future__ import annotations

import json
import threading
import unittest
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from s_n_sales.api.app import make_server
from s_n_sales.api.store import OperatorStore
from s_n_sales.pipeline.draft import observation_to_rank
from s_n_sales.pipeline.publication import build_publication_candidate

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

    def _json(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = Request(
            self.base + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"} if body is not None else {},
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


if __name__ == "__main__":
    unittest.main()
