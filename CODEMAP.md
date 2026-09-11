# CODEMAP.md — muốn đổi gì thì chạm đâu

| Muốn | Nguồn sự thật | Phải kiểm |
|---|---|---|
| Đổi luật làm việc | `AGENTS.md`, `CONTRIBUTING.md` | `make check`, đọc diff |
| Đổi kiến trúc/rành giới module | `ARCHITECTURE.md`, ADR mới trong `docs/adr/` | link ADR trong PR |
| Đổi trường quan sát ưu đãi | `schemas/offer-observation.v1.json`, `docs/HOP-DONG-DU-LIEU.md` | version mới nếu breaking; `make check` |
| Đổi hợp đồng bản nháp đăng | `schemas/publication-candidate.v1.json`, `docs/HOP-DONG-DU-LIEU.md` | approval/hash/disclosure invariants |
| Đổi hợp đồng duyệt | `schemas/approval-record.v1.json` | draft_sha256 khớp, decided_by/at |
| Đổi hợp đồng receipt đăng | `schemas/publish-receipt.v1.json` | read-back từ nền tảng, idempotency |
| Đổi xếp hạng | `schemas/rank-result.v1.json` + domain ranking service | reasons + rank_version, không model |
| Thêm nền tảng | adapter mới + tài liệu nguồn chính thức + contract test dùng fixture đã khử dữ liệu nhạy cảm | rate limit, domain allowlist, lỗi/quota, ToS |
| Đổi cách tính giá/giảm giá/xếp hạng | domain service xác định + test biên | tiền nguyên, timezone, stale data, đối chiếu độc lập |
| Đổi tạo link affiliate | module `affiliate` của adapter + allowlist | test open-redirect, ký URL, idempotency |
| Đổi nội dung hoặc prompt | nguồn prompt có version + schema output + fixture/eval offline | không gọi model trả phí trong CI |
| Đổi đăng kênh | `publishing` + ADR quyền hành động | dry-run, approval hash, idempotency, read-back receipt |
| Lộ trình phát triển | `docs/ROADMAP.md` | task pack tương ứng |
| Thêm cổng CI | `.github/workflows/ci.yml`; nối vào `needs` của `quality` | PR thật phải chạy cổng đó |
| Ghi bẫy tái diễn | `TRAPS.md` | ngày, triệu chứng, nguyên nhân, cách rà, PR |
| Giao việc phiên mới | `docs/TASK-PACK.md` / `docs/task-packs/` | đủ mục tiêu, phạm vi, nghiệm thu |

Các đường dẫn module chưa có trong cây file là **điểm đặt dự kiến**, không phải lời khẳng định đã triển khai. Khi chọn stack ứng dụng, ADR phải cập nhật bảng này bằng path thật trước hoặc cùng PR đầu tiên.
