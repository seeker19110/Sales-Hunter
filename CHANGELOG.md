# Changelog

Mọi thay đổi đáng kể của dự án được ghi tại đây theo [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) và Conventional Commits.

## Chưa phát hành

### Thêm

- `docs/SUBAGENT-TASK-CONVENTION.md`: quy ước chia phase/việc lớn thành subtask, giao subagent, chọn model theo tier T0–T4.
- `docs/task-packs/TEMPLATE-SUBTASK.md`: mẫu giao từng subagent.
- `docs/impl/PHASE-2` … `PHASE-6-IMPLEMENTATION.md` và task-pack 0004–0008.
- `docs/impl/PHASE-1` / `PHASE-1.5-IMPLEMENTATION.md` và task-pack 0003.
- `docs/PHASES.md` + ROADMAP Phase 1.5.
- Runtime validation observation; Pyright; pip-audit; Dependabot; hướng dẫn deploy subdomain.

### Sửa

- `AGENTS.md`, `TASK-PACK.md`, `PROMPT-SHEET.md`: gắn quy ước subagent.
- Ranking yêu cầu clock có timezone.
- `.gitattributes` LF trên Windows.

### Đã có từ trước

- Khung vận hành + schema v1 + CI placeholder.
- ADR-0002 + PLATFORM subdomain.
- Phase 1 code: Money, ranking, pipeline, fake adapter, tests.
