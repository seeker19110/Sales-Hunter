# PROJECT STATUS — Sales-Hunter

> **Single source of truth cho tiến độ thực thi.** Mọi phiên làm việc phải đọc file này trước khi đọc ROADMAP hoặc bắt đầu sửa repo.

## Snapshot hiện tại

- Ngày cập nhật: 2026-09-25
- Base branch: `bootstrap/base`
- Base hiện tại: `0159c420ad8976939a98fb579bc9f5404bfcec89`
- Trạng thái: Phase 1 → Phase 6 skeleton đã hợp nhất vào base; PR #30–#34 đã hoàn tất. ADR-0006 đã triển khai SQLite, Token Auth và Web Operator Dashboard. Audit 25/09 đã được lưu cùng bằng chứng và lộ trình; **các sửa lỗi/nâng cấp trong audit chưa được triển khai bởi PR tài liệu này**.
- Side effect thật: **chưa bật**. Publisher vẫn mặc định dry-run; chưa DNS/TLS/cutover production; chưa client mạng thật.
- Báo cáo: [audit 25/09/2026](docs/audits/2026-09-25/README.md), 27 hạng mục và cổng nghiệm thu A–G. Chưa coi skeleton là đủ điều kiện external staging/production.

## PR đã hoàn tất trong chuỗi hiện tại

- #34 — đồng bộ `PROJECT-STATUS.md` sau khi PR #33 merge
- #33 — hoàn thiện Phase 4: SQLite datastore bền vững, Token Auth và Web Operator Dashboard
- #32 — đồng bộ `PROJECT-STATUS.md` sau khi PR #30 và #31 merge
- #31 — dependabot: bump `astral-sh/setup-uv` từ 10.0.1 lên 10.1.0 (nhãn `no-changelog`)
- #30 — dependabot: bump `ruff` từ 0.16.6 lên 0.16.7 (nhãn `no-changelog`)
- #29 — đồng bộ `PROJECT-STATUS.md` sau khi PR #28 merge
- #28 — ADR-0005 canonical draft hash cho multi-channel publishing
- #27 — log dependabot metadata-gate trap trong TRAPS.md
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

Tất cả PR trên đã được rebase/merge tuần tự vào `bootstrap/base` và qua CI/PR policy tại thời điểm merge. SHA trong snapshot là base đã đối chiếu trước PR tài liệu, không dự đoán SHA merge của chính PR.

## Blocker sau audit

- SH-001/002: tính lại hash từ payload và kiểm approval đầy đủ/tin cậy; hash so sánh đơn thuần chưa bảo đảm nội dung đã duyệt bất biến.
- SH-003/004: auth fail-closed, bỏ token khỏi URL/log và sửa runtime dependency/schema packaging trước external deploy/phát hành artifact.
- SH-005: chống đăng trùng phải bền vững, có đối soát khi chưa rõ kết quả; dict trong Publisher chưa phải bảo đảm sau restart.
- SH-006–018: hợp đồng sau duyệt, transaction/revision, giá dashboard, payload/disclosure, freshness, điều kiện deal, URL, UTC, pause và HTTP production cần nghiệm thu như báo cáo.
- Chưa có bằng chứng deploy, restore hoặc quyền client nền tảng thật. CI xanh và báo cáo đã lưu không thay thế các bằng chứng đó.

## Việc tiếp theo

1. Bắt đầu đợt A trong audit: các PR nhỏ có regression cho hash/approval, runtime-only packaging và auth fail-closed. Chưa bật mạng/publish thật; không chờ migration framework mới sửa integrity.
2. Sau đợt A, lần lượt identity/transaction → operator workflow → outbox/pause/reconcile → staging có thể phục hồi → pilot hẹp → tối ưu có dữ liệu. Mỗi bước có cổng nghiệm thu trong báo cáo.
3. Django LTS/PostgreSQL/server-rendered là **đề xuất**, cần ADR và migration plan riêng; chưa thay runtime stdlib/SQLite hiện tại. Không coi yêu cầu tạo PR báo cáo là đã phê duyệt cutover hay cấp quyền tài khoản nền tảng.
4. ADR-0003 và ADR-0004 đã được owner chấp nhận có điều kiện ngày 2026-09-12; điều kiện checklist và evidence vẫn bắt buộc. Không cutover trước khi `docs/PRODUCTION-CHECKLIST.md` được duyệt/tick bằng evidence thực tế và blocker audit được xử lý.
5. Khi tích hợp thật phải xác minh account/program, tài liệu official áp dụng, scope/quota và owner; không scraping/endpoint không được phép. Trước external deploy cần owner zone/origin/secret manager/on-call.
6. ADR-0005 (canonical content hash channel-agnostic) đã triển khai; audit yêu cầu kiểm lại hash thực tế và scope payload/approval. ADR-0006 (SQLite/Token/Dashboard) đã triển khai nhưng không tự chứng minh external staging an toàn.

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
- `docs/audits/`: đánh giá tại commit cố định và bằng chứng lịch sử; không phải danh sách sửa lỗi đã hoàn tất.
- `docs/sessions/`: lịch sử từng phiên và bằng chứng bàn giao.
- `CHANGELOG.md`: thay đổi đáng kể đã đưa vào code/docs.
