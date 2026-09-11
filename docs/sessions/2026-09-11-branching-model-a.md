# Session 2026-09-11 — Mô hình nhánh A toàn cục

## Quyết định
- **Mặc định toàn cục:** phương án A — 1 việc lớn = 1 remote branch; subtask = commit tuần tự; 1 PR.
- **Ngoại lệ B:** chỉ khi parallel thật + không overlap path.
- Nhiều việc lớn: nhiều nhánh → rebase/merge tuần tự theo phụ thuộc.

## Đã cập nhật
- SUBAGENT-TASK-CONVENTION.md (§2.1, §2.2, §7, §10)
- QUY-TRINH-GIT.md, TEMPLATE-SUBTASK, PROMPT-SHEET, CONTRIBUTING
- prompts/phase-1.5/README.md

## Hệ quả
- Phase 1.5 code đã làm đúng tinh thần A (`feat/1.5-publication-candidate`).
- Không khuyến khích feat/1.5.a, feat/1.5.b riêng khi một agent tuần tự.
