# ADR-0011: read-only Sales pilot in the DHCB platform

- Status: Proposed — human T4 review required on the exact PR diff.
- Date: 2026-09-26
- Parent: [ADR-0002](0002-platform-subdomain-dhcb.md).

## Scope

Provide a separately authenticated read-only web view at the Sales subdomain without
exposing the existing loopback-only stdlib operator API. This is the first integration
slice, not a complete production operator workflow or SSO rollout. No approval, ingestion,
publication, export or mutation endpoint exists in the new WSGI application.

## Boundary

Gunicorn serves a WSGI app on loopback. A separately configured Cloudflare Tunnel must
validate Access tokens before forwarding. The app additionally checks the exact configured
Sales Host and separate operator Basic authentication. HTTPS is mandatory at the edge;
Basic authentication is never intended for public plaintext HTTP. No forwarded identity,
Learning cookie, billing token, shared data or end-user role grants access to Sales.

The read-only SQLite URI refuses missing databases and never runs migrations. Initial
staging uses a consistent snapshot from a disposable Sales database; do not point this
service at Learning. Snapshot refresh is an explicit operator action, so this view does
not claim real-time freshness or platform-confirmed publication. The startup and health
checks detect unreadable/invalid candidate data in the first page. The view is noindex
and no-store. It is not an audit of every row or proof that a deal is still available.

## Deployment gates and rollback

No deployment or DNS update is performed by this change. Use the
[pilot runbook](../PLATFORM-PILOT.md), retain version/artifact SHA, review dependency audit,
verify deny-by-default Access and HTTPS from outside, test restart and rollback, then
consider enabling the independent DHCB frontend launch flag. Turning off that flag does
not revoke existing Sales access; revoke Access and stop the Sales service separately.
Full operator mutations, session SSO and live publication require separate reviewed work.
