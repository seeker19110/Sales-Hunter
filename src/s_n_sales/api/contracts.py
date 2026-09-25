"""Stable input errors and v1 projection validation, shared by both stores."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from s_n_sales.pipeline.approval import ApprovalError, _approval_validator
from s_n_sales.pipeline.publication import _publication_validator, assert_candidate_integrity


class RevisionRequired(ApprovalError):
    """A mutation must identify the operator state that was actually viewed."""


class RevisionConflict(ApprovalError):
    """The viewed state has changed; reload rather than silently overwrite."""


class StoreIntegrityError(ApprovalError):
    """Persisted projections, hashes, or schema are inconsistent."""


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def timestamp(now: datetime | None = None) -> str:
    clock = now if now is not None else datetime.now(UTC)
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise ValueError("timezone_required")
    return clock.astimezone(UTC).isoformat().replace("+00:00", "Z")


def require_actor(actor: str) -> str:
    if not isinstance(actor, str) or not actor.strip() or len(actor) > 300:
        raise ValueError("actor_required")
    return actor.strip()


def require_revision(expected: int | None, actual: int) -> None:
    if type(expected) is not int or expected < 1:
        raise RevisionRequired("expected_revision_required")
    if expected != actual:
        raise RevisionConflict("revision_conflict")


def approval_projection(approval: dict[str, Any]) -> dict[str, Any]:
    fields = ("status", "draft_sha256", "decided_by", "decided_at", "reason")
    return {name: deepcopy(approval[name]) for name in fields if name in approval}


def candidate_from_json(payload: str) -> dict[str, Any]:
    candidate: dict[str, Any] = json.loads(payload)
    if isinstance(candidate.get("approval"), dict):
        candidate["approval"] = approval_projection(candidate["approval"])
    return candidate


def validate_candidate(candidate: dict[str, Any]) -> None:
    if not _publication_validator().is_valid(candidate):
        raise ValueError("candidate_contract_invalid")
    assert_candidate_integrity(candidate)
    claim = candidate["claim_snapshot"]
    for field in ("sale_price_minor", "list_price_minor"):
        value = claim.get(field)
        if value is not None and type(value) is not int:
            raise ValueError("money_must_be_integer")
    if candidate["approval"]["draft_sha256"] != candidate["draft_sha256"]:
        raise ValueError("candidate_approval_hash_mismatch")
    listed = claim.get("list_price_minor")
    if listed is not None and claim["sale_price_minor"] > listed:
        raise ValueError("sale_above_list")


def validate_approval_record(record: dict[str, Any], candidate: dict[str, Any]) -> None:
    if not _approval_validator().is_valid(record) or not record["decided_by"].strip():
        raise StoreIntegrityError("stored_approval_contract_invalid")
    if any(record[field] != candidate[field] for field in ("publication_id", "draft_sha256")):
        raise StoreIntegrityError("stored_approval_mismatch")
    if record["status"] != candidate["approval"]["status"]:
        raise StoreIntegrityError("stored_approval_status_mismatch")
    if approval_projection(record) != candidate["approval"]:
        raise StoreIntegrityError("stored_approval_projection_mismatch")


def pending_import(candidate: dict[str, Any]) -> dict[str, Any]:
    copied = deepcopy(candidate)
    validate_candidate(copied)
    approval = copied["approval"]
    if approval != {"status": "pending", "draft_sha256": copied["draft_sha256"]}:
        raise ValueError("import_must_be_pending_without_authority")
    return copied


def draft_fields(candidate: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in candidate.items() if key != "approval"}
