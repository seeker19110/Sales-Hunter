"""Approval records bound to draft_sha256 — no network side effects."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from functools import lru_cache
from importlib.resources import files
from typing import Any
from uuid import uuid4

from jsonschema import Draft202012Validator, FormatChecker

from s_n_sales.pipeline.publication import PublicationBuildError, assert_candidate_integrity


class ApprovalError(ValueError):
    """Approval không hợp lệ hoặc không còn khớp draft."""


@lru_cache(maxsize=1)
def _approval_validator() -> Draft202012Validator:
    resource = files("s_n_sales").joinpath("schemas", "approval-record.v1.json")
    schema = json.loads(resource.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def decide_approval(
    publication_candidate: dict[str, Any],
    *,
    status: str,
    decided_by: str,
    decided_at: datetime,
    reason: str | None = None,
    policy_version: str | None = None,
    approval_id: str | None = None,
) -> dict[str, Any]:
    """Tạo approval-record.v1 gắn đúng draft_sha256 của candidate hiện tại."""
    publication_candidate = deepcopy(publication_candidate)
    try:
        assert_candidate_integrity(publication_candidate)
    except PublicationBuildError as exc:
        raise ApprovalError(str(exc)) from exc
    if status not in ("approved", "rejected"):
        raise ApprovalError("status phải là approved hoặc rejected")
    if not isinstance(decided_by, str) or not decided_by.strip():
        raise ApprovalError("decided_by bắt buộc")
    if decided_at.tzinfo is None or decided_at.utcoffset() is None:
        raise ApprovalError("decided_at phải có timezone")

    draft_sha256 = publication_candidate.get("draft_sha256")
    publication_id = publication_candidate.get("publication_id")
    if not isinstance(draft_sha256, str) or len(draft_sha256) != 64:
        raise ApprovalError("publication_candidate.draft_sha256 không hợp lệ")
    if not isinstance(publication_id, str) or not publication_id:
        raise ApprovalError("publication_candidate.publication_id bắt buộc")

    decided_at_utc = decided_at.astimezone(UTC)
    record: dict[str, Any] = {
        "schema_version": "approval-record.v1",
        "approval_id": approval_id or f"apr-{uuid4().hex[:16]}",
        "publication_id": publication_id,
        "draft_sha256": draft_sha256,
        "status": status,
        "decided_by": decided_by.strip(),
        "decided_at": decided_at_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reason": reason,
        "policy_version": policy_version,
    }

    errors = sorted(_approval_validator().iter_errors(record), key=lambda e: list(e.path))
    if errors:
        raise ApprovalError(f"approval-record không khớp schema: {errors[0].message}")
    return record


def assert_approval_matches_draft(
    approval: dict[str, Any],
    publication_candidate: dict[str, Any],
) -> None:
    """Sửa draft → approval cũ vô hiệu."""
    try:
        assert_candidate_integrity(publication_candidate)
    except PublicationBuildError as exc:
        raise ApprovalError(str(exc)) from exc
    if not _approval_validator().is_valid(approval):
        raise ApprovalError("approval-record does not match the complete contract")
    if not approval["decided_by"].strip():
        raise ApprovalError("approval actor must not be blank")
    if approval.get("status") != "approved":
        raise ApprovalError("chỉ bản approved mới được dùng để publish")
    if approval.get("publication_id") != publication_candidate.get("publication_id"):
        raise ApprovalError("approval.publication_id không khớp candidate")
    if approval.get("draft_sha256") != publication_candidate.get("draft_sha256"):
        raise ApprovalError("approval.draft_sha256 không khớp draft hiện tại (draft đã đổi)")
