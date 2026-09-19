# ROADMAP — Sales-Hunter

Trạng thái: **skeleton Phase 0–6 đã merge vào `bootstrap/base`**. Các checkbox còn mở dưới đây là năng lực vận hành/production, không phải trạng thái merge code. Xem [PROJECT-STATUS](../PROJECT-STATUS.md) để có checkpoint thực thi hiện tại.

Đặc tả chi tiết từng phase: **[PHASES.md](PHASES.md)**.  
Triển khai kỹ thuật: `docs/impl/PHASE-*-IMPLEMENTATION.md`.  
**Vận hành agent (bắt buộc):** mọi phase/việc lớn phải tách **subtask** + gán **`model_tier` T0–T4** theo [SUBAGENT-TASK-CONVENTION.md](SUBAGENT-TASK-CONVENTION.md).

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
- [x] Publication-candidate builder đầy đủ (disclosure + draft_sha256) → Phase 1.5
- [ ] mypy strict (tuỳ chọn)

## Phase 1.5 — Content draft đầy đủ

- [x] Tách subtask theo convention (xem impl + task-pack 0003)
- [x] Builder `publication-candidate.v1` hoàn chỉnh
- [x] `claim_snapshot` + `draft_sha256` deterministic
- [x] Template disclosure affiliate bắt buộc
- [x] Contract test

## Phase 2 — Adapter + nguồn hợp pháp

- [ ] Tách subtask; ADR/ToS = **T4 + human** trước code mạng
- [ ] ADR ToS + allowlist domain + rate limit
- [ ] Cập nhật `GIA-DINH-NEN-TANG.md` (xác minh nguồn)
- [x] Manual pipeline chất lượng cao → observation do operator cung cấp
- [x] Contract test + kill switch cho manual adapter
- [x] End-to-end manual observation → rank → publication-candidate

## Phase 3 — Approval + Publisher

- [ ] Tách subtask; publish path = **T4**
- [x] Lưu `approval-record.v1` in-memory (hash-bound)
- [x] Publisher idempotent + read-back fake `publish-receipt.v1`
- [x] Kill switch nền tảng + toàn hệ thống
- [x] Dry-run mặc định

## Phase 4 — Staging + Operator UI

- [x] Tách subtask (API / UI / datastore / deploy theo ADR-0006)
- [x] HTTP service tối thiểu (operator API + Web Dashboard)
- [x] Dashboard duyệt draft (approve/reject, claim snapshot, disclosure)
- [x] SQLite persistent datastore (`SqliteOperatorStore`) + Token Auth
- [ ] Deploy staging `sales.donghanhcungban.org` theo checklist
- [ ] HTTPS + health check origin ngoài

## Phase 5 — Analytics + Feedback loop

- [ ] Tách subtask
- [ ] Tracking click / conversion cơ bản
- [x] Metric skeleton tách “không có sale” vs “không thu thập được”
- [ ] Cải thiện ranking qua `rank_version` mới, dựa trên dữ liệu thật
- [x] Quy trình thu hồi nội dung khi deal hết hạn

## Phase 6 — Production + Scale

- [ ] Tách subtask; production cutover = **T4 + human**
- [ ] ADR auth/SSO (nếu cần)
- [x] Runbook + production checklist skeleton
- [ ] Production deploy + monitoring
- [ ] Thêm adapter thứ hai (TikTok Shop) chỉ sau khi Shopee ổn định
- [ ] Multi-channel publish theo cùng quy trình approval

---

**Ghi chú chiến lược:** Ưu tiên chứng minh **một vòng kín hợp pháp** (Shopee + human approval) trước khi mở rộng nền tảng hoặc bật auto-publish.
