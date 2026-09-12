# Session handoff — 2026-09-12

## Đã hoàn tất

Chuỗi PR phụ thuộc đã được rebuild/rebase lên `bootstrap/base`, sửa các lệch CI cũ và merge tuần tự:

- #20 branding
- #13 Phase 1.5
- #15 Phase 2
- #16 Phase 3
- #17 Phase 4
- #18 Phase 5
- #19 Phase 6

Base sau #19: `ae4698167554720a4efbe2da944c21ce5754e321`.

Các lỗi CI gặp trong quá trình rebase chủ yếu là Pyright/Ruff do nhánh cũ lệch cấu hình hiện tại; đã sửa mà không mở side effect thật.

## Handoff mới

- `PROJECT-STATUS.md` là nguồn trạng thái thực thi chuẩn giữa các phiên.
- `AGENTS.md` bắt buộc mọi phiên đọc file đó đầu tiên và cập nhật nó trong cùng PR khi tiến độ thay đổi.
- `docs/ROADMAP.md` tiếp tục là lộ trình, không phải checkpoint thực thi.

## Việc tiếp theo

Rà ADR-0003 và ADR-0004; chưa cutover production cho đến khi production checklist được duyệt/tick và có quyết định explicit của owner.
