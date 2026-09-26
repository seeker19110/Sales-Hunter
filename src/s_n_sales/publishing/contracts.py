"""Explicit failure classes and strict, payload-bound delivery evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from s_n_sales.domain.json_value import utc


class RetryableNotSent(ValueError):
    """The transport positively knows the provider did not accept this attempt."""


class TerminalNotSent(ValueError):
    """The provider positively rejected the attempt without accepting it."""


class LeaseLost(ValueError):
    """A stale worker must not change the current intent."""


class Paused(ValueError):
    """A persistent operator pause blocks claiming or sending."""


class DuplicateBusinessDeal(ValueError):
    """An active, unknown or recently confirmed deal already covers this business key."""


@dataclass(frozen=True)
class Lease:
    intent_id: str
    token: str
    worker_id: str


@dataclass(frozen=True)
class QueuePolicy:
    max_attempts: int = 3
    lease_seconds: int = 30
    backoff_seconds: int = 5
    cooldown_seconds: int = 3600

    def __post_init__(self) -> None:
        limits = {
            "max_attempts": (1, 10),
            "lease_seconds": (5, 300),
            "backoff_seconds": (1, 300),
            "cooldown_seconds": (1, 86400),
        }
        for name, (minimum, maximum) in limits.items():
            value = getattr(self, name)
            if type(value) is not int or not minimum <= value <= maximum:
                raise ValueError("queue_policy_invalid")


class DeliveryTransport(Protocol):
    proof_kind: str
    capability_version: str
    definitive_absence: bool

    def publish(
        self, payload: dict[str, Any], *, idempotency_key: str, now: datetime
    ) -> dict[str, Any]: ...
    def lookup(self, idempotency_key: str, *, now: datetime) -> dict[str, Any] | None: ...
    def withdraw(self, idempotency_key: str, *, now: datetime) -> dict[str, Any]: ...


def validate_transport(transport: DeliveryTransport) -> None:
    # This release intentionally has no enabled live provider implementation.
    if transport.proof_kind != "fake" or transport.capability_version != "local-simulator-v1":
        raise ValueError("live_transport_capability_not_verified")


def validate_proof(
    proof: dict[str, Any],
    payload: dict[str, Any],
    *,
    key: str,
    now: datetime,
    withdrawn: bool = False,
) -> None:
    required = {
        "schema_version",
        "proof_kind",
        "idempotency_key",
        "platform_post_id",
        "platform_post_url",
        "target_channel",
        "payload_sha256",
        "text",
        "published_at",
        "read_back_at",
        "withdrawn",
    }
    if not isinstance(proof, dict) or set(proof) != required:
        raise ValueError("delivery_proof_contract_invalid")
    if any(not isinstance(proof[name], str) for name in required - {"withdrawn"}):
        raise ValueError("delivery_proof_types_invalid")
    if (
        proof["schema_version"] != "delivery-proof.v1"
        or proof["proof_kind"] != "fake"
        or proof["idempotency_key"] != key
        or proof["target_channel"] != payload["target_channel"]
        or proof["payload_sha256"] != payload["payload_sha256"]
        or proof["text"] != payload["text"]
        or proof["withdrawn"] is not withdrawn
        or not re.fullmatch(r"fake-[0-9a-f]{32}", proof["platform_post_id"])
        or proof["platform_post_url"] != "https://example.com/posts/" + proof["platform_post_id"]
    ):
        raise ValueError("delivery_proof_mismatch")
    published, read_back, clock = utc(proof["published_at"]), utc(proof["read_back_at"]), utc(now)
    if published > read_back or read_back > clock:
        raise ValueError("delivery_proof_clock_invalid")
