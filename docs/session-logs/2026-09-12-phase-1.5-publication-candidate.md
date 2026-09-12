# Session log — Phase 1.5 publication candidate

Ngày: 2026-09-12

## Phạm vi

- Thêm pure builder `build_publication_candidate`.
- Thêm canonical `compute_draft_sha256`.
- Bắt buộc disclosure, HTTPS affiliate URL và pending approval hash-bound.
- Thêm unit + contract tests.

## Side effects

Không có side effect mạng/publish trong runtime mới.

## Kiểm định

CI của branch/PR là nguồn xác nhận cuối cùng cho unittest, static, schema và repository contracts.
