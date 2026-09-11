# Triển khai `sales.donghanhcungban.org`

Trạng thái: **chưa triển khai**. Repository hiện chỉ có domain core; chưa có HTTP application, VPS origin, Cloudflare zone access hoặc cấu hình DNS/TLS để phục vụ subdomain.

Quyết định kiến trúc gốc: [ADR-0002](adr/0002-platform-subdomain-dhcb.md). Ranh giới và vai trò: [PLATFORM](PLATFORM.md).

## Điều kiện trước khi triển khai

- [ ] ADR riêng chốt HTTP runtime, hosting origin, health check, logging và rollback.
- [ ] Owner xác nhận zone Cloudflare `donghanhcungban.org` và origin VPS được phép dùng.
- [ ] Tạo môi trường `staging` trước; không trỏ DNS production khi chưa có smoke test.
- [ ] Có secret manager/biến môi trường; không đưa credentials Cloudflare, SSO, affiliate hay webhook vào git.
- [ ] Có kill switch cho adapter và publisher trước khi bật network hoặc publish.
- [ ] Auth/SSO và operator authorization có ADR riêng; Sales không dùng credential hay dữ liệu Learning mặc định.

## Trình tự triển khai đã duyệt

1. Build HTTP service có `GET /healthz` không tiết lộ secret/PII.
2. Deploy staging vào origin cô lập; kiểm `healthz`, log và rollback bằng artifact/version cụ thể.
3. Tạo DNS `sales` và TLS qua Cloudflare sau khi staging được duyệt.
4. Chỉ sau read-back DNS/TLS và smoke test HTTPS mới mở traffic production.
5. Auto-publish vẫn tắt mặc định; domain online không là quyền publish.

## Bằng chứng cần lưu trong PR deploy

- URL staging và production, commit/artifact SHA, thời điểm deploy.
- Kết quả HTTPS + `/healthz` read-back.
- Phạm vi DNS record và TLS mode đã được người có quyền phê duyệt.
- Kế hoạch rollback và trạng thái kill switch.

Không đưa endpoint origin nội bộ, IP, token, cookie hay configuration secret vào tài liệu này.
