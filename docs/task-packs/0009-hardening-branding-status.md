# Task pack 0009 — Sales-Hunter hardening, trạng thái và branding

## Mục tiêu

Đồng bộ base hiện hành, chuẩn hóa tên hiển thị Sales-Hunter và làm cổng kiểm tra chạy ổn định trên Windows mà không đổi contract hay mở side effect.

## Subtask

| ID | Tier | Mục tiêu | Side effect |
|---|---|---|---|
| 9.a | T1 | Audit branding hiển thị | none |
| 9.b | T2 | Sửa cổng Pyright/pip-audit Windows | none |
| 9.c | T1 | Đồng bộ trạng thái roadmap/deploy | none |

## Ràng buộc

- Branching A: `chore/sales-hunter-hardening`.
- Không đổi package `s_n_sales` hoặc schema v1: đó là contract kỹ thuật, cần ADR/migration riêng.
- Không xác minh ToS, không gọi mạng, không deploy hoặc publish.

## Kiểm

- Test đỏ/xanh cho service identity operator.
- `ruff`, unittest, schema validation, Pyright và pip-audit.
