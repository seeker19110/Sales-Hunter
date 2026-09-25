# PROJECT STATUS — Sales-Hunter

> Điểm resume thực thi. Đối chiếu GitHub trước mọi thay đổi; CI và source không thay bằng chứng staging/production.

## Snapshot đã kiểm

- Ngày cập nhật: 2026-09-25.
- Base branch: `bootstrap/base`.
- Base hiện tại: `0fea06578b04b832c07df6b31c60444510d25c79` (PR #40), CI push 36150453741 success.
- Đã merge: #35 audit (tài liệu), #37 giá/dashboard, #36 runtime packaging, #38 integrity/current approval/UTC, #40 candidate approval projection.
- Phase 1–6 là skeleton đã có trước; không phải toàn bộ 27 hạng mục đã hoàn thiện.
- Chưa network client nền tảng, DNS/TLS/cutover production hoặc đăng công khai. Dry-run là mặc định.

## Stack đang thực thi

| Epic | Bằng chứng source/CI | Gate tích hợp |
|---|---|---|
| AUTH #39 | HEAD `f48346c8596073a464c8289605945e9617ce9c4f`, CI36150731331 success; Bearer/session/CSRF local, đề xuất ADR0007 | Chưa merge; human T4 trên HEAD cuối; external identity/TLS không thuộc nghiệm thu này |
| DATA #41 | HEAD `75c302b7ba0eda15c6eb1b4228713c8192cd10be`, tree6af8047; CI36156814136 + metadata36156814141 success, 133 tests local, Windows/Ubuntu, browser và wheel đều đạt | Stack trên #39; refresh sau squash và human T4/ADR0008; không auto-merge khi thiếu dependency/review |
| DEAL `feat/audit-deal-quality-20260925` | 161 tests local; facts/evidence/eligibility/final payload/manual input/grounded composer đã có source và contracts | Stack trên #41; CI remote chưa xác minh tại checkpoint; ADR0009/T4 trước merge |
| PUB / LEDGER / OPS | Theo task pack toàn đợt; không tính các lời đề xuất là code hoàn tất | Chỉ mở quyền tích hợp sau các gate tương ứng; không gọi kết quả fake là live |

DATA: revision đã xem bắt buộc, CAS transaction, lịch sử chỉ-thêm, invalidate approval khi
edit, snapshot authority nguyên tử, ETag/409/428, migration preview read-only và rollback
legacy lỗi. Không đồng nhất SQLite pilot với PostgreSQL multi-node.

DEAL: observation đầy đủ trong deal-facts.v1, evidence giữ payload khử nhạy cảm và hai hash
nguồn/bản lưu; permission attestation/expiry/tombstone. Eligibility độc lập score, variant,
stock, stale/future, coupon/conditions. Renderer giữ link/disclosure/điều kiện và payload
hash/version/channel. Nhập manual tạo ID/hash phía server; preview không ghi DB thực.
Model tùy chọn chỉ chọn introduction/order fact IDs đã khóa, không tự tạo số/link/text.
Không có adapter LLM trả phí được bật hoặc provider benchmark/live verification.

## Còn thiếu hoặc bị chặn

- PUB: final-payload scoped approval, outbox/lease/attempt/unknown outcome, pause bền vững,
  kiểm freshness trước send, receipt/reconcile/recall và cooldown qua restart.
- LEDGER: history giá theo variant, conversion/commission events bền vững và chống webhook trùng.
- OPS/UI: CSV/form preview và inbox/bulk được phân quyền, doctor/backup/restore drill,
  health/heartbeat/structured log, runtime configuration và deploy tái lập.
- Production: framework/database ADR chưa được chấp nhận; Django/PostgreSQL không tự
  triển khai hay coi là đã chọn. Quyền account/program/scope/quota official, zone/origin,
  secret manager/on-call và staging evidence phải có trước live cutover.
- T4 human review là gate riêng cho từng diff. AI review/CI không thay người ký.

## Tài liệu và resume

1. Đọc file này, xác minh base/PR mở/checks/review trên GitHub; không reset về audit #35.
2. Đọc AGENTS/TRAPS/ARCHITECTURE/CODEMAP và ADR/task pack liên quan.
3. Làm trên một branch mỗi epic; một integrator, không có subagent thật trong phiên này.
4. Giữ nguyên historic audit; ghi test/HEAD/CI mới vào session và execution matrix.
5. Source chỉ được đánh dấu merged khi đọc lại merge SHA/base/checks; stack chưa được
   tích hợp không được coi là complete. Không ép merge hoặc chạy migration user data.

- [Task pack toàn đợt](docs/task-packs/2026-09-25-completion.md)
- [Ma trận 27 hạng mục](docs/implementation/2026-09-25/execution-matrix.md)
- [Audit lịch sử](docs/audits/2026-09-25/README.md)
- [Roadmap](docs/ROADMAP.md) và [Checklist production](docs/PRODUCTION-CHECKLIST.md)
