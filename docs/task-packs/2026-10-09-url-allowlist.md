# Allowlist URL version hóa cho mọi đường tạo candidate — ADR-0011 (2026-10-09)

Phạm vi: mục "còn lại" đầu tiên trong [session audit](../sessions/2026-10-09-line-audit.md). Owner giao toàn quyền quyết định trong luật `AGENTS.md`. Branching A: nhánh `claude/affectionate-bohr-pk3fsx` làm lại từ base sau khi #47 merge; subtask là commit tuần tự; một integrator, không subagent.

Baseline: `bootstrap/base` `7e00135063207bf0b38f0b62870c783708142f0e` (#47 đã merge), mọi cổng cục bộ xanh.

| subtask_id | model_tier | dependency | allowed scope | acceptance |
|---|---|---|---|---|
| URL-ADR | T4 | baseline | `docs/adr/0011-versioned-url-allowlist.md` | ADR nêu hợp đồng, fail-closed, phạm vi đường tạo candidate; không thêm domain thật |
| URL-CONTRACT | T2 | URL-ADR | `schemas/url-allowlist.v1.json` (+ bản package), mẫu valid/invalid, `config/url-allowlist.v1.json`, `tools/validate_repo.py` | schema Draft 2020-12, mỗi host bắt buộc `reference` HTTPS + `verified_on`; config sai schema làm `validate_repo` báo lỗi |
| URL-LOADER | T2 | URL-CONTRACT | `quality/allowlist.py`, `quality/urls.py` | parse chặt (khóa trùng, sai schema, không đọc được → `ValueError`); `UrlPolicy.version` |
| URL-ENFORCE | T4 | URL-LOADER | `pipeline/publication.py`, `pipeline/manual_draft_flow.py`, `content/render.py`, `api/app.py`, `api/__main__.py`, caller trong test/tools | builder/flow bắt buộc `url_policy`, kiểm `affiliate_url` + `evidence.source_url`; API 403 khi chưa cấu hình, 400 `url_not_allowed` |
| URL-DOCS | T0 | preceding | CHANGELOG, CODEMAP, ARCHITECTURE, HOP-DONG-DU-LIEU, RUNBOOK, AN-TOAN-AFFILIATE, PROJECT-STATUS, session | trạng thái khớp GitHub |

Cấm: thêm domain Shopee/TikTok hoặc domain thật vào config, migrate/sửa candidate đã lưu, đổi luồng duyệt/publish, bật transport thật, đổi cổng CI, skip/xfail test, sửa PR đang mở khác (#44, #45, #46).

Nghiệm thu: `tests/test_url_allowlist.py` đỏ trước bản sửa vì đúng lý do (thiếu module/tham số, URL ngoài allowlist được nhận) và xanh sau; toàn bộ cổng `CONTRIBUTING.md`, browser smoke và smoke wheel runtime-only xanh. URL-ADR/URL-ENFORCE là T4: cần người duyệt trước merge.

Rollback: revert commit; không có migration dữ liệu hay side effect ngoài. Server khởi động không có `--url-allowlist` vẫn đọc/duyệt được candidate cũ.
