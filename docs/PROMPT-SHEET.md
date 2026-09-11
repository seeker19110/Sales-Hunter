# Prompt sheet — câu lệnh chuẩn

Chỉ giữ câu lệnh đã giúp duy trì ranh giới của S-N Sales. Khi thêm prompt, ghi lý do và ngày dùng đầu tiên.

## Bắt đầu phiên

```text
Đọc AGENTS.md, TRAPS.md, ARCHITECTURE.md và dòng liên quan trong CODEMAP.md. Kiểm git status/worktree. Điền task pack cho yêu cầu này; nêu rõ hành động ngoài hệ thống nào bị cấm. Sau đó làm theo TDD và chạy đúng cổng của CONTRIBUTING.md.
```

## Thêm adapter nền tảng

```text
Trước khi code adapter <nền tảng>: xác định API/nguồn được phép bằng tài liệu chính thức có ngày truy cập; liệt kê auth, quota, rate limit, pagination, timezone, currency, lỗi và điều khoản lưu dữ liệu. Định nghĩa/đổi schema cùng contract test dùng fixture đã khử bí mật. Không fallback sang scraping khi API thiếu.
```

## Điều tra giá hoặc sale sai

```text
Không suy từ message lỗi. Lấy một observation raw, giữ nguyên observed_at/account/region/currency, tái hiện normalizer bằng test. Tách lần lượt giá gốc, giá sale, coupon, shipping và eligibility. Test phải đỏ khi chưa sửa; sau sửa rà mọi adapter dùng cùng công thức và phân biệt stale-data với source-unavailable.
```

## Chuẩn bị đăng nội dung

```text
Kiểm schema publication candidate, tuổi của claim snapshot, affiliate disclosure, allowlist URL và approval hash. Chỉ chạy dry-run nếu chưa được người vận hành cho phép đăng. Nếu đăng thật, dùng idempotency key rồi đọc lại platform post ID/URL; không nhận lời khai "đã đăng" từ model.
```

## Kết thúc phiên

```text
Chạy lint, test và repository contract; đọc toàn bộ diff so với base. Kiểm commit remote nằm trong PR và CI trên head hiện tại. Ghi docs/sessions/<ngày>.md chỉ gồm việc xong, việc dở + lý do, PR mở, bẫy mới và điều phiên sau không được quên.
```
