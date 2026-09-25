"""One durable publication iteration, dry-run by default, no background promise."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from s_n_sales.publishing.contracts import (
    DeliveryTransport,
    LeaseLost,
    Paused,
    RetryableNotSent,
    TerminalNotSent,
    validate_proof,
    validate_transport,
)
from s_n_sales.publishing.queue import PublicationQueue


class PublicationWorker:
    def __init__(
        self,
        queue: PublicationQueue,
        transport: DeliveryTransport,
        *,
        dry_run: bool = True,
        worker_id: str | None = None,
    ) -> None:
        validate_transport(transport)
        self.queue, self.transport, self.dry_run = queue, transport, dry_run
        self.worker_id = worker_id or "worker-" + uuid4().hex

    def run_once(self, *, now: datetime) -> dict[str, Any]:
        self.queue.heartbeat(self.worker_id, now=now, dry_run=self.dry_run)
        if self.dry_run:
            return {"status": "dry_run", "transport_called": False}
        claim = self.queue.claim(worker_id=self.worker_id, now=now)
        if claim is None:
            return {"status": "idle"}
        try:
            intent = self.queue.start_send(claim, now=now)
        except Paused:
            return {"status": "paused", "intent_id": claim.intent_id}
        except LeaseLost:
            return {"status": "lease_lost", "intent_id": claim.intent_id}
        except ValueError:
            return self.queue.get(claim.intent_id)
        try:
            proof = self.transport.publish(
                intent["payload"], idempotency_key=intent["logical_key"], now=now
            )
            validate_proof(proof, intent["payload"], key=intent["logical_key"], now=now)
        except RetryableNotSent:
            return self.queue.failed(claim, retryable_not_sent=True, now=now)
        except TerminalNotSent:
            return self.queue.failed(
                claim, retryable_not_sent=False, terminal_not_sent=True, now=now
            )
        except Exception:
            return self.queue.failed(claim, retryable_not_sent=False, now=now)
        # A DB failure after acceptance must remain SENDING until recovery -> UNKNOWN.
        # Do not classify it as a provider rejection or automatically resend.
        return self.queue.confirmed(claim, proof, now=now)
