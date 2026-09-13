# Changelog

Mọi thay đổi đáng kể của dự án được ghi tại đây theo [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) và Conventional Commits.

## Chưa phát hành

### Thêm

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

- Cập nhật `PROJECT-STATUS.md` sau khi PR #28 merge.
- Thêm ADR-0005: Chuẩn hóa `draft_sha256` thành channel-agnostic content hash; giải quyết dứt điểm mâu thuẫn bất biến hash giữa `publication-candidate.v1`, `approval-record.v1` và `publish_multi_channel`.
- Cập nhật `PROJECT-STATUS.md` sau khi #7 (dependabot `astral-sh/setup-uv` → 10.0.1) merge; base hiện tại `ab1586d`.
- Cập nhật `PROJECT-STATUS.md`: base hiện tại là `2b8402f` (sau #22, #23), thêm #22/#23 vào danh sách PR đã hoàn tất.
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
