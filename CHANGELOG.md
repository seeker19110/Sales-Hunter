# Changelog

Mọi thay đổi đáng kể của dự án được ghi tại đây theo [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) và Conventional Commits.

## Chưa phát hành

### Thêm

- Khung vận hành lập trình rút gọn từ Claude-Agents: luật repo, kiến trúc, codemap, task pack, prompt sheet, bảo mật, schema v1 và CI.
- Đặc tả Phase 1: schema `approval-record.v1`, `publish-receipt.v1`, `rank-result.v1` kèm examples valid/invalid.
- `docs/ROADMAP.md` và task pack `0002-phase1-domain-core`.
- Mở rộng hợp đồng dữ liệu và luật AGENTS (Money, allowlist, ranking deterministic).
- CI tăng cường: job `schema` tách riêng, `ruff format --check`, matrix Python 3.11/3.12, trigger `bootstrap/base`.
- CD placeholder (dry-run, chưa deploy) trong `.github/workflows/cd.yml`.

### Thay đổi

- Makefile: thêm `format-check`, `schema`; `check` gồm lint + format + test + schema.
