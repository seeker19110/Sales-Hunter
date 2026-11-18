"""Separate durable simulated-provider database. No network or real publication."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from s_n_sales.domain.json_value import canonical, iso
from s_n_sales.publishing.contracts import RetryableNotSent


class SimulatedCrash(BaseException):
    """A process death after provider acceptance, intentionally not an Exception."""


class FakeTransport:
    proof_kind = "fake"
    capability_version = "local-simulator-v1"
    definitive_absence = True

    def __init__(self, path: str | Path) -> None:
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self.faults: list[str] = []
        with self._conn:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS remote_posts "
                "(idempotency_key TEXT PRIMARY KEY, proof_json TEXT NOT NULL)"
            )
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS remote_calls "
                "(call_id TEXT PRIMARY KEY, idempotency_key TEXT NOT NULL)"
            )

    def publish(
        self, payload: dict[str, Any], *, idempotency_key: str, now: datetime
    ) -> dict[str, Any]:
        with self._lock:
            fault = self.faults.pop(0) if self.faults else None
            with self._conn:
                self._conn.execute(
                    "INSERT INTO remote_calls VALUES (?,?)", (uuid4().hex, idempotency_key)
                )
            if fault == "before_send":
                raise RetryableNotSent("simulated_not_accepted")
            row = self._conn.execute(
                "SELECT proof_json FROM remote_posts WHERE idempotency_key=?", (idempotency_key,)
            ).fetchone()
            if row:
                proof = json.loads(row["proof_json"])
            else:
                identifier = "fake-" + uuid4().hex
                proof = {
                    "schema_version": "delivery-proof.v1",
                    "proof_kind": "fake",
                    "idempotency_key": idempotency_key,
                    "platform_post_id": identifier,
                    "platform_post_url": "https://example.com/posts/" + identifier,
                    "target_channel": payload["target_channel"],
                    "payload_sha256": payload["payload_sha256"],
                    "text": payload["text"],
                    "published_at": iso(now),
                    "read_back_at": iso(now),
                    "withdrawn": False,
                }
                with self._conn:
                    self._conn.execute(
                        "INSERT INTO remote_posts VALUES (?,?)", (idempotency_key, canonical(proof))
                    )
            if fault == "crash_after_accept":
                raise SimulatedCrash("simulated_process_death_after_accept")
            if fault == "after_accept_timeout":
                raise TimeoutError("simulated_ambiguous_network_timeout")
            if fault == "bad_readback":
                return {**proof, "text": "different remote text"}
            return {**proof, "read_back_at": iso(now)}

    def lookup(self, idempotency_key: str, *, now: datetime) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT proof_json FROM remote_posts WHERE idempotency_key=?", (idempotency_key,)
            ).fetchone()
        return {**json.loads(row["proof_json"]), "read_back_at": iso(now)} if row else None

    def withdraw(self, idempotency_key: str, *, now: datetime) -> dict[str, Any]:
        with self._lock, self._conn:
            row = self._conn.execute(
                "SELECT proof_json FROM remote_posts WHERE idempotency_key=?", (idempotency_key,)
            ).fetchone()
            if row is None:
                raise ValueError("unknown_provider_identifier")
            proof = {**json.loads(row["proof_json"]), "read_back_at": iso(now), "withdrawn": True}
            self._conn.execute(
                "UPDATE remote_posts SET proof_json=? WHERE idempotency_key=?",
                (canonical(proof), idempotency_key),
            )
        return proof

    def call_count(self) -> int:
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) FROM remote_calls").fetchone()[0]

    def post_count(self) -> int:
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) FROM remote_posts").fetchone()[0]

    def close(self) -> None:
        with self._lock:
            self._conn.close()
