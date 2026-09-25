"""Full manual source/evidence/facts/payload flow, including boundary regressions."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from s_n_sales.api.store_sqlite import SqliteOperatorStore
from s_n_sales.domain.json_value import canonical, digest, iso

NOW = datetime(2026, 9, 25, tzinfo=UTC)
ROOT = Path(__file__).resolve().parents[1]


def manual_request() -> dict[str, Any]:
    observation = json.loads(
        (ROOT / "schemas/examples/valid/offer-observation.v1.json").read_text()
    )
    for key in ("schema_version", "observation_id", "source_method", "evidence"):
        del observation[key]
    observation.update(
        observed_at=iso(NOW),
        stock_status="in_stock",
        variant_id="blue-128",
        sale_price_minor=80000,
        list_price_minor=100000,
        eligibility={"scope": "all_users", "notes": None},
    )
    return {
        "offer": observation,
        "source_url": "https://example.com/source",
        "variant_scope": "explicit_variant",
        "valid_until": iso(NOW + timedelta(hours=2)),
        "affiliate_url": "https://example.com/aff",
        "target_channel": "manual_export",
        "permission_ref": "operator-allowed-fixture",
        "permitted_until": iso(NOW + timedelta(days=1)),
    }


class GroundedFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        from s_n_sales.quality.repository import DealRepository
        from s_n_sales.quality.urls import UrlPolicy

        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "flow.db"
        self.store = SqliteOperatorStore(self.path)
        self.policy = UrlPolicy(frozenset({"example.com"}))
        self.repo = DealRepository(self.store, url_policy=self.policy)

    def tearDown(self) -> None:
        self.store.close()
        self.directory.cleanup()

    def save(self):
        return self.repo.import_manual(
            canonical(manual_request()).encode(), actor="reviewer", now=NOW
        )

    def test_preview_does_not_change_actual_database(self) -> None:
        preview = self.repo.preview_manual(
            canonical(manual_request()).encode(), actor="reviewer", now=NOW
        )
        self.assertTrue(preview["eligible"])
        self.assertIn("80.000 VND", preview["payload"]["text"])
        for table in ("candidates", "evidence_manifests", "deal_facts", "candidate_payloads"):
            self.assertEqual(
                self.store._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 0
            )

    def test_manual_payload_roundtrip_survives_restart_and_matches_source_digest(self) -> None:
        from s_n_sales.quality.repository import DealRepository

        raw = canonical(manual_request()).encode()
        saved = self.repo.import_manual(raw, actor="reviewer", now=NOW)
        pub_id = saved.snapshot.candidate["publication_id"]
        self.assertNotIn("approval_id", saved.snapshot.candidate["approval"])
        self.store.close()
        self.store = SqliteOperatorStore(self.path)
        self.repo = DealRepository(self.store, url_policy=self.policy)
        reloaded = self.repo.get(pub_id)
        self.assertEqual(reloaded.payload, saved.payload)
        self.assertEqual(reloaded.facts, saved.facts)
        self.assertEqual(reloaded.payload["text"], reloaded.snapshot.candidate["content"])
        retained = self.repo.vault.read(saved.facts["evidence_id"], now=NOW)
        self.assertEqual(retained["document"], manual_request())
        self.assertEqual(
            retained["manifest"]["source_sha256"],
            saved.facts["observation"]["evidence"]["payload_sha256"],
        )

    def test_caller_fields_cannot_forge_source_authority(self) -> None:
        for key in ("approval", "publication_id", "draft_sha256", "actor"):
            request = manual_request()
            request[key] = "forged"
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.repo.import_manual(canonical(request).encode(), actor="reviewer", now=NOW)
        request = manual_request()
        request["offer"]["source_method"] = "official_api"
        with self.assertRaises(ValueError):
            self.repo.import_manual(canonical(request).encode(), actor="reviewer", now=NOW)
        self.assertEqual(self.store.list_candidates(), [])

    def test_missing_source_permission_and_variant_block_import(self) -> None:
        from s_n_sales.quality.facts import EligibilityError

        for field, value in (("permission_ref", ""), ("variant_scope", "unknown")):
            request = manual_request()
            request[field] = value
            with self.subTest(field=field), self.assertRaises((ValueError, EligibilityError)):
                self.repo.import_manual(canonical(request).encode(), actor="reviewer", now=NOW)
        self.assertEqual(self.store.list_candidates(), [])

    def test_evidence_and_fact_history_are_immutable(self) -> None:
        saved = self.save()
        for table in (
            "deal_facts",
            "candidate_payloads",
            "evidence_manifests",
            "evidence_payloads",
        ):
            with self.subTest(table=table), self.assertRaises(sqlite3.IntegrityError):
                self.store._conn.execute(f"DELETE FROM {table}")
        self.assertEqual(
            self.repo.get(saved.snapshot.candidate["publication_id"]).payload, saved.payload
        )

    def test_retired_evidence_blocks_eligibility_but_preserves_audit_manifest(self) -> None:
        from s_n_sales.quality.facts import evaluate_eligibility

        saved = self.save()
        evidence = saved.facts["evidence_id"]
        self.repo.vault.retire(evidence, actor="admin", reason="permission_revoked", now=NOW)
        self.assertFalse(
            evaluate_eligibility(
                saved.facts, vault=self.repo.vault, url_policy=self.policy, now=NOW
            ).eligible
        )
        self.assertEqual(
            self.store._conn.execute("SELECT COUNT(*) FROM evidence_payloads").fetchone()[0], 0
        )
        self.assertEqual(
            self.store._conn.execute("SELECT COUNT(*) FROM evidence_manifests").fetchone()[0], 1
        )

    def test_same_payload_reimport_keeps_existing_decision_and_provenance(self) -> None:
        saved = self.save()
        pub_id = saved.snapshot.candidate["publication_id"]
        approval = self.store.approve(
            pub_id, decided_by="reviewer", expected_revision=saved.snapshot.revision
        )
        repeated = self.repo.save(
            saved.facts,
            affiliate_url="https://example.com/aff",
            target_channel="manual_export",
            actor="reviewer",
            now=NOW,
            publication_id=pub_id,
            expected_revision=self.store.get_revision(pub_id),
        )
        self.assertEqual(repeated.payload, saved.payload)
        self.assertEqual(repeated.snapshot.approval, approval)

    def test_payload_tamper_even_with_recomputed_hash_is_rejected(self) -> None:
        from s_n_sales.content.render import validate_payload

        saved = self.save()
        candidate = saved.snapshot.candidate
        for field, value in (
            ("text", "Giá chỉ 1 đồng"),
            ("target_channel", "fake:other"),
            ("composition", {"style": "neutral", "order": ["title"]}),
            ("composition", {"style": [], "order": []}),
        ):
            payload = deepcopy(saved.payload)
            payload[field] = value
            payload["payload_sha256"] = digest(
                {k: v for k, v in payload.items() if k != "payload_sha256"}
            )
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_payload(payload, candidate, saved.facts, url_policy=self.policy)

    def test_business_key_distinguishes_variant_and_conditions_not_title_or_price(self) -> None:
        from s_n_sales.quality.facts import build_facts, business_key

        saved = self.save()
        facts = saved.facts

        def changed(**changes):
            observation = deepcopy(facts["observation"])
            observation.update(changes)
            return build_facts(
                observation,
                evidence_id=facts["evidence_id"],
                variant_scope="explicit_variant",
                valid_until=None,
                actor="reviewer",
                adapter_version="manual-record-v1",
            )

        original = business_key(facts)
        self.assertEqual(
            original, business_key(changed(sale_price_minor=75000, title="Different title"))
        )
        self.assertNotEqual(original, business_key(changed(variant_id="red-256")))
        self.assertNotEqual(
            original,
            business_key(
                changed(
                    eligibility={
                        "scope": "account_or_region_dependent",
                        "notes": "Chỉ tài khoản mới",
                    }
                )
            ),
        )

    def test_final_total_requires_matching_separate_evidence(self) -> None:
        from s_n_sales.quality.facts import build_facts, evaluate_eligibility

        saved = self.save()
        original = saved.facts
        evidence = self.repo.vault.retain(
            canonical(
                {
                    "verified_total_minor": 90000,
                    "currency": "VND",
                    "conditions": original["observation"]["eligibility"],
                }
            ).encode(),
            source_url="https://example.com/total",
            actor="reviewer",
            permission_ref="allowed",
            permitted_until=NOW + timedelta(days=1),
            now=NOW,
            url_policy=self.policy,
        )

        def total_facts(amount):
            return build_facts(
                original["observation"],
                evidence_id=original["evidence_id"],
                variant_scope="explicit_variant",
                valid_until=None,
                actor="reviewer",
                adapter_version="manual-record-v1",
                verified_total={"amount_minor": amount, "evidence_id": evidence["evidence_id"]},
            )

        self.assertTrue(
            evaluate_eligibility(
                total_facts(90000), vault=self.repo.vault, url_policy=self.policy, now=NOW
            ).eligible
        )
        self.assertFalse(
            evaluate_eligibility(
                total_facts(1), vault=self.repo.vault, url_policy=self.policy, now=NOW
            ).eligible
        )

    def test_sensitive_source_text_is_not_copied_into_facts_or_publication(self) -> None:
        request = manual_request()
        request["offer"]["title"] = "Bearer should-not-be-retained"
        with self.assertRaises(ValueError):
            self.repo.import_manual(canonical(request).encode(), actor="reviewer", now=NOW)
        self.assertEqual(self.store.list_candidates(), [])
        rows = self.store._conn.execute("SELECT body_json FROM evidence_payloads").fetchall()
        self.assertNotIn("should-not-be-retained", str([row[0] for row in rows]))

    def test_duplicate_json_keys_and_nonfinite_input_are_rejected(self) -> None:
        for raw in (b'{"offer":{},"offer":{}}', b'{"offer":NaN}', b"\xff"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.repo.import_manual(raw, actor="op", now=NOW)

    def test_new_customer_fact_is_not_deleted_as_personal_identity(self) -> None:
        item = self.repo.vault.retain(
            b'{"new_customer_only":true,"buyer_email":"private@example.com"}',
            source_url="https://example.com/a",
            actor="reviewer",
            permission_ref="allowed",
            permitted_until=NOW + timedelta(days=1),
            now=NOW,
            url_policy=self.policy,
        )
        document = self.repo.vault.read(item["evidence_id"], now=NOW)["document"]
        self.assertIs(document["new_customer_only"], True)
        self.assertEqual(document["buyer_email"], "[REDACTED]")


class ComposerBoundaryTests(unittest.TestCase):
    def test_cache_is_bound_to_facts_and_budget_is_reserved_before_call(self) -> None:
        from s_n_sales.content.grounded import GroundedComposer, ModelSettings

        class Model:
            calls = 0

            def propose(self, request, *, max_output_tokens):
                self.calls += 1
                return {"style": "friendly", "order": list(reversed(request["fact_ids"]))}

        model = Model()
        composer = GroundedComposer(
            ModelSettings(
                provider="test",
                enabled=True,
                model="fake",
                max_calls=1,
                budget_microunits=2,
                call_cost_ceiling_microunits=2,
            ),
            model=model,
        )
        blocks = {"title": "Sản phẩm", "price": "80.000 VND", "condition": "Tài khoản mới"}
        first = composer.compose(blocks)
        second = composer.compose(blocks)
        self.assertEqual(first.text, second.text)
        self.assertEqual(second.mode, "model_cache")
        changed = composer.compose(dict(blocks, price="90.000 VND"))
        self.assertEqual(changed.mode, "template_fallback")
        self.assertIn("90.000 VND", changed.text)
        self.assertEqual(model.calls, 1)
        self.assertEqual(composer.usage, {"calls": 1, "reserved_cost_microunits": 2})

    def test_invalid_model_output_never_drops_a_condition(self) -> None:
        from s_n_sales.content.grounded import GroundedComposer, ModelSettings

        for proposal in (
            {"style": "neutral", "order": ["title"]},
            {"style": [], "order": ["title", "condition"]},
            {"style": "neutral", "order": ["title", "title"]},
            {
                "style": "neutral",
                "order": ["title", "condition"],
                "content": "Rẻ nhất mọi thời đại",
            },
        ):

            class Model:
                def __init__(self, output: dict[str, Any]) -> None:
                    self.output = output

                def propose(self, request, *, max_output_tokens):
                    return self.output

            composed = GroundedComposer(
                ModelSettings(provider="test", enabled=True, max_calls=1), model=Model(proposal)
            ).compose({"title": "A", "condition": "Không áp dụng mọi tài khoản"})
            self.assertEqual(composed.mode, "template_fallback")
            self.assertIn("Không áp dụng mọi tài khoản", composed.text)

    def test_input_budget_never_disables_the_manual_template(self) -> None:
        from s_n_sales.content.grounded import GroundedComposer, ModelSettings

        class Model:
            calls = 0

            def propose(self, request, *, max_output_tokens):
                self.calls += 1
                return {"style": "neutral", "order": request["fact_ids"]}

        model = Model()
        composer = GroundedComposer(
            ModelSettings(provider="test", enabled=True, max_calls=1, max_input_bytes=1),
            model=model,
        )
        result = composer.compose({"price": "Giá bán 80.000 VND; phí ship chưa xác minh"})
        self.assertEqual(result.mode, "template_fallback")
        self.assertIn("80.000 VND", result.text)
        self.assertEqual(model.calls, 0)

    def test_no_model_and_no_paid_budget_preserve_template(self) -> None:
        from s_n_sales.content.grounded import GroundedComposer, ModelSettings

        self.assertEqual(GroundedComposer().compose({"price": "0 VND"}).text, "0 VND")
        self.assertEqual(
            GroundedComposer(ModelSettings(enabled=True)).compose({"price": "0 VND"}).mode,
            "template_fallback",
        )
        with self.assertRaises(ValueError):
            ModelSettings(provider="paid-provider", enabled=True)


class UrlDnsTests(unittest.TestCase):
    def test_private_or_mixed_dns_results_are_blocked(self) -> None:
        from s_n_sales.quality.urls import assert_public_addresses

        assert_public_addresses(["93.184.216.34"])
        for addresses in (
            [],
            ["127.0.0.1"],
            ["::1"],
            ["169.254.169.254"],
            ["93.184.216.34", "10.0.0.1"],
            ["::ffff:127.0.0.1"],
        ):
            with self.subTest(addresses=addresses), self.assertRaises(ValueError):
                assert_public_addresses(addresses)
