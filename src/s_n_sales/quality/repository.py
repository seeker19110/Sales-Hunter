"""Application flow for server-owned manual drafts, immutable facts and payloads."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from s_n_sales.api.contracts import RevisionConflict, require_actor
from s_n_sales.api.store import OperatorStore
from s_n_sales.api.store_sqlite import SqliteOperatorStore
from s_n_sales.content.grounded import GroundedComposer
from s_n_sales.content.render import render_candidate, validate_payload
from s_n_sales.domain.json_value import canonical, iso, json_object, utc
from s_n_sales.domain.publication_state import CandidateSnapshot
from s_n_sales.evidence.vault import EvidenceVault
from s_n_sales.quality.facts import build_facts, eligible_rank, evaluate_eligibility, validate_facts
from s_n_sales.quality.urls import UrlPolicy

_OFFER_FIELDS = frozenset(
    {
        "platform",
        "external_offer_id",
        "item_id",
        "variant_id",
        "merchant_id",
        "market",
        "title",
        "product_url",
        "observed_at",
        "currency",
        "list_price_minor",
        "sale_price_minor",
        "shipping_price_minor",
        "stock_status",
        "coupon_codes",
        "eligibility",
    }
)
_REQUEST_FIELDS = frozenset(
    {
        "offer",
        "source_url",
        "variant_scope",
        "valid_until",
        "affiliate_url",
        "target_channel",
        "permission_ref",
        "permitted_until",
    }
)


@dataclass(frozen=True)
class DealPackage:
    snapshot: CandidateSnapshot
    facts: dict[str, Any]
    payload: dict[str, Any]


class DealRepository:
    def __init__(self, store: SqliteOperatorStore, *, url_policy: UrlPolicy) -> None:
        self.store = store
        self.url_policy = url_policy
        self.vault = EvidenceVault(store)
        with store.transaction() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS deal_facts (facts_id TEXT PRIMARY "
                "KEY, facts_json TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS candidate_payloads (publication_id "
                "TEXT NOT NULL REFERENCES candidates(publication_id), "
                "draft_sha256 TEXT NOT NULL, facts_id TEXT NOT NULL REFERENCES "
                "deal_facts(facts_id), payload_json TEXT NOT NULL, PRIMARY "
                "KEY(publication_id, draft_sha256))"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS deal_rank_results (facts_id TEXT "
                "NOT NULL REFERENCES deal_facts(facts_id), rank_version TEXT "
                "NOT NULL, ranked_at TEXT NOT NULL, rank_json TEXT NOT NULL, "
                "PRIMARY KEY(facts_id, rank_version, "
                "ranked_at))"
            )
            for table in ("deal_facts", "candidate_payloads", "deal_rank_results"):
                for action in ("UPDATE", "DELETE"):
                    connection.execute(
                        f"CREATE TRIGGER IF NOT EXISTS {table}_immutable_{action} "
                        f"BEFORE {action} ON {table} "
                        "BEGIN SELECT RAISE(ABORT, 'immutable_facts_or_payload'); END"
                    )

    def save(
        self,
        facts: dict[str, Any],
        *,
        affiliate_url: str,
        target_channel: str,
        actor: str,
        now: datetime,
        publication_id: str | None = None,
        expected_revision: int | None = None,
        composer: GroundedComposer | None = None,
    ) -> DealPackage:
        actor = require_actor(actor)
        candidate, payload = render_candidate(
            facts,
            vault=self.vault,
            url_policy=self.url_policy,
            affiliate_url=affiliate_url,
            target_channel=target_channel,
            now=now,
            publication_id=publication_id,
            composer=composer,
        )
        validate_facts(facts)
        ranking = eligible_rank(facts, vault=self.vault, url_policy=self.url_policy, now=now)
        with self.store.transaction() as connection:
            previous = connection.execute(
                "SELECT facts_json FROM deal_facts WHERE facts_id=?", (facts["facts_id"],)
            ).fetchone()
            if previous is not None and previous["facts_json"] != canonical(facts):
                raise ValueError("facts_id_collision")
            connection.execute(
                "INSERT OR IGNORE INTO deal_facts VALUES (?, ?)",
                (facts["facts_id"], canonical(facts)),
            )
            connection.execute(
                "INSERT OR IGNORE INTO deal_rank_results VALUES (?, ?, ?, ?)",
                (
                    facts["facts_id"],
                    ranking["rank_version"],
                    ranking["ranked_at"],
                    canonical(ranking),
                ),
            )
        self.store.upsert_candidate(
            candidate, expected_revision=expected_revision, actor=actor, now=now
        )
        # Facts may remain orphaned after a conflict; they confer no approval/send authority.
        # Bind only to the exact immutable draft hash, never to a concurrently changed draft.
        with self.store.transaction() as connection:
            snapshot = self.store.get_snapshot(candidate["publication_id"])
            if snapshot is None or snapshot.candidate["draft_sha256"] != candidate["draft_sha256"]:
                raise RevisionConflict("draft_changed_before_payload_binding")
            old = connection.execute(
                (
                    "SELECT payload_json FROM candidate_payloads WHERE "
                    "publication_id=? AND draft_sha256=?"
                ),
                (candidate["publication_id"], candidate["draft_sha256"]),
            ).fetchone()
            if old is None:
                connection.execute(
                    "INSERT INTO candidate_payloads VALUES (?, ?, ?, ?)",
                    (
                        candidate["publication_id"],
                        candidate["draft_sha256"],
                        facts["facts_id"],
                        canonical(payload),
                    ),
                )
            else:
                # Same facts/content/renderer reuse the original immutable provenance record.
                payload = json.loads(old["payload_json"])
                validate_payload(payload, snapshot.candidate, facts, url_policy=self.url_policy)
        return DealPackage(snapshot, json.loads(canonical(facts)), payload)

    def get(self, publication_id: str, *, snapshot: CandidateSnapshot | None = None) -> DealPackage:
        current = snapshot if snapshot is not None else self.store.get_snapshot(publication_id)
        if current is None or current.candidate["publication_id"] != publication_id:
            raise KeyError(publication_id)
        with self.store._lock:
            row = self.store._conn.execute(
                (
                    "SELECT f.facts_json, p.payload_json FROM candidate_payloads p "
                    "JOIN deal_facts f USING(facts_id) WHERE p.publication_id=? "
                    "AND p.draft_sha256=?"
                ),
                (publication_id, current.candidate["draft_sha256"]),
            ).fetchone()
        if row is None:
            raise ValueError("draft_has_no_verified_facts_payload")
        facts, payload = json.loads(row["facts_json"]), json.loads(row["payload_json"])
        validate_payload(payload, current.candidate, facts, url_policy=self.url_policy)
        return DealPackage(current, facts, payload)

    def get_rankings(self, facts_id: str) -> list[dict[str, Any]]:
        with self.store._lock:
            rows = self.store._conn.execute(
                (
                    "SELECT rank_json FROM deal_rank_results WHERE facts_id=? "
                    "ORDER BY ranked_at DESC, rank_version"
                ),
                (facts_id,),
            ).fetchall()
        return [json.loads(row["rank_json"]) for row in rows]

    def import_manual(self, raw: bytes, *, actor: str, now: datetime) -> DealPackage:
        request = json_object(raw)
        if set(request) != _REQUEST_FIELDS:
            raise ValueError("manual_request_fields_invalid")
        offer = request["offer"]
        if (
            not isinstance(offer, dict)
            or not set(offer).issubset(_OFFER_FIELDS)
            or not (_OFFER_FIELDS - {"variant_id"}).issubset(offer)
        ):
            raise ValueError("caller_cannot_set_server_fields")
        if any(
            not isinstance(request[name], str)
            for name in (
                "source_url",
                "affiliate_url",
                "target_channel",
                "permission_ref",
                "permitted_until",
                "variant_scope",
            )
        ):
            raise ValueError("manual_request_types_invalid")
        source_url = self.url_policy.validate(request["source_url"])
        item = self.vault.retain(
            raw,
            source_url=source_url,
            actor=actor,
            permission_ref=request["permission_ref"],
            permitted_until=utc(request["permitted_until"]),
            now=now,
            url_policy=self.url_policy,
        )
        observation = {
            **offer,
            "schema_version": "offer-observation.v1",
            "observation_id": "obs-" + hashlib.sha256(raw).hexdigest()[:32],
            "source_method": "manual",
            "evidence": {
                "source_url": source_url,
                "fetched_at": iso(now),
                "payload_sha256": hashlib.sha256(raw).hexdigest(),
            },
        }
        facts = build_facts(
            observation,
            evidence_id=item["evidence_id"],
            actor=actor,
            variant_scope=request["variant_scope"],
            valid_until=utc(request["valid_until"]) if request["valid_until"] is not None else None,
            adapter_version="manual-record-v1",
        )
        return self.save(
            facts,
            affiliate_url=request["affiliate_url"],
            target_channel=request["target_channel"],
            actor=actor,
            now=now,
        )

    def preview_manual(self, raw: bytes, *, actor: str, now: datetime) -> dict[str, Any]:
        temporary = OperatorStore()
        try:
            preview = DealRepository(temporary, url_policy=self.url_policy)
            package = preview.import_manual(raw, actor=actor, now=now)
            decision = evaluate_eligibility(
                package.facts, vault=preview.vault, url_policy=self.url_policy, now=now
            )
            return {
                "candidate": package.snapshot.candidate,
                "facts": package.facts,
                "payload": package.payload,
                "eligible": decision.eligible,
                "expires_at": decision.expires_at,
            }
        finally:
            temporary.close()
