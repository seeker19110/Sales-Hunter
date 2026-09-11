# Đặc tả triển khai chi tiết — Phase 6 (Production + Scale)

**Trạng thái:** Chưa bắt đầu.  
**Phụ thuộc:** Phase 5 + staging ổn định ≥ thời gian quan sát.

---

## 1. Mục tiêu

- Chạy **production** ổn định tại `sales.donghanhcungban.org`.
- Monitoring, alerting, runbook sự cố.
- Kill switch production đã kiểm chứng.
- Mở thêm kênh / adapter thứ hai **chỉ sau** khi Shopee (hoặc nguồn chính) ổn.
- Auth/SSO nếu cần gắn hub DHCB (ADR riêng).

---

## 2. Phạm vi được làm

| Thành phần | Mô tả |
|------------|--------|
| Production deploy | DNS/TLS production, rollback, backup |
| Monitoring | Health, error rate, publish fail, quota |
| Alerting | Kênh thông báo operator (Telegram/email…) |
| Runbook | Khóa tài khoản, deal sai, rate limit, thu hồi |
| SSO / auth | ADR + implement nếu chia sẻ identity hub |
| Adapter #2 | TikTok Shop (sau xác minh GIA-DINH + ADR) |
| Multi-channel | Thêm publisher channel theo cùng approval flow |
| Tài liệu vận hành | Operator guide |

## 3. Phạm vi **không** được làm vội

- Auto-publish toàn bộ không người duyệt (trừ khi ADR riêng + kill switch + quan sát đủ lâu).
- Microservices tách sớm khi monolith còn chịu tải.

---

## 4. Thiết kế & checklist production

### 4.1. Trước khi bật production traffic

- [ ] Staging chạy ổn (thời gian tối thiểu do owner quyết định).
- [ ] Kill switch đã test (tắt adapter / publisher thật).
- [ ] Backup store (approval, receipt, config).
- [ ] Secret chỉ trong secret manager.
- [ ] Rollback plan (artifact trước + DNS).
- [ ] Runbook sự cố bản nháp đã review.

### 4.2. Monitoring tối thiểu

- `/healthz` + uptime check.
- Số publish failed / rate limit hit.
- Hàng đợi dead-letter (nếu có).
- Disk/memory nếu self-host.

### 4.3. Thêm nền tảng mới

Mọi nền tảng mới lặp lại quy trình Phase 2:

1. ADR ToS + allowlist.
2. Cập nhật GIA-DINH-NEN-TANG.
3. Adapter + contract test.
4. Không scrap.

### 4.4. Multi-channel publish

- Cùng `publication-candidate` có thể có nhiều `target_channel` (hoặc candidate riêng per channel).
- Mỗi channel: approval riêng hoặc policy rõ ràng.
- Idempotency key phân biệt theo channel.

### 4.5. SSO (nếu cần)

- ADR auth: phạm vi claim, issuer, mapping role Operator.
- Sales **không** đọc mastery/billing Learning.

---

## 5. Nghiệm thu (DoD)

- [ ] Production HTTPS + health xanh ≥ 2 tuần không sự cố nghiêm trọng (hoặc tiêu chí owner).
- [ ] Runbook sự cố tồn tại và đã diễn tập ít nhất 1 lần (kill switch).
- [ ] Adapter/channel mới chỉ vào sau ADR + GIA-DINH.
- [ ] Tài liệu operator đủ để người khác vận hành.

---

## 6. Rủi ro

| Rủi ro | Xử lý |
|--------|--------|
| Sự cố publish hàng loạt | Kill switch global + rollback |
| Khóa tài khoản affiliate | Tắt adapter; chuyển manual; liên hệ chương trình |
| Scope creep multi-platform | Chỉ mở khi metric Phase 5 ủng hộ |

---

## 7. Liên kết

- Task pack: `docs/task-packs/0008-phase6-production.md`
- Deploy: `docs/DEPLOY-SALES-SUBDOMAIN.md`
