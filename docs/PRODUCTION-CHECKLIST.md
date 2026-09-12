# Checklist cutover production

Trạng thái: **chưa production**. Tick khi có bằng chứng (PR, log, read-back).

## Trước cutover

- [ ] Chuỗi Phase 1.5–5 đã merge base; CI `quality` xanh trên SHA cutover
- [ ] ADR-0003 (manual-first) được **người** chấp nhận hoặc thay bằng nguồn official đã xác minh trong `GIA-DINH-NEN-TANG.md`
- [ ] ADR production cutover (xem `docs/adr/0004-production-cutover.md`) được duyệt
- [ ] Kill switch adapter + publisher đã diễn tập (runbook §1)
- [ ] `Publisher.dry_run` mặc định **True** trên config production cho đến khi owner bật tường minh
- [ ] Secret ngoài git; không commit token/cookie
- [ ] Staging: HTTPS + `/healthz` read-back (DEPLOY checklist)
- [ ] Operator biết approve/reject qua API hoặc quy trình file

## Cutover

- [ ] Deploy artifact/SHA cụ thể
- [ ] DNS/TLS theo `DEPLOY-SALES-SUBDOMAIN.md` (nếu public)
- [ ] Smoke: healthz, một vòng manual observation → candidate → approve (không bắt buộc publish thật)
- [ ] Monitoring/alert tối thiểu (uptime healthz) — chủ sở hữu hạ tầng

## Sau 2 tuần

- [ ] Không sự cố nghiêm trọng (ToS, leak, publish sai hàng loạt)
- [ ] Runbook đã dùng được trong ít nhất một diễn tập
- [ ] Mới xét adapter thứ hai (TikTok) — **không** song song khi Shopee/manual chưa ổn

## Cấm

- Auto-publish không người duyệt
- Scraping / CAPTCHA / cookie stuffing
- Hạ cổng CI để “xanh”
