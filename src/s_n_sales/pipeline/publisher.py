"""Publisher — dry-run mặc định, idempotent theo idempotency_key.

Không gọi mạng thật trong Phase 3 skeleton. Receipt chỉ được tạo khi
chế độ dry_run=False *và* có read-back (FakePlatformClient trong test).
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import lru_cache
from importlib.resources import files
from typing import Any, Protocol
from uuid import uuid4

from jsonschema import Draft202012Validator, FormatChecker

from s_n_sales.domain.publication_state import CandidateSnapshot
from s_n_sales.pipeline.approval import ApprovalError, assert_approval_matches_draft


class PublishError(ValueError):
    """Không publish được."""


class PlatformClient(Protocol):
    def publish_and_read_back(
        self,
        *,
        content: str,
        target_channel: str,
        idempotency_key: str,
        now: datetime,
    ) -> dict[str, str]:
        """Trả platform_post_id, platform_post_url, published_at (ISO)."""
        ...


class ApprovalSource(Protocol):
    """Server-configured authority; never constructed from a publish request."""

    def get_snapshot(self, publication_id: str) -> CandidateSnapshot | None: ...


@dataclass
class FakePlatformClient:
    """Read-back giả lập cho test — không mạng."""

    posts: dict[str, dict[str, str]] = field(default_factory=dict)

    def publish_and_read_back(
        self,
        *,
        content: str,
        target_channel: str,
        idempotency_key: str,
        now: datetime,
    ) -> dict[str, str]:
        if idempotency_key in self.posts:
            return self.posts[idempotency_key]
        post_id = f"fake-post-{uuid4().hex[:12]}"
        url = f"https://example.com/posts/{post_id}"
        published_at = now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = {
            "platform_post_id": post_id,
            "platform_post_url": url,
            "published_at": published_at,
        }
        self.posts[idempotency_key] = payload
        return payload


@lru_cache(maxsize=1)
def _receipt_validator() -> Draft202012Validator:
    resource = files("s_n_sales").joinpath("schemas", "publish-receipt.v1.json")
    schema = json.loads(resource.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


@dataclass
class Publisher:
    """Idempotent publisher. dry_run=True mặc định — không gọi client."""

    client: PlatformClient | None = None
    dry_run: bool = True
    approval_source: ApprovalSource | None = None
    _receipts_by_key: dict[str, dict[str, Any]] = field(default_factory=dict)

    def preflight_approval(self, candidate: dict[str, Any], approval: dict[str, Any]) -> None:
        """Recheck the current authority even on retries and cached receipts."""
        assert_approval_matches_draft(approval, candidate)
        if self.dry_run:
            return  # No client call or delivery success is possible in dry-run mode.
        if self.approval_source is None:
            raise ApprovalError("a trusted approval_source is required before publish")
        snapshot = self.approval_source.get_snapshot(candidate["publication_id"])
        if snapshot is None or snapshot.approval is None:
            raise ApprovalError("no current approval in the trusted source")
        current = deepcopy(snapshot.approval)
        assert_approval_matches_draft(current, candidate)
        assert_approval_matches_draft(current, snapshot.candidate)
        if current != approval:
            raise ApprovalError("supplied approval is not the current trusted approval")

    def publish(
        self,
        publication_candidate: dict[str, Any],
        approval: dict[str, Any],
        *,
        now: datetime,
        system_kill_switch: bool = False,
        channel_kill_switch: bool = False,
    ) -> dict[str, Any]:
        if system_kill_switch:
            raise PublishError("system kill switch đang bật")
        if channel_kill_switch:
            raise PublishError("channel kill switch đang bật")
        if now.tzinfo is None or now.utcoffset() is None:
            raise PublishError("now phải có timezone")

        now = now.astimezone(UTC)
        publication_candidate = deepcopy(publication_candidate)
        approval = deepcopy(approval)
        self.preflight_approval(publication_candidate, approval)

        idempotency_key = publication_candidate.get("idempotency_key")
        if not isinstance(idempotency_key, str) or not idempotency_key:
            raise PublishError("idempotency_key bắt buộc")

        if idempotency_key in self._receipts_by_key:
            return self._receipts_by_key[idempotency_key]

        if self.dry_run:
            raise PublishError(
                "dry_run=True: không publish thật. Tắt dry_run và cung cấp PlatformClient."
            )

        if self.client is None:
            raise PublishError("thiếu PlatformClient khi dry_run=False")

        content = publication_candidate["content"]
        target_channel = publication_candidate["target_channel"]
        read = self.client.publish_and_read_back(
            content=content,
            target_channel=target_channel,
            idempotency_key=idempotency_key,
            now=now,
        )
        read_back_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        receipt: dict[str, Any] = {
            "schema_version": "publish-receipt.v1",
            "receipt_id": f"rcpt-{uuid4().hex[:16]}",
            "publication_id": publication_candidate["publication_id"],
            "idempotency_key": idempotency_key,
            "target_channel": target_channel,
            "platform_post_id": read["platform_post_id"],
            "platform_post_url": read["platform_post_url"],
            "published_at": read["published_at"],
            "read_back_at": read_back_at,
            "status": "published",
            "error_code": None,
            "error_message": None,
        }
        errors = sorted(_receipt_validator().iter_errors(receipt), key=lambda e: list(e.path))
        if errors:
            raise PublishError(f"receipt không khớp schema: {errors[0].message}")

        self._receipts_by_key[idempotency_key] = receipt
        return receipt
