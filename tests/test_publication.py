from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from s_n_sales.pipeline.draft import observation_to_rank
from s_n_sales.pipeline.publication import (
    DISCLOSURE_TEMPLATE,
    PublicationBuildError,
    build_publication_candidate,
    compute_draft_sha256,
)

ROOT = Path(__file__).resolve().parents[1]


def _base_claim() -> dict[str, Any]:
    return {
        "platform": "shopee",
        "observed_at": "2026-09-11T03:00:00Z",
        "currency": "VND",
        "sale_price_minor": 150000,
        "list_price_minor": 200000,
        "source_url": "https://example.com/evidence/obs-demo-001",
    }


class ComputeDraftSha256Tests(unittest.TestCase):
    def test_compute_draft_sha256_stable(self) -> None:
        a = compute_draft_sha256(
            content="Deal demo",
            affiliate_url="https://example.com/a",
            affiliate_disclosure=DISCLOSURE_TEMPLATE,
            claim_snapshot=_base_claim(),
            target_channel="telegram:demo",
            observation_id="obs-demo-001",
        )
        b = compute_draft_sha256(
            content="Deal demo",
            affiliate_url="https://example.com/a",
            affiliate_disclosure=DISCLOSURE_TEMPLATE,
            claim_snapshot=_base_claim(),
            target_channel="telegram:demo",
            observation_id="obs-demo-001",
        )
        self.assertEqual(a, b)
        self.assertRegex(a, r"^[0-9a-f]{64}$")

    def test_compute_draft_sha256_changes_on_content(self) -> None:
        h1 = compute_draft_sha256(
            content="A",
            affiliate_url="https://example.com/a",
            affiliate_disclosure=DISCLOSURE_TEMPLATE,
            claim_snapshot=_base_claim(),
            target_channel="telegram:demo",
            observation_id="obs-demo-001",
        )
        h2 = compute_draft_sha256(
            content="B",
            affiliate_url="https://example.com/a",
            affiliate_disclosure=DISCLOSURE_TEMPLATE,
            claim_snapshot=_base_claim(),
            target_channel="telegram:demo",
            observation_id="obs-demo-001",
        )
        self.assertNotEqual(h1, h2)

    def test_compute_draft_sha256_changes_on_disclosure(self) -> None:
        h1 = compute_draft_sha256(
            content="Deal",
            affiliate_url="https://example.com/a",
            affiliate_disclosure="one",
            claim_snapshot=_base_claim(),
            target_channel="telegram:demo",
            observation_id="obs-demo-001",
        )
        h2 = compute_draft_sha256(
            content="Deal",
            affiliate_url="https://example.com/a",
            affiliate_disclosure="two",
            claim_snapshot=_base_claim(),
            target_channel="telegram:demo",
            observation_id="obs-demo-001",
        )
        self.assertNotEqual(h1, h2)

    def test_compute_draft_sha256_changes_on_claim_snapshot(self) -> None:
        c1 = _base_claim()
        c2 = _base_claim()
        c2["sale_price_minor"] = 149000
        self.assertNotEqual(
            compute_draft_sha256(
                content="Deal",
                affiliate_url="https://example.com/a",
                affiliate_disclosure=DISCLOSURE_TEMPLATE,
                claim_snapshot=c1,
                target_channel="telegram:demo",
                observation_id="obs-demo-001",
            ),
            compute_draft_sha256(
                content="Deal",
                affiliate_url="https://example.com/a",
                affiliate_disclosure=DISCLOSURE_TEMPLATE,
                claim_snapshot=c2,
                target_channel="telegram:demo",
                observation_id="obs-demo-001",
            ),
        )


class BuildPublicationCandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.observation: dict[str, Any] = json.loads(
            (ROOT / "schemas/examples/valid/offer-observation.v1.json").read_text(encoding="utf-8")
        )
        self.now = datetime(2026, 9, 11, 4, 0, tzinfo=UTC)
        self.rank = observation_to_rank(self.observation, now=self.now)
        self.content = "Sản phẩm minh họa đang giảm — kiểm tra link trước khi mua."
        self.affiliate_url = "https://example.com/aff/item-demo-001"
        self.channel = "telegram:s-n-sales-demo"

    def test_build_sets_pending_approval(self) -> None:
        candidate = build_publication_candidate(
            self.observation,
            self.rank,
            content=self.content,
            affiliate_url=self.affiliate_url,
            target_channel=self.channel,
        )
        self.assertEqual(candidate["approval"]["status"], "pending")
        self.assertEqual(candidate["approval"]["draft_sha256"], candidate["draft_sha256"])
        self.assertEqual(candidate["schema_version"], "publication-candidate.v1")

    def test_build_uses_default_disclosure_when_none(self) -> None:
        candidate = build_publication_candidate(
            self.observation,
            self.rank,
            content=self.content,
            affiliate_url=self.affiliate_url,
            target_channel=self.channel,
            disclosure=None,
        )
        self.assertEqual(candidate["affiliate_disclosure"], DISCLOSURE_TEMPLATE)
        self.assertTrue(len(candidate["affiliate_disclosure"]) > 0)

    def test_build_uses_default_disclosure_when_empty(self) -> None:
        candidate = build_publication_candidate(
            self.observation,
            self.rank,
            content=self.content,
            affiliate_url=self.affiliate_url,
            target_channel=self.channel,
            disclosure="   ",
        )
        self.assertEqual(candidate["affiliate_disclosure"], DISCLOSURE_TEMPLATE)

    def test_build_rejects_empty_content(self) -> None:
        with self.assertRaises(PublicationBuildError):
            build_publication_candidate(
                self.observation,
                self.rank,
                content="  ",
                affiliate_url=self.affiliate_url,
                target_channel=self.channel,
            )

    def test_build_claim_snapshot_matches_observation(self) -> None:
        candidate = build_publication_candidate(
            self.observation,
            self.rank,
            content=self.content,
            affiliate_url=self.affiliate_url,
            target_channel=self.channel,
        )
        snap = candidate["claim_snapshot"]
        self.assertEqual(snap["platform"], self.observation["platform"])
        self.assertEqual(snap["observed_at"], self.observation["observed_at"])
        self.assertEqual(snap["currency"], self.observation["currency"])
        self.assertEqual(snap["sale_price_minor"], self.observation["sale_price_minor"])
        self.assertEqual(snap["list_price_minor"], self.observation["list_price_minor"])
        self.assertEqual(snap["source_url"], self.observation["evidence"]["source_url"])

    def test_build_requires_https_affiliate_url(self) -> None:
        with self.assertRaises(PublicationBuildError):
            build_publication_candidate(
                self.observation,
                self.rank,
                content=self.content,
                affiliate_url="http://example.com/aff",
                target_channel=self.channel,
            )

    def test_build_passes_publication_schema(self) -> None:
        candidate = build_publication_candidate(
            self.observation,
            self.rank,
            content=self.content,
            affiliate_url=self.affiliate_url,
            target_channel=self.channel,
        )
        schema = json.loads(
            (ROOT / "schemas/publication-candidate.v1.json").read_text(encoding="utf-8")
        )
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(candidate)

    def test_draft_sha256_matches_compute(self) -> None:
        candidate = build_publication_candidate(
            self.observation,
            self.rank,
            content=self.content,
            affiliate_url=self.affiliate_url,
            target_channel=self.channel,
        )
        expected = compute_draft_sha256(
            content=self.content,
            affiliate_url=self.affiliate_url,
            affiliate_disclosure=candidate["affiliate_disclosure"],
            claim_snapshot=candidate["claim_snapshot"],
            target_channel=self.channel,
            observation_id=self.observation["observation_id"],
        )
        self.assertEqual(candidate["draft_sha256"], expected)


class PublicationFixtureContractTests(unittest.TestCase):
    def test_valid_publication_example_matches_schema(self) -> None:
        path = ROOT / "schemas/examples/valid/publication-candidate.v1.json"
        self.assertTrue(path.is_file(), f"missing fixture {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        schema = json.loads(
            (ROOT / "schemas/publication-candidate.v1.json").read_text(encoding="utf-8")
        )
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(data)


if __name__ == "__main__":
    unittest.main()
