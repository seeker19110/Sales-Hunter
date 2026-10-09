# Audit từng dòng và vá cứng sau Phase 1–6 (2026-10-09)

Phạm vi: yêu cầu của owner ngày 2026-10-09 ("audit từng dòng code từng quy trình rồi hoàn thiện"), owner giao toàn quyền quyết định trong luật `AGENTS.md`. Branching A: một nhánh `claude/affectionate-bohr-pk3fsx`, subtask là commit tuần tự; một integrator, không subagent.

Baseline: `bootstrap/base` `a78da48eac625621fd22371563eb5a828db2bf39` (#43 đã merge). Mọi cổng cục bộ xanh trừ `pip_audit` (urllib3 2.7.0 có 3 CVE).

| subtask_id | model_tier | dependency | allowed scope | acceptance |
|---|---|---|---|---|
| AUD-READ | T1 | baseline | đọc toàn bộ `src/`, `tools/`, CI; probe cục bộ | danh sách phát hiện có tái hiện, không sửa code |
| AUD-HTTP | T3 | AUD-READ | `api/app.py`, `domain/json_value.py`, adapter JSON loader | lỗi handler trả 4xx/5xx ổn định, JSON trùng khóa bị từ chối, URL dashboard mã hóa đúng một lần |
| AUD-PUB | T4 | AUD-READ | `publishing/worker.py`, `publishing/recall.py`, `pipeline/publisher.py` | mất lease sau khi provider nhận không làm worker crash và không gửi lại; recall giữ `outcome_unknown` khi transport lỗi; quét recall không bị giới hạn trang |
| AUD-STORE | T2 | AUD-READ | `api/contracts.py::timestamp` | timestamp lưu trữ sắp xếp được theo chuỗi |
| AUD-DEPS | T1 | baseline | `uv.lock` | `pip_audit` sạch, không đổi dependency trực tiếp |
| AUD-DOCS | T0 | preceding | CHANGELOG, TRAPS, CODEMAP, PROJECT-STATUS, session | trạng thái khớp GitHub; bẫy mới có bằng chứng |

Cấm: đổi schema/ADR/ranh giới module, nới allowlist, bật transport thật, đổi cổng CI, skip/xfail test, sửa PR đang mở khác (#44, #45, #46).

Nghiệm thu: 13 test hồi quy trong `tests/test_audit_hardening.py` đỏ trước bản sửa vì đúng lý do và xanh sau; toàn bộ cổng `CONTRIBUTING.md`, browser smoke và smoke wheel runtime-only xanh. AUD-PUB là T4: cần người duyệt trước merge.

Rollback: revert commit trên nhánh; không có migration dữ liệu hay side effect ngoài.
