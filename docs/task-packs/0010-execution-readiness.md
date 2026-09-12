# Task pack 0010 — Sales-Hunter execution readiness

## Mục tiêu

Thực thi phần readiness đã được owner duyệt T4, nhưng không suy diễn credential, quyền nền
tảng hoặc thay đổi hạ tầng không có định danh/bằng chứng.

## Subtask

| ID | Tier | Mục tiêu | Side effect |
|---|---|---|---|
| 10.a | T4 | Xác minh nguồn official/API và quyền account | ingest-network (research only) |
| 10.b | T3 | Hardening auth, persistence, audit và config | none |
| 10.c | T3 | Chuẩn bị artifact/deploy checklist không secret | none |
| 10.d | T4 | Staging DNS/TLS, smoke/read-back | account-change |
| 10.e | T4 | Kết nối publisher chính thức + publish được duyệt | publish |

## Điều kiện dừng

- Không có URL/tài liệu official, account/program hoặc credential: dừng trước client mạng.
- Không có owner/zone/origin cụ thể: dừng trước DNS/TLS/deploy.
- Không có channel/platform client được phép: dừng trước publisher thật.

## Kiểm

- Mỗi subtask có test/cổng riêng và session log.
- Mọi side effect phải có định danh/read-back do nền tảng sinh ra.
