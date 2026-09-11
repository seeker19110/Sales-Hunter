# Changelog

Mọi thay đổi đáng kể của dự án được ghi tại đây theo [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) và Conventional Commits.

## Chưa phát hành

### Thêm

- `docs/impl/PHASE-2-IMPLEMENTATION.md` … `PHASE-6-IMPLEMENTATION.md`: đặc tả triển khai chi tiết toàn bộ phase còn lại.
- Task-pack `0004` → `0008` (adapter, approval/publisher, staging UI, analytics, production).
- `docs/impl/PHASE-1-IMPLEMENTATION.md` và `PHASE-1.5-IMPLEMENTATION.md`.
- Task-pack `0003-phase1.5-publication-candidate.md`.
- `docs/PHASES.md`: đặc tả Phase 1.5 → Phase 6.
- Cập nhật ROADMAP với Phase 1.5 và lộ trình ưu tiên vòng kín hợp pháp.
- Runtime validation cho raw observation trước ranking; từ chối schema-invalid, giá trị tiền boolean, timestamp thiếu timezone và URL không HTTPS.
- Typecheck Pyright, dependency audit bằng pip-audit và Dependabot cho uv/GitHub Actions.
- Hướng dẫn triển khai có kiểm chứng cho `sales.donghanhcungban.org`.

### Sửa

- Ranking yêu cầu clock có timezone để kết quả tái tạo được.
- Thêm `.gitattributes` để checkout source/config theo LF trên Windows.

### Đã có từ trước

- Khung vận hành + schema v1 + CI/CD placeholder.
- Đặc tả Phase 1 schemas approval/receipt/rank + ROADMAP.
- ADR-0002 + PLATFORM: subdomain `sales.donghanhcungban.org`.
- Phase 1 code: `Money`, ranking deterministic, pipeline, fake adapter, tests.
