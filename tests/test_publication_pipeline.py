from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from s_n_sales.pipeline.publication import (
    DISCLOSURE_TEMPLATE,
    PublicationValidationError,
    build_publication_candidate,
    compute_draft_sha256,
)

ROOT = Path(__file__).resolve().parents[1]


class PublicationPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.observation = json.loads(
            (ROOT / "schemas/examples/valid/offer-observation.v1.json").read_text(encoding="utf-8")
        )
        self.rank_result = {
            "schema_version": "rank-result.v1",
            "rank_id": "rank-obs-demo-001",
            "observation_id": "obs-demo-001",
            "score": 0.5,
            "rank_version": "rank-v1.0.0",
            "ranked_at": "2026-09-11T03:01:00Z",
            "reasons": [],
            "features": {},
        }
        self.kwargs = {
            "content": "Deal minh họa",
            "affiliate_url": "https://example.com/go/item-demo-001",
            "target_channel": "telegram:sales-hunter",
        }

    def test_compute_draft_sha256_stable_across_claim_key_order(self) -> None:
        claim_a = {"platform": "shopee", "currency": "VND"}
        claim_b = {"currency": "VND", "platform": "shopee"}
        common = dict(
            content="Nội dung Unicode ✓",
            affiliate_url="https://example.com/a",
            affiliate_disclosure=DISCLOSURE_TEMPLATE,
            target_channel="telegram:sales-hunter",
            observation_id="obs-1",
        )
        self.assertEqual(
            compute_draft_sha256(claim_snapshot=claim_a, **common),
            compute_draft_sha256(claim_snapshot=claim_b, **common),
        )

    def test_hash_changes_when_canonical_input_changes(self) -> None:
        candidate = build_publication_candidate(self.observation, self.rank_result, **self.kwargs)
        changed = build_publication_candidate(
            self.observation,
            self.rank_result,
            **{**self.kwargs, "content": "Deal minh họa đã đổi"},
        )
        self.assertNotEqual(candidate["draft_sha256"], changed["draft_sha256"])

    def test_build_sets_pending_approval_and_default_disclosure(self) -> None:
        candidate = build_publication_candidate(self.observation, self.rank_result, **self.kwargs)
        self.assertEqual(candidate["approval"]["status"], "pending")
        self.assertEqual(candidate["approval"]["draft_sha256"], candidate["draft_sha256"])
        self.assertEqual(candidate["affiliate_disclosure"], DISCLOSURE_TEMPLATE)

    def test_build_claim_snapshot_matches_observation(self) -> None:
        candidate = build_publication_candidate(self.observation, self.rank_result, **self.kwargs)
        self.assertEqual(
            candidate["claim_snapshot"],
            {
                "platform": "shopee",
                "observed_at": "2026-09-11T03:00:00Z",
                "currency": "VND",
                "list_price_minor": 200000,
                "sale_price_minor": 150000,
                "source_url": "https://example.com/evidence/obs-demo-001",
            },
        )

    def test_build_rejects_non_https_url(self) -> None:
        with self.assertRaises(PublicationValidationError):
            build_publication_candidate(
                self.observation,
                self.rank_result,
                **{**self.kwargs, "affiliate_url": "http://example.com/a"},
            )

    def test_build_rejects_empty_content(self) -> None:
        with self.assertRaises(PublicationValidationError):
            build_publication_candidate(
                self.observation, self.rank_result, **{**self.kwargs, "content": "  "}
            )

    def test_empty_disclosure_falls_back_to_template(self) -> None:
        candidate = build_publication_candidate(
            self.observation, self.rank_result, disclosure="  ", **self.kwargs
        )
        self.assertEqual(candidate["affiliate_disclosure"], DISCLOSURE_TEMPLATE)

    def test_rank_result_must_match_observation(self) -> None:
        rank_result = {**self.rank_result, "observation_id": "other"}
        with self.assertRaises(PublicationValidationError):
            build_publication_candidate(self.observation, rank_result, **self.kwargs)

    def test_output_validates_against_schema(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/publication-candidate.v1.json").read_text(encoding="utf-8")
        )
        candidate = build_publication_candidate(self.observation, self.rank_result, **self.kwargs)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(candidate)


if __name__ == "__main__":
    unittest.main()
