# PROJECT STATUS — Sales-Hunter

> **Single source of truth cho tiến độ thực thi.** Mọi phiên làm việc phải đọc file này trước khi đọc ROADMAP hoặc bắt đầu sửa repo.

## Snapshot hiện tại

- Ngày cập nhật: 2026-09-25
- Base branch: `bootstrap/base`
- Base hiện tại: `683683710dd0de99857912487d4b2d5341f05c0e`
- Trạng thái: Phase 1 → Phase 6 skeleton, SH-010 (#37), SH-004 (#36) và phần integrity (#38) đã hợp nhất vào base. ADR-0006 đã triển khai SQLite, Token Auth và Web Operator Dashboard. Audit 25/09 ghi 27 hạng mục; các blocker khác còn mở.
- Side effect thật: **chưa bật**. Publisher vẫn mặc định dry-run; chưa DNS/TLS/cutover production; chưa client mạng thật.
- Báo cáo: [audit 25/09/2026](docs/audits/2026-09-25/README.md), 27 hạng mục và cổng nghiệm thu A–G. Chưa coi skeleton là đủ điều kiện external staging/production.

## Đợt thực thi audit 25/09/2026

- PR #38 đã merge sau human T4 review trên HEAD `9d8c290` và CI xanh.
- SH-007 ở nhánh `fix/audit-candidate-projection-2026-09-25`: test đỏ/xanh trên SQLite và HTTP, cần CI và merge; chưa sửa transaction/revision/history.
- SH-003 ở PR #39: local auth đã qua CI, chờ human T4 review trên đúng HEAD; chưa external staging.
- PR #35 đã merge báo cáo; PR #37 đã merge SH-010, browser gate đạt CI. PR #36 đã merge SH-004 tại `a61cffe` với artifact gate đạt CI trên HEAD `dae6650`.
- PR #38 xử lý một phần SH-001/002/016/023, đã qua CI và human T4 review trước merge. Identity/revision/payload scope vẫn mở.
- [Ma trận thực thi 27 hạng mục](docs/implementation/2026-09-25/execution-matrix.md) phân biệt phần chưa làm và phần đã kiểm; không coi audit #35 là implementation.
- T4 identity/publisher/ADR vẫn cần human review. Django/PostgreSQL chưa được chấp nhận. Chưa staging/production, không bật side effect thật.
- Task pack: [dashboard prices](docs/task-packs/2026-09-25-audit-dashboard-prices.md), [runtime packaging](docs/task-packs/2026-09-25-audit-runtime-packaging.md), [integrity](docs/task-packs/2026-09-25-audit-integrity.md). Trạng thái PR/CI mới nhất phải đọc GitHub.

## PR đã hoàn tất trong chuỗi hiện tại

- #38 — integrity hash/current approval và UTC/preflight đa kênh (một phần SH-001/002/016/023)
- #36 — SH-004 runtime packaging, clean-wheel artifact gate
- #37 — SH-010 hiển thị giá/nền tảng đúng và cổng browser mobile bắt buộc
- #35 — lưu audit 27 hạng mục (chỉ tài liệu)
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

- SH-001/002: PR #38 đã sửa phần hash và trusted approval; identity/role, immutable revision, channel scope còn mở tới khi có PR và bằng chứng tương ứng.
- SH-003: PR #39 sửa local auth fail-closed và bỏ token khỏi URL, đang chờ T4 review; external deploy còn cần TLS/role/session production. SH-004 packaging đã merge trong #36.
- SH-005: chống đăng trùng phải bền vững, có đối soát khi chưa rõ kết quả; dict trong Publisher chưa phải bảo đảm sau restart.
- SH-006–018: hợp đồng sau duyệt, transaction/revision, giá dashboard, payload/disclosure, freshness, điều kiện deal, URL, UTC, pause và HTTP production cần nghiệm thu như báo cáo.
- Chưa có bằng chứng deploy, restore hoặc quyền client nền tảng thật. CI xanh và báo cáo đã lưu không thay thế các bằng chứng đó.

## Việc tiếp theo

1. Merge SH-007 sau CI; cập nhật/rebase PR #39 và lấy human T4 review trên đúng HEAD. Tiếp tục SH-006/008/009 và outbox trong PR riêng. Chưa bật mạng/publish thật.
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
