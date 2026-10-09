"""ADR-0011: every candidate creation path uses a versioned, verified URL allowlist."""

from __future__ import annotations

import http.client
import json
import shutil
import tempfile
import threading
import unittest
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from s_n_sales.api.app import make_server
from s_n_sales.api.store import OperatorStore
from s_n_sales.pipeline.draft import observation_to_rank
from s_n_sales.pipeline.manual_draft_flow import run_manual_to_publication_candidate
from s_n_sales.pipeline.publication import PublicationBuildError, build_publication_candidate
from s_n_sales.quality.allowlist import load_url_policy
from s_n_sales.quality.urls import UrlPolicy

ROOT = Path(__file__).resolve().parents[1]
OBSERVATION = ROOT / "schemas/examples/valid/offer-observation.v1.json"
EXAMPLE_POLICY = UrlPolicy(frozenset({"example.com"}))
NOW = datetime(2026, 9, 11, 6, tzinfo=UTC)


def _observation() -> dict[str, Any]:
    return json.loads(OBSERVATION.read_text(encoding="utf-8"))


def _allowlist(**changes: Any) -> dict[str, Any]:
    document: dict[str, Any] = {
        "schema_version": "url-allowlist.v1",
        "version": "2026-10-09.1",
        "max_redirects": 2,
        "hosts": [
            {
                "host": "example.com",
                "purpose": "affiliate",
                "reference": "https://www.rfc-editor.org/rfc/rfc2606",
                "verified_on": "2026-10-09",
            },
            {
                "host": "example.com",
                "purpose": "evidence",
                "reference": "https://www.rfc-editor.org/rfc/rfc2606",
                "verified_on": "2026-10-09",
            },
        ],
    }
    document.update(changes)
    return document


class AllowlistLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "url-allowlist.v1.json"

    def test_loads_versioned_policy(self) -> None:
        self.path.write_text(json.dumps(_allowlist()), encoding="utf-8")
        policy = load_url_policy(self.path)
        self.assertEqual(policy.allowed_hosts, frozenset({"example.com"}))
        self.assertEqual(policy.max_redirects, 2)
        self.assertEqual(policy.version, "2026-10-09.1")
        self.assertEqual(policy.validate("https://example.com/aff"), "https://example.com/aff")

    def test_rejects_unverified_host_duplicate_keys_and_bad_files(self) -> None:
        unverified = _allowlist()
        del unverified["hosts"][0]["verified_on"]
        cases = {
            "contract": json.dumps(unverified),
            "duplicate": '{"version": "2026-10-09.1", "version": "2026-10-09.2"}',
            "array": "[]",
        }
        for name, text in cases.items():
            with self.subTest(name), self.assertRaises(ValueError):
                self.path.write_text(text, encoding="utf-8")
                load_url_policy(self.path)
        with self.assertRaises(ValueError):
            load_url_policy(self.path.with_name("missing.json"))

    def test_repository_default_is_fail_closed(self) -> None:
        policy = load_url_policy(ROOT / "config/url-allowlist.v1.json")
        self.assertEqual(policy.allowed_hosts, frozenset())
        with self.assertRaises(ValueError):
            policy.validate("https://example.com/aff")


