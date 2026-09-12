# Handoff — execution readiness

## Đã hoàn thành

- Subtask 10.b (T3, side effect: none): cấu hình package Sales-Hunter editable qua Hatchling. Các lệnh quality được quy định giờ chạy trực tiếp trên PowerShell, không cần `PYTHONPATH` từ Makefile.
- Bằng chứng xanh: `uv sync --locked`; Ruff; Pyright; unittest (53 tests); repository contract; pip-audit. Pip-audit không thấy dependency có lỗ hổng và bỏ qua package nội bộ không có trên PyPI.

## Blocker

- 10.a / 10.d / 10.e vẫn cần tài liệu official + account/program, owner DNS/origin/secret manager và publisher/channel được phép. Không có network, DNS/TLS hay publish được thực hiện.
- `publish_multi_channel` đổi `target_channel` sau approval dù nó nằm trong `draft_sha256`; phải có ADR T4 + human chốt semantics hash/approval trước publisher thật.

## Không được quên

- `.hermes/` là untracked có sẵn, không thuộc thay đổi readiness.
- Không tick production checklist khi chưa có evidence hạ tầng/read-back thực tế.
