"""Immutable container for an atomically read operator state; JSON remains copied."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CandidateSnapshot:
    revision: int
    candidate: dict[str, Any]
    approval: dict[str, Any] | None
