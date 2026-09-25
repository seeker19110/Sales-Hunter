# Audit integrity and current-approval epic

- branching: A; parent_branch: `fix/audit-integrity-2026-09-25`; target: `bootstrap/base`.
- Base: `2522c4db9e168865957d128cab1e597dbb41abb4`, tree `b09885f273fbb634382583c5dcffd6f231759344`. Local reconstructed tree matches exactly; local snapshot commit IDs are NOT upstream ancestry.
- No subagents are available; one sequential integrator. No network client, account change, secret or production operation.
- T4 human review required before merge. Never arm auto-merge from this task pack alone.

| subtask_id | model_tier | dependency | allowed files | acceptance |
|---|---|---|---|---|
| INT-RED | T1 | none | tests/test_integrity_boundaries.py | reproduce protected-value tamper, incomplete approval, UTC and global preflight |
| INT-HASH | T3 | INT-RED | pipeline/publication.py, approval.py; api/store.py, store_sqlite.py | recompute all five ADR-0005 fields on ingest/approve/publish; reject noncanonical JSON |
| INT-AUTHORITY | T4 | INT-HASH | pipeline/publisher.py, multi_channel.py; existing publisher/API/multichannel tests | no send without configured approval authority; reject forged/currently rejected records even after restart or cached receipt |
| INT-FREEZE-UTC | T4 | INT-AUTHORITY | same publisher files | isolate caller mutation across client call, UTC before serialization, validate all channel names before any client call |
| INT-HANDOFF | T1 | previous subtasks | CHANGELOG, PROJECT-STATUS, CODEMAP, session, execution matrix | exact HEAD CI and diff review; keep pending human review |

Forbidden: auth HTTP routes, schema meaning, database layout/migrations, framework, provider endpoints, original audit evidence, CI rules/permissions, dependency/lockfile and production deployment. Approval source is server-configured through `Publisher(approval_source=store)`, never taken from request JSON. Dry-run still cannot contact the client; a successful send always requires the authority.

ADR-0005's five-field channel-agnostic hash is unchanged. This is a bug fix inside that accepted boundary, NOT approval of new per-channel rendered-payload semantics. No new schema/architecture ADR is claimed accepted.

Remaining: identity/roles and CSRF, immutable revision/CAS/history, final payload/channel approval scope, durable outbox/unknown outcome and pause. A trusted current-record lookup is not a transaction spanning a remote network call. The existing manual HTTP identity remains unsuitable for external deployment.

Tests: 12 initial regressions produce 31 failed assertions on baseline, then pass. Four additional authority regressions fail while the authority field is present but not enforced, then pass after enforcement. Final diagnostic: Python3.13.5, `PYTHONPATH=src python -m unittest discover -s tests -v`: 98 tests, exit0. Locked quality/format/type/security/browser checks must pass on GitHub before review. Local DNS/Chrome-policy restrictions remain; do not call local diagnostics full locked acceptance.

Rollback: revert epic through PR. No data migration. Applications intentionally must configure approval_source before any non-dry-run call. Existing API integration test uses its actual SQLite store; domain tests use OperatorStore. No fake transport result is live evidence.
