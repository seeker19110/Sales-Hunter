"""Durable payload-scoped outbox for the local pilot; transport calls stay outside SQL."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from s_n_sales.api.contracts import require_actor, require_revision
from s_n_sales.domain.json_value import canonical, digest, iso, utc
from s_n_sales.pipeline.approval import assert_approval_matches_draft
from s_n_sales.publishing.contracts import (
    DeliveryTransport,
    DuplicateBusinessDeal,
    Lease,
    LeaseLost,
    Paused,
    QueuePolicy,
    validate_proof,
    validate_transport,
)
from s_n_sales.publishing.schema import initialize
from s_n_sales.quality.facts import business_key, evaluate_eligibility
from s_n_sales.quality.repository import DealPackage, DealRepository

DEFAULT_QUEUE_POLICY = QueuePolicy()
_ACTIVE = ("ready", "claimed", "sending", "retryable_failed", "outcome_unknown")
_FIELDS = frozenset(
    {
        "attempts",
        "available_at",
        "lease_token",
        "lease_until",
        "worker_id",
        "receipt_json",
        "error_code",
        "cooldown_until",
    }
)


class PublicationQueue:
    def __init__(self, repository: DealRepository, *, policy: QueuePolicy = DEFAULT_QUEUE_POLICY):
        self.repository, self.store, self.policy = repository, repository.store, policy
        initialize(self.store)

    @staticmethod
    def _event(
        connection: sqlite3.Connection,
        intent_id: str | None,
        kind: str,
        actor: str,
        now: datetime,
        detail: dict[str, Any] | None = None,
    ) -> None:
        connection.execute(
            "INSERT INTO publish_events VALUES (?, ?, ?, ?, ?, ?)",
            (uuid4().hex, intent_id, kind, actor, iso(now), canonical(detail or {})),
        )

    def _transition(
        self,
        connection: sqlite3.Connection,
        intent_id: str,
        status: str,
        *,
        actor: str,
        now: datetime,
        **changes: Any,
    ) -> None:
        if not set(changes).issubset(_FIELDS):
            raise ValueError("invalid_internal_transition_fields")
        assignments = ", ".join(f"{key}=?" for key in changes)
        suffix = ", " + assignments if assignments else ""
        connection.execute(
            "UPDATE publish_intents SET status=?, updated_at=?" + suffix + " WHERE intent_id=?",
            (status, iso(now), *changes.values(), intent_id),
        )
        self._event(
            connection, intent_id, status, actor, now, {"error_code": changes.get("error_code")}
        )

    def set_pause(
        self, scope: str, scope_key: str, *, paused: bool, actor: str, reason: str, now: datetime
    ) -> None:
        actor = require_actor(actor)
        if (
            scope not in ("global", "source", "channel")
            or type(paused) is not bool
            or not isinstance(scope_key, str)
            or not scope_key.strip()
            or len(scope_key) > 200
            or (scope == "global" and scope_key != "*")
            or not isinstance(reason, str)
            or not reason.strip()
            or len(reason) > 300
        ):
            raise ValueError("pause_contract_invalid")
        with self.store.transaction() as connection:
            connection.execute(
                "INSERT INTO publish_pauses VALUES (?,?,?,?,?,?) ON CONFLICT(scope,scope_key) "
                "DO UPDATE SET paused=excluded.paused,actor=excluded.actor,reason=excluded.reason,"
                "updated_at=excluded.updated_at",
                (scope, scope_key, int(paused), actor, reason, iso(now)),
            )
            self._event(
                connection,
                None,
                "pause_changed",
                actor,
                now,
                {"scope": scope, "scope_key": scope_key, "paused": paused, "reason": reason},
            )

    def pauses(self) -> list[dict[str, Any]]:
        with self.store._lock:
            return [dict(row) for row in self.store._conn.execute("SELECT * FROM publish_pauses")]

    @staticmethod
    def _is_paused(connection: sqlite3.Connection, source: str, channel: str) -> bool:
        row = connection.execute(
            "SELECT 1 FROM publish_pauses WHERE paused=1 AND ((scope='global' AND scope_key='*') "
            "OR (scope='source' AND scope_key=?) OR (scope='channel' AND scope_key=?))",
            (source, channel),
        ).fetchone()
        return row is not None

    def _eligible(self, package: DealPackage, *, now: datetime) -> None:
        decision = evaluate_eligibility(
            package.facts,
            vault=self.repository.vault,
            url_policy=self.repository.url_policy,
            now=now,
        )
        if not decision.eligible:
            raise ValueError("publication_eligibility_failed")

    def approve_payload(
        self,
        publication_id: str,
        *,
        expected_revision: int,
        expected_payload_sha256: str,
        actor: str,
        now: datetime,
        reason: str | None = None,
    ) -> dict[str, Any]:
        actor = require_actor(actor)
        with self.store.transaction() as connection:
            package = self.repository.get(publication_id)
            require_revision(expected_revision, package.snapshot.revision)
            if package.payload["payload_sha256"] != expected_payload_sha256:
                raise ValueError("viewed_payload_hash_mismatch")
            self._eligible(package, now=now)
            record = self.store._decide_in_transaction(
                connection,
                publication_id,
                status="approved",
                decided_by=actor,
                expected_revision=expected_revision,
                reason=reason,
                now=now,
            )
            scope = {
                "schema_version": "payload-approval.v1",
                "publication_id": publication_id,
                "revision": expected_revision + 1,
                "viewed_revision": expected_revision,
                "approval_id": record["approval_id"],
                "draft_sha256": record["draft_sha256"],
                "payload_sha256": expected_payload_sha256,
                "facts_id": package.facts["facts_id"],
                "target_channel": package.payload["target_channel"],
                "renderer_version": package.payload["renderer_version"],
                "actor": actor,
                "decided_at": record["decided_at"],
            }
            scope_id = "scope-" + digest(scope)
            connection.execute(
                "INSERT INTO payload_approvals VALUES (?,?,?,?,?)",
                (
                    scope_id,
                    publication_id,
                    scope["revision"],
                    record["approval_id"],
                    canonical(scope),
                ),
            )
            self._event(connection, None, "payload_approved", actor, now, {"scope_id": scope_id})
        return {"scope_id": scope_id, **scope}

    def _current_scope(
        self, publication_id: str, *, expected_revision: int, payload_hash: str, now: datetime
    ) -> tuple[DealPackage, str]:
        if not self.store._conn.in_transaction:
            raise RuntimeError("scope_check_requires_owned_transaction")
        package = self.repository.get(publication_id)
        require_revision(expected_revision, package.snapshot.revision)
        record = package.snapshot.approval
        if record is None:
            raise ValueError("approval_missing")
        assert_approval_matches_draft(record, package.snapshot.candidate)
        row = self.store._conn.execute(
            "SELECT * FROM payload_approvals WHERE approval_id=?", (record["approval_id"],)
        ).fetchone()
        if row is None:
            raise ValueError("payload_scoped_approval_missing")
        scope = json.loads(row["scope_json"])
        if (
            row["scope_id"] != "scope-" + digest(scope)
            or scope["revision"] != expected_revision
            or scope["publication_id"] != publication_id
            or scope["payload_sha256"] != payload_hash
            or payload_hash != package.payload["payload_sha256"]
            or scope["target_channel"] != package.payload["target_channel"]
            or scope["draft_sha256"] != package.payload["draft_sha256"]
            or scope["facts_id"] != package.facts["facts_id"]
        ):
            raise ValueError("payload_scoped_approval_mismatch")
        self._eligible(package, now=now)
        return package, row["scope_id"]

    def enqueue(
        self,
        publication_id: str,
        *,
        expected_revision: int,
        expected_payload_sha256: str,
        actor: str,
        now: datetime,
    ) -> dict[str, Any]:
        return self.enqueue_many(
            [
                {
                    "publication_id": publication_id,
                    "expected_revision": expected_revision,
                    "expected_payload_sha256": expected_payload_sha256,
                }
            ],
            actor=actor,
            now=now,
        )[0]

    def enqueue_many(
        self, requests: list[dict[str, Any]], *, actor: str, now: datetime
    ) -> list[dict[str, Any]]:
        actor = require_actor(actor)
        if not requests or len(requests) > 100:
            raise ValueError("enqueue_batch_size_invalid")
        prepared: list[tuple[DealPackage, str]] = []
        identifiers: list[str] = []
        with self.store.transaction() as connection:
            for request in requests:
                if set(request) != {
                    "publication_id",
                    "expected_revision",
                    "expected_payload_sha256",
                }:
                    raise ValueError("enqueue_request_fields_invalid")
                prepared.append(
                    self._current_scope(
                        request["publication_id"],
                        expected_revision=request["expected_revision"],
                        payload_hash=request["expected_payload_sha256"],
                        now=now,
                    )
                )
            for package, scope_id in prepared:
                if not package.payload["target_channel"].startswith("fake:"):
                    raise ValueError("manual_export_is_not_publication")
                previous = connection.execute(
                    "SELECT intent_id FROM publish_intents WHERE logical_key=?", (scope_id,)
                ).fetchone()
                if previous:
                    identifiers.append(previous["intent_id"])
                    continue
                key, channel = business_key(package.facts), package.payload["target_channel"]
                overlaps = connection.execute(
                    (
                        "SELECT status,cooldown_until FROM publish_intents WHERE "
                        "business_key=? AND channel=?"
                    ),
                    (key, channel),
                ).fetchall()
                if any(
                    row["status"] in _ACTIVE
                    or (row["cooldown_until"] and utc(row["cooldown_until"]) > utc(now))
                    for row in overlaps
                ):
                    raise DuplicateBusinessDeal("active_unknown_or_cooldown_deal")
                identifier = "intent-" + uuid4().hex
                connection.execute(
                    """INSERT INTO publish_intents (intent_id,logical_key,scope_id,publication_id,
                    revision,channel,source,business_key,payload_json,policy_json,status,available_at,
                    created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,'ready',?,?,?)""",
                    (
                        identifier,
                        scope_id,
                        scope_id,
                        package.snapshot.candidate["publication_id"],
                        package.snapshot.revision,
                        channel,
                        package.facts["observation"]["platform"],
                        key,
                        canonical(package.payload),
                        canonical(asdict(self.policy)),
                        iso(now),
                        iso(now),
                        iso(now),
                    ),
                )
                self._event(connection, identifier, "enqueued", actor, now)
                identifiers.append(identifier)
        return [self.get(identifier) for identifier in identifiers]

    def get(self, intent_id: str) -> dict[str, Any]:
        with self.store._lock:
            row = self.store._conn.execute(
                "SELECT * FROM publish_intents WHERE intent_id=?", (intent_id,)
            ).fetchone()
        if row is None:
            raise KeyError(intent_id)
        item = dict(row)
        item["payload"] = json.loads(item.pop("payload_json"))
        item["policy"] = json.loads(item.pop("policy_json"))
        receipt = item.pop("receipt_json")
        item["receipt"] = json.loads(receipt) if receipt else None
        return item

    def list_intents(self, *, limit: int = 100, status: str | None = None) -> list[dict[str, Any]]:
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("intent_limit_invalid")
        with self.store._lock:
            rows = self.store._conn.execute(
                "SELECT intent_id FROM publish_intents WHERE (? IS NULL OR status=?) "
                "ORDER BY created_at DESC,intent_id LIMIT ?",
                (status, status, limit),
            ).fetchall()
        return [self.get(row["intent_id"]) for row in rows]

    def _recover(self, connection: sqlite3.Connection, *, now: datetime) -> None:
        rows = connection.execute(
            (
                "SELECT * FROM publish_intents WHERE status IN "
                "('claimed','sending') AND lease_until<=?"
            ),
            (iso(now),),
        ).fetchall()
        for row in rows:
            ambiguous = row["status"] == "sending"
            self._transition(
                connection,
                row["intent_id"],
                "outcome_unknown" if ambiguous else "ready",
                actor="system:lease",
                now=now,
                lease_token=None,
                worker_id=None,
                lease_until=None,
                error_code="lease_expired_during_send" if ambiguous else None,
            )

    def recover_leases(self, *, now: datetime) -> None:
        with self.store.transaction() as connection:
            self._recover(connection, now=now)

    def claim(self, *, worker_id: str, now: datetime) -> Lease | None:
        worker_id = require_actor(worker_id)
        with self.store.transaction() as connection:
            self._recover(connection, now=now)
            rows = connection.execute(
                "SELECT * FROM publish_intents WHERE status IN ('ready','retryable_failed') "
                "AND available_at<=? ORDER BY available_at,intent_id",
                (iso(now),),
            ).fetchall()
            for row in rows:
                if self._is_paused(connection, row["source"], row["channel"]):
                    continue
                policy = QueuePolicy(**json.loads(row["policy_json"]))
                token = uuid4().hex
                self._transition(
                    connection,
                    row["intent_id"],
                    "claimed",
                    actor=worker_id,
                    now=now,
                    lease_token=token,
                    worker_id=worker_id,
                    lease_until=iso(utc(now) + timedelta(seconds=policy.lease_seconds)),
                )
                return Lease(row["intent_id"], token, worker_id)
        return None

    def _leased(
        self,
        connection: sqlite3.Connection,
        claim: Lease,
        status: str,
        *,
        now: datetime,
        require_unexpired: bool = True,
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM publish_intents WHERE intent_id=?", (claim.intent_id,)
        ).fetchone()
        if (
            row is None
            or row["status"] != status
            or row["lease_token"] != claim.token
            or row["worker_id"] != claim.worker_id
            or (require_unexpired and utc(row["lease_until"]) <= utc(now))
        ):
            raise LeaseLost("stale_or_expired_lease")
        return row

    def start_send(self, claim: Lease, *, now: datetime) -> dict[str, Any]:
        failure: str | None = None
        with self.store.transaction() as connection:
            row = self._leased(connection, claim, "claimed", now=now)
            if self._is_paused(connection, row["source"], row["channel"]):
                failure = "paused"
                self._transition(
                    connection,
                    claim.intent_id,
                    "ready",
                    actor=claim.worker_id,
                    now=now,
                    lease_token=None,
                    worker_id=None,
                    lease_until=None,
                    error_code="paused",
                )
            else:
                payload = json.loads(row["payload_json"])
                try:
                    _, scope_id = self._current_scope(
                        row["publication_id"],
                        expected_revision=row["revision"],
                        payload_hash=payload["payload_sha256"],
                        now=now,
                    )
                    if scope_id != row["scope_id"]:
                        raise ValueError("scope_changed")
                except (ValueError, KeyError):
                    failure = "authority_or_eligibility_changed"
                    self._transition(
                        connection,
                        claim.intent_id,
                        "terminal_failed",
                        actor=claim.worker_id,
                        now=now,
                        error_code=failure,
                        lease_token=None,
                        worker_id=None,
                        lease_until=None,
                    )
                if failure is None:
                    policy = QueuePolicy(**json.loads(row["policy_json"]))
                    if row["attempts"] >= policy.max_attempts:
                        failure = "attempt_limit"
                        self._transition(
                            connection,
                            claim.intent_id,
                            "terminal_failed",
                            actor=claim.worker_id,
                            now=now,
                            error_code=failure,
                            lease_token=None,
                            worker_id=None,
                            lease_until=None,
                        )
                    else:
                        connection.execute(
                            "INSERT INTO publish_attempts VALUES (?,?,?,?,?,?)",
                            (
                                uuid4().hex,
                                claim.intent_id,
                                row["attempts"] + 1,
                                claim.token,
                                claim.worker_id,
                                iso(now),
                            ),
                        )
                        self._transition(
                            connection,
                            claim.intent_id,
                            "sending",
                            actor=claim.worker_id,
                            now=now,
                            attempts=row["attempts"] + 1,
                            error_code=None,
                            lease_until=iso(utc(now) + timedelta(seconds=policy.lease_seconds)),
                        )
        if failure == "paused":
            raise Paused("persistent_pause")
        if failure is not None:
            raise ValueError(failure)
        return self.get(claim.intent_id)

    def failed(
        self,
        claim: Lease,
        *,
        retryable_not_sent: bool,
        terminal_not_sent: bool = False,
        now: datetime,
    ) -> dict[str, Any]:
        with self.store.transaction() as connection:
            row = self._leased(connection, claim, "sending", now=now, require_unexpired=False)
            policy = QueuePolicy(**json.loads(row["policy_json"]))
            status = "outcome_unknown"
            code = "ambiguous_outcome"
            if terminal_not_sent or (retryable_not_sent and row["attempts"] >= policy.max_attempts):
                status, code = "terminal_failed", "provider_not_accepted_terminal"
            elif retryable_not_sent:
                status, code = "retryable_failed", "provider_not_accepted_retryable"
            delay = min(300, policy.backoff_seconds * 2 ** max(0, row["attempts"] - 1))
            self._transition(
                connection,
                claim.intent_id,
                status,
                actor=claim.worker_id,
                now=now,
                error_code=code,
                lease_token=None,
                worker_id=None,
                lease_until=None,
                available_at=iso(utc(now) + timedelta(seconds=delay)),
            )
        return self.get(claim.intent_id)

    def _confirm(
        self,
        connection: sqlite3.Connection,
        row: sqlite3.Row,
        proof: dict[str, Any],
        *,
        actor: str,
        now: datetime,
    ) -> None:
        policy = QueuePolicy(**json.loads(row["policy_json"]))
        connection.execute(
            "INSERT INTO publish_confirmations VALUES (?,?,?)",
            (row["intent_id"], canonical(proof), iso(now)),
        )
        self._transition(
            connection,
            row["intent_id"],
            "confirmed",
            actor=actor,
            now=now,
            receipt_json=canonical(proof),
            lease_token=None,
            worker_id=None,
            lease_until=None,
            error_code=None,
            cooldown_until=iso(utc(now) + timedelta(seconds=policy.cooldown_seconds)),
        )
        try:
            self._current_scope(
                row["publication_id"],
                expected_revision=row["revision"],
                payload_hash=proof["payload_sha256"],
                now=now,
            )
        except (ValueError, KeyError):
            connection.execute(
                "INSERT OR IGNORE INTO recall_intents "
                "(intent_id,status,reason,created_at) VALUES (?,'pending',?,?)",
                (row["intent_id"], "authority_or_eligibility_changed", iso(now)),
            )
            self._event(connection, row["intent_id"], "recall_required", actor, now)

    def confirmed(self, claim: Lease, proof: dict[str, Any], *, now: datetime) -> dict[str, Any]:
        with self.store.transaction() as connection:
            row = self._leased(connection, claim, "sending", now=now, require_unexpired=False)
            validate_proof(proof, json.loads(row["payload_json"]), key=row["logical_key"], now=now)
            self._confirm(connection, row, proof, actor=claim.worker_id, now=now)
        return self.get(claim.intent_id)

    def reconcile(
        self, intent_id: str, transport: DeliveryTransport, *, actor: str, now: datetime
    ) -> dict[str, Any]:
        actor = require_actor(actor)
        validate_transport(transport)
        previous = self.get(intent_id)
        if previous["status"] != "outcome_unknown":
            raise ValueError("reconcile_requires_unknown")
        try:
            proof = transport.lookup(previous["logical_key"], now=now)
            if proof is not None:
                validate_proof(proof, previous["payload"], key=previous["logical_key"], now=now)
        except Exception:
            return previous  # No guessed absence or exception text retained.
        with self.store.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM publish_intents WHERE intent_id=?", (intent_id,)
            ).fetchone()
            if row["status"] != "outcome_unknown":
                return self.get(intent_id)
            if proof is not None:
                self._confirm(connection, row, proof, actor=actor, now=now)
            elif transport.definitive_absence:
                policy = QueuePolicy(**json.loads(row["policy_json"]))
                try:
                    self._current_scope(
                        row["publication_id"],
                        expected_revision=row["revision"],
                        payload_hash=previous["payload"]["payload_sha256"],
                        now=now,
                    )
                    valid = row["attempts"] < policy.max_attempts
                except (ValueError, KeyError):
                    valid = False
                self._transition(
                    connection,
                    intent_id,
                    "retryable_failed" if valid else "terminal_failed",
                    actor=actor,
                    now=now,
                    error_code="provider_confirmed_absent",
                    available_at=iso(utc(now) + timedelta(seconds=policy.backoff_seconds)),
                )
            else:
                self._event(connection, intent_id, "manual_review_required", actor, now)
        return self.get(intent_id)

    def export_approved(
        self,
        publication_id: str,
        *,
        expected_revision: int,
        expected_payload_sha256: str,
        actor: str,
        now: datetime,
    ) -> dict[str, Any]:
        actor = require_actor(actor)
        with self.store.transaction() as connection:
            package, scope_id = self._current_scope(
                publication_id,
                expected_revision=expected_revision,
                payload_hash=expected_payload_sha256,
                now=now,
            )
            if package.payload["target_channel"] != "manual_export":
                raise ValueError("export_requires_manual_channel")
            result = {
                "export_id": "export-" + uuid4().hex,
                "status": "exported_not_published",
                "scope_id": scope_id,
                "payload": package.payload,
                "actor": actor,
                "at": iso(now),
            }
            connection.execute(
                "INSERT INTO approved_exports VALUES (?,?,?,?,?)",
                (result["export_id"], scope_id, iso(now), actor, canonical(result)),
            )
            self._event(
                connection, None, "manual_export", actor, now, {"export_id": result["export_id"]}
            )
        return result

    def heartbeat(self, worker_id: str, *, now: datetime, dry_run: bool) -> None:
        with self.store.transaction() as connection:
            connection.execute(
                "INSERT INTO worker_heartbeats VALUES (?,?,?) ON CONFLICT(worker_id) "
                "DO UPDATE SET last_seen=excluded.last_seen,mode=excluded.mode",
                (require_actor(worker_id), iso(now), "dry_run" if dry_run else "fake"),
            )
