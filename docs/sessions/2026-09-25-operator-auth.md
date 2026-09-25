# SH-003 local operator authentication — handoff

- Base `683683710dd0de99857912487d4b2d5341f05c0e`, after PR #36/#37/#38 merge.
- Branch `fix/audit-operator-auth-2026-09-25`, task pack `2026-09-25-operator-auth.md`, ADR-0007 proposed. AUTH-RED T1 → AUTH-DECISION T4 → AUTH-IMPL T4 → AUTH-REGRESSION T2 → AUTH-HANDOFF T1.
- Security regression tests preceded implementation. Default missing token fails closed; API uses bearer only; dashboard POST login establishes opaque process-local session with CSRF and logout; actor is configured server-side. Local anonymous mode is explicit and loopback-only. No token printed in CLI URL/argv.
- Container: `compileall`, `uv lock --check --offline`, `git diff --check` available. Complete locked suite unavailable locally because package downloads are blocked; exact HEAD CI must establish acceptance. Do not call local syntax checks an integration pass.
- No remote bind, TLS, production server, multi-user roles, persistent session, platform network client, deployment or live publish. External operator staging and SH-003 production closure remain blocked on reviewed identity/server decision and evidence.
- T4 human review is required on exact HEAD before merge; prior approval for PR #38 is scoped to its HEAD only.
