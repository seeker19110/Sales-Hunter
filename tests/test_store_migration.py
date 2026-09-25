"""Migration must preview without writes and roll back incompatible legacy data."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from s_n_sales.api.store_sqlite import SqliteOperatorStore
from s_n_sales.pipeline.publication import build_publication_candidate


class MigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "legacy.db"
        observation = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas/examples/valid/offer-observation.v1.json"
            ).read_text(encoding="utf-8")
        )
        self.candidate = build_publication_candidate(
            observation,
            {},
            content="Migration fixture",
            affiliate_url="https://example.com/aff",
            target_channel="manual_export",
        )

    def tearDown(self) -> None:
        self.directory.cleanup()

    def legacy(self, *, invalid: bool = False) -> None:
        candidate = dict(self.candidate)
        if invalid:
            candidate["content"] = "Tampered but old hash"
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """CREATE TABLE candidates (publication_id TEXT PRIMARY KEY,
                draft_sha256 TEXT NOT NULL, status TEXT NOT NULL, candidate_json TEXT NOT NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"""
            )
            connection.execute(
                "INSERT INTO candidates VALUES (?, ?, 'pending', ?, ?, ?)",
                (
                    candidate["publication_id"],
                    candidate["draft_sha256"],
                    json.dumps(candidate),
                    "2026-09-25T00:00:00Z",
                    "2026-09-25T00:00:00Z",
                ),
            )

    def test_preview_is_read_only_and_matches_applied_source_manifest(self) -> None:
        from s_n_sales.api.migration import preview_migration

        self.legacy()
        original = hashlib.sha256(self.path.read_bytes()).hexdigest()
        preview = preview_migration(self.path)
        self.assertTrue(preview["valid"])
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), original)
        store = SqliteOperatorStore(self.path)
        try:
            manifest = store.migration_manifest()
            self.assertEqual(manifest["candidate_count"], 1)
            self.assertEqual(manifest["source_sha256"], preview["manifest"]["source_sha256"])
            self.assertEqual(store.get_candidate(self.candidate["publication_id"]), self.candidate)
            self.assertEqual(
                store.list_history(self.candidate["publication_id"])[0]["kind"], "legacy_snapshot"
            )
        finally:
            store.close()

    def test_failed_migration_leaves_schema_and_content_unchanged(self) -> None:
        self.legacy(invalid=True)
        with self.assertRaises(ValueError):
            SqliteOperatorStore(self.path)
        with sqlite3.connect(self.path) as connection:
            columns = [row[1] for row in connection.execute("PRAGMA table_info(candidates)")]
            self.assertNotIn("revision", columns)
            payload = connection.execute("SELECT candidate_json FROM candidates").fetchone()[0]
            self.assertEqual(json.loads(payload)["content"], "Tampered but old hash")
            self.assertFalse(
                connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE name='candidate_revisions'"
                ).fetchall()
            )

    def test_preview_invalid_legacy_has_error_without_payload(self) -> None:
        from s_n_sales.api.migration import preview_migration

        self.legacy(invalid=True)
        report = preview_migration(self.path)
        self.assertFalse(report["valid"])
        self.assertNotIn("Tampered", json.dumps(report))

    def test_missing_source_is_not_created_by_preview(self) -> None:
        from s_n_sales.api.migration import preview_migration

        with self.assertRaises(FileNotFoundError):
            preview_migration(self.path)
        self.assertFalse(self.path.exists())
