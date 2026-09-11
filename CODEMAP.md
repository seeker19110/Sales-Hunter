# CODEMAP.md — muốn đổi gì thì chạm đâu

| Muốn | Nguồn sự thật | Phải kiểm |
|---|---|---|
| Đổi luật làm việc | `AGENTS.md`, `CONTRIBUTING.md` | `make check`, đọc diff |
| **Chia phase / giao subagent / chọn model** | **`docs/SUBAGENT-TASK-CONVENTION.md`**, `docs/task-packs/TEMPLATE-SUBTASK.md` | mỗi subtask có `model_tier` T0–T4; T4 cần người |
| Đổi kiến trúc/rành giới module | `ARCHITECTURE.md`, ADR mới trong `docs/adr/` | link ADR trong PR |
| Gắn platform DHCB / subdomain | `docs/PLATFORM.md`, `docs/adr/0002-platform-subdomain-dhcb.md` | không leak dữ liệu Learning |
| Đổi trường quan sát ưu đãi | `schemas/offer-observation.v1.json`, `docs/HOP-DONG-DU-LIEU.md` | version mới nếu breaking; `make check` |
| Đổi hợp đồng bản nháp đăng | `schemas/publication-candidate.v1.json`, `docs/HOP-DONG-DU-LIEU.md` | approval/hash/disclosure invariants |
| Đổi hợp đồng duyệt | `schemas/approval-record.v1.json` | draft_sha256 khớp, decided_by/at |
| Đổi hợp đồng receipt đăng | `schemas/publish-receipt.v1.json` | read-back từ nền tảng, idempotency |
| Đổi xếp hạng | `src/s_n_sales/domain/ranking.py`, `schemas/rank-result.v1.json` | reasons + rank_version, không model |
| Đổi Money / tiền | `src/s_n_sales/domain/money.py` | không float; test biên |
| Pipeline draft từ observation | `src/s_n_sales/pipeline/draft.py` | unit test |
| Publication candidate builder | `src/s_n_sales/pipeline/` + `docs/impl/PHASE-1.5-IMPLEMENTATION.md` | disclosure + draft_sha256 |
| Fake fixture adapter | `src/s_n_sales/adapters/fake.py` | không mạng |
| Thêm nền tảng | adapter mới + tài liệu nguồn chính thức + contract test | rate limit, domain allowlist, ToS; subtask ≥ T4 |
| Lộ trình phát triển | `docs/ROADMAP.md`, `docs/PHASES.md`, `docs/impl/` | task pack + subtask theo convention |
| Thêm cổng CI | `.github/workflows/ci.yml`; nối vào `needs` của `quality` | PR thật phải chạy cổng đó |
| Ghi bẫy tái diễn | `TRAPS.md` | ngày, triệu chứng, nguyên nhân, cách rà, PR |
| Giao việc phiên mới | `docs/TASK-PACK.md` / `docs/task-packs/` | đủ mục tiêu, phạm vi, nghiệm thu; việc lớn → subtask |
