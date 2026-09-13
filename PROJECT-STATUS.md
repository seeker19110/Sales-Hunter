# PROJECT STATUS — Sales-Hunter

> **Single source of truth cho tiến độ thực thi.** Mọi phiên làm việc phải đọc file này trước khi đọc ROADMAP hoặc bắt đầu sửa repo.

## Snapshot hiện tại

- Ngày cập nhật: 2026-09-13
- Base branch: `bootstrap/base`
- Base hiện tại: `6add4235e65f048da435c682c7860b77bca7763a`
- Trạng thái: Phase 1 → Phase 6 skeleton đã được hợp nhất vào base; bốn commit handoff sau chuỗi phase đã đồng bộ trạng thái. #22 (harden readiness), #23 (kiểm freshness của chính file này), #24 và #25 (đồng bộ file này) và #7 (dependabot: bump `astral-sh/setup-uv` lên 10.0.1, nhãn `no-changelog`) đã merge. Không còn PR mở.
- Side effect thật: **chưa bật**. Publisher vẫn mặc định dry-run; chưa DNS/TLS/cutover production; chưa client mạng thật.

## PR đã hoàn tất trong chuỗi hiện tại

- #25 — đồng bộ `PROJECT-STATUS.md` sau khi #7 merge
- #7 — dependabot: bump `astral-sh/setup-uv` từ 7.6.0 lên 10.0.1 (nhãn `no-changelog`)
- #24 — đồng bộ `PROJECT-STATUS.md` sau khi #22/#23 merge
- #23 — `tools/check_status_freshness.py` + job CI `status-freshness` đối chiếu file này với git thật
- #22 — harden readiness
- #20 — chuẩn hóa branding Sales-Hunter
- #13 — Phase 1.5 publication candidate
- #15 — Phase 2 manual observation + kill switch
- #16 — Phase 3 approval + dry-run publisher
- #17 — Phase 4 operator HTTP API skeleton
- #18 — Phase 5 analytics + recall
- #19 — Phase 6 runbook + production skeleton

Tất cả PR trên đã được rebase/merge tuần tự vào `bootstrap/base` và qua CI/PR policy tại thời điểm merge.

## Việc tiếp theo

1. ADR-0003 và ADR-0004 đã được owner chấp nhận có điều kiện ngày 2026-09-12; điều kiện checklist và evidence vẫn bắt buộc.
2. Chưa thực hiện cutover production cho đến khi `docs/PRODUCTION-CHECKLIST.md` được duyệt/tick đầy đủ bằng evidence thực tế.
3. Khi bắt đầu tích hợp nền tảng thật, cần account/program, tài liệu official áp dụng, scope/quota và owner; không dùng scraping hay endpoint không được phép.
4. Trước external deploy cần owner zone/origin/secret manager/on-call; trước API operator public cần ADR auth/authorization và datastore.
5. Multi-channel skeleton hiện mâu thuẫn với bất biến `draft_sha256` vì thay `target_channel` sau approval; trước publisher thật cần ADR T4 chốt approval/hash theo từng kênh hoặc canonical hash không gồm kênh.

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
