"""Run with the clean venv Python outside the checkout, never with uv run.

Only deterministic fixtures and FakePlatformClient are used. No live publication.
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import s_n_sales
from s_n_sales.api.store import OperatorStore
from s_n_sales.pipeline.draft import observation_to_rank, validate_observation
from s_n_sales.pipeline.publication import build_publication_candidate
from s_n_sales.pipeline.publisher import FakePlatformClient, Publisher, PublishError


def main() -> None:
    checkout = Path(sys.argv[1]).resolve()
    if Path(s_n_sales.__file__).resolve().is_relative_to(checkout):
        raise AssertionError("runtime imported from checkout")
    if "PYTHONPATH" in os.environ:
        raise AssertionError("PYTHONPATH must be unset")
    for dependency in ("ruff", "pyright", "pip-audit", "hatchling"):
        try:
            version(dependency)
        except PackageNotFoundError:
            continue
        raise AssertionError(f"dev/build dependency installed in runtime: {dependency}")

    now = datetime(2026, 9, 25, tzinfo=UTC)
    observation = {
        "schema_version": "offer-observation.v1",
        "observation_id": "artifact-observation",
        "platform": "shopee",
        "external_offer_id": "fixture-offer",
        "item_id": "fixture-item",
        "merchant_id": "fixture-merchant",
        "market": "VN",
        "source_method": "manual",
        "title": "Fixture only",
        "product_url": "https://example.com/item",
        "observed_at": "2026-09-25T00:00:00Z",
        "currency": "VND",
        "list_price_minor": 299000,
        "sale_price_minor": 199000,
        "shipping_price_minor": None,
        "stock_status": "in_stock",
        "coupon_codes": [],
        "eligibility": {"scope": "all_users", "notes": None},
        "evidence": {
            "source_url": "https://example.com/evidence",
            "fetched_at": "2026-09-25T00:00:00Z",
            "payload_sha256": "a" * 64,
        },
    }
    validate_observation(observation, now=now)
    ranked = observation_to_rank(observation, now=now)
    candidate = build_publication_candidate(
        observation,
        ranked,
        content="Fixture: 199.000 VND, chưa gồm phí vận chuyển.",
        affiliate_url="https://example.com/affiliate",
        target_channel="manual_export",
    )
    store = OperatorStore()
    store.upsert_candidate(candidate)
    approval = store.approve(
        candidate["publication_id"],
        decided_by="artifact-smoke",
        now=now,
        expected_revision=store.get_revision(candidate["publication_id"]),
    )
    client = FakePlatformClient()
    try:
        Publisher(client=client).publish(candidate, approval, now=now)
    except PublishError as exc:
        if "dry_run=True" not in str(exc):
            raise
    else:
        raise AssertionError("default publisher did not refuse a side effect")
    if client.posts:
        raise AssertionError("dry-run contacted the client")
    receipt = Publisher(client=client, dry_run=False, approval_source=store).publish(
        candidate, approval, now=now
    )
    if receipt["publication_id"] != candidate["publication_id"]:
        raise AssertionError("fake receipt does not match candidate")
    print("runtime-only wheel: validation, candidate, approval, dry-run and fake receipt OK")


if __name__ == "__main__":
    main()
