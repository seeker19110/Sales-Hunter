"""SQLite evidence with immutable provenance, redacted payload and explicit retention.

Permission is an operator attestation, not proof of live platform authorization.
Original bytes are hashed in memory and never persisted before redaction.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any

from s_n_sales.api.contracts import require_actor
from s_n_sales.api.store_sqlite import SqliteOperatorStore
from s_n_sales.domain.json_value import canonical, digest, iso, json_object, utc
from s_n_sales.quality.urls import UrlPolicy

_SENSITIVE_KEY = re.compile(
    r"^(?:customer|buyer)$|(?:^|[_ .-])"
    r"(?:token|secret|password|passwd|cookie|authorization|api.?key|email|phone|address|"
    r"customer.?id|buyer.?id|user.?id)(?:$|[_ .-])",
    re.I,
)
_SENSITIVE_TEXT = re.compile(
    r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}|\b(?:sk|ghp|github_pat)[-_][A-Za-z0-9_-]{8,}|\bBearer\s+\S+",
    re.I,
)


def has_sensitive_text(value: str) -> bool:
    return bool(_SENSITIVE_TEXT.search(value))


def _redact(value: Any, path: str, changed: list[str], depth: int = 0) -> Any:
    if depth > 16:
        raise ValueError("evidence_depth_limit")
    if isinstance(value, dict):
        if len(value) > 200:
            raise ValueError("evidence_field_limit")
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not re.fullmatch(r"[A-Za-z0-9_. -]{1,100}", key):
                raise ValueError("evidence_key_invalid")
            child = f"{path}.{key}"
            if _SENSITIVE_KEY.search(key):
                changed.append(child)
                result[key] = "[REDACTED]"
            else:
                result[key] = _redact(item, child, changed, depth + 1)
        return result
    if isinstance(value, list):
        if len(value) > 1024:
            raise ValueError("evidence_collection_limit")
        return [_redact(item, f"{path}[{i}]", changed, depth + 1) for i, item in enumerate(value)]
    if isinstance(value, str):
        if len(value) > 8000:
            raise ValueError("evidence_text_limit")
        if _SENSITIVE_TEXT.search(value):
            changed.append(path)
            return "[REDACTED]"
    return value


class EvidenceVault:
    def __init__(self, store: SqliteOperatorStore) -> None:
        self.store = store
        with store.transaction() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS evidence_manifests (evidence_id "
                "TEXT PRIMARY KEY, manifest_json TEXT NOT "
                "NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS evidence_payloads (evidence_id "
                "TEXT PRIMARY KEY REFERENCES evidence_manifests(evidence_id), "
                "body_json TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS evidence_tombstones (evidence_id "
                "TEXT PRIMARY KEY REFERENCES evidence_manifests(evidence_id), "
                "actor TEXT NOT NULL, reason TEXT NOT NULL, retired_at TEXT "
                "NOT NULL)"
            )
            for table in ("evidence_manifests", "evidence_tombstones"):
                for action in ("UPDATE", "DELETE"):
                    connection.execute(
                        f"CREATE TRIGGER IF NOT EXISTS {table}_immutable_{action} "
                        f"BEFORE {action} ON {table} "
                        "BEGIN SELECT RAISE(ABORT, 'immutable_evidence'); END"
                    )
            connection.execute(
                "CREATE TRIGGER IF NOT EXISTS evidence_payload_immutable "
                "BEFORE UPDATE ON evidence_payloads BEGIN SELECT RAISE(ABORT, "
                "'immutable_evidence'); END"
            )
            connection.execute(
                "CREATE TRIGGER IF NOT EXISTS evidence_payload_retention "
                "BEFORE DELETE ON evidence_payloads WHEN NOT EXISTS (SELECT 1 "
                "FROM evidence_tombstones WHERE evidence_id=OLD.evidence_id) "
                "BEGIN SELECT RAISE(ABORT, 'retention_record_required'); "
                "END"
            )

    def retain(
        self,
        raw: bytes,
        *,
        source_url: str,
        actor: str,
        permission_ref: str,
        permitted_until: datetime,
        now: datetime,
        url_policy: UrlPolicy,
    ) -> dict[str, Any]:
        source_url = url_policy.validate(source_url)
        actor = require_actor(actor)
        if (
            not isinstance(permission_ref, str)
            or not permission_ref.strip()
            or len(permission_ref) > 300
            or has_sensitive_text(permission_ref)
        ):
            raise ValueError("evidence_permission_required")
        if utc(permitted_until) <= utc(now):
            raise ValueError("evidence_permission_expired")
        original = json_object(raw)
        redacted: list[str] = []
        body = _redact(original, "$", redacted)
        manifest: dict[str, Any] = {
            "schema_version": "evidence-manifest.v1",
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "retained_sha256": digest(body),
            "source_url": source_url,
            "captured_by": actor,
            "captured_at": iso(now),
            "permitted_until": iso(permitted_until),
            "permission_ref": permission_ref.strip(),
            "redaction_policy": "known-sensitive-v1",
            "redacted_paths": redacted,
            "media_type": "application/json",
        }
        evidence_id = "ev-" + digest(manifest)
        with self.store.transaction() as connection:
            existing = connection.execute(
                "SELECT 1 FROM evidence_manifests WHERE evidence_id=?", (evidence_id,)
            ).fetchone()
            if existing is None:
                connection.execute(
                    "INSERT INTO evidence_manifests VALUES (?, ?)",
                    (evidence_id, canonical(manifest)),
                )
                connection.execute(
                    "INSERT INTO evidence_payloads VALUES (?, ?)", (evidence_id, canonical(body))
                )
            elif connection.execute(
                "SELECT 1 FROM evidence_tombstones WHERE evidence_id=?", (evidence_id,)
            ).fetchone():
                raise ValueError("evidence_retired")
        return {"evidence_id": evidence_id, **manifest}

    def read(self, evidence_id: str, *, now: datetime) -> dict[str, Any]:
        with self.store._lock:
            row = self.store._conn.execute(
                (
                    "SELECT m.manifest_json, p.body_json, t.retired_at FROM "
                    "evidence_manifests m LEFT JOIN evidence_payloads p "
                    "USING(evidence_id) LEFT JOIN evidence_tombstones t "
                    "USING(evidence_id) WHERE m.evidence_id=?"
                ),
                (evidence_id,),
            ).fetchone()
        if row is None or row["body_json"] is None or row["retired_at"] is not None:
            raise ValueError("evidence_missing_or_retired")
        manifest = json_object(row["manifest_json"].encode("utf-8"))
        if evidence_id != "ev-" + digest(manifest):
            raise ValueError("evidence_manifest_tampered")
        if utc(now) >= utc(manifest["permitted_until"]):
            raise ValueError("evidence_permission_expired")
        body = json_object(row["body_json"].encode("utf-8"))
        if digest(body) != manifest["retained_sha256"]:
            raise ValueError("evidence_payload_tampered")
        return {"evidence_id": evidence_id, "manifest": manifest, "document": body}

    def retire(self, evidence_id: str, *, actor: str, reason: str, now: datetime) -> bool:
        actor = require_actor(actor)
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 300:
            raise ValueError("retention_reason_required")
        with self.store.transaction() as connection:
            if not connection.execute(
                "SELECT 1 FROM evidence_manifests WHERE evidence_id=?", (evidence_id,)
            ).fetchone():
                raise KeyError(evidence_id)
            changed = connection.execute(
                "INSERT OR IGNORE INTO evidence_tombstones VALUES (?, ?, ?, ?)",
                (evidence_id, actor, reason, iso(now)),
            ).rowcount
            connection.execute("DELETE FROM evidence_payloads WHERE evidence_id=?", (evidence_id,))
        return bool(changed)

    def expire(self, *, now: datetime) -> int:
        with self.store._lock:
            rows = self.store._conn.execute(
                "SELECT m.* FROM evidence_manifests m LEFT JOIN "
                "evidence_tombstones t USING(evidence_id) WHERE t.evidence_id "
                "IS NULL"
            ).fetchall()
        count = 0
        for row in rows:
            manifest = json_object(row["manifest_json"].encode("utf-8"))
            if utc(manifest["permitted_until"]) <= utc(now):
                count += self.retire(
                    row["evidence_id"],
                    actor="system:retention",
                    reason="permission_expired",
                    now=now,
                )
        return count
