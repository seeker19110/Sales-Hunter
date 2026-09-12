# Changelog

Mọi thay đổi đáng kể của dự án được ghi tại đây theo [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) và Conventional Commits.

## Chưa phát hành

### Thêm

- Phase 1.5: builder `publication-candidate.v1` deterministic với `claim_snapshot`, `draft_sha256`, disclosure bắt buộc, pending approval và idempotency key.
- Unit/contract coverage cho hash stability, HTTPS affiliate URL, disclosure, claim snapshot và schema validation.
- `docs/prompts/ORCHESTRATOR.md` + `docs/prompts/phase-1.5/*`: prompt sẵn — mỗi subagent một subtask Phase 1.5.
- `docs/SUBAGENT-TASK-CONVENTION.md` + `TEMPLATE-SUBTASK.md`; áp dụng toàn cục README/CODEMAP/CONTRIBUTING/ROADMAP/PHASES/QUY-TRINH-GIT.
- `docs/impl/PHASE-*` và task-pack 0003–0008; PHASES + ROADMAP Phase 1.5.
- Runtime validation observation; Pyright; pip-audit; Dependabot; hướng dẫn deploy subdomain.

### Sửa

- Chuẩn hóa tên hiển thị và package metadata thành Sales-Hunter.
- `AGENTS.md`, `TASK-PACK.md`, `PROMPT-SHEET.md`: gắn quy ước subagent và link prompts.
- Ranking yêu cầu clock có timezone.
- `.gitattributes` LF trên Windows.

### Đã có từ trước

- Khung vận hành + schema v1 + CI placeholder.
- ADR-0002 + PLATFORM subdomain.
- Phase 1 code: Money, ranking, pipeline, fake adapter, tests.
