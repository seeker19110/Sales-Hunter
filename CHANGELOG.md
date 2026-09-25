# Changelog

Mọi thay đổi đáng kể của dự án được ghi tại đây theo [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) và Conventional Commits.

## Chưa phát hành

### Deal chất lượng và nội dung có chứng cứ (chờ T4)

- SH-011–015/025/026/027: facts v1 chứa toàn observation và provenance; retained evidence được phép lưu, khử nhạy cảm, expiry/thu hồi; eligibility tách ranking; final payload có link/disclosure và scope/hash/version; manual input tạo ID/hash server, preview read-only và binding bất biến. Giữ schema v1 cũ.
- Grounded composer tùy chọn chỉ chọn introduction/order fact IDs, có budget/cache/version và fallback template; không tự sinh số/link/claims hoặc gọi API trả phí. Cổng runtime-only smoke mở rộng cho luồng mới; chưa có durable publish hoặc live connector.

### Dữ liệu và giao dịch (chờ review T4)

- SH-006/008/009/026: nhập pending đúng schema, revision bắt buộc khi sửa/duyệt, transaction SQLite, history chỉ-thêm, vô hiệu approval khi edit và đọc authority nguyên tử. HTTP 409/428, form version, Host/Origin và UTF-8/framing giới hạn. Migration preview chỉ đọc, manifest và rollback khi legacy data lỗi; chưa chọn PostgreSQL/production.

### Thêm

