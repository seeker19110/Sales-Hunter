from __future__ import annotations

import base64
import hashlib
import io
import json
import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch
from wsgiref.util import setup_testing_defaults
from wsgiref.validate import validator

from s_n_sales.api.store_sqlite import SqliteOperatorStore
from s_n_sales.pipeline.draft import observation_to_rank
from s_n_sales.pipeline.publication import build_publication_candidate
from s_n_sales.platform_web import PlatformPilot, create_app

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "test-only-operator-token-not-a-real-secret-0000"
ORIGIN = "https://sales-staging.donghanhcungban.org"


class PlatformWebTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "pilot.db"
        self.store = SqliteOperatorStore(self.path)
        observation = json.loads(
            (ROOT / "schemas/examples/valid/offer-observation.v1.json").read_text(encoding="utf-8")
        )
        rank = observation_to_rank(observation, now=datetime(2026, 9, 11, 6, tzinfo=UTC))
        candidate = build_publication_candidate(
            observation,
            rank,
            content='<script>alert("unsafe")</script>',
            affiliate_url="https://example.com/aff/item-demo-001",
            target_channel="telegram:sales-hunter-demo",
        )
        self.store.upsert_candidate(candidate)
        self.store.close()
        self.app = self.new_app()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def new_app(self) -> PlatformPilot:
        return PlatformPilot(origin=ORIGIN, db_path=self.path, actor="operator", token=TOKEN)

    def request(
        self,
        path: str = "/dashboard",
        *,
        auth: bool = True,
        method: str = "GET",
        query: str = "",
        host: str = "sales-staging.donghanhcungban.org",
        authorization: str | None = None,
        extra: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], str]:
        environ: dict[str, Any] = {}
        setup_testing_defaults(environ)
        environ.update(
            {
                "PATH_INFO": path,
                "REQUEST_METHOD": method,
                "QUERY_STRING": query,
                "HTTP_HOST": host,
                "wsgi.input": io.BytesIO(b""),
            }
        )
        if auth:
            encoded = base64.b64encode(f"operator:{TOKEN}".encode()).decode()
            environ["HTTP_AUTHORIZATION"] = "Basic " + encoded
        if authorization is not None:
            environ["HTTP_AUTHORIZATION"] = authorization
        if extra:
            environ.update(extra)
        captured: list[Any] = []

        def start_response(
            status: str, headers: list[tuple[str, str]], exc_info: Any = None
        ) -> None:
            captured.extend([status, headers])

        output = validator(self.app)(environ, start_response)
        try:
            body = b"".join(output).decode()
        finally:
            output.close()
        return int(captured[0].split()[0]), dict(captured[1]), body

    def test_health_has_no_data_and_explicit_read_only_mode(self) -> None:
        code, _, body = self.request("/healthz", auth=False)
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["mode"], "read_only")
        self.assertIs(json.loads(body)["live_publish"], False)
        self.assertNotIn(TOKEN, body)
        self.assertNotIn(str(self.path), body)

    def test_dashboard_requires_independent_credentials(self) -> None:
        code, headers, body = self.request(auth=False)
        self.assertEqual(code, 401)
        self.assertIn("WWW-Authenticate", headers)
        self.assertNotIn("item-demo", body)
        code, _, _ = self.request(
            auth=False,
            extra={
                "HTTP_COOKIE": "learning_session=anything",
                "HTTP_CF_ACCESS_AUTHENTICATED_USER_EMAIL": "operator@example.invalid",
            },
        )
        self.assertEqual(code, 401)

    def test_bad_and_forged_credentials_do_not_authenticate(self) -> None:
        values = (
            "Basic !!!",
            "Basic //8=",
            "Bearer " + TOKEN,
            "Basic " + "A" * 3000,
            "Basic " + base64.b64encode(b"wrong:wrong").decode(),
        )
        for value in values:
            with self.subTest(value=value[:20]):
                self.assertEqual(self.request(authorization=value)[0], 401)

    def test_no_query_or_cookie_authentication(self) -> None:
        self.assertEqual(self.request(auth=False, query="token=" + TOKEN)[0], 401)
        self.assertEqual(self.request(query="token=" + TOKEN)[0], 400)

    def test_all_mutations_are_disabled(self) -> None:
        for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"):
            code, headers, _ = self.request(method=method)
            self.assertEqual(code, 405)
            self.assertEqual(headers["Allow"], "GET")
        self.assertEqual(self.request("/api/v1/candidates")[0], 404)
        self.assertEqual(self.request("/publish")[0], 404)

    def test_host_cannot_be_replaced_by_forwarded_header(self) -> None:
        hosts = (
            "evil.example",
            "en-vi.donghanhcungban.org",
            "sales-staging.donghanhcungban.org.evil",
        )
        for host in hosts:
            code, _, _ = self.request(
                host=host,
                extra={"HTTP_X_FORWARDED_HOST": "sales-staging.donghanhcungban.org"},
            )
            self.assertEqual(code, 400)

    def test_render_is_escaped_and_does_not_claim_publication(self) -> None:
        code, headers, body = self.request()
        self.assertEqual(code, 200)
        self.assertIn("&lt;script&gt;", body)
        self.assertNotIn("<script>", body)
        self.assertIn("chỉ đọc", body)
        self.assertIn("không phải xác nhận", body)
        self.assertIn('href="https://donghanhcungban.org"', body)
        self.assertNotIn("<form", body)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertNotIn(TOKEN, body)
        self.assertEqual(headers["X-Robots-Tag"], "noindex, nofollow")

    def test_database_hash_unchanged_across_reads_and_restart(self) -> None:
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.request()
        self.request("/healthz", auth=False)
        self.app = self.new_app()
        self.assertEqual(self.request()[0], 200)
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), before)
        self.assertFalse(Path(str(self.path) + "-journal").exists())

    def test_bad_page_and_duplicate_fields_fail_closed(self) -> None:
        queries = ("page=-1", "page=10001", "page=a", "page=1&page=2", "page=", "x=1", "page=%FF")
        for query in queries:
            with self.subTest(query=query):
                self.assertEqual(self.request(query=query)[0], 400)
        self.assertIn("Chưa có bản nháp", self.request(query="page=1")[2])

    def test_missing_file_and_empty_database_are_not_initialized(self) -> None:
        missing = self.path.parent / "missing.db"
        with self.assertRaises(ValueError):
            PlatformPilot(origin=ORIGIN, db_path=missing, actor="operator", token=TOKEN)
        self.assertFalse(missing.exists())
        empty = self.path.parent / "empty.db"
        empty.write_bytes(b"")
        with self.assertRaises(sqlite3.Error):
            PlatformPilot(origin=ORIGIN, db_path=empty, actor="operator", token=TOKEN)
        self.assertEqual(empty.read_bytes(), b"")

    def test_configuration_is_explicit_and_fail_closed(self) -> None:
        for origin in ("http://sales.donghanhcungban.org", "https://evil.example", ORIGIN + "/"):
            with self.assertRaises(ValueError):
                PlatformPilot(origin=origin, db_path=self.path, actor="operator", token=TOKEN)
        for actor, token in (("", TOKEN), ("x:y", TOKEN), ("operator", "short")):
            with self.assertRaises(ValueError):
                PlatformPilot(origin=ORIGIN, db_path=self.path, actor=actor, token=token)
        with patch.dict("os.environ", {}, clear=True), self.assertRaises(KeyError):
            create_app()

    def test_failed_read_exposes_no_database_error_details(self) -> None:
        with patch.object(self.app, "_read_page", side_effect=sqlite3.OperationalError("secret path")):
            for path in ("/healthz", "/dashboard"):
                code, _, body = self.request(path)
                self.assertEqual(code, 503)
                self.assertNotIn("secret path", body)


if __name__ == "__main__":
    unittest.main()
