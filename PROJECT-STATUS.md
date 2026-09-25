# PROJECT STATUS — Sales-Hunter

> **Single source of truth cho tiến độ thực thi.** Đọc trước ROADMAP; đối chiếu GitHub trước mỗi phiên.

## Snapshot hiện tại

- Ngày cập nhật: 2026-09-26
- Base branch: `bootstrap/base`
- Base hiện tại: `edec94751e137423338f9d5e3619139df5a770bc`
- #39 đã squash-merge vào base. Tree `947985091fd4d20ed56b09190d7ed53674a67ea7` khớp HEAD auth cũ `f48346c`; không triển khai lại auth đã có.
- Phase 1–6 skeleton, packaging #36, giá/dashboard #37, integrity #38, projection #40 và local auth #39 đã tích hợp. Chưa hoàn tất audit 27 hạng mục.
- Publisher mặc định dry-run. Chưa client nền tảng thật, staging/production, DNS/TLS/cutover hoặc migration dữ liệu người dùng.

## Sửa CI/xung đột các PR mở

- #41 DATA — `feat/audit-revision-transactions-20260925`: đã đồng bộ ancestry với base sau squash, HEAD `0cff6697e8e44563f5c3d4799966f76d7715c950`; CI `36200730335` và metadata `36200730334` đạt. Revision/CAS/history/migration vẫn chờ human T4 trước merge.
- #42 DEAL — `feat/audit-deal-quality-20260925`, phụ thuộc #41: sửa hai loader fixture UTF-8 và thêm hai regression locale; HEAD `28fbd8cef0644a7733a2e81e16d4254bfd3942bd`; CI `36201165521`, metadata `36201165470` đạt. Giữ facts/evidence/eligibility và các assertion cũ. Chưa merge.
- #43 PUB — `feat/audit-durable-publishing-20260925`, phụ thuộc #42: checkpoint này đưa implementation đã giữ trong handoff vào remote, không còn chỉ test/spec. Có queue/lease/reconcile/pause/cooldown/recall, scope duyệt nguyên tử và wheel smoke bằng fake transport. Sửa lỗi tham số/ownership token thu hồi, thêm ba regression; 197 test diagnostic cục bộ đạt. Phải kiểm CI trên HEAD mới; chưa merge/human T4.
- #44 setup-uv — HEAD `23bc6bfb5351824ec9aa7f7f76ad92b5a5733efd`; CI `36201277638`, metadata `36201277627` đạt. Đồng bộ base và bổ sung CHANGELOG, giữ bump 10.2.0.
- #45 Ruff — HEAD `41f6821e8245895481bd79428f49ce7a5b196e6d`; CI `36201323368`, metadata `36201323328` đạt. Đồng bộ base và bổ sung CHANGELOG, giữ bump 0.16.8 cùng lockfile.
- Không dùng miễn kiểm tra, skip/xfail hoặc giảm validation. Không PR nào được merge/arm auto-merge bởi đợt sửa này. Xác minh trạng thái mới trên GitHub; checkpoint không dự đoán kết quả CI hoặc merge sau đó.
- [Task pack sửa CI/xung đột](docs/task-packs/2026-09-26-ci-repair.md), [sửa DATA](docs/sessions/2026-09-26-ci-repair.md), [sửa QUALITY](docs/sessions/2026-09-26-quality-ci-repair.md), [sửa PUBLISHING](docs/sessions/2026-09-26-publishing-ci-repair.md).

## Đã tích hợp trước đợt sửa

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

- Human T4 và tích hợp từng diff #41/#42/#43 đúng thứ tự, sau CI trên HEAD cuối. Approval #39 không áp dụng cho PR khác.
- Identity nhiều người dùng, RBAC/TLS/server production và vòng đời secret còn thiếu.
- Durable publisher có source trên nhánh này, nhưng chỉ kiểm fake/fixture; chưa có provider thật hay bằng chứng vận hành production. Sau tích hợp phải kiểm lại base.
- Analytics/commission ledger, operator form/CSV/inbox/bulk workflow, lịch sử giá và bộ vận hành/restore drill chưa hoàn tất.
- Chưa xác minh quyền client/account/program nền tảng thật. Không bịa API, scraping hoặc dùng fake làm bằng chứng live.
- [Ma trận 27 mục](docs/implementation/2026-09-25/execution-matrix.md) là checkpoint theo nhánh; dùng session sửa CI và GitHub để đối chiếu cập nhật. [Audit lịch sử](docs/audits/2026-09-25/README.md) không sửa hồi tố.

## Việc tiếp theo

1. Kiểm CI #43 trên HEAD mới và xử lý mọi lỗi thật; xác nhận cả năm PR không xung đột với nhánh đích hiện tại, CI/metadata trên đúng HEAD.
2. Sau review T4 từng PR, tích hợp tuần tự; refresh stack sau squash, kiểm CI base trước phần phụ thuộc.
3. Tiếp tục ledger, operator workflow và phục hồi cô lập theo [task pack toàn đợt](docs/task-packs/2026-09-25-completion.md). Không lấy thiếu credential làm lý do bỏ việc nội bộ.
4. Django/PostgreSQL là đề xuất cần ADR được chấp nhận, chưa thay stdlib/SQLite. ADR-0003/0004 được chấp nhận có điều kiện; checklist/evidence vẫn bắt buộc trước external cutover.

## Quy tắc resume

Đọc file này trước, đối chiếu base/PR/CI, rồi đọc AGENTS/TRAPS/ARCHITECTURE/CODEMAP và quy ước subtask. Bảo toàn worktree và dùng nhánh riêng. Cập nhật trạng thái trong cùng PR, ghi session note; GitHub thắng khi checkpoint stale. Không push trực tiếp base, không force/bypass/skip test, không tự ký human review và không bật side effect thật.
