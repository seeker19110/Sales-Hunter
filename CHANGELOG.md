# Changelog

Mọi thay đổi đáng kể của dự án được ghi tại đây theo [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) và Conventional Commits.

## Chưa phát hành

### Thêm

- `docs/impl/PHASE-1-IMPLEMENTATION.md`: đặc tả triển khai chi tiết Phase 1 (hiện trạng + phần còn lại).
- `docs/impl/PHASE-1.5-IMPLEMENTATION.md`: đặc tả kỹ thuật đầy đủ Phase 1.5 (builder, canonical hash, disclosure, TDD).
- Task-pack `0003-phase1.5-publication-candidate.md`.
- `docs/PHASES.md`: đặc tả đầy đủ Phase 1.5 → Phase 6 (mục tiêu, phạm vi, nghiệm thu, ràng buộc, rủi ro).
- Cập nhật ROADMAP với Phase 1.5 và lộ trình ưu tiên vòng kín hợp pháp.
- Runtime validation cho raw observation trước ranking; từ chối schema-invalid, giá trị tiền boolean, timestamp thiếu timezone và URL không HTTPS.
- Typecheck Pyright, dependency audit bằng pip-audit và Dependabot cho uv/GitHub Actions.
- Hướng dẫn triển khai có kiểm chứng cho `sales.donghanhcungban.org`; domain chưa được triển khai khi chưa có HTTP service, DNS/TLS và read-back.

### Sửa

- Ranking yêu cầu clock có timezone để kết quả tái tạo được.
- Thêm `.gitattributes` để checkout source/config theo LF trên Windows.

### Đã có từ trước

- Khung vận hành + schema v1 + CI/CD placeholder.
- Đặc tả Phase 1 schemas approval/receipt/rank + ROADMAP.
- ADR-0002 + PLATFORM: subdomain `sales.donghanhcungban.org` của donghanhcungban.org.
- Phase 1 code: `Money`, ranking deterministic, pipeline, fake adapter, tests.
