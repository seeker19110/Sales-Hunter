# SH-003 — operator authentication hardening

- branching: A; parent_branch: `fix/audit-operator-auth-2026-09-25`; target: `bootstrap/base`.
- baseline: `683683710dd0de99857912487d4b2d5341f05c0e` after PR #38.
- side effects: branch/PR/CI only; no external bind, credentials, deployment or public posting.
- T4 human review on exact HEAD before merge; no general approval carries over.

| subtask_id | tier | paths | acceptance |
|---|---|---|---|
| AUTH-RED | T1 | `tests/test_operator_auth_security.py` | unauthenticated API/dashboard, query/form token, forged actor, missing CSRF, invalid session and remote bind tests fail for expected reasons |
| AUTH-DECISION | T4 | `docs/adr/0007-operator-auth-hardening.md` | decision explains principal, session/CSRF, fail-closed, loopback-only service, migration from ADR-0006 |
| AUTH-IMPL | T4 | `src/s_n_sales/api/app.py`, `src/s_n_sales/api/__main__.py` | Bearer API, server-owned actor, local dashboard session with CSRF, no URL/form token; missing auth fails closed; remote bind refused |
| AUTH-REGRESSION | T2 | `tests/test_operator_api.py`, `tools/browser_dashboard_smoke.py`, `tests/test_operator_auth_security.py` | existing workflows use explicit local test mode, real browser gate, security regressions green |
| AUTH-HANDOFF | T1 | `CHANGELOG.md`, `PROJECT-STATUS.md`, `CODEMAP.md`, `docs/sessions/` | precise CI/HEAD evidence, T4 review scope and remaining limits |

Explicit unauthenticated local mode is only for deterministic tests or trusted development; it cannot bind outside loopback. Protected mode requires a configured secret. This epic does not add a public production HTTP server, SSO or external deployment. Publisher remains dry-run.
