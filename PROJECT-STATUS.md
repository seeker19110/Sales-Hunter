# PROJECT STATUS — Sales-Hunter

> **Single source of truth cho tiến độ thực thi.** Mọi phiên làm việc phải đọc file này trước khi đọc ROADMAP hoặc bắt đầu sửa repo.

## Snapshot hiện tại

- Ngày cập nhật: 2026-09-12
- Base branch: `bootstrap/base`
- Base hiện tại: `6bc16b8ff01f5e64cc7a152d01d56785f24b9308`
- Trạng thái: Phase 1 → Phase 6 skeleton đã được hợp nhất vào base; bốn commit handoff sau chuỗi phase đã đồng bộ trạng thái.
- Side effect thật: **chưa bật**. Publisher vẫn mặc định dry-run; chưa DNS/TLS/cutover production; chưa client mạng thật.

## PR đã hoàn tất trong chuỗi hiện tại

- #20 — chuẩn hóa branding Sales-Hunter
- #13 — Phase 1.5 publication candidate
- #15 — Phase 2 manual observation + kill switch
- #16 — Phase 3 approval + dry-run publisher
- #17 — Phase 4 operator HTTP API skeleton
- #18 — Phase 5 analytics + recall
- #19 — Phase 6 runbook + production skeleton

Tất cả PR trên đã được rebase/merge tuần tự vào `bootstrap/base` và qua CI/PR policy tại thời điểm merge.

## Việc tiếp theo

1. Rà và quyết định trạng thái ADR-0003 (`docs/adr/0003-manual-first-observation.md`).
2. Rà và quyết định trạng thái ADR-0004 (`docs/adr/0004-production-cutover.md`) — đây là quyết định T4/người duyệt.
3. Chưa thực hiện cutover production cho đến khi `docs/PRODUCTION-CHECKLIST.md` được duyệt/tick đầy đủ.
4. Khi bắt đầu tích hợp nền tảng thật, tạo task/ADR riêng cho adapter/client chính thức; không dùng scraping hay endpoint không được phép.

## Quy tắc resume cho mọi phiên

1. Đọc `PROJECT-STATUS.md` **đầu tiên**.
2. Đối chiếu `bootstrap/base`, PR mở và CI để xác nhận snapshot chưa stale.
3. Chỉ sau đó đọc `docs/ROADMAP.md`, `AGENTS.md`, `TRAPS.md`, `ARCHITECTURE.md` và phần CODEMAP liên quan.
4. Sau mỗi merge, thay đổi phase, blocker hoặc quyết định kiến trúc, cập nhật file này **trong cùng PR**.
5. Cuối phiên, ghi session note trong `docs/sessions/` và bảo đảm mục “Việc tiếp theo” ở đây khớp với thực tế.
6. Nếu `PROJECT-STATUS.md` mâu thuẫn với GitHub, GitHub là bằng chứng thực tế; sửa file này ngay trong PR kế tiếp.

## Phân biệt tài liệu

- `PROJECT-STATUS.md`: tiến độ thực thi thực tế + điểm resume.
- `docs/ROADMAP.md`: lộ trình/mục tiêu sản phẩm.
- `docs/sessions/`: lịch sử từng phiên và bằng chứng bàn giao.
- `CHANGELOG.md`: thay đổi đáng kể đã đưa vào code/docs.
