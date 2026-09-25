# SH-010 — operator price/read-model epic

- branching: A; parent_branch: `fix/audit-dashboard-prices-2026-09-25`; target: `bootstrap/base`.
- Baseline: d17d33eae7230aeccc56047db5dd48bf35cdcb1d. Independent of PR #36.
- One integrator, sequential subtasks, no real subagents. External side effects: none.

| subtask_id | model_tier | dependency | allowed files / goal | acceptance |
|---|---|---|---|---|
| UI-RED | T1 | none | tests/test_dashboard_prices.py | real builder -> renderer catches wrong fields, null, zero, large integers |
| UI-VIEW | T2 | UI-RED | api/read_model.py, display sections only in api/app.py | same typed view in list/detail, integer half-up percentage, unknown explicit |
| UI-BROWSER | T2 | UI-VIEW | tools/browser_dashboard_smoke.py, tools/browser/dashboard.mjs, CI | builder -> SQLite -> HTTP -> actual Chrome; 390x844, exact row amounts, disclosure, no executable source script; gate required by quality |
| UI-CHECKPOINT | T1 | UI-BROWSER | CHANGELOG, CODEMAP, PROJECT-STATUS, session | exact HEAD CI and review before normal merge |

Forbidden: API/auth/approval semantics, source schemas, DB layout, publisher, secret, original audit evidence. No framework/architecture migration. Node 22+ built-in WebSocket controls Chrome only in acceptance tooling; application remains Python. Browser absence/failure is hard failure, not skip. New job contents:read, no expanded write permission.

Evidence: local Python 3.13.5/PYTHONPATH diagnostic, seven tests initially failed (wrong price fields/malformed snapshot); final 82 tests including original 75 pass. Expected 9.93% is half-up calculation, not truncation. Unknown-discount assertion targets HTML values rather than CSS width:100%. Local Chromium144 starts, but loopback navigation is ERR_BLOCKED_BY_ADMINISTRATOR; this is not a passing E2E. GitHub CI is required for the locked suite, static/type/security, and actual browser result.

Rollback: revert epic through a PR, no migration/data changes. Does not close SH-024 full inbox/import/bulk workflow or SH-026 all DTO boundaries. Full identity and publishing acceptance remain independent blockers.
