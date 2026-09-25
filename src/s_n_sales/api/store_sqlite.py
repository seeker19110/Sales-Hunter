"""Transactional SQLite pilot store with versioned state and append-only history.

All writes acquire BEGIN IMMEDIATE, compare the viewed revision, and commit the
projection + history + current authority together. No network call occurs here.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import sqlite3
import threading
from collections.abc import Iterator
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from s_n_sales.api.contracts import (
    StoreIntegrityError,
    approval_projection,
    candidate_from_json,
    canonical_json,
    draft_fields,
    pending_import,
    require_actor,
    require_revision,
    timestamp,
    validate_approval_record,
    validate_candidate,
)
from s_n_sales.domain.publication_state import CandidateSnapshot
from s_n_sales.pipeline.approval import decide_approval
from s_n_sales.pipeline.publisher import _receipt_validator

# Backward-compatible names used by earlier projection code/tests.
_candidate_approval_projection = approval_projection
_candidate_from_json = candidate_from_json


class SqliteOperatorStore:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = str(db_path if db_path is not None else Path("var/operator.db"))
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA busy_timeout = 5000")
        try:
            self._init_schema()
            if self.db_path != ":memory:":
                self._conn.execute("PRAGMA journal_mode = WAL")
        except BaseException:
            self._conn.close()
            raise

    @contextlib.contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Short local write transaction. Never hold across network operations."""
        with self._lock:
            if self._conn.in_transaction:
                raise RuntimeError("nested_transaction_not_supported")
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                yield self._conn
                self._conn.commit()
            except BaseException:
                self._conn.rollback()
                raise

    def _init_schema(self) -> None:
        with self.transaction() as connection:
            for statement in (
                """CREATE TABLE IF NOT EXISTS candidates (
                    publication_id TEXT PRIMARY KEY, draft_sha256 TEXT NOT NULL,
                    status TEXT NOT NULL, candidate_json TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    revision INTEGER NOT NULL DEFAULT 1 CHECK(revision > 0))""",
                """CREATE TABLE IF NOT EXISTS approvals (
                    publication_id TEXT PRIMARY KEY, draft_sha256 TEXT NOT NULL,
                    status TEXT NOT NULL, decided_by TEXT NOT NULL, decided_at TEXT NOT NULL,
                    reason TEXT, approval_json TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY(publication_id) REFERENCES candidates(publication_id))""",
                """CREATE TABLE IF NOT EXISTS publish_receipts (
                    receipt_id TEXT PRIMARY KEY, idempotency_key TEXT UNIQUE NOT NULL,
                    target_channel TEXT NOT NULL, published_at TEXT NOT NULL,
                    receipt_json TEXT NOT NULL)""",
                """CREATE TABLE IF NOT EXISTS store_migrations (
                    name TEXT PRIMARY KEY, version INTEGER NOT NULL,
                    manifest_json TEXT NOT NULL)""",
                """CREATE TABLE IF NOT EXISTS candidate_revisions (
                    publication_id TEXT NOT NULL, revision INTEGER NOT NULL,
                    candidate_json TEXT NOT NULL, created_at TEXT NOT NULL,
                    PRIMARY KEY(publication_id, revision),
                    FOREIGN KEY(publication_id) REFERENCES candidates(publication_id))""",
                """CREATE TABLE IF NOT EXISTS candidate_events (
                    event_id TEXT PRIMARY KEY, publication_id TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    kind TEXT NOT NULL, actor TEXT NOT NULL, created_at TEXT NOT NULL,
                    reviewed_revision INTEGER, approval_json TEXT,
                    FOREIGN KEY(publication_id, revision)
                        REFERENCES candidate_revisions(publication_id, revision))""",
            ):
                connection.execute(statement)
            for table in ("candidates", "approvals"):
                columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
                if "revision" not in columns:
                    connection.execute(
                        f"ALTER TABLE {table} ADD COLUMN revision INTEGER NOT NULL DEFAULT 1"
                    )
            for table in ("candidate_revisions", "candidate_events"):
                for action in ("UPDATE", "DELETE"):
                    connection.execute(
                        f"CREATE TRIGGER IF NOT EXISTS {table}_no_{action.lower()} "
                        f"BEFORE {action} ON {table} BEGIN "
                        "SELECT RAISE(ABORT, 'append_only_history'); END"
                    )
            installed = connection.execute(
                "SELECT version FROM store_migrations WHERE name='operator_revision'"
            ).fetchone()
            if installed is not None:
                if installed["version"] != 1:
                    raise StoreIntegrityError("unsupported_operator_schema")
                return
            sources: list[dict[str, Any]] = []
            for row in connection.execute(
                "SELECT * FROM candidates ORDER BY publication_id"
            ).fetchall():
                candidate = candidate_from_json(row["candidate_json"])
                validate_candidate(candidate)
                if (
                    candidate["publication_id"] != row["publication_id"]
                    or candidate["draft_sha256"] != row["draft_sha256"]
                    or candidate["approval"]["status"] != row["status"]
                ):
                    raise StoreIntegrityError("legacy_candidate_projection_mismatch")
                old = connection.execute(
                    "SELECT approval_json FROM approvals WHERE publication_id=?",
                    (row["publication_id"],),
                ).fetchone()
                record = json.loads(old["approval_json"]) if old else None
                if record is not None:
                    validate_approval_record(record, candidate)
                elif row["status"] != "pending":
                    raise StoreIntegrityError("legacy_approval_missing")
                sources.append({"candidate": dict(row), "approval": record})
                self._append_version(
                    connection,
                    candidate,
                    row["revision"],
                    kind="legacy_snapshot",
                    actor="system:migration",
                    at=timestamp(),
                    record=record,
                )
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise StoreIntegrityError("foreign_key_check_failed")
            manifest = {
                "version": 1,
                "candidate_count": len(sources),
                "approval_count": sum(item["approval"] is not None for item in sources),
                "source_sha256": hashlib.sha256(
                    canonical_json(sources).encode("utf-8")
                ).hexdigest(),
                "migrated_at": timestamp(),
                "history_before_migration": "not_reconstructed",
            }
            connection.execute(
                "INSERT INTO store_migrations VALUES ('operator_revision', 1, ?)",
                (canonical_json(manifest),),
            )

    @staticmethod
    def _append_version(
        connection: sqlite3.Connection,
        candidate: dict[str, Any],
        revision: int,
        *,
        kind: str,
        actor: str,
        at: str,
        reviewed_revision: int | None = None,
        record: dict[str, Any] | None = None,
    ) -> None:
        connection.execute(
            "INSERT INTO candidate_revisions VALUES (?, ?, ?, ?)",
            (candidate["publication_id"], revision, canonical_json(candidate), at),
        )
        connection.execute(
            "INSERT INTO candidate_events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"evt-{uuid4().hex}",
                candidate["publication_id"],
                revision,
                kind,
                actor,
                at,
                reviewed_revision,
                canonical_json(record) if record is not None else None,
            ),
        )

    def close(self) -> None:
        with self._lock, contextlib.suppress(sqlite3.ProgrammingError):
            self._conn.close()

    def upsert_candidate(
        self,
        candidate: dict[str, Any],
        *,
        expected_revision: int | None = None,
        actor: str = "system:import",
        now: datetime | None = None,
    ) -> dict[str, Any]:
        copied = pending_import(candidate)
        actor, at = require_actor(actor), timestamp(now)
        pub_id = copied["publication_id"]
        with self.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM candidates WHERE publication_id=?", (pub_id,)
            ).fetchone()
            if row is not None:
                require_revision(expected_revision, row["revision"])
                previous = candidate_from_json(row["candidate_json"])
                if draft_fields(previous) == draft_fields(copied):
                    return previous  # An idempotent import never revokes an existing decision.
                revision = row["revision"] + 1
                old = connection.execute(
                    "SELECT approval_json FROM approvals WHERE publication_id=?", (pub_id,)
                ).fetchone()
                connection.execute("DELETE FROM approvals WHERE publication_id=?", (pub_id,))
                connection.execute(
                    """UPDATE candidates SET draft_sha256=?, status='pending', candidate_json=?,
                       updated_at=?, revision=? WHERE publication_id=? AND revision=?""",
                    (
                        copied["draft_sha256"],
                        canonical_json(copied),
                        at,
                        revision,
                        pub_id,
                        row["revision"],
                    ),
                )
                self._append_version(
                    connection,
                    copied,
                    revision,
                    kind="edited",
                    actor=actor,
                    at=at,
                    reviewed_revision=row["revision"],
                    record=json.loads(old["approval_json"]) if old else None,
                )
            else:
                if expected_revision is not None:
                    raise StoreIntegrityError("new_candidate_has_revision")
                connection.execute(
                    "INSERT INTO candidates VALUES (?, ?, 'pending', ?, ?, ?, 1)",
                    (pub_id, copied["draft_sha256"], canonical_json(copied), at, at),
                )
                self._append_version(connection, copied, 1, kind="created", actor=actor, at=at)
        return deepcopy(copied)

    def get_snapshot(self, publication_id: str) -> CandidateSnapshot | None:
        with self._lock:
            row = self._conn.execute(
                """SELECT c.*, a.approval_json, a.revision AS approval_revision,
                          r.candidate_json AS revision_json
                   FROM candidates c LEFT JOIN approvals a USING(publication_id)
                   LEFT JOIN candidate_revisions r
                     ON r.publication_id=c.publication_id AND r.revision=c.revision
                   WHERE c.publication_id=?""",
                (publication_id,),
            ).fetchone()
        if row is None:
            return None
        candidate = candidate_from_json(row["candidate_json"])
        validate_candidate(candidate)
        if (
            row["revision_json"] is None
            or candidate != candidate_from_json(row["revision_json"])
            or candidate["draft_sha256"] != row["draft_sha256"]
            or candidate["approval"]["status"] != row["status"]
        ):
            raise StoreIntegrityError("stored_projection_mismatch")
        record = json.loads(row["approval_json"]) if row["approval_json"] else None
        if record is not None:
            if row["approval_revision"] != row["revision"]:
                raise StoreIntegrityError("stored_approval_revision_mismatch")
            validate_approval_record(record, candidate)
        elif row["status"] != "pending":
            raise StoreIntegrityError("stored_approval_missing")
        return CandidateSnapshot(row["revision"], candidate, record)

    def get_revision(self, publication_id: str) -> int:
        snapshot = self.get_snapshot(publication_id)
        if snapshot is None:
            raise KeyError(publication_id)
        return snapshot.revision

    def get_candidate(self, publication_id: str) -> dict[str, Any] | None:
        snapshot = self.get_snapshot(publication_id)
        return snapshot.candidate if snapshot else None

    def get_approval(self, publication_id: str) -> dict[str, Any] | None:
        snapshot = self.get_snapshot(publication_id)
        return snapshot.approval if snapshot else None

    def list_candidates(self, status: str | None = None) -> list[dict[str, Any]]:
        if status not in (None, "pending", "approved", "rejected"):
            raise ValueError("invalid_status_filter")
        with self._lock:
            rows = self._conn.execute(
                "SELECT publication_id FROM candidates WHERE (? IS NULL OR status=?) "
                "ORDER BY created_at DESC, publication_id",
                (status, status),
            ).fetchall()
            snapshots = [self.get_snapshot(row["publication_id"]) for row in rows]
        return [snapshot.candidate for snapshot in snapshots if snapshot is not None]

    def _decide(
        self,
        publication_id: str,
        *,
        status: str,
        decided_by: str,
        expected_revision: int | None,
        reason: str | None,
        now: datetime | None,
    ) -> dict[str, Any]:
        clock = now if now is not None else datetime.now(UTC)
        actor, at = require_actor(decided_by), timestamp(clock)
        with self.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM candidates WHERE publication_id=?", (publication_id,)
            ).fetchone()
            if row is None:
                raise KeyError(publication_id)
            require_revision(expected_revision, row["revision"])
            candidate = candidate_from_json(row["candidate_json"])
            validate_candidate(candidate)
            record = decide_approval(
                candidate,
                status=status,
                decided_by=actor,
                decided_at=clock,
                reason=reason,
            )
            candidate["approval"] = approval_projection(record)
            validate_candidate(candidate)
            revision = row["revision"] + 1
            connection.execute(
                """UPDATE candidates SET status=?, candidate_json=?, updated_at=?, revision=?
                   WHERE publication_id=? AND revision=?""",
                (status, canonical_json(candidate), at, revision, publication_id, row["revision"]),
            )
            connection.execute(
                """INSERT INTO approvals VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(publication_id) DO UPDATE SET
                       draft_sha256=excluded.draft_sha256, status=excluded.status,
                       decided_by=excluded.decided_by, decided_at=excluded.decided_at,
                       reason=excluded.reason, approval_json=excluded.approval_json,
                       revision=excluded.revision""",
                (
                    publication_id,
                    record["draft_sha256"],
                    status,
                    actor,
                    record["decided_at"],
                    reason,
                    canonical_json(record),
                    revision,
                ),
            )
            self._append_version(
                connection,
                candidate,
                revision,
                kind=status,
                actor=actor,
                at=at,
                reviewed_revision=row["revision"],
                record=record,
            )
        return deepcopy(record)

    def approve(
        self,
        publication_id: str,
        *,
        decided_by: str,
        reason: str | None = None,
        now: datetime | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        return self._decide(
            publication_id,
            status="approved",
            decided_by=decided_by,
            reason=reason,
            now=now,
            expected_revision=expected_revision,
        )

    def reject(
        self,
        publication_id: str,
        *,
        decided_by: str,
        reason: str | None = None,
        now: datetime | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        return self._decide(
            publication_id,
            status="rejected",
            decided_by=decided_by,
            reason=reason,
            now=now,
            expected_revision=expected_revision,
        )

    def list_history(self, publication_id: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """SELECT e.*, r.candidate_json FROM candidate_events e
                   JOIN candidate_revisions r USING(publication_id, revision)
                   WHERE publication_id=? ORDER BY revision""",
                (publication_id,),
            ).fetchall()
        return [
            {
                "revision": row["revision"],
                "kind": row["kind"],
                "actor": row["actor"],
                "created_at": row["created_at"],
                "reviewed_revision": row["reviewed_revision"],
                "candidate": candidate_from_json(row["candidate_json"]),
                "approval": json.loads(row["approval_json"]) if row["approval_json"] else None,
            }
            for row in rows
        ]

    def migration_manifest(self) -> dict[str, Any]:
        with self._lock:
            row = self._conn.execute(
                "SELECT manifest_json FROM store_migrations WHERE name='operator_revision'"
            ).fetchone()
        return json.loads(row["manifest_json"])

    def save_receipt(self, receipt: dict[str, Any]) -> dict[str, Any]:
        if not _receipt_validator().is_valid(receipt):
            raise ValueError("receipt_contract_invalid")
        copied = deepcopy(receipt)
        with self.transaction() as connection:
            try:
                connection.execute(
                    "INSERT INTO publish_receipts VALUES (?, ?, ?, ?, ?)",
                    (
                        copied["receipt_id"],
                        copied["idempotency_key"],
                        copied["target_channel"],
                        copied["published_at"],
                        canonical_json(copied),
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("duplicate_receipt_or_idempotency_key") from exc
        return copied

    def list_receipts(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT receipt_json FROM publish_receipts ORDER BY published_at DESC, receipt_id"
            ).fetchall()
        return [json.loads(row["receipt_json"]) for row in rows]

    def get_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT receipt_json FROM publish_receipts WHERE receipt_id=?", (receipt_id,)
            ).fetchone()
        return json.loads(row["receipt_json"]) if row else None
