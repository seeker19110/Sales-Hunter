# ADR-0004 — Production cutover (dry-run publish mặc định)

- **Trạng thái:** Đề xuất (T4 — chờ người duyệt)
- **Ngày:** 2026-09-11
- **Phase:** 6

## Bối cảnh

Đã có vòng kín code: manual observation → rank → publication-candidate → approval → publisher (fake client) → operator API → analytics skeleton.
Chưa có client publish mạng thật, chưa xác minh official API Shopee/TikTok.

## Quyết định

1. Production **được phép** chạy operator API + manual pipeline khi checklist `PRODUCTION-CHECKLIST.md` đạt.
2. **Publish thật** vẫn tắt mặc định (`dry_run=True`) cho đến khi có ADR client kênh + owner bật config tường minh.
3. Multi-channel: cùng approval + cùng `draft_sha256`; mỗi kênh idempotency_key riêng (`…:{channel}:{hash}`).
4. Adapter thứ hai (TikTok Shop) chỉ sau khi manual/Shopee path ổn định ≥ 2 tuần (checklist).
5. Auth/SSO: trì hoãn; API staging bind localhost / mạng tin cậy cho đến ADR auth riêng.

## Hệ quả

- Domain online ≠ quyền auto-publish.
- Giảm rủi ro ToS bằng manual-first + human approval.

## Kiểm chứng

- Unittest publisher dry-run + multi-channel helper
- Diễn tập kill switch theo RUNBOOK
