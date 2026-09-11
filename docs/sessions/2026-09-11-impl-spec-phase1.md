# Session 2026-09-11 — Đặc tả triển khai chi tiết Phase 1 & 1.5

## Việc đã làm
- Tạo `docs/impl/PHASE-1-IMPLEMENTATION.md`: hiện trạng Phase 1, phần còn lại, nghiệm thu.
- Tạo `docs/impl/PHASE-1.5-IMPLEMENTATION.md`: đặc tả kỹ thuật đầy đủ để implement publication-candidate (API, canonical hash, disclosure, test, thứ tự TDD).
- Tạo task-pack `0003-phase1.5-publication-candidate.md`.
- Cập nhật CHANGELOG.

## Quyết định
- Phase 1 coi là gần xong; phần publication-candidate chuyển hẳn sang Phase 1.5.
- Canonicalization `draft_sha256` dùng `json.dumps(..., sort_keys=True, separators=(",", ":"))` + SHA-256 UTF-8.
- Disclosure có template mặc định, không cho phép tắt.

## Việc bàn giao
- Sau khi merge PR này có thể bắt đầu code Phase 1.5 theo task-pack 0003.
