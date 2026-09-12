"""In-memory store for operator staging — không persistence, không mạng ngoài."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from s_n_sales.pipeline.approval import decide_approval


class OperatorStore:
    def __init__(self) -> None:
        self._candidates: dict[str, dict[str, Any]] = {}
        self._approvals: dict[str, dict[str, Any]] = {}

    def upsert_candidate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        pub_id = candidate.get("publication_id")
        if not isinstance(pub_id, str) or not pub_id:
            raise ValueError("publication_id bắt buộc")
        self._candidates[pub_id] = deepcopy(candidate)
        return deepcopy(candidate)

    def list_candidates(self) -> list[dict[str, Any]]:
        return [deepcopy(c) for c in self._candidates.values()]

    def get_candidate(self, publication_id: str) -> dict[str, Any] | None:
        c = self._candidates.get(publication_id)
        return deepcopy(c) if c is not None else None

    def approve(
        self,
        publication_id: str,
        *,
        decided_by: str,
        reason: str | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        candidate = self.get_candidate(publication_id)
        if candidate is None:
            raise KeyError(publication_id)
        clock = now if now is not None else datetime.now(UTC)
        record = decide_approval(
            candidate,
            status="approved",
            decided_by=decided_by,
            decided_at=clock,
            reason=reason,
        )
        self._approvals[publication_id] = record
        return deepcopy(record)

    def reject(
        self,
        publication_id: str,
        *,
        decided_by: str,
        reason: str | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        candidate = self.get_candidate(publication_id)
        if candidate is None:
            raise KeyError(publication_id)
        clock = now if now is not None else datetime.now(UTC)
        record = decide_approval(
            candidate,
            status="rejected",
            decided_by=decided_by,
            decided_at=clock,
            reason=reason,
        )
        self._approvals[publication_id] = record
        return deepcopy(record)

    def get_approval(self, publication_id: str) -> dict[str, Any] | None:
        a = self._approvals.get(publication_id)
        return deepcopy(a) if a is not None else None
