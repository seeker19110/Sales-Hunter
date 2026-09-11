# Task pack: dựng khung vận hành cho repository săn sale

## 1. Mục tiêu

Repository Sales-Hunter đang trống. Rút phần hữu ích từ Claude-Agents để agent/lập trình viên có luật, bản đồ, hợp đồng và cổng kiểm định trước khi xây tích hợp Shopee/TikTok Shop.

## 2. Xong nghĩa là gì

- [x] Có bộ tài liệu vận hành tiếng Việt, kiến trúc khởi đầu và schema v1.
- [x] Validator/test từng đỏ khi module chưa tồn tại rồi xanh sau triển khai.
- [x] PR mở; CI `quality` và `metadata` xanh (theo dõi tại PR #1).

## 3. Phạm vi

Được chạm: file khởi tạo repo, `docs/`, `schemas/`, `tools/`, `tests/`, `.github/`.

Không được chạm: tài khoản/API thật, scraper, crawler, publisher, secret, runtime multi-agent của Claude-Agents.

## 4. Bối cảnh đã đọc

- `Claude-Agents`: `AGENTS.md`, `ARCHITECTURE.md`, `CODEMAP.md`, `TRAPS.md`, `CONTRIBUTING.md`, `SECURITY.md`, task pack, prompt sheet, quy trình Git và CI.
- Yêu cầu sản phẩm: kênh săn sale đa nền tảng có link affiliate Shopee/TikTok.

## 5. Ràng buộc

Schema-first; tiền dùng integer; thời gian có timezone; dữ liệu nguồn/model chưa tin cậy; draft + người duyệt mặc định; không bịa API nền tảng.

## 6. Bẫy và ca biên

Repo GitHub trống không có base branch để mở PR; dùng một empty commit trên `bootstrap/base`, sau đó mọi nội dung đi qua PR từ nhánh tính năng.

## 7. Kiểm và báo

- Đỏ: `python -m unittest discover -s tests -v` lỗi vì chưa có `tools.validate_repo`.
- Xanh: `uv sync --locked`, ruff, unittest, repository validator, `git diff --check`.
- Báo: PR, head SHA, trạng thái CI và phần chưa triển khai.
