# Audit execution matrix — đợt hoàn thiện 25/09/2026

Base đã đối chiếu: `0fea06578b04b832c07df6b31c60444510d25c79`, CI36150453741 success.
Lịch sử audit không bị sửa. Đây là source checkpoint; đọc lại GitHub khi tiếp tục.

## Registry bằng chứng

| Key | PR / HEAD / CI | Trạng thái tích hợp | Test / giới hạn |
|---|---|---|---|
| BASE | #36 packaging, #37 UI, #38 integrity/UTC, #40 projection; base0fea065 | Đã merge | clean-wheel, browser, schema, matrix CI; không live |
| AUTH | #39 / f48346c / CI36150731331 success | Chờ human T4; chưa merge | local Bearer/session/CSRF; chưa roles/TLS production |
| DATA | #41 / 75c302b / CI36156814136 và metadata36156814141 success | Chờ #39 + refresh + humanT4/ADR0008 | 133 diagnostic tests; CI đủ Windows/Ubuntu/browser/wheel; SQLite pilot, không PostgreSQL |
| DEAL | feat/audit-deal-quality-20260925 / xem PR HEAD | Local verified, chưa merge/CI tại checkpoint | 161 tổng diagnostic tests; test_deal_quality, test_grounded_flow; runtime smoke mở rộng; ADR0009/T4 |
| NONE | Chưa có implementation được nghiệm thu | Không tính hoàn tất | Cần code/test/CI/review tương ứng |

## SH-001–027

| ID | Hiện trạng và phạm vi sửa | Dependency / nghiệm thu còn thiếu | Evidence |
|---|---|---|---|
| SH-001 | Hash thực tế đã merge; DATA thêm snapshot/revision chống ABA | DATA tích hợp; không giữ DB transaction qua network | BASE/DATA |
| SH-002 | Authority đầy đủ/current đã merge; revision/event atomic trong DATA | AUTH identity; scoped final payload và queue trong PUB; humanT4 | BASE/DATA |
| SH-003 | AUTH local fail-closed; DATA thêm Host/Origin/framing/time/UTF8 | Review #39; roles/object permissions, TLS và production server riêng | AUTH/DATA |
| SH-004 | Runtime deps/package schemas/clean wheel đã merge | DEAL có hai contract mới, phải qua wheel gate đúng HEAD | BASE/DEAL |
| SH-005 | Legacy publisher còn RAM dictionary | PUB durable intent/atomic lease/attempt/readback/restart/unknown-outcome tests | NONE |
| SH-006 | DATA chỉ nhận pending đúng schema/hash; DEAL manual input không cho caller IDs/hash/approval | Tích hợp DATA/DEAL; legacy import giữ tương thích nhưng không đủ điều kiện queue mới nếu thiếu facts | DATA/DEAL |
| SH-007 | Projection schema đúng đã merge #40; DATA validates transitions/reload | DATA migration thêm history, không giả lịch sử cũ | BASE/DATA |
| SH-008 | DATA revision CAS, HTTP409/428, hai connection chỉ một thắng | HumanT4/ADR0008 + merge; PostgreSQL concurrency chưa chạy | DATA |
| SH-009 | DATA version/event chỉ-thêm, edit invalidate authority, ABA không hồi approval | Merge DATA; final-payload decision events PUB chưa có | DATA |
| SH-010 | Canonical integer VND/null/zero/platform/mobile + browser đã merge | UI mới phải giữ đúng dữ liệu thực builder | BASE |
| SH-011 | DEAL deterministic final payload link/disclosure/facts/hash/channel và binding bất biến | PUB duyệt đúng payload revision và gửi/readback chính payload đó |
| SH-012 | DEAL eligibility kiểm freshness/stock/expiry/evidence | PUB kiểm lại trước send, recall intent/thực thi/xác nhận | DEAL |
| SH-013 | DEAL eligible_rank chặn độc lập score | Queue mới phải cưỡng chế cùng policy; không gọi legacy score là authorization | DEAL |
| SH-014 | DEAL facts.v1 giữ toàn observation/variant/coupon/ship/conditions/evidence, total có chứng cứ riêng | ADR0009/review; dữ kiện vẫn là nguồn manual có attestation, không platform-live proof | DEAL |
| SH-015 | DEAL exact-host HTTPS allowlist/redirect, public-address validation | Transport phải pin resolved address và verify TLS; actual connector permission chưa có | DEAL |
| SH-016 | UTC đã merge; helpers giữ aware UTC cho facts/evidence | Không có timestamp provider live | BASE/DEAL |
| SH-017 | Pause legacy còn transient | PUB persist global/source/channel actor/reason/time; restart/pre-send tests | NONE |
| SH-018 | DATA input/framing/Host/Origin/time limits local | Accepted production framework/server ADR, external readiness/load tests | AUTH/DATA |
| SH-019 | Analytics skeleton cũ | Durable dedup events/conversion lifecycle/commission ledger/signature/replay | NONE |
| SH-020 | Artifact gate đã có; DATA preview migration/count/hash/rollback | OPS doctor/backup/restore drill, pause after restore, deployment/heartbeat | BASE/DATA |
| SH-021 | Checkpoint/registry cập nhật, tách stack chưa merge | Đồng bộ sau mỗi merge, selected production ADR và actual runbook evidence | DATA/DEAL |
| SH-022 | Chưa có credential/account capability official được xác minh | Disabled live; hoàn thiện manual/fake transport và official capability review trước network | NONE |
| SH-023 | Base preflight kênh/hash, DATA authority snapshot | PUB per-channel durable outcomes/unknown/reconcile/scoped payload | BASE/DATA/DEAL |
| SH-024 | Base mobile + DEAL manual JSON preview không ghi DB thực | OPS CSV/form/inbox/search/pagination/revision diff/bulk permission and browser actions | BASE/DEAL |
| SH-025 | DEAL retained JSON, source/retained digests, immutable metadata, redaction/expiry/revoke/tombstones | OPS authorized export/retention UI; redaction là known-sensitive policy, không máy tự chứng minh mọi PII đã sạch | DEAL |
| SH-026 | DATA contracts/errors/snapshot + DEAL facts/payload schemas/manual-input whitelist | API/UI/queue/ledger new boundaries phải nối/test; không chỉ thêm DTO không sử dụng | DATA/DEAL |
| SH-027 | DEAL business key đúng seller/product/variant/conditions và retained rank_version/reasons | LEDGER price history + PUB persistent cooldown, duplicate/restart tests | DEAL |

## AI nội dung

DEAL có template baseline và composer schema-constrained: model chỉ chọn introduction và
thứ tự mọi fact IDs; không được thêm số/link/nội dung tự do hoặc bỏ điều kiện. Prompt/model/
policy/cost ceiling/call cap/cache được cấu hình và kiểm bằng fake model; thiếu model/budget
hoặc output sai -> template. Chưa có SDK/provider live, chưa benchmark có phí, không tuyên
bố chất lượng văn phong free-form đã được đánh giá. Test tiếng Việt có coupon, null/zero,
stale/stock/variant và nguồn chứa instruction không cấp quyền tool/publish.

Source: phần triển khai nội bộ đang kiểm/stack. Staging và production: chưa deploy, không
credential thật/DNS/network publishing. Chờ review không phải lý do bỏ các epic độc lập.
