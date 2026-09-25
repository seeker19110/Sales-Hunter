# Audit execution matrix — 25/09/2026

Historical audit is immutable. This is implementation status, not proof of production readiness. Base verified: `0fea06578b04b832c07df6b31c60444510d25c79`. Read GitHub for PR changes after this checkpoint.

## Evidence registry

| Key | PR / branch | HEAD | CI | Merge / gate | Evidence |
|---|---|---|---|---|---|
| UI | #37 | aedba6c5e9574290e40b72e8e0e6087c49b35c8a | 36139653615 success; metadata 36139653640 success; post-merge 36140091351 success | merged 2522c4db9e168865957d128cab1e597dbb41abb4 | 82 tests, real Chrome mobile list/detail from builder+SQLite; tree verified |
| PKG | #36 | dae66501b8d1fdec4ce6d26194385c5682d9c26c | quality, artifact and matrix success | merged a61cffe5d95e335614375d35037cdd010e7e5fc6 | runtime dependency and five package schemas, clean wheel smoke outside checkout |
| INT | #38 | 9d8c290a75640b45c27f7b82822c90270da6adad | quality, artifact, browser and matrix success | human T4 reviewed exact HEAD; merged 683683710dd0de99857912487d4b2d5341f05c0e | 16 integrity regressions, trusted approval authority and UTC; partial SH-002/023 |
| PROJ | #40 | 6b5d50ce8633d65aaf59063a8644a768609179fb | quality, artifact, browser and matrix success | merged 0fea06578b04b832c07df6b31c60444510d25c79 | candidate nested approval v1 projection and legacy readback; 104 local tests |
| AUTH | fix/audit-operator-auth-2026-09-25 | see PR HEAD | CI pending | T4 human review required | local-only fail-closed auth/session/CSRF; no external identity or deployment |
| NONE | none | none | not run | not started | audit/code inspection is not implementation acceptance |

## Item matrix

Each evidence key resolves PR, HEAD, CI, merge and verification limits above. “Partial” never means closed. Dependencies name the missing acceptance work, not permission to skip it.

| ID | Current status / implemented scope | Dependencies / acceptance still required | Evidence |
|---|---|---|---|
| SH-001 | Merged, CI verified: recompute all five protected fields at both stores, approve and publish; freeze candidate | immutable revision/CAS in SH-008/009 | INT |
| SH-002 | Partial merged: full approval contract; configured authority; reject missing/forged/currently rejected records and cached receipt after reject/restart | SH-003 external identity/roles; SH-008/009 revision/history; SH-011 final payload/channel scope | INT |
| SH-003 | PR #39: local auth fail-closed, Bearer API, dashboard session/CSRF, server actor and loopback-only bind | CI on updated HEAD and T4 review/merge; production identity/roles, TLS/server and external staging decision | AUTH |
| SH-004 | Merged, CI verified: runtime dependencies, package resources and clean wheel outside checkout | External deployment remains separate | PKG |
| SH-005 | Not started: RAM idempotency remains | Durable intent/outbox, unique key, leases, attempts, finite retry, unknown-outcome reconciliation; restart/concurrency/crash tests; T4 | NONE |
| SH-006 | Partial: hash integrity now checked on ingest; caller/server DTO separation NOT done | Reject caller-owned approval/hash metadata; full candidate input schema and stable API errors | INT |
| SH-007 | Merged #40, CI verified: SQLite writes and reads five-field candidate approval projection; standalone approval remains full; legacy nested records projected on read | Revision/history remain SH-008/009 | PROJ |
| SH-008 | Not started: current authority lookup is NOT revision CAS | Atomic update/approve expected-revision transaction; controlled race tests on selected production database | NONE |
| SH-009 | Partial: current rejection rechecked before send; history still overwritten | Append-only approval/revision events, transactional invalidation and consistent projections | INT |
| SH-010 | Merged and CI verified: canonical integer VND, platform, null/zero/large values, mobile display | No production claim; full inbox workflow remains SH-024 | UI |
| SH-011 | Not started: platform client still sends content only | Deterministic final payload/link/disclosure/capability hash; exact preview/approval/sent equivalence; T4 | NONE |
| SH-012 | Not started: no final freshness/stock revalidation | Provider capability and timestamp policy; stale/future/stock/expiry pre-send tests | NONE |
| SH-013 | Not started: eligibility still mixed with ranking | Explicit blocking policy independent of score; stale/out-of-stock/coupon eligibility tests | NONE |
| SH-014 | Not started: claim snapshot incomplete | Versioned product/shop/variant/prices/coupon/shipping/eligibility/evidence contract; ADR/migration and boundary fixtures | NONE |
| SH-015 | Not started: URL validation remains scheme-only | Configured allowlist/host/redirect validation; SSRF controls at actual fetch boundary; malformed URL tests | NONE |
| SH-016 | Merged, CI verified: publisher normalizes aware clock before client/receipt; fake provider uses UTC | No real provider timestamp evidence | INT |
| SH-017 | Not started: pause flags still transient | Persistent global/source/channel actor/reason/time; restart and pre-retry/pre-send checks | NONE |
| SH-018 | Not started: stdlib HTTP not production server | Accepted server/framework ADR, time/body limits, Host/Origin/UTF-8/JSON tests, readiness | NONE |
| SH-019 | Not started: analytics skeleton only | Durable event IDs, signature/replay policy by actual provider, conversion lifecycle and commission ledger/reconciliation | NONE |
| SH-020 | Not started: CD still placeholder | SHA artifact/promote, real doctor/migrate/pause/reconcile/export/backup/restore drill, health/heartbeat/runbook; no production cutover authorized | NONE |
| SH-021 | Partial status accuracy: known PR35 docs versus PR37 code separated | Accepted architecture/database/server decisions, tested rollback/restore and current operational docs | UI / INT |
| SH-022 | Not started: no official account capability verified | Program/region/scope/quota/policy/owner evidence; disabled connector until authorized; manual/fake contracts do not prove live | NONE |
| SH-023 | Partial local verified: validate all channels and global integrity/current approval before first send | Durable per-channel outcome/unknown read-back/reconcile, final payload scope; T4 | INT |
| SH-024 | Partial: mobile list/detail monetary read model and real-browser gate only | Form/CSV preview, search/filter/pagination, evidence/revision/final payload preview, RBAC-aware bulk approval and E2E actions | UI |
| SH-025 | Not started: digest is not retained raw evidence | Permissioned immutable redacted evidence, versions/hash/retention/export, tamper and retrieval tests | NONE |
| SH-026 | Partial: shared typed price read model and protected-value checks | Typed caller/server DTOs throughout API, store, renderer and publisher; bool/float/null/malformed boundary tests | UI / INT |
| SH-027 | Not started: business dedup/cooldown/history absent | Product+variant+condition keys, persisted cooldown, exact historical claims and duplicate/restart tests | NONE |

AI grounded content: not implemented. Deterministic facts/template baseline, numeric/link/disclosure/schema validator, model configuration, bounded costs/cache and Vietnamese adversarial evaluation remain required; no paid benchmark has run.

Source: partial implementation. Staging: not verified/deployed. Production: not deployed, no external publishing/credential/DNS changes. AUTH requires human T4 review; previous INT review and merge do not authorize it. Unimplemented items above are not mislabeled as external blockers.
