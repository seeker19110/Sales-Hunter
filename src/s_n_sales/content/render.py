"""Final, channel-scoped payloads built from verified fact blocks, never LLM numbers."""

from __future__ import annotations

import json
import re
from datetime import datetime
from functools import lru_cache
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from s_n_sales.content.grounded import INTRODUCTIONS, GroundedComposer
from s_n_sales.domain.json_value import digest
from s_n_sales.evidence.vault import EvidenceVault
from s_n_sales.pipeline.publication import (
    DISCLOSURE_TEMPLATE,
    assert_candidate_integrity,
    build_publication_candidate,
)
from s_n_sales.quality.facts import eligible_rank, validate_facts
from s_n_sales.quality.urls import UrlPolicy

RENDERER_VERSION = "grounded-text-v1"
CAPABILITY_VERSION = "manual-text-v1"


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    resource = files("s_n_sales").joinpath("schemas", "publication-payload.v1.json")
    return Draft202012Validator(
        json.loads(resource.read_text(encoding="utf-8")), format_checker=FormatChecker()
    )


def _money(value: int | None) -> str:
    return "chưa xác minh" if value is None else f"{value:,}".replace(",", ".") + " VND"


def fact_blocks(facts: dict[str, Any], affiliate_url: str) -> dict[str, str]:
    validate_facts(facts)
    obs = facts["observation"]
    conditional = facts["sale_price_scope"] == "conditional"
    variant_label = obs.get("variant_id") or "một biến thể đã được operator xác nhận"
    price_label = "Giá bán theo điều kiện" if conditional else "Giá bán ghi nhận"
    blocks = {
        "title": "Tên sản phẩm theo nguồn: " + obs["title"],
        "identity": (
            f"Nền tảng: {obs['platform']}; shop: {obs['merchant_id']}; "
            f"sản phẩm: {obs['item_id']}; biến thể: {variant_label}."
        ),
        "sale": f"{price_label}: {_money(obs['sale_price_minor'])}.",
        "list": "Giá niêm yết theo nguồn: " + _money(obs["list_price_minor"]) + ".",
        "shipping": "Phí vận chuyển: " + _money(obs["shipping_price_minor"]) + ".",
        "conditions": "Điều kiện mua: "
        + (obs["eligibility"]["notes"] or "Nguồn ghi áp dụng cho mọi người dùng.")
        + "; phạm vi: "
        + obs["eligibility"]["scope"]
        + ".",
        "coupons": "Mã giảm giá theo nguồn: "
        + (", ".join(obs["coupon_codes"]) or "không ghi nhận")
        + ". Không tự trừ mã vào giá bán.",
        "total": "Giá cuối: chưa xác minh; không tự cộng/trừ coupon hoặc suy ra tổng thanh toán.",
        "freshness": (
            f"Quan sát lúc {obs['observed_at']}; "
            f"tồn kho theo nguồn: {obs['stock_status']}. "
            f"Hết hạn theo nguồn: {facts['valid_until'] or 'chưa xác minh'}. "
            "Giá và tồn kho có thể thay đổi."
        ),
        "facts": "Mã dữ kiện: " + facts["facts_id"],
        "evidence": (
            f"Nguồn chứng cứ: {obs['evidence']['source_url']}; mã chứng cứ: {facts['evidence_id']}."
        ),
        "affiliate": "Link tiếp thị liên kết: " + affiliate_url,
        "disclosure": DISCLOSURE_TEMPLATE,
    }
    if facts["verified_total"] is not None:
        blocks["total"] = (
            "Tổng giá có chứng cứ cho đúng điều kiện trên: "
            + _money(facts["verified_total"]["amount_minor"])
            + "."
        )
    return blocks


def _capability(channel: str) -> None:
    if not isinstance(channel, str) or (
        channel != "manual_export" and not re.fullmatch(r"fake:[A-Za-z0-9_.-]{1,80}", channel)
    ):
        raise ValueError("channel_capability_not_verified")


