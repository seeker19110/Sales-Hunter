# Sales-Hunter × Đồng Hành: first integration slice

**State: source implementation, not deployed.** This slice provides a separately protected,
read-only operator view, not the complete approval/publishing UI. Main website integration
lives in `seeker19110/donghanh`; Sales runtime and data remain in this repository.

## What runs

- `s_n_sales.platform_web:create_app()` is a WSGI factory; no stdlib HTTP server exposure.
- Only `GET /`, `GET /dashboard` and minimal `GET /healthz` exist. Every other method is
  rejected; the dashboard additionally requires separate Basic credentials over HTTPS.
- Host is restricted to the configured Sales staging or production origin. The outer
  Cloudflare Access application must allow only the approved operator and be validated by
  cloudflared (`originRequest.access.required`). No Learning identity or database is read.
- The database is an existing, isolated, consistent Sales snapshot opened with `mode=ro`.
  The listing uses canonical prices and escaped excerpts, 50 records per page. Draft
  approval is not a publish receipt; historical prices are not advertised as current deals.

## Staging installation (operator execution required)

1. Accept ADR-0011 and review the exact diff. Check existing VPS CPU/RAM/disk before reuse.
2. Prepare a release checkout/artifact under `/opt/sales-hunter/releases/<commit>`.
   Run `uv sync --locked --no-dev`, then install the pinned deployment server:

   ```bash
   uv pip install --python .venv/bin/python -r deploy/platform-pilot/requirements.txt
   ```

   Resolve and retain the resulting dependency inventory and audit it; the deployment
   server is not part of the core uv.lock yet. Do not call this a locked production build.
3. Create a dedicated `sales-hunter` system account. Build a disposable Sales database
   with the existing local flow, then create a consistent snapshot using SQLite's Backup
   API. Keep the source database unchanged. Place the snapshot as the absolute path in
   `pilot.env.example`; ensure only the Sales account can read it. Never raw-copy a live
   WAL database. The service intentionally refuses to create a missing database.
4. Set `/opt/sales-hunter/current` to the reviewed release. Install the systemd unit and
   environment outside git. Generate a unique high-entropy operator token; do not paste
   it into URLs, commits or logs. The service has read-only filesystem restrictions.
5. Start locally. With Host `sales-staging.donghanhcungban.org`, `/healthz` must return
   `mode=read_only, live_publish=false`; `/dashboard` without credentials must return 401.
   Wrong Host must return 400; POST must return 405. Verify an authenticated empty/populated
   dashboard, XSS escaping, pagination and database hash unchanged after requests/restart.
6. Configure Access deny-by-default, authorized operator, tunnel credential and audience
   from the owning account; use `cloudflared.example.yml` as a TEMPLATE, not a ready secret.
   Check ingress rules and ensure no direct public port/origin bypass exists.
7. Only then configure staging DNS and validate HTTPS externally, unauthorized denial,
   authenticated display, logs, service restart and rollback. Record exact SHA/time/results.
8. Production hostname and DHCB launch flag remain off until the same checks are reviewed.
   Main DHCB entry uses `VITE_SALES_HUNTER_PILOT_ENABLED=true` only after this gate.

Basic credentials may be cached by the browser. Use a dedicated/private operator browser
session. To revoke access, revoke Access and rotate the Sales token; logging out of Learning
is not a Sales logout. There is no shared SSO session or end-user operator role in this slice.

## Rollback

Disable the DHCB launch flag and rebuild its frontend. Separately revoke the Access policy
or stop the pilot service to cut off existing access. Restore the previous release symlink
and restart; restore a verified snapshot rather than modifying history. Learning is never
part of this rollback. No automatic publishing process is started by the unit.

## Remaining gates

Human T4 review, deployment dependency lock/audit, VPS and Cloudflare permissions, actual
staging installation, external HTTPS/Access read-back, backup/restore drill and production
activation are NOT claimed complete. The current local approval workflow remains local;
full web forms, CSV ingestion, scoped payload decisions and live-provider integration are
separate work, not silently enabled by placing Sales under a DHCB subdomain.
