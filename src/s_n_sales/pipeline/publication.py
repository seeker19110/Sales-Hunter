"""Build publication candidates deterministically without external side effects."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker

DISCLOSURE_TEMPLATE = (
    "#affiliate — Bài viết có thể chứa liên kết tiếp thị liên kết. "
    "Giá và tồn kho được quan sát tại thời điểm ghi nhận, có thể đã thay đổi."
)


class PublicationValidationError(ValueError):
    """Publication candidate không đạt invariant hoặc JSON Schema."""


@lru_cache(maxsize=1)
def _publication_validator() -> Draft202012Validator:
    root = Path(__file__).resolve().parents[3]
    schema = json.loads(
        (root / "schemas" / "publication-candidate.v1.json").read_text(encoding="utf-8")
    )
    return Draft202012Validator(schema, format_checker=FormatChecker())


def compute_draft_sha256(
    *,
    content: str,
    affiliate_url: str,
    affiliate_disclosure: str,
    claim_snapshot: dict[str, Any],
    target_channel: str,
    observation_id: str,
) -> str:
    """Return SHA-256 over the canonical, claim-bound draft payload."""
    canonical_object = {
        "content": content,
        "affiliate_url": affiliate_url,
        "affiliate_disclosure": affiliate_disclosure,
        "claim_snapshot": claim_snapshot,
        "target_channel": target_channel,
        "observation_id": observation_id,
    }
    canonical_json = json.dumps(
        canonical_object, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def build_publication_candidate(
    observation: dict[str, Any],
    rank_result: dict[str, Any],
    *,
    content: str,
    affiliate_url: str,
    target_channel: str,
    disclosure: str | None = None,
    publication_id: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Build and validate a pending publication candidate from validated pipeline data."""
    if not isinstance(content, str) or not content.strip():
        raise PublicationValidationError("content không được rỗng")
    if not isinstance(target_channel, str) or not target_channel.strip():
        raise PublicationValidationError("target_channel không được rỗng")
    parsed_url = urlparse(affiliate_url) if isinstance(affiliate_url, str) else None
    if parsed_url is None or parsed_url.scheme != "https" or not parsed_url.netloc:
        raise PublicationValidationError("affiliate_url phải là HTTPS URL hợp lệ")

    observation_id = observation.get("observation_id")
    if not isinstance(observation_id, str) or not observation_id:
        raise PublicationValidationError("observation_id không hợp lệ")
    if rank_result.get("observation_id") != observation_id:
        raise PublicationValidationError("rank_result không thuộc observation")

    evidence = observation.get("evidence")
    if not isinstance(evidence, dict):
        raise PublicationValidationError("observation.evidence không hợp lệ")

    claim_snapshot: dict[str, Any] = {
        "platform": observation.get("platform"),
        "observed_at": observation.get("observed_at"),
        "currency": observation.get("currency"),
        "sale_price_minor": observation.get("sale_price_minor"),
        "source_url": evidence.get("source_url"),
    }
    if "list_price_minor" in observation:
        claim_snapshot["list_price_minor"] = observation["list_price_minor"]

    affiliate_disclosure = disclosure.strip() if isinstance(disclosure, str) else ""
    if not affiliate_disclosure:
        affiliate_disclosure = DISCLOSURE_TEMPLATE

    draft_sha256 = compute_draft_sha256(
        content=content,
        affiliate_url=affiliate_url,
        affiliate_disclosure=affiliate_disclosure,
        claim_snapshot=claim_snapshot,
        target_channel=target_channel,
        observation_id=observation_id,
    )
    candidate = {
        "schema_version": "publication-candidate.v1",
        "publication_id": publication_id or f"pub-{observation_id}-{draft_sha256[:12]}",
        "observation_id": observation_id,
        "target_channel": target_channel,
        "content": content,
        "affiliate_url": affiliate_url,
        "affiliate_disclosure": affiliate_disclosure,
        "claim_snapshot": claim_snapshot,
        "draft_sha256": draft_sha256,
        "approval": {"status": "pending", "draft_sha256": draft_sha256},
        "idempotency_key": idempotency_key
        or f"{observation_id}:{target_channel}:{draft_sha256}",
    }

    errors = sorted(
        _publication_validator().iter_errors(candidate), key=lambda error: list(error.path)
    )
    if errors:
        raise PublicationValidationError(
            f"publication candidate không khớp schema: {errors[0].message}"
        )
    if candidate["approval"]["draft_sha256"] != candidate["draft_sha256"]:
        raise PublicationValidationError("approval.draft_sha256 không khớp draft_sha256")
    return candidate