def render_candidate(
    facts: dict[str, Any],
    *,
    vault: EvidenceVault,
    url_policy: UrlPolicy,
    affiliate_url: str,
    target_channel: str,
    now: datetime,
    composer: GroundedComposer | None = None,
    publication_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _capability(target_channel)
    url_policy.validate(affiliate_url)
    ranking = eligible_rank(facts, vault=vault, url_policy=url_policy, now=now)
    composition = (composer or GroundedComposer()).compose(fact_blocks(facts, affiliate_url))
    candidate = build_publication_candidate(
        facts["observation"],
        ranking,
        content=composition.text,
        affiliate_url=affiliate_url,
        target_channel=target_channel,
        publication_id=publication_id
        or "pub-"
        + digest(
            {
                "facts_id": facts["facts_id"],
                "target_channel": target_channel,
                "content": composition.text,
            }
        )[:48],
    )
    payload: dict[str, Any] = {
        "schema_version": "publication-payload.v1",
        "facts_id": facts["facts_id"],
        "target_channel": target_channel,
        "draft_sha256": candidate["draft_sha256"],
        "renderer_version": RENDERER_VERSION,
        "capability_version": CAPABILITY_VERSION,
        "text": composition.text,
        "composition": {"style": composition.style, "order": list(composition.order)},
        "content_mode": composition.mode,
        "model_id": composition.model_id,
        "prompt_version": composition.prompt_version,
    }
    payload["payload_sha256"] = digest(payload)
    validate_payload(payload, candidate, facts, url_policy=url_policy)
    return candidate, payload


def validate_payload(
    payload: dict[str, Any],
    candidate: dict[str, Any],
    facts: dict[str, Any],
    *,
    url_policy: UrlPolicy,
) -> None:
    if not _validator().is_valid(payload):
        raise ValueError("payload_contract_invalid")
    validate_facts(facts)
    assert_candidate_integrity(candidate)
    _capability(candidate["target_channel"])
    url_policy.validate(candidate["affiliate_url"])
    if payload["payload_sha256"] != digest(
        {k: v for k, v in payload.items() if k != "payload_sha256"}
    ):
        raise ValueError("payload_hash_mismatch")
    if (
        payload["facts_id"] != facts["facts_id"]
        or payload["draft_sha256"] != candidate["draft_sha256"]
        or payload["target_channel"] != candidate["target_channel"]
        or payload["renderer_version"] != RENDERER_VERSION
        or payload["capability_version"] != CAPABILITY_VERSION
    ):
        raise ValueError("payload_scope_mismatch")
    blocks = fact_blocks(facts, candidate["affiliate_url"])
    composition = payload["composition"]
    if not isinstance(composition, dict) or set(composition) != {"style", "order"}:
        raise ValueError("payload_composition_invalid")
    order = composition["order"]
    if (
        composition["style"] not in INTRODUCTIONS
        or not isinstance(order, list)
        or any(not isinstance(item, str) for item in order)
        or len(order) != len(blocks)
        or set(order) != set(blocks)
    ):
        raise ValueError("payload_fact_omission")
    text = "\n".join(
        part
        for part in [INTRODUCTIONS[composition["style"]], *(blocks[key] for key in order)]
        if part
    )
    if text != payload["text"] or text != candidate["content"] or len(text) > 16000:
        raise ValueError("payload_text_not_grounded")
    if candidate["affiliate_disclosure"] != DISCLOSURE_TEMPLATE:
        raise ValueError("payload_disclosure_mismatch")
    obs = facts["observation"]
    claim = candidate["claim_snapshot"]
    expected = {
        key: obs[key]
        for key in ("platform", "observed_at", "currency", "sale_price_minor", "list_price_minor")
    }
    expected["source_url"] = obs["evidence"]["source_url"]
    if claim != expected or candidate["observation_id"] != obs["observation_id"]:
        raise ValueError("candidate_facts_mismatch")
