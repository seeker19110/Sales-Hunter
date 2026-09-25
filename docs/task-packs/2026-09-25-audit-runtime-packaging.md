# SH-004 — runtime artifact epic

- branching: A; one sequential integrator, no subagents available in this session.
- parent_branch: `fix/audit-runtime-packaging-2026-09-25`; target `bootstrap/base`.
- baseline: `d17d33eae7230aeccc56047db5dd48bf35cdcb1d`; no open PRs at start.
- Prior #35 is audit documentation, not implementation. Historical evidence stays unchanged.
- side-effect scope: repository branch/PR/CI only; no live publishing, secrets or deployment.

| subtask_id | model_tier | dependency | goal and allowed paths | acceptance |
|---|---|---|---|---|
| PKG-RED | T1 | none | tests/test_runtime_packaging.py, tools/runtime_smoke.py | missing runtime dependency/resources fail with specific evidence |
| PKG-CI | T2 | PKG-RED | .github/workflows/ci.yml | immutable sdist/wheel + hash-pinned runtime install; artifact is required by quality |
| PKG-FIX | T2 | PKG-RED | pyproject.toml, uv.lock, package schema resources, pipeline schema loading | validation/candidate/approval/dry-run/fake receipt outside checkout without dev dependencies |
| PKG-HANDOFF | T1 | PKG-FIX | CHANGELOG.md, PROJECT-STATUS.md, CODEMAP.md, docs/sessions/ | current HEAD checks, diff review, checkpoint and honest verification limits |

Forbidden: schema semantics, approval/publish decisions, API/auth, database changes, original audit evidence, branch protection and secret permissions. Packaging copies of schemas must match root contracts byte-for-byte in discovery tests; runtime uses only package resources. No architecture/schema contract change.

Baseline CI: run 36119757744 success on baseline. Container Python 3.13.5/uv 0.10.0/git available; gh absent; git ls-remote exits 128 (DNS resolution unavailable). Local locked sync/full suite not claimed. Remote CI is the authoritative complete environment; local reconstructed-file checks are reported separately. Full branch-protection read returns 403; branch summary confirms required quality/metadata for everyone. No bypass.

Rollback: revert this epic via PR; no data migration. PR remains draft during red/green cycle. Auto-merge only after exact HEAD checks and non-GitHub gates are satisfied.
