# SH-007 — candidate approval projection

- branching: A; parent_branch: `fix/audit-candidate-projection-2026-09-25`; target `bootstrap/base`.
- baseline: `683683710dd0de99857912487d4b2d5341f05c0e`.
- side effects: repository/PR/CI only; no network, publishing or deploy.

| subtask_id | tier | paths | acceptance |
|---|---|---|---|
| PROJ-RED | T1 | `tests/test_sqlite_store.py`, `tests/test_operator_api.py` | validate candidate contract after create/approve/reject/reload and API; errors reproduce old nested full approval record |
| PROJ-FIX | T2 | `src/s_n_sales/api/store_sqlite.py` | nested approval projection uses only v1 candidate fields; full approval record stays in approvals table/API; no schema or DB migration |
| PROJ-HANDOFF | T1 | `CHANGELOG.md`, `PROJECT-STATUS.md`, `docs/sessions/` | CI evidence, no production claim, progress accurate |

The nested candidate approval and standalone approval record have different existing v1 contracts. This fix does not redefine either contract, add revision history or change publisher authority. Check both persisted/reloaded data and HTTP responses. Keep publisher dry-run by default.
