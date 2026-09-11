# ROADMAP — S-N Sales

Trạng thái: **Phase 0 xong** · **Phase 0.5 ADR platform** · **Phase 1 domain core (code)** trên nhánh feature.

## Phase 0 — Khung vận hành

- [x] Luật repo, schema observation/publication, CI cơ bản

## Phase 0.5 — Platform DHCB

- [x] ADR-0002 subdomain `sales.donghanhcungban.org`
- [x] `docs/PLATFORM.md`

## Phase 1 — Domain core + ranking

- [x] `Money` value object
- [x] Ranking deterministic + `rank-result.v1`
- [x] Skeleton `src/s_n_sales/`
- [x] Fake fixture loader + pipeline observation → rank
- [ ] Publication-candidate builder đầy đủ (disclosure + draft_sha256) — tiếp
- [ ] mypy strict (tuỳ chọn)

## Phase 2 — Adapter official API

- [ ] ADR ToS + allowlist domain
- [ ] Shopee / TikTok adapters (chỉ nguồn chính thức)

## Phase 3 — Approval + Publisher

- [ ] Human approval + publish receipt read-back

## Phase 4 — Staging subdomain

- [ ] Deploy staging `sales.donghanhcungban.org`

## Phase 5 — Production + SSO

- [ ] ADR auth/SSO + production
