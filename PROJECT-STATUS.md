# PROJECT STATUS — Sales-Hunter

> **Single source of truth cho tiến độ thực thi.** Đọc trước ROADMAP; đối chiếu GitHub trước mỗi phiên.

## Snapshot hiện tại

- Ngày cập nhật: 2026-09-26
- Base branch: `bootstrap/base`
- Base hiện tại: `edec94751e137423338f9d5e3619139df5a770bc`
- #39 đã squash-merge vào base. Tree `947985091fd4d20ed56b09190d7ed53674a67ea7` khớp hoàn toàn HEAD auth cũ `f48346c`; không triển khai lại auth đã có.
- Phase 1–6 skeleton, packaging #36, giá/dashboard #37, integrity #38, projection #40 và local auth #39 đã tích hợp. Chưa hoàn tất audit 27 hạng mục.
- Publisher mặc định dry-run. Chưa client nền tảng thật, staging/production, DNS/TLS/cutover hoặc migration dữ liệu người dùng.

## PR đang xử lý

- #41 — DATA, nhánh `feat/audit-revision-transactions-20260925`: input pending đúng schema, revision/CAS, lịch sử bất biến, migration preview và HTTP ETag/409/428. Đang đồng bộ với base sau squash #39; phải kiểm CI trên HEAD mới và human T4 trước merge. Diagnostic baseline: 133 tests, Ruff và validate_repo đạt; không coi đó là kiểm locked runtime.
- #42 — DEAL, nhánh `feat/audit-deal-quality-20260925`, phụ thuộc #41: facts/evidence, eligibility và grounded payload. CI Windows tại `ef275d5` lỗi đọc fixture tiếng Việt bằng encoding mặc định; đang sửa, chưa đóng hạng mục.
- #43 — PUB, nhánh `feat/audit-durable-publishing-20260925`, phụ thuộc #42: remote còn ở commit test/spec `1447c44`; cần tích hợp implementation đã giữ trong handoff và chạy CI, không xóa test đỏ.
- #44/#45 — Dependabot setup-uv/Ruff: kiểm lại metadata và đồng bộ base; không hạ cổng để làm xanh.
- [Task pack sửa CI/xung đột](docs/task-packs/2026-09-26-ci-repair.md) và [checkpoint](docs/sessions/2026-09-26-ci-repair.md). Đọc PR conversations để lấy HEAD/run ID sau checkpoint này.

## Đã tích hợp

- #39 — local auth fail-closed, Bearer API, dashboard session/CSRF; merge `edec947`. Không tự chứng minh production identity/RBAC/TLS.
- #40 — SH-007 candidate approval projection; merge `0fea065`.
- #38 — canonical integrity/current approval, UTC và preflight; merge `6836837`. Chưa giải quyết toàn bộ SH-002/023.
- #36 — runtime dependency, năm schema và clean-wheel gate; merge `a61cffe`.
- #37 — canonical integer price/platform, mobile browser gate; merge `2522c4d`.
- #35 — audit và bằng chứng lịch sử, chỉ tài liệu.
- #34/#32/#29/#24 — đồng bộ trạng thái các đợt trước.
- #33 — SQLite, token auth và operator dashboard ban đầu.
- #31/#30/#7 — cập nhật setup-uv/Ruff; #27 ghi bẫy metadata Dependabot.
- #28 — ADR-0005 channel-agnostic content hash.
- #23 — status-freshness; #22 readiness; #20 branding.
- #13/#15/#16/#17/#18/#19 — skeleton các Phase 1.5–6.

Các SHA trên là mốc đã kiểm, không dự đoán merge SHA của chính PR. CI xanh không có nghĩa đã merge hoặc production sẵn sàng.

## Công việc còn mở

- Review T4 và tích hợp từng diff #41/#42/#43 đúng thứ tự, sau CI trên HEAD cuối; không tự lấy approval #39 làm approval cho PR khác.
- Identity nhiều người dùng, RBAC/TLS/server production và vòng đời secret còn thiếu.
- Durable publisher phải có implementation, crash/restart/reconcile/pause evidence trước khi đóng SH-005/011/017/023/027.
- Analytics/commission ledger, operator form/CSV/inbox/bulk workflow, lịch sử giá và bộ vận hành/restore drill chưa hoàn tất.
- Chưa xác minh quyền client/account/program nền tảng thật. Không bịa API, scraping hoặc dùng fake làm bằng chứng live.
- [Ma trận 27 mục](docs/implementation/2026-09-25/execution-matrix.md) là checkpoint theo nhánh; đối chiếu trạng thái PR hiện tại. [Audit lịch sử](docs/audits/2026-09-25/README.md) không sửa hồi tố.

## Việc tiếp theo

1. Sửa xung đột/CI cho tất cả PR mở, giữ mọi gate hiện hành và kiểm lại đúng HEAD.
2. Sau review T4 từng PR, tích hợp tuần tự; refresh stack sau squash, kiểm CI base trước phần phụ thuộc.
3. Tiếp tục ledger, operator workflow và phục hồi cô lập theo [task pack toàn đợt](docs/task-packs/2026-09-25-completion.md). Không lấy thiếu credential làm lý do bỏ việc nội bộ.
4. Django/PostgreSQL là đề xuất cần ADR được chấp nhận, chưa thay stdlib/SQLite. ADR-0003/0004 được chấp nhận có điều kiện; checklist/evidence vẫn bắt buộc trước external cutover.

## Quy tắc resume

Đọc file này trước, đối chiếu base/PR/CI, rồi đọc AGENTS/TRAPS/ARCHITECTURE/CODEMAP và quy ước subtask. Bảo toàn worktree và dùng nhánh riêng. Cập nhật trạng thái trong cùng PR, ghi session note; GitHub thắng khi checkpoint stale. Không push trực tiếp base, không force/bypass/skip test, không tự ký human review và không bật side effect thật.
