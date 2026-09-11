# ROADMAP — S-N Sales

Trạng thái: **Phase 0 xong** · **Phase 0.5 ADR platform** · **Phase 1 domain core (code)** · **Phase 1.5 đang mở**.

Đặc tả chi tiết từng phase: **[PHASES.md](PHASES.md)**.

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
- [ ] Publication-candidate builder đầy đủ (disclosure + draft_sha256) → chuyển sang Phase 1.5
- [ ] mypy strict (tuỳ chọn)

## Phase 1.5 — Content draft đầy đủ

- [ ] Builder `publication-candidate.v1` hoàn chỉnh
- [ ] `claim_snapshot` + `draft_sha256` deterministic
- [ ] Template disclosure affiliate bắt buộc
- [ ] Contract test + cập nhật HOP-DONG-DU-LIEU nếu cần

## Phase 2 — Adapter + nguồn hợp pháp

- [ ] ADR ToS + allowlist domain + rate limit
- [ ] Cập nhật `GIA-DINH-NEN-TANG.md` (xác minh nguồn)
- [ ] Adapter Shopee (hoặc manual pipeline chất lượng cao) → observation thật
- [ ] Contract test + kill switch theo adapter
- [ ] End-to-end observation → rank → publication-candidate với dữ liệu thật

## Phase 3 — Approval + Publisher

- [ ] Lưu `approval-record.v1` (hash-bound)
- [ ] Publisher idempotent + read-back `publish-receipt.v1`
- [ ] Kill switch nền tảng + toàn hệ thống
- [ ] Dry-run mặc định

## Phase 4 — Staging + Operator UI

- [ ] HTTP service tối thiểu
- [ ] Dashboard duyệt draft (approve/reject)
- [ ] Deploy staging `sales.donghanhcungban.org` theo checklist
- [ ] HTTPS + health check

## Phase 5 — Analytics + Feedback loop

- [ ] Tracking click / conversion cơ bản
- [ ] Metric tách “không có sale” vs “không thu thập được”
- [ ] Cải thiện ranking qua `rank_version` mới
- [ ] Quy trình thu hồi nội dung khi deal hết hạn

## Phase 6 — Production + Scale

- [ ] ADR auth/SSO (nếu cần)
- [ ] Production deploy + monitoring + runbook
- [ ] Thêm adapter thứ hai (TikTok Shop) chỉ sau khi Shopee ổn định
- [ ] Multi-channel publish theo cùng quy trình approval

---

**Ghi chú chiến lược:** Ưu tiên chứng minh **một vòng kín hợp pháp** (Shopee + human approval) trước khi mở rộng nền tảng hoặc bật auto-publish.
