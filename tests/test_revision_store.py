"""SH-006/008/009: imports cannot manufacture authority or bypass contracts."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from s_n_sales.api.store import OperatorStore
from s_n_sales.api.store_sqlite import SqliteOperatorStore
from s_n_sales.pipeline.publication import build_publication_candidate, compute_draft_sha256

ROOT = Path(__file__).resolve().parents[1]


def draft() -> dict[str, Any]:
    observation = json.loads(
        (ROOT / "schemas/examples/valid/offer-observation.v1.json").read_text(encoding="utf-8")
    )
    return build_publication_candidate(
        observation, {}, content="Nội dung thử nghiệm", affiliate_url="https://example.com/aff",
        target_channel="manual_export",
    )


def rehash(candidate: dict[str, Any]) -> dict[str, Any]:
    candidate["draft_sha256"] = compute_draft_sha256(
        content=candidate["content"], affiliate_url=candidate["affiliate_url"],
        affiliate_disclosure=candidate["affiliate_disclosure"],
        claim_snapshot=candidate["claim_snapshot"], observation_id=candidate["observation_id"],
    )
    candidate["approval"]["draft_sha256"] = candidate["draft_sha256"]
    return candidate


class ImportAuthorityTests(unittest.TestCase):
    def check_rejected(self, candidate: dict[str, Any]) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for store in (OperatorStore(), SqliteOperatorStore(Path(directory) / "operator.db")):
                try:
                    with self.subTest(store=type(store).__name__), self.assertRaises(ValueError):
                        store.upsert_candidate(candidate)
                    self.assertEqual(store.list_candidates(), [])
                finally:
                    store.close()

    def test_import_cannot_self_approve(self) -> None:
        candidate = draft()
        candidate["approval"].update(
            status="approved", decided_by="caller-admin", decided_at="2026-09-25T00:00:00Z"
        )
        self.check_rejected(candidate)

    def test_import_requires_full_claim_contract_not_only_matching_hash(self) -> None:
        candidate = draft()
        del candidate["claim_snapshot"]["currency"]
        self.check_rejected(rehash(candidate))

    def test_import_rejects_unknown_server_fields(self) -> None:
        candidate = draft()
        candidate["role"] = "admin"
        self.check_rejected(candidate)

    def test_import_rejects_float_or_boolean_money(self) -> None:
        for value in (True, 1.0, -1):
            candidate = draft()
            candidate["claim_snapshot"]["sale_price_minor"] = value
            with self.subTest(value=value):
                self.check_rejected(rehash(candidate))


if __name__ == "__main__":
    unittest.main()
