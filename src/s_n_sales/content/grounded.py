"""Optional AI composition over locked fact IDs, with no free numeric/link claims.

A model may only choose a known introduction and reorder every existing block.
It cannot add text, omit purchase conditions, change facts, or obtain publish tools.
"""

from __future__ import annotations

import threading
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Protocol

from s_n_sales.domain.json_value import digest

INTRODUCTIONS = {
    "neutral": "",
    "friendly": "Thông tin ưu đãi được ghi nhận:",
    "compact": "Thông tin ưu đãi:",
}


@dataclass(frozen=True)
class ModelSettings:
    provider: str = "disabled"
    model: str = "template"
    enabled: bool = False
    max_calls: int = 0
    max_output_tokens: int = 256
    max_input_bytes: int = 16384
    max_attempts: int = 1
    call_cost_ceiling_microunits: int = 0
    budget_microunits: int = 0
    prompt_version: str = "fact-order-v1"
    policy_version: str = "grounded-compose-v1"

    def __post_init__(self) -> None:
        for name in ("max_calls", "call_cost_ceiling_microunits", "budget_microunits"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError("model_budget_invalid")
        if (
            any(
                type(getattr(self, name)) is not int
                for name in ("max_attempts", "max_output_tokens", "max_input_bytes")
            )
            or not 1 <= self.max_attempts <= 3
            or not 1 <= self.max_output_tokens <= 1024
            or not 1 <= self.max_input_bytes <= 65536
        ):
            raise ValueError("model_limits_invalid")
        if (
            self.enabled
            and self.provider not in ("test", "disabled")
            and self.call_cost_ceiling_microunits <= 0
        ):
            raise ValueError("paid_provider_requires_call_cost_ceiling")


class CompositionModel(Protocol):
    def propose(self, request: dict[str, Any], *, max_output_tokens: int) -> dict[str, Any]: ...


@dataclass(frozen=True)
class Composition:
    blocks: dict[str, str]
    order: tuple[str, ...]
    style: str
    mode: str
    error_code: str | None
    model_id: str
    prompt_version: str

    @property
    def text(self) -> str:
        return "\n".join(
            part
            for part in [INTRODUCTIONS[self.style], *(self.blocks[key] for key in self.order)]
            if part
        )


class GroundedComposer:
    def __init__(
        self, settings: ModelSettings | None = None, *, model: CompositionModel | None = None
    ) -> None:
        self.settings = settings if settings is not None else ModelSettings()
        self.model = model
        self._lock = threading.Lock()
        self._cache: dict[str, dict[str, Any]] = {}
        self._calls = 0
        self._reserved_cost = 0

    @property
    def usage(self) -> dict[str, int]:
        with self._lock:
            return {"calls": self._calls, "reserved_cost_microunits": self._reserved_cost}

    def compose(self, blocks: dict[str, str]) -> Composition:
        if (
            not blocks
            or len(blocks) > 32
            or any(not isinstance(k, str) or not isinstance(v, str) for k, v in blocks.items())
        ):
            raise ValueError("fact_blocks_invalid")
        copied = dict(blocks)
        too_large_for_model = (
            sum(len(value.encode("utf-8")) for value in copied.values())
            > self.settings.max_input_bytes
        )
        key = digest(
            {
                "blocks": copied,
                "provider": self.settings.provider,
                "model": self.settings.model,
                "prompt": self.settings.prompt_version,
                "policy": self.settings.policy_version,
            }
        )
        result: dict[str, Any] | None = None
        error = None
        mode = "template"
        if self.settings.enabled and self.model is not None and not too_large_for_model:
            with self._lock:
                result = deepcopy(self._cache.get(key))
            if result is not None:
                mode = "model_cache"
            for _ in range(self.settings.max_attempts if result is None else 0):
                with self._lock:
                    projected_cost = (
                        self._reserved_cost + self.settings.call_cost_ceiling_microunits
                    )
                    if (
                        self._calls >= self.settings.max_calls
                        or projected_cost > self.settings.budget_microunits
                    ):
                        error = "model_budget_exhausted"
                        break
                    self._calls += 1
                    self._reserved_cost = projected_cost
                try:
                    # Only IDs are sent. Untrusted source strings are not instructions to the model.
                    proposal = self.model.propose(
                        {
                            "fact_ids": list(copied),
                            "styles": list(INTRODUCTIONS),
                            "language": "vi",
                            "prompt_version": self.settings.prompt_version,
                        },
                        max_output_tokens=self.settings.max_output_tokens,
                    )
                    if not isinstance(proposal, dict) or set(proposal) != {"style", "order"}:
                        raise ValueError("composition_schema_invalid")
                    order = proposal["order"]
                    if (
                        proposal["style"] not in INTRODUCTIONS
                        or not isinstance(order, list)
                        or any(not isinstance(item, str) for item in order)
                        or len(order) != len(copied)
                        or set(order) != set(copied)
                    ):
                        raise ValueError("composition_facts_changed")
                    result = deepcopy(proposal)
                    with self._lock:
                        if len(self._cache) >= 256:
                            self._cache.pop(next(iter(self._cache)))
                        self._cache[key] = deepcopy(result)
                    mode = "model"
                    break
                except Exception:
                    error = "composition_rejected"
            if result is None:
                mode = "template_fallback"
        elif self.settings.enabled:
            mode = "template_fallback"
            error = "model_input_limit" if too_large_for_model else "model_unavailable"
        if result is None:
            result = {"style": "neutral", "order": list(copied)}
        return Composition(
            copied,
            tuple(result["order"]),
            result["style"],
            mode,
            error,
            f"{self.settings.provider}:{self.settings.model}",
            self.settings.prompt_version,
        )
