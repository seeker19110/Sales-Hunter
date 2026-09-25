# SH-007 — candidate schema after approval

- Baseline `683683710dd0de99857912487d4b2d5341f05c0e`; branch `fix/audit-candidate-projection-2026-09-25`.
- PROJ-RED T1: tests failed on extra `schema_version`, `approval_id`, `publication_id` and `policy_version` in nested candidate approval after approve/reject and HTTP readback.
- PROJ-FIX T2: SQLite writes only five existing candidate approval fields; reads project legacy full nested approval without changing stored standalone approval records.
- PROJ-HANDOFF T1: 26 focused tests, Ruff lint/format and Pyright passed locally. Full locked suite, browser and artifact gate remain CI acceptance on exact HEAD.
- No schema version change, database migration, revision CAS, approval event history or live publishing. SH-008/009 remain open.