- Audit 25/09/2026 tại `docs/audits/2026-09-25/`: báo cáo 27 hạng mục, lộ trình A–G ưu tiên chất lượng/dễ vận hành, 12 probe local và JSON bằng chứng có manifest SHA. Đây là bàn giao tài liệu; không phải đã sửa các phát hiện, thay kiến trúc hoặc bật publish thật.
- Hướng dẫn đọc/chạy lại bộ audit và session note bàn giao; liên kết từ README và checkpoint tới các blocker trước external deploy.
- ADR-0006 và Phase 4: `SqliteOperatorStore` (lưu trữ bền vững chuẩn stdlib sqlite3), xác thực Token Auth và Web Operator Dashboard (giao diện duyệt deal trực quan, xem claim/disclosure, form duyệt/từ chối, lọc trạng thái, chống XSS).
- `TRAPS.md`: ghi bẫy PR dependabot kẹt ở cổng `metadata` vì không tự sửa được `CHANGELOG.md` (#7); cách rà và cách gỡ (nhãn `no-changelog`).
- `tools/check_status_freshness.py` + job CI `status-freshness` (chạy khi push `bootstrap/base`): đối chiếu SHA/nhánh ghi trong `PROJECT-STATUS.md` với git thật, chặn tài liệu trạng thái lỗi thời âm thầm sau merge.
- `PROJECT-STATUS.md` làm single source of truth cho tiến độ thực thi và điểm resume giữa các phiên; `AGENTS.md` bắt buộc đọc/cập nhật trạng thái này.
- Phase 6: runbook, production checklist, ADR-0004 đề xuất và helper multi-channel publish; không thực hiện DNS/TLS/cutover hay client mạng thật.
- Phase 5: analytics event/metrics skeleton, tách no_sale vs source_unavailable và recall content theo tuổi observation; chưa tracking pixel/API conversion/rank tuning.
- Phase 4: operator HTTP API skeleton (stdlib) với healthz, candidate store và approve/reject; in-memory, chưa deploy/auth/publish qua HTTP.
- Phase 3: approval hash-bound và publisher dry-run mặc định, idempotent, có kill switch hệ thống/kênh và read-back receipt qua fake client trong test.
- Phase 2: manual observation adapter, adapter kill switch và draft-only end-to-end flow; ADR-0003 được ghi ở trạng thái đề xuất, không có network side effect.
- Phase 1.5: `publication-candidate.v1` builder với `claim_snapshot`, `draft_sha256` deterministic, disclosure bắt buộc, pending approval và contract/unit tests.
- `docs/prompts/ORCHESTRATOR.md` + `docs/prompts/phase-1.5/*`: prompt sẵn — mỗi subagent một subtask Phase 1.5.
- `docs/SUBAGENT-TASK-CONVENTION.md` + `TEMPLATE-SUBTASK.md`; áp dụng toàn cục README/CODEMAP/CONTRIBUTING/ROADMAP/PHASES/QUY-TRINH-GIT.
- `docs/impl/PHASE-*` và task-pack 0003–0008; PHASES + ROADMAP Phase 1.5.
- Runtime validation observation; Pyright; pip-audit; Dependabot; hướng dẫn deploy subdomain.

### Sửa

- Khắc phục CI các PR bảo trì công cụ: đồng bộ nhánh với base sau #39 và ghi CHANGELOG để cổng metadata kiểm đúng, không dùng miễn kiểm tra. Phiên bản công cụ và bằng chứng riêng của từng PR nằm trong session note tương ứng.

- SH-003 (local operator): xác thực fail-closed, API chỉ nhận Bearer header, dashboard dùng session/CSRF và actor cấu hình phía server; bỏ query/form token và CLI argv secret, chặn bind ngoài loopback. Chưa cho phép external staging/production.
- SH-007: candidate sau approve/reject và khi đọc bản ghi SQLite cũ chỉ chứa approval projection hợp lệ theo schema v1; approval record đầy đủ vẫn nằm trong bảng và endpoint riêng.
- Wheel smoke sau SH-001/002 dùng approval được commit vào trusted store trước khi gọi fake publisher, giữ cổng artifact chạy đủ vòng ngoài checkout.
- SH-001/002/016/023: tính lại canonical hash tại ingest/approve/publish; kiểm approval đầy đủ và đối chiếu approval hiện hành từ store cấu hình phía server trước gửi hoặc trả receipt cache; chặn approval tự khai/rejected sau restart. Đóng băng candidate qua lời gọi client, chuẩn UTC và preflight toàn bộ tên kênh. T4 chờ người duyệt; chưa hoàn thiện identity/revision/outbox hay payload scope mới.

- SH-010: danh sách/chi tiết dashboard dùng chung read model lấy đúng `claim_snapshot.*_price_minor` và nền tảng; hiển thị VND bằng số nguyên, giá chưa xác minh không biến thành 0. Thêm regression builder thật và cổng browser mobile bắt buộc trong `quality`; không đổi auth/approval/publish.
- SH-004: khai báo `jsonschema[format-nongpl]` là runtime dependency, đóng gói năm schema v1 byte-for-byte trong wheel và tải contract qua package resources; job artifact kiểm wheel cài ngoài checkout với chỉ runtime dependencies.

- Đồng bộ `PROJECT-STATUS.md` tới baseline `0159c42` sau #34, bổ sung blocker audit và phân biệt rõ “đã lưu kế hoạch” với “đã triển khai/đủ điều kiện production”.
- Cập nhật `PROJECT-STATUS.md` sau khi PR #33 (Phase 4 SQLite & Operator Dashboard) merge; base hiện tại `fbc2a1b`.
- Cập nhật `PROJECT-STATUS.md` sau khi PR #30 (ruff 0.16.7) và PR #31 (setup-uv 10.1.0) merge; base hiện tại `c620c10`.
- Cập nhật `PROJECT-STATUS.md` sau khi PR #28 merge.
- Thêm ADR-0005: Chuẩn hóa `draft_sha256` thành channel-agnostic content hash; giải quyết dứt điểm mâu thuẫn bất biến hash giữa `publication-candidate.v1`, `approval-record.v1` và `publish_multi_channel`.
- Cập nhật `PROJECT-STATUS.md`: base hiện tại là `2b8402f` (sau #22, #23), thêm #22/#23 vào danh sách PR đã hoàn tất.
- Cập nhật `PROJECT-STATUS.md` sau khi #7 (dependabot `astral-sh/setup-uv` → 10.0.1) merge; base hiện tại `ab1586d`.
- Cài Sales-Hunter editable bằng Hatchling để các lệnh quality bắt buộc chạy trực tiếp được trên PowerShell/Windows, không còn phụ thuộc `PYTHONPATH` của Makefile.
- Đồng bộ trạng thái skeleton Phase 1–6 trong roadmap, kiến trúc và tài liệu deploy; giữ rõ các điều kiện T4/production chưa hoàn tất.
- Chuẩn hóa toàn bộ tên hiển thị còn lại thành Sales-Hunter; giữ nguyên package `s_n_sales` và schema v1 là định danh kỹ thuật tương thích.
- Chạy Pyright và pip-audit qua `python -m` để tránh Windows console-script trampoline.
- ADR manual-first và production cutover được owner chấp nhận có điều kiện; checklist/evidence vẫn là cổng bắt buộc trước side effect.

### Sửa

- Chuẩn hóa tên hiển thị và package metadata thành Sales-Hunter.
- `AGENTS.md`, `TASK-PACK.md`, `PROMPT-SHEET.md`: gắn quy ước subagent và link prompts.
- Ranking yêu cầu clock có timezone.
- `.gitattributes` LF trên Windows.

### Đã có từ trước

- Khung vận hành + schema v1 + CI placeholder.
- ADR-0002 + PLATFORM subdomain.
- Phase 1 code: Money, ranking, pipeline, fake adapter, tests.
