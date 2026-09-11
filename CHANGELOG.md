# Changelog

Mọi thay đổi đáng kể của dự án được ghi tại đây theo [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) và Conventional Commits.

## Chưa phát hành

### Thêm

- Khung vận hành lập trình rút gọn từ Claude-Agents: luật repo, kiến trúc, codemap, task pack, prompt sheet, bảo mật, schema v1 và CI.
- CI tăng cường: job `schema` tách riêng, `ruff format --check`, matrix Python 3.11/3.12, trigger `bootstrap/base`.
- CD placeholder (dry-run, chưa deploy) trong `.github/workflows/cd.yml`.

### Thay đổi

- Makefile: thêm `format-check`, `schema`; `check` gồm lint + format + test + schema.
