"""Versioned complete facts; publication eligibility is not a ranking score."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from s_n_sales.domain.json_value import digest, iso, utc
from s_n_sales.evidence.vault import EvidenceVault, has_sensitive_text
from s_n_sales.pipeline.draft import observation_to_rank, validate_observation
from s_n_sales.quality.urls import UrlPolicy


class EligibilityError(ValueError):
    """A high score never overrides missing or invalid publication evidence."""


@dataclass(frozen=True)
class EligibilityPolicy:
    version: str = "pilot-eligibility-v1"
    max_age_seconds: int = 21600
    clock_skew_seconds: int = 300

    def __post_init__(self) -> None:
        if type(self.max_age_seconds) is not int or not 1 <= self.max_age_seconds <= 86400:
            raise ValueError("invalid_freshness_policy")
        if type(self.clock_skew_seconds) is not int or not 0 <= self.clock_skew_seconds <= 300:
            raise ValueError("invalid_clock_skew_policy")


DEFAULT_POLICY = EligibilityPolicy()


@dataclass(frozen=True)
class EligibilityDecision:
    eligible: bool
    codes: tuple[str, ...]
    policy_version: str
    expires_at: str | None


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    resource = files("s_n_sales").joinpath("schemas", "deal-facts.v1.json")
    return Draft202012Validator(
        json.loads(resource.read_text(encoding="utf-8")), format_checker=FormatChecker()
    )


def _price_scope(observation: dict[str, Any]) -> str:
    scope = observation["eligibility"]["scope"]
    if scope == "unknown":
        return "unknown"
    return (
        "conditional"
        if scope == "account_or_region_dependent" or observation["coupon_codes"]
        else "unconditional"
    )


def validate_facts(facts: dict[str, Any]) -> None:
    if not _validator().is_valid(facts):
        raise ValueError("facts_contract_invalid")
    core = {key: value for key, value in facts.items() if key != "facts_id"}
    if facts["facts_id"] != "fact-" + digest(core):
        raise ValueError("facts_hash_mismatch")
    observation = facts["observation"]
    validate_observation(observation, now=utc(observation["observed_at"]))
    for field in ("sale_price_minor", "list_price_minor", "shipping_price_minor"):
        amount = observation[field]
        if amount is not None and type(amount) is not int:
            raise ValueError("money_must_be_integer")
    source_text = [
        observation[key] for key in ("title", "item_id", "merchant_id", "external_offer_id")
    ]
    source_text.extend([observation.get("variant_id"), observation["eligibility"]["notes"]])
    if any(isinstance(value, str) and has_sensitive_text(value) for value in source_text):
        raise ValueError("facts_sensitive_source_text")
    total = facts["verified_total"]
    if total is not None and type(total["amount_minor"]) is not int:
        raise ValueError("money_must_be_integer")
    if facts["sale_price_scope"] != _price_scope(observation):
        raise ValueError("price_scope_mismatch")
    if not facts["captured_by"].strip() or not facts["adapter_version"].strip():
        raise ValueError("facts_provenance_required")


def build_facts(
    observation: dict[str, Any],
    *,
    evidence_id: str,
    variant_scope: str,
    valid_until: datetime | None,
    actor: str,
    adapter_version: str,
    verified_total: dict[str, Any] | None = None,
) -> dict[str, Any]:
    copied = deepcopy(observation)
    validate_observation(copied, now=utc(copied["observed_at"]))
    core = {
        "schema_version": "deal-facts.v1",
        "observation": copied,
        "evidence_id": evidence_id,
        "variant_scope": variant_scope,
        "valid_until": iso(valid_until) if valid_until is not None else None,
        "captured_by": actor,
        "adapter_version": adapter_version,
        "normalizer_version": "normalizer-v1",
        "sale_price_scope": _price_scope(copied),
        "verified_total": deepcopy(verified_total),
    }
    result = {"facts_id": "fact-" + digest(core), **core}
    validate_facts(result)
    return result


def business_key(facts: dict[str, Any]) -> str:
    validate_facts(facts)
    observation = facts["observation"]
    identity = {
        key: observation[key]
        for key in ("platform", "merchant_id", "item_id", "market", "currency")
    }
    identity.update(
        variant_id=observation.get("variant_id"),
        variant_scope=facts["variant_scope"],
        eligibility=observation["eligibility"],
        coupon_codes=sorted(observation["coupon_codes"]),
        sale_price_scope=facts["sale_price_scope"],
    )
    return "deal-" + digest(identity)


def evaluate_eligibility(
    facts: dict[str, Any],
    *,
    vault: EvidenceVault,
    url_policy: UrlPolicy,
    now: datetime,
    policy: EligibilityPolicy = DEFAULT_POLICY,
) -> EligibilityDecision:
    clock = utc(now)
    codes: list[str] = []
    try:
        validate_facts(facts)
    except ValueError:
        return EligibilityDecision(False, ("invalid_facts",), policy.version, None)
    obs = facts["observation"]
    observed = utc(obs["observed_at"])
    fetched = utc(obs["evidence"]["fetched_at"])
    skew = timedelta(seconds=policy.clock_skew_seconds)
    expiry = observed + timedelta(seconds=policy.max_age_seconds)
    if facts["valid_until"] is not None:
        expiry = min(expiry, utc(facts["valid_until"]))
    if observed > clock + skew or fetched > clock + skew or observed > fetched + skew:
        codes.append("future_or_inconsistent_clock")
    if clock >= expiry:
        codes.append("stale_or_expired")
    if obs["stock_status"] != "in_stock":
        codes.append("stock_not_confirmed")
    variant = obs.get("variant_id")
    if (
        facts["variant_scope"] == "unknown"
        or (facts["variant_scope"] == "explicit_variant" and not variant)
        or (facts["variant_scope"] == "single_variant_verified" and variant is not None)
    ):
        codes.append("variant_not_confirmed")
    eligibility = obs["eligibility"]
    if eligibility["scope"] == "unknown":
        codes.append("eligibility_unknown")
    if (obs["coupon_codes"] or eligibility["scope"] == "account_or_region_dependent") and not (
        eligibility["notes"] or ""
    ).strip():
        codes.append("purchase_conditions_missing")
    try:
        url_policy.validate(obs["product_url"])
        url_policy.validate(obs["evidence"]["source_url"])
        item = vault.read(facts["evidence_id"], now=clock)
        manifest = item["manifest"]
        if (
            manifest["source_sha256"] != obs["evidence"]["payload_sha256"]
            or manifest["source_url"] != obs["evidence"]["source_url"]
        ):
            codes.append("evidence_provenance_mismatch")
        if utc(manifest["captured_at"]) > clock + skew:
            codes.append("evidence_future")
        expiry = min(expiry, utc(manifest["permitted_until"]))
        total = facts["verified_total"]
        if total is not None:
            total_evidence = vault.read(total["evidence_id"], now=clock)
            document = total_evidence["document"]
            if (
                document.get("verified_total_minor") != total["amount_minor"]
                or type(document.get("verified_total_minor")) is not int
                or document.get("currency") != "VND"
                or document.get("conditions") != eligibility
            ):
                codes.append("final_price_evidence_mismatch")
            expiry = min(expiry, utc(total_evidence["manifest"]["permitted_until"]))
    except ValueError:
        codes.append("evidence_or_url_unavailable")
    return EligibilityDecision(not codes, tuple(codes), policy.version, iso(expiry))


def eligible_rank(
    facts: dict[str, Any],
    *,
    vault: EvidenceVault,
    url_policy: UrlPolicy,
    now: datetime,
    policy: EligibilityPolicy = DEFAULT_POLICY,
) -> dict[str, Any]:
    decision = evaluate_eligibility(
        facts, vault=vault, url_policy=url_policy, now=now, policy=policy
    )
    if not decision.eligible:
        raise EligibilityError(",".join(decision.codes))
    return observation_to_rank(facts["observation"], now=utc(now))
