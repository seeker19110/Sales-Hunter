"""SQLite persistent store for operator API and web dashboard."""

from __future__ import annotations

import contextlib
import json
import sqlite3
import threading
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from s_n_sales.pipeline.approval import decide_approval
from s_n_sales.pipeline.publication import assert_candidate_integrity


class SqliteOperatorStore:
    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            db_path = Path("var/operator.db")
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        if self.db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock, self._conn:
            cur = self._conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    publication_id TEXT PRIMARY KEY,
                    draft_sha256 TEXT NOT NULL,
                    status TEXT NOT NULL,
                    candidate_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS approvals (
                    publication_id TEXT PRIMARY KEY,
                    draft_sha256 TEXT NOT NULL,
                    status TEXT NOT NULL,
                    decided_by TEXT NOT NULL,
                    decided_at TEXT NOT NULL,
                    reason TEXT,
                    approval_json TEXT NOT NULL,
                    FOREIGN KEY(publication_id) REFERENCES candidates(publication_id)
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS publish_receipts (
                    receipt_id TEXT PRIMARY KEY,
                    idempotency_key TEXT UNIQUE NOT NULL,
                    target_channel TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    receipt_json TEXT NOT NULL
                );
            """)

    def close(self) -> None:
        with self._lock, contextlib.suppress(sqlite3.ProgrammingError):
            self._conn.close()

    def upsert_candidate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        candidate = deepcopy(candidate)
        assert_candidate_integrity(candidate)
        pub_id = candidate.get("publication_id")
        if not isinstance(pub_id, str) or not pub_id:
            raise ValueError("publication_id bắt buộc")

        draft_sha256 = candidate.get("draft_sha256", "")
        approval = candidate.get("approval")
        status = "pending"
        if isinstance(approval, dict) and isinstance(approval.get("status"), str):
            status = approval["status"]

        now_iso = datetime.now(UTC).isoformat()
        payload = json.dumps(candidate, ensure_ascii=False)

        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO candidates (
                    publication_id, draft_sha256, status,
                    candidate_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(publication_id) DO UPDATE SET
                    draft_sha256 = excluded.draft_sha256,
                    status = excluded.status,
                    candidate_json = excluded.candidate_json,
                    updated_at = excluded.updated_at
                """,
                (pub_id, draft_sha256, status, payload, now_iso, now_iso),
            )
        return deepcopy(candidate)

    def list_candidates(self, status: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            if status is not None:
                cur = self._conn.execute(
                    """
                    SELECT candidate_json FROM candidates
                    WHERE status = ? ORDER BY created_at DESC
                    """,
                    (status,),
                )
            else:
                cur = self._conn.execute(
                    "SELECT candidate_json FROM candidates ORDER BY created_at DESC"
                )
            rows = cur.fetchall()
        return [json.loads(row["candidate_json"]) for row in rows]

    def get_candidate(self, publication_id: str) -> dict[str, Any] | None:
        with self._lock:
            cur = self._conn.execute(
                "SELECT candidate_json FROM candidates WHERE publication_id = ?",
                (publication_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return json.loads(row["candidate_json"])

    def approve(
        self,
        publication_id: str,
        *,
        decided_by: str,
        reason: str | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        candidate = self.get_candidate(publication_id)
        if candidate is None:
            raise KeyError(publication_id)

        clock = now if now is not None else datetime.now(UTC)
        record = decide_approval(
            candidate,
            status="approved",
            decided_by=decided_by,
            decided_at=clock,
            reason=reason,
        )

        candidate["approval"] = record
        candidate_json = json.dumps(candidate, ensure_ascii=False)
        approval_json = json.dumps(record, ensure_ascii=False)
        updated_at = clock.isoformat()

        with self._lock, self._conn:
            self._conn.execute(
                """
                UPDATE candidates
                SET status = 'approved', candidate_json = ?, updated_at = ?
                WHERE publication_id = ?
                """,
                (candidate_json, updated_at, publication_id),
            )
            self._conn.execute(
                """
                INSERT INTO approvals (
                    publication_id, draft_sha256, status,
                    decided_by, decided_at, reason, approval_json
                ) VALUES (?, ?, 'approved', ?, ?, ?, ?)
                ON CONFLICT(publication_id) DO UPDATE SET
                    draft_sha256 = excluded.draft_sha256,
                    status = excluded.status,
                    decided_by = excluded.decided_by,
                    decided_at = excluded.decided_at,
                    reason = excluded.reason,
                    approval_json = excluded.approval_json
                """,
                (
                    publication_id,
                    record["draft_sha256"],
                    decided_by,
                    record["decided_at"],
                    reason,
                    approval_json,
                ),
            )

        return deepcopy(record)

    def reject(
        self,
        publication_id: str,
        *,
        decided_by: str,
        reason: str | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        candidate = self.get_candidate(publication_id)
        if candidate is None:
            raise KeyError(publication_id)

        clock = now if now is not None else datetime.now(UTC)
        record = decide_approval(
            candidate,
            status="rejected",
            decided_by=decided_by,
            decided_at=clock,
            reason=reason,
        )

        candidate["approval"] = record
        candidate_json = json.dumps(candidate, ensure_ascii=False)
        approval_json = json.dumps(record, ensure_ascii=False)
        updated_at = clock.isoformat()

        with self._lock, self._conn:
            self._conn.execute(
                """
                UPDATE candidates
                SET status = 'rejected', candidate_json = ?, updated_at = ?
                WHERE publication_id = ?
                """,
                (candidate_json, updated_at, publication_id),
            )
            self._conn.execute(
                """
                INSERT INTO approvals (
                    publication_id, draft_sha256, status,
                    decided_by, decided_at, reason, approval_json
                ) VALUES (?, ?, 'rejected', ?, ?, ?, ?)
                ON CONFLICT(publication_id) DO UPDATE SET
                    draft_sha256 = excluded.draft_sha256,
                    status = excluded.status,
                    decided_by = excluded.decided_by,
                    decided_at = excluded.decided_at,
                    reason = excluded.reason,
                    approval_json = excluded.approval_json
                """,
                (
                    publication_id,
                    record["draft_sha256"],
                    decided_by,
                    record["decided_at"],
                    reason,
                    approval_json,
                ),
            )

        return deepcopy(record)

    def get_approval(self, publication_id: str) -> dict[str, Any] | None:
        with self._lock:
            cur = self._conn.execute(
                "SELECT approval_json FROM approvals WHERE publication_id = ?",
                (publication_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return json.loads(row["approval_json"])

    def save_receipt(self, receipt: dict[str, Any]) -> dict[str, Any]:
        receipt_id = receipt.get("receipt_id")
        idempotency_key = receipt.get("idempotency_key")
        target_channel = receipt.get("target_channel")
        published_at = receipt.get("published_at")

        if not receipt_id or not idempotency_key or not target_channel or not published_at:
            raise ValueError("Thiếu trường bắt buộc trong publish receipt")

        payload = json.dumps(receipt, ensure_ascii=False)

        with self._lock:
            try:
                with self._conn:
                    self._conn.execute(
                        """
                        INSERT INTO publish_receipts (
                            receipt_id, idempotency_key, target_channel,
                            published_at, receipt_json
                        ) VALUES (?, ?, ?, ?, ?)
                        """,
                        (receipt_id, idempotency_key, target_channel, published_at, payload),
                    )
            except sqlite3.IntegrityError as exc:
                msg = f"Biên lai hoặc idempotency_key đã tồn tại: {idempotency_key}"
                raise ValueError(msg) from exc

        return deepcopy(receipt)

    def list_receipts(self) -> list[dict[str, Any]]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT receipt_json FROM publish_receipts ORDER BY published_at DESC"
            )
            rows = cur.fetchall()
        return [json.loads(row["receipt_json"]) for row in rows]

    def get_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        with self._lock:
            cur = self._conn.execute(
                "SELECT receipt_json FROM publish_receipts WHERE receipt_id = ?",
                (receipt_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return json.loads(row["receipt_json"])
