"""Publication candidate builder — draft only, no network side effects."""

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


class PublicationBuildError(ValueError):
    """Publication candidate không thỏa schema hoặc invariant domain."""


def compute_draft_sha256(
    *,
    content: str,
    affiliate_url: str,
    affiliate_disclosure: str,
    claim_snapshot: dict[str, Any],
    target_channel: str,
    observation_id: str,
) -> str:
    """SHA-256 hex của canonical JSON (sort_keys, separators cố định, UTF-8)."""
    canonical_object = {
        "affiliate_disclosure": affiliate_disclosure,
        "affiliate_url": affiliate_url,
        "claim_snapshot": claim_snapshot,
        "content": content,
        "observation_id": observation_id,
        "target_channel": target_channel,
    }
    canonical_json = json.dumps(
        canonical_object,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def _publication_validator() -> Draft202012Validator:
    root = Path(__file__).resolve().parents[3]
    schema_path = root / "schemas" / "publication-candidate.v1.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _claim_snapshot_from_observation(observation: dict[str, Any]) -> dict[str, Any]:
    evidence = observation.get("evidence")
    if not isinstance(evidence, dict):
        raise PublicationBuildError("observation.evidence phải là object")
    source_url = evidence.get("source_url")
    if not isinstance(source_url, str) or not source_url:
        raise PublicationBuildError("evidence.source_url bắt buộc")

    snapshot: dict[str, Any] = {
        "platform": observation["platform"],
        "observed_at": observation["observed_at"],
        "currency": observation["currency"],
        "sale_price_minor": observation["sale_price_minor"],
        "source_url": source_url,
    }
    if "list_price_minor" in observation:
        snapshot["list_price_minor"] = observation["list_price_minor"]
    return snapshot


def _require_https(url: str, *, field: str) -> None:
    if urlparse(url).scheme != "https":
        raise PublicationBuildError(f"{field} phải dùng HTTPS")


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
    """Tạo publication-candidate.v1 từ observation + rank (draft-only)."""
    del rank_result  # reserved for future metadata; schema v1 không bắt buộc score

    if not isinstance(content, str) or not content.strip():
        raise PublicationBuildError("content không được rỗng")
    if not isinstance(affiliate_url, str) or not affiliate_url:
        raise PublicationBuildError("affiliate_url bắt buộc")
    if not isinstance(target_channel, str) or not target_channel.strip():
        raise PublicationBuildError("target_channel không được rỗng")

    observation_id = observation.get("observation_id")
    if not isinstance(observation_id, str) or not observation_id:
        raise PublicationBuildError("observation_id bắt buộc")

    _require_https(affiliate_url, field="affiliate_url")

    resolved_disclosure = disclosure.strip() if isinstance(disclosure, str) else ""
    if not resolved_disclosure:
        resolved_disclosure = DISCLOSURE_TEMPLATE

    claim_snapshot = _claim_snapshot_from_observation(observation)
    draft_sha256 = compute_draft_sha256(
        content=content,
        affiliate_url=affiliate_url,
        affiliate_disclosure=resolved_disclosure,
        claim_snapshot=claim_snapshot,
        target_channel=target_channel,
        observation_id=observation_id,
    )

    if publication_id is None:
        publication_id = f"pub-{observation_id}-{draft_sha256[:12]}"
    if idempotency_key is None:
        idempotency_key = f"{observation_id}:{target_channel}:{draft_sha256}"

    candidate: dict[str, Any] = {
        "schema_version": "publication-candidate.v1",
        "publication_id": publication_id,
        "observation_id": observation_id,
        "target_channel": target_channel,
        "content": content,
        "affiliate_url": affiliate_url,
        "affiliate_disclosure": resolved_disclosure,
        "claim_snapshot": claim_snapshot,
        "draft_sha256": draft_sha256,
        "approval": {
            "status": "pending",
            "draft_sha256": draft_sha256,
        },
        "idempotency_key": idempotency_key,
    }

    errors = sorted(
        _publication_validator().iter_errors(candidate),
        key=lambda error: list(error.path),
    )
    if errors:
        raise PublicationBuildError(f"publication-candidate không khớp schema: {errors[0].message}")

    return candidate
