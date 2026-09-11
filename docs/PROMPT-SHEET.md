# Prompt sheet — câu lệnh chuẩn

Chỉ giữ câu lệnh đã giúp duy trì ranh giới của S-N Sales. Khi thêm prompt, ghi lý do và ngày dùng đầu tiên.

**Bộ prompt sẵn (copy-paste):**
- Orchestrator: [docs/prompts/ORCHESTRATOR.md](prompts/ORCHESTRATOR.md)
- Phase 1.5 — mỗi subagent một file: [docs/prompts/phase-1.5/](prompts/phase-1.5/)

## Bắt đầu phiên (orchestrator hoặc agent đơn)

```text
Đọc AGENTS.md, TRAPS.md, ARCHITECTURE.md, docs/SUBAGENT-TASK-CONVENTION.md và dòng liên quan trong CODEMAP.md. Kiểm git status/worktree. Điền task pack cho yêu cầu này; nếu việc lớn/phase thì tách subtask + model_tier (T0–T4) trước khi code. Nêu rõ hành động ngoài hệ thống nào bị cấm. Sau đó làm theo TDD và chạy đúng cổng của CONTRIBUTING.md.
```

## Orchestrator — tách phase thành subtask

Dùng bản đầy đủ trong `docs/prompts/ORCHESTRATOR.md`, hoặc:

```text
Bạn là orchestrator S-N Sales. Đọc docs/impl/PHASE-<x>-IMPLEMENTATION.md và task-pack phase tương ứng. Tách thành danh sách subtask đủ nhỏ theo docs/SUBAGENT-TASK-CONVENTION.md. Mỗi subtask: id, model_tier T0–T4, side effect, path được/không được chạm, DoD. Không giao cả phase cho một subagent. Không gán dưới T3 nếu có side effect mạng/publish. Xuất bảng subtask rồi dừng để duyệt trước khi giao.
```

## Giao một subagent

Ưu tiên mở đúng file trong `docs/prompts/phase-*/` và copy nguyên khối. Mẫu generic:

```text
Bạn là subagent S-N Sales. Chỉ làm đúng subtask trong block/template sau đây. Đọc AGENTS.md và các file trong mục "Bối cảnh phải đọc". Không sửa ngoài phạm vi, không tự publish/ADR, không tiện tay làm subtask khác. TDD nếu có code. Kết thúc bằng báo cáo theo mục 9 của TEMPLATE-SUBTASK.

<dán nội dung TEMPLATE-SUBTASK hoặc file docs/prompts/... đã điền>
```

## Thêm adapter nền tảng

```text
Trước khi code adapter <nền tảng>: xác định API/nguồn được phép bằng tài liệu chính thức có ngày truy cập; liệt kê auth, quota, rate limit, pagination, timezone, currency, lỗi và điều khoản lưu dữ liệu. Định nghĩa/đổi schema cùng contract test dùng fixture đã khử bí mật. Không fallback sang scraping khi API thiếu. Việc này tối thiểu tier T4 (ADR + human) trước implement mạng.
```

## Điều tra giá hoặc sale sai

```text
Không suy từ message lỗi. Lấy một observation raw, giữ nguyên observed_at/account/region/currency, tái hiện normalizer bằng test. Tách lần lượt giá gốc, giá sale, coupon, shipping và eligibility. Test phải đỏ khi chưa sửa; sau sửa rà mọi adapter dùng cùng công thức và phân biệt stale-data với source-unavailable.
```

## Chuẩn bị đăng nội dung

```text
Kiểm schema publication candidate, tuổi của claim snapshot, affiliate disclosure, allowlist URL và approval hash. Chỉ chạy dry-run nếu chưa được người vận hành cho phép đăng. Nếu đăng thật, dùng idempotency key rồi đọc lại platform post ID/URL; không nhận lời khai "đã đăng" từ model. Mọi subtask publish = T4.
```

## Kết thúc phiên

```text
Chạy lint, test và repository contract; đọc toàn bộ diff so với base. Kiểm commit remote nằm trong PR và CI trên head hiện tại. Ghi docs/sessions/<ngày>.md chỉ gồm việc xong (kèm subtask id + tier), việc dở + lý do, PR mở, bẫy mới và điều phiên sau không được quên.
```
