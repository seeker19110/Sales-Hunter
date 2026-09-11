# ROADMAP — S-N Sales

Trạng thái hiện tại: **Phase 0 hoàn thành** (khung vận hành + schema v1 quan sát/bản nháp).

## Phase 0 — Khung vận hành (đã xong)

- [x] Luật repo (`AGENTS.md`), kiến trúc, codemap, traps
- [x] Schema `offer-observation.v1` + `publication-candidate.v1`
- [x] CI (ruff, unittest, validate_repo, gitleaks)
- [x] Task pack / prompt sheet / quy trình Git

## Phase 1 — Domain core + ranking deterministic (đặc tả này)

Mục tiêu: có domain value object và pipeline xếp hạng xác định, vẫn **không** kết nối API thật.

- [ ] Value object `Money` (amount_minor + currency, không float)
- [ ] Domain service ranking deterministic + version hóa trọng số
- [ ] Schema `rank-result.v1`, `approval-record.v1`, `publish-receipt.v1`
- [ ] Skeleton `src/s_n_sales/` (adapters interface, domain, services)
- [ ] Fake/file-based adapter đọc fixture → full draft pipeline
- [ ] Contract test + property test cho money & ranking invariants
- [ ] Cổng `ruff format --check` + (tuỳ chọn) mypy strict

**Nghiệm thu Phase 1:**
- `make check` xanh
- Có thể chạy pipeline từ fixture observation → ranked → publication-candidate (draft) mà không cần mạng
- Mọi số tiền đi qua `Money`; ranking trả `rank-result.v1` có lý do giải thích được

## Phase 2 — Adapter thật (chỉ nguồn chính thức)

- [ ] ADR cho phép adapter Shopee / TikTok Shop (dẫn ToS + ngày kiểm chứng)
- [ ] Allowlist domain + redirect validation
- [ ] Rate limit, quota, dead-letter
- [ ] Lưu raw observation append-only + evidence hash

## Phase 3 — Approval + Publisher

- [ ] Luồng human approval gắn `draft_sha256`
- [ ] Publisher idempotent + read-back receipt
- [ ] Kill switch theo nền tảng và toàn hệ thống
- [ ] Analytics nhận conversion có attribution nguồn

## Phase 4 — Auto-publish (chỉ sau ADR riêng)

- [ ] ADR nêu phạm vi, cơ chế dừng, audit
- [ ] Dry-run mặc định; bật auto chỉ khi kill switch sẵn sàng

---

Mỗi phase kết thúc bằng session log trong `docs/sessions/` và cập nhật CHANGELOG.
