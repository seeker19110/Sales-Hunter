"""Persistent withdrawal intents; deciding that a post is stale is not a withdrawal."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from s_n_sales.api.contracts import require_actor
from s_n_sales.domain.json_value import canonical, iso, utc
from s_n_sales.publishing.contracts import DeliveryTransport, validate_proof, validate_transport
from s_n_sales.publishing.queue import PublicationQueue


class RecallService:
    def __init__(self, queue: PublicationQueue) -> None:
        self.queue, self.store = queue, queue.store

    def request(self, intent_id: str, *, actor: str, reason: str, now: datetime) -> dict[str, Any]:
        actor = require_actor(actor)
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 300:
            raise ValueError("recall_reason_required")
        with self.store.transaction() as connection:
            original = self.queue.get(intent_id)
            if original["status"] != "confirmed":
                raise ValueError("recall_requires_confirmed_publication")
            inserted = connection.execute(
                "INSERT OR IGNORE INTO recall_intents (intent_id,status,reason,created_at) "
                "VALUES (?,'pending',?,?)",
                (intent_id, reason, iso(now)),
            ).rowcount
            if inserted:
                self.queue._event(
                    connection, intent_id, "recall_required", actor, now, {"reason": reason}
                )
        return self.get(intent_id)

    def get(self, intent_id: str) -> dict[str, Any]:
        with self.store._lock:
            row = self.store._conn.execute(
                "SELECT * FROM recall_intents WHERE intent_id=?", (intent_id,)
            ).fetchone()
        if row is None:
            raise KeyError(intent_id)
        result = dict(row)
        encoded = result.pop("receipt_json")
        result["receipt"] = json.loads(encoded) if encoded else None
        return result

    def scan(self, *, now: datetime) -> int:
        count = 0
        for intent in self.queue.list_intents(limit=1000, status="confirmed"):
            valid = True
            with self.store.transaction():
                try:
                    self.queue._current_scope(
                        intent["publication_id"],
                        expected_revision=intent["revision"],
                        payload_hash=intent["payload"]["payload_sha256"],
                        now=now,
                    )
                except (ValueError, KeyError):
                    valid = False
                existed = self.store._conn.execute(
                    "SELECT 1 FROM recall_intents WHERE intent_id=?", (intent["intent_id"],)
                ).fetchone()
            if not valid:
                self.request(
                    intent["intent_id"],
                    actor="system:freshness",
                    reason="authority_or_eligibility_changed",
                    now=now,
                )
                count += int(existed is None)
        return count

    def _confirm(
        self,
        intent_id: str,
        proof: dict[str, Any],
        *,
        actor: str,
        now: datetime,
        expected_token: str | None = None,
    ) -> None:
        with self.store.transaction() as connection:
            current = self.get(intent_id)
            if current["status"] == "confirmed":
                return
            if expected_token is not None:
                if (
                    current["status"] != "withdrawing"
                    or current["lease_token"] != expected_token
                    or current["lease_until"] <= iso(now)
                ):
                    return
            elif current["status"] != "outcome_unknown":
                return
            connection.execute(
                "UPDATE recall_intents SET status='confirmed',receipt_json=?,"
                "lease_token=NULL,worker_id=NULL,lease_until=NULL WHERE intent_id=?",
                (canonical(proof), intent_id),
            )
            self.queue._event(
                connection,
                intent_id,
                "withdrawal_confirmed",
                actor,
                now,
                {"proof_kind": proof["proof_kind"], "platform_post_id": proof["platform_post_id"]},
            )

    def reconcile(
        self, intent_id: str, transport: DeliveryTransport, *, actor: str, now: datetime
    ) -> dict[str, Any]:
        actor = require_actor(actor)
        validate_transport(transport)
        if self.get(intent_id)["status"] != "outcome_unknown":
            raise ValueError("recall_reconcile_requires_unknown")
        original = self.queue.get(intent_id)
        try:
            proof = transport.lookup(original["logical_key"], now=now)
            if proof is None:
                return self.get(intent_id)
            validate_proof(
                proof, original["payload"], key=original["logical_key"], now=now, withdrawn=True
            )
        except (ValueError, TypeError):
            return self.get(intent_id)
        if proof is not None:
            self._confirm(intent_id, proof, actor=actor, now=now)
        return self.get(intent_id)

    def run_once(
        self,
        transport: DeliveryTransport,
        *,
        now: datetime,
        dry_run: bool = True,
        worker_id: str = "recall-worker",
    ) -> dict[str, Any]:
        validate_transport(transport)
        worker_id = require_actor(worker_id)
        if dry_run:
            return {"status": "dry_run"}
        token = uuid4().hex
        with self.store.transaction() as connection:
            expired = connection.execute(
                "SELECT intent_id FROM recall_intents "
                "WHERE status='withdrawing' AND lease_until<=?",
                (iso(now),),
            ).fetchall()
            for old in expired:
                connection.execute(
                    "UPDATE recall_intents SET status='outcome_unknown',lease_token=NULL,"
                    "worker_id=NULL,lease_until=NULL WHERE intent_id=?",
                    (old["intent_id"],),
                )
                self.queue._event(
                    connection, old["intent_id"], "withdrawal_unknown", "system:lease", now
                )
            row = connection.execute(
                "SELECT r.intent_id FROM recall_intents r JOIN publish_intents p USING(intent_id) "
                "WHERE r.status='pending' AND r.attempts<3 AND NOT EXISTS ("
                "SELECT 1 FROM publish_pauses x WHERE x.paused=1 AND ("
                "(x.scope='global' AND x.scope_key='*') OR "
                "(x.scope='source' AND x.scope_key=p.source) OR "
                "(x.scope='channel' AND x.scope_key=p.channel))) "
                "ORDER BY r.created_at,r.intent_id LIMIT 1"
            ).fetchone()
            if row is None:
                return {"status": "idle"}
            intent_id = row["intent_id"]
            connection.execute(
                "UPDATE recall_intents SET status='withdrawing',attempts=attempts+1,"
                "lease_token=?,worker_id=?,lease_until=? WHERE intent_id=?",
                (token, worker_id, iso(utc(now) + timedelta(seconds=30)), intent_id),
            )
            self.queue._event(connection, intent_id, "withdrawal_started", worker_id, now)
        original = self.queue.get(intent_id)
        try:
            proof = transport.withdraw(original["logical_key"], now=now)
            validate_proof(
                proof, original["payload"], key=original["logical_key"], now=now, withdrawn=True
            )
        except Exception:
            with self.store.transaction() as connection:
                current = self.get(intent_id)
                if current["lease_token"] == token and current["status"] == "withdrawing":
                    connection.execute(
                        "UPDATE recall_intents SET status='outcome_unknown',"
                        "lease_token=NULL,worker_id=NULL,lease_until=NULL WHERE intent_id=?",
                        (intent_id,),
                    )
                    self.queue._event(connection, intent_id, "withdrawal_unknown", worker_id, now)
            return self.get(intent_id)
        with self.store.transaction():
            current = self.get(intent_id)
            owned = current["status"] == "withdrawing" and current["lease_token"] == token
        if owned:
            self._confirm(intent_id, proof, actor=worker_id, now=now, expected_token=token)
        return self.get(intent_id)
