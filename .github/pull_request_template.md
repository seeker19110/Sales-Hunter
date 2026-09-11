# Mẫu pull request

## Mục tiêu / issue

<!-- Kết quả người dùng hoặc sự cố cần giải quyết. -->

## Thay đổi

<!-- Nêu phạm vi; không chép lại toàn bộ diff. -->

## Dữ liệu và kiến trúc

- [ ] Không đổi schema/rành giới module
- [ ] Có schema/ADR/migration tương ứng
- [ ] Đổi logic giá, voucher, shipping hoặc commission
- [ ] Đổi adapter, nguồn dữ liệu hoặc giả định nền tảng

## Side effect ngoài hệ thống

`none | ingest-network | affiliate-link-create | publish | account-change`

- Chế độ đã thử: `offline | fixture | dry-run | live`
- Read-back/receipt nếu có:

## Policy snapshot

- Nguồn chính thức:
- Ngày đọc:
- Phạm vi/khu vực:
- Điều chưa xác minh:

## Kiểm định

- Test đỏ trước bản sửa:
- Lệnh lint/test/contract:
- Kiểm tay hoặc read-back:

## An toàn

- [ ] Không có secret, cookie, PII hoặc payload thương mại thật
- [ ] Không bypass CAPTCHA, rate limit hoặc cơ chế chống bot
- [ ] URL affiliate/destination qua allowlist và redirect validation
- [ ] Nội dung thương mại có disclosure phù hợp
- [ ] Đã đọc diff và không có thay đổi ngoài phạm vi
