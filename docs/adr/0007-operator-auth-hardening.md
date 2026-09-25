# ADR-0007 — Fail-closed operator identity on loopback

- Status: proposed; T4 human review on exact PR HEAD required before merge.
- Date: 2026-09-25.
- Supersedes the query-token and optional-auth portions of ADR-0006 when accepted.

## Context

ADR-0006 allowed anonymous operation when a token was omitted and placed that token in browser URLs and forms. A request could also choose `decided_by`. The current `http.server` service is a local operator skeleton, without a production TLS, proxy, session or role boundary. SH-003 identifies these as blockers before any external bind.

## Decision

1. Protected operation requires a configured token. `/healthz` remains public. Anonymous local operation is an explicit test/development choice and is forbidden for a non-loopback bind.
2. API requests send a bearer token only in `Authorization`. Query and form credentials have no authority. Approval actor comes from server configuration, never from request JSON or a form field.
3. The loopback dashboard exchanges a token in a POST body for an opaque, random, process-local session. A cookie uses `HttpOnly`, `SameSite=Strict`, and `Path=/dashboard`; sessions expire and logout invalidates them. All state-changing dashboard forms require a session-bound CSRF value. Login and approval responses do not include credentials in URLs, pages or redirects.
4. The stdlib server refuses a non-loopback bind, even with a configured token. External use requires a later production-server/TLS and identity ADR with a reviewed role model, session store, secret rotation and trusted proxy configuration. No forwarding-header-based exception is implicit.
5. One configured principal has reviewer authority in this local stage. The API and browser share that principal; a future viewer/reviewer/admin mapping must be reviewed before external staging. This decision does not assert SH-003 is completely resolved for production.

## Acceptance and rollout

- Tests cover missing/wrong bearer, URL/form token rejection, forged actor, logout/expiration, missing/wrong CSRF, cookie flags and refusal to bind outside loopback.
- Existing tests and browser smoke opt into anonymous loopback explicitly or use a configured identity; they cannot silently fall back to open mode.
- CLI reads the secret from `OPERATOR_TOKEN` and never accepts it in `argv` or prints it. No real credential is written to the repository.
- No network platform integration, public deployment or live publishing is authorized. Before external staging, complete identity/roles and production HTTP controls under a separate reviewed decision.

## Consequences

The dashboard's old `?token=` links stop working. Sessions are invalidated on restart. A token typed into the local dashboard travels only to the loopback service; an external origin remains unsupported until TLS and a production server exist.
