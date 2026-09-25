"""Run with the clean venv Python outside the checkout, never with uv run.

Only deterministic fixtures and FakePlatformClient are used. No live publication.
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from tempfile import TemporaryDirectory

import s_n_sales
from s_n_sales.api.store import OperatorStore
from s_n_sales.domain.json_value import canonical, iso
from s_n_sales.pipeline.draft import observation_to_rank, validate_observation
from s_n_sales.pipeline.publication import build_publication_candidate
from s_n_sales.pipeline.publisher import FakePlatformClient, Publisher, PublishError
from s_n_sales.publishing.fake import FakeTransport
from s_n_sales.publishing.queue import PublicationQueue
from s_n_sales.publishing.recall import RecallService
from s_n_sales.publishing.worker import PublicationWorker
from s_n_sales.quality.repository import DealRepository
from s_n_sales.quality.urls import UrlPolicy


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
    repository = DealRepository(store, url_policy=UrlPolicy(frozenset({"example.com"})))
    offer = {
        key: value
        for key, value in observation.items()
        if key not in {"schema_version", "observation_id", "source_method", "evidence"}
    }
    request = {
        "offer": offer,
        "source_url": "https://example.com/evidence",
        "variant_scope": "single_variant_verified",
        "valid_until": iso(now + timedelta(hours=2)),
        "affiliate_url": "https://example.com/affiliate",
        "target_channel": "manual_export",
        "permission_ref": "artifact-fixture-only",
        "permitted_until": iso(now + timedelta(days=1)),
    }
    package = repository.import_manual(canonical(request).encode(), actor="artifact-smoke", now=now)
    fetched = repository.get(package.snapshot.candidate["publication_id"])
    if fetched.payload["text"] != fetched.snapshot.candidate["content"]:
        raise AssertionError("grounded payload and preview differ")
    if "199.000 VND" not in fetched.payload["text"] or "#affiliate" not in fetched.payload["text"]:
        raise AssertionError("grounded payload lost price or disclosure")
    request["target_channel"] = "fake:artifact"
    package = repository.import_manual(canonical(request).encode(), actor="artifact-smoke", now=now)
    queue = PublicationQueue(repository)
    identifier = package.snapshot.candidate["publication_id"]
    scoped = queue.approve_payload(
        identifier,
        expected_revision=package.snapshot.revision,
        expected_payload_sha256=package.payload["payload_sha256"],
        actor="artifact-smoke",
        now=now,
    )
    intent = queue.enqueue(
        identifier,
        expected_revision=scoped["revision"],
        expected_payload_sha256=package.payload["payload_sha256"],
        actor="artifact-smoke",
        now=now,
    )
    with TemporaryDirectory() as directory:
        transport = FakeTransport(Path(directory) / "remote.db")
        try:
            if PublicationWorker(queue, transport).run_once(now=now)["status"] != "dry_run":
                raise AssertionError("durable worker did not default to dry-run")
            worker = PublicationWorker(queue, transport, dry_run=False)
            if worker.run_once(now=now)["status"] != "idle" or transport.call_count() != 0:
                raise AssertionError("default global pause was not enforced")
            queue.set_pause(
                "global", "*", paused=False, actor="artifact-smoke", reason="fixture", now=now
            )
            result = worker.run_once(now=now)
            if (
                result["status"] != "confirmed"
                or result["receipt"]["text"] != package.payload["text"]
            ):
                raise AssertionError("durable simulated receipt does not match viewed payload")
            recall = RecallService(queue)
            recall.request(intent["intent_id"], actor="artifact-smoke", reason="fixture", now=now)
            if recall.run_once(transport, now=now, dry_run=False)["status"] != "confirmed":
                raise AssertionError("simulated withdrawal was not confirmed")
        finally:
            transport.close()
    store.close()
    print("runtime-only wheel: grounded draft, scoped approval, durable fake send and recall OK")


if __name__ == "__main__":
    main()
