"""Security contract for the local operator API and dashboard."""

from __future__ import annotations

import http.client
import json
import re
import threading
import unittest
from datetime import UTC, datetime
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode

from s_n_sales.api.app import make_server
from s_n_sales.api.store import OperatorStore
from s_n_sales.pipeline.draft import observation_to_rank
from s_n_sales.pipeline.publication import build_publication_candidate


def seeded_store() -> tuple[OperatorStore, str]:
    store = OperatorStore()
    fixture = (
        Path(__file__).resolve().parents[1]
        / "schemas/examples/valid/offer-observation.v1.json"
    )
    observation = json.loads(fixture.read_text(encoding="utf-8"))
    rank = observation_to_rank(observation, now=datetime(2026, 9, 11, 6, tzinfo=UTC))
    candidate = build_publication_candidate(
        observation,
        rank,
        content="Security test candidate",
        affiliate_url="https://example.com/aff/security-test",
        target_channel="telegram:security-test",
    )
    store.upsert_candidate(candidate)
    return store, candidate["publication_id"]


class OperatorAuthSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store, self.publication_id = seeded_store()
        self.server = make_server(self.store, auth_token="test-secret")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], str]:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        payload = urlencode(body).encode("utf-8") if body is not None else None
        request_headers = {"Content-Type": "application/x-www-form-urlencoded"} if body else {}
        request_headers.update(headers or {})
        try:
            connection.request(method, path, body=payload, headers=request_headers)
            response = connection.getresponse()
            status = response.status
            response_headers = dict(response.getheaders())
            text = response.read().decode("utf-8")
            return status, response_headers, text
        finally:
            connection.close()

    def login(self) -> tuple[str, str]:
        status, headers, _ = self.request("POST", "/dashboard/login", body={"token": "test-secret"})
        self.assertEqual(status, 303)
        self.assertEqual(headers.get("Location"), "/dashboard")
        set_cookie = headers.get("Set-Cookie", "")
        self.assertIn("HttpOnly", set_cookie)
        self.assertIn("SameSite=Strict", set_cookie)
        self.assertIn("Path=/dashboard", set_cookie)
        cookie = set_cookie.split(";", 1)[0]
        self.assertTrue(cookie)
        self.assertNotIn("test-secret", cookie)
        status, _, detail = self.request(
            "GET", f"/dashboard/candidates/{self.publication_id}", headers={"Cookie": cookie}
        )
        self.assertEqual(status, 200)
        match = re.search(r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"', detail)
        self.assertIsNotNone(match, "decision form must include a CSRF token")
        assert match is not None
        return cookie, match.group(1)

    def test_api_rejects_token_in_query_but_accepts_bearer(self) -> None:
        status, _, _ = self.request("GET", "/api/v1/candidates?token=test-secret")
        self.assertEqual(status, 401)
        status, _, _ = self.request(
            "GET", "/api/v1/candidates", headers={"Authorization": "Bearer test-secret"}
        )
        self.assertEqual(status, 200)

    def test_dashboard_rejects_token_in_query_or_form(self) -> None:
        status, _, _ = self.request("GET", "/dashboard")
        self.assertEqual(status, 401)
        status, _, _ = self.request("GET", "/dashboard?token=test-secret")
        self.assertEqual(status, 401)
        status, _, _ = self.request(
            "POST",
            f"/dashboard/candidates/{self.publication_id}/approve",
            body={"token": "test-secret", "decided_by": "attacker"},
        )
        self.assertEqual(status, 401)
        self.assertIsNone(self.store.get_approval(self.publication_id))

    def test_dashboard_session_and_csrf_contract(self) -> None:
        status, _, _ = self.request("GET", "/dashboard/login")
        self.assertEqual(status, 200)
        status, _, _ = self.request(
            "GET", "/dashboard", headers={"Cookie": "operator_session=forged"}
        )
        self.assertEqual(status, 401)
        cookie, csrf = self.login()
        status, _, listing = self.request("GET", "/dashboard", headers={"Cookie": cookie})
        self.assertEqual(status, 200)
        self.assertNotIn("test-secret", listing)
        self.assertNotIn("?token=", listing)
        self.assertTrue(csrf)
        status, _, _ = self.request(
            "POST",
            f"/dashboard/candidates/{self.publication_id}/approve",
            body={"reason": "checked"},
            headers={"Cookie": cookie},
        )
        self.assertEqual(status, 403)
        self.assertIsNone(self.store.get_approval(self.publication_id))
        status, _, _ = self.request(
            "POST",
            f"/dashboard/candidates/{self.publication_id}/reject",
            body={"reason": "checked", "csrf_token": "forged"},
            headers={"Cookie": cookie},
        )
        self.assertEqual(status, 403)
        self.assertIsNone(self.store.get_approval(self.publication_id))
        status, headers, _ = self.request(
            "POST",
            f"/dashboard/candidates/{self.publication_id}/approve",
            body={"reason": "verified", "csrf_token": csrf, "decided_by": "forged"},
            headers={"Cookie": cookie},
        )
        self.assertEqual(status, 303)
        self.assertNotIn("test-secret", headers.get("Location", ""))
        approval = self.store.get_approval(self.publication_id)
        self.assertIsNotNone(approval)
        assert approval is not None
        self.assertEqual(approval["decided_by"], "operator")
        status, headers, _ = self.request(
            "POST", "/dashboard/logout", body={"csrf_token": csrf}, headers={"Cookie": cookie}
        )
        self.assertEqual(status, 303)
        self.assertEqual(headers.get("Location"), "/dashboard/login")
        status, _, _ = self.request("GET", "/dashboard", headers={"Cookie": cookie})
        self.assertEqual(status, 401)


class OperatorAuthConfigurationTests(unittest.TestCase):
    def test_missing_auth_configuration_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            server = make_server(OperatorStore(), host="127.0.0.1", port=0)
            server.server_close()

    def test_remote_bind_refused_in_all_modes(self) -> None:
        with self.assertRaises(ValueError):
            server = make_server(
                OperatorStore(), host="0.0.0.0", port=0, allow_unauthenticated_local=True
            )
            server.server_close()
        with self.assertRaises(ValueError):
            server = make_server(OperatorStore(), host="0.0.0.0", port=0, auth_token="secret")
            server.server_close()

    def test_authenticated_actor_cannot_be_forged_by_api_caller(self) -> None:
        store, publication_id = seeded_store()
        server: ThreadingHTTPServer = make_server(
            store, host="127.0.0.1", port=0, auth_token="secret", auth_actor="reviewer"
        )
        try:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            connection = http.client.HTTPConnection(
                "127.0.0.1", server.server_address[1], timeout=5
            )
            try:
                connection.request(
                    "POST",
                    f"/api/v1/candidates/{publication_id}/approve",
                    body=b'{"decided_by":"attacker"}',
                    headers={
                        "Authorization": "Bearer secret",
                        "Content-Type": "application/json",
                    },
                )
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                response.read()
                approval = store.get_approval(publication_id)
                self.assertIsNotNone(approval)
                assert approval is not None
                self.assertEqual(approval["decided_by"], "reviewer")
            finally:
                connection.close()
                server.shutdown()
                thread.join(timeout=5)
        finally:
            server.server_close()


if __name__ == "__main__":
    unittest.main()