class BuilderAllowlistTests(unittest.TestCase):
    def build(self, observation: dict[str, Any], affiliate_url: str, policy: UrlPolicy) -> dict:
        return build_publication_candidate(
            observation,
            observation_to_rank(observation, now=NOW),
            content="Allowlist test",
            affiliate_url=affiliate_url,
            target_channel="telegram:allowlist",
            url_policy=policy,
        )

    def test_builder_requires_a_policy(self) -> None:
        observation = _observation()
        with self.assertRaises(TypeError):
            build_publication_candidate(  # type: ignore[call-arg]
                observation,
                observation_to_rank(observation, now=NOW),
                content="Allowlist test",
                affiliate_url="https://example.com/aff",
                target_channel="telegram:allowlist",
            )

    def test_affiliate_and_evidence_urls_must_be_allowlisted(self) -> None:
        observation = _observation()
        self.assertEqual(
            self.build(observation, "https://example.com/aff", EXAMPLE_POLICY)["affiliate_url"],
            "https://example.com/aff",
        )
        with self.assertRaisesRegex(PublicationBuildError, "affiliate_url"):
            self.build(observation, "https://attacker.example/aff", EXAMPLE_POLICY)
        observation["evidence"]["source_url"] = "https://evidence.example/page"
        with self.assertRaisesRegex(PublicationBuildError, "source_url"):
            self.build(observation, "https://example.com/aff", EXAMPLE_POLICY)

    def test_manual_flow_requires_and_applies_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "observation.json"
            observation = _observation()
            observation["source_method"] = "manual"
            path.write_text(json.dumps(observation), encoding="utf-8")
            candidate = run_manual_to_publication_candidate(
                path,
                content="Manual allowlist",
                affiliate_url="https://example.com/aff",
                target_channel="telegram:allowlist",
                now=NOW,
                url_policy=EXAMPLE_POLICY,
            )
            self.assertEqual(candidate["affiliate_url"], "https://example.com/aff")
            with self.assertRaises(PublicationBuildError):
                run_manual_to_publication_candidate(
                    path,
                    content="Manual allowlist",
                    affiliate_url="https://attacker.example/aff",
                    target_channel="telegram:allowlist",
                    now=NOW,
                    url_policy=EXAMPLE_POLICY,
                )


class ApiImportAllowlistTests(unittest.TestCase):
    def serve(self, policy: UrlPolicy | None) -> int:
        store = OperatorStore()
        self.addCleanup(store.close)
        server = make_server(store, auth_token="allowlist-secret", url_policy=policy)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 5)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.store = store
        return server.server_address[1]

    def post(self, port: int, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            connection.request(
                "POST",
                "/api/v1/candidates",
                body=json.dumps(body).encode(),
                headers={
                    "Authorization": "Bearer allowlist-secret",
                    "Content-Type": "application/json",
                },
            )
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def candidate(self, affiliate_url: str) -> dict[str, Any]:
        observation = _observation()
        # Built under a permissive test policy to simulate an externally supplied draft.
        return build_publication_candidate(
            observation,
            observation_to_rank(observation, now=NOW),
            content="API allowlist",
            affiliate_url=affiliate_url,
            target_channel="telegram:allowlist",
            url_policy=UrlPolicy(frozenset({"example.com", "attacker.example"})),
        )

    def test_import_is_disabled_without_configured_allowlist(self) -> None:
        port = self.serve(None)
        status, body = self.post(port, self.candidate("https://example.com/aff"))
        self.assertEqual((status, body), (403, {"error": "url_allowlist_not_configured"}))
        self.assertEqual(self.store.list_candidates(), [])

    def test_import_rejects_urls_outside_allowlist(self) -> None:
        port = self.serve(EXAMPLE_POLICY)
        status, body = self.post(port, self.candidate("https://attacker.example/aff"))
        self.assertEqual((status, body), (400, {"error": "url_not_allowed"}))
        self.assertEqual(self.store.list_candidates(), [])
        status, _ = self.post(port, self.candidate("https://example.com/aff"))
        self.assertEqual(status, 201)


class RepositoryConfigContractTests(unittest.TestCase):
    def test_config_files_are_validated_against_their_schema(self) -> None:
        from tools.validate_repo import validate_repository

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            shutil.copytree(
                ROOT,
                root,
                ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "var", "dist"),
            )
            bad = _allowlist()
            del bad["hosts"][0]["reference"]
            (root / "config/url-allowlist.v1.json").write_text(json.dumps(bad), encoding="utf-8")
            errors = validate_repository(root)
        self.assertTrue(any("config/url-allowlist.v1.json" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
