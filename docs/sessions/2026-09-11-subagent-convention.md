# Session 2026-09-11 — Quy ước subagent task

## Đã hoàn thành
- Thêm `docs/SUBAGENT-TASK-CONVENTION.md` (chuẩn chia phase → subtask → model_tier T0–T4).
- Thêm `docs/task-packs/TEMPLATE-SUBTASK.md`.
- Cập nhật `TASK-PACK.md`, `PROMPT-SHEET.md`, `AGENTS.md` để tham chiếu quy ước.
- CHANGELOG.

## Quyết định
- Orchestrator tách việc; subagent không tự mở rộng phạm vi.
- Side effect mạng/publish → tối thiểu T3, thường T4 + human.
- Không hard-code tên model vendor trong repo; chỉ bắt buộc `model_tier`.

## Không được quên
- Mọi phase sau này áp dụng quy ước này trước khi giao agent.
