# PROJECT STATUS — Sales-Hunter

> **Single source of truth cho tiến độ thực thi.** Đọc trước ROADMAP và đối chiếu GitHub trước mỗi phiên.

## Snapshot hiện tại

- Ngày cập nhật: 2026-09-26
- Base branch: `bootstrap/base`
- Base hiện tại: `e458f2130eb661553fb085ae9229a7b04d365c84`
- #41 đã squash-merge trên GitHub trong lúc sửa CI. Tree `f05cfce7f3a00412e612a961dd5b5c36d724f1e7` khớp HEAD đã sửa `0cff6697`; CI sau merge `36201882276` đạt. Integrator phiên sửa CI không thực hiện merge hoặc ký human approval.
- Base đã có skeleton Phase 1–6, #35 audit, #36 packaging, #37 giá/dashboard, #38 integrity, #40 projection, #39 local auth và #41 revision/transaction/history.
- Chưa production/staging thực, chưa client nền tảng thật, chưa đổi DNS/secret hoặc chạy migration dữ liệu người dùng. Dry-run và review vẫn là cổng bắt buộc.

## PR còn mở và sửa CI

- #42 DEAL: target `bootstrap/base`; sửa UTF-8 fixture và thêm hai test mô phỏng locale Windows. CI `36201165521`/metadata `36201165470` đã đạt ở `28fbd8ce`; đang đồng bộ ancestry với squash #41 bằng merge không force. Mã nghiệp vụ/test không đổi trong lần đồng bộ này; phải kiểm CI trên HEAD mới và human T4 trước merge.
- #43 PUB: target nhánh #42; implementation handoff đã được đẩy tại `0fc86ec9f36aa66df1bb8378edafe1ff426c3af9`, không còn chỉ test/spec. Có queue/scope/reconcile/pause/cooldown/recall và ba test chống stale/expired/unleased recall confirmation. Diagnostic 197 tests đạt; đang kiểm CI remote và tiếp tục đồng bộ theo #42. Chưa merge/T4.
- #44 setup-uv: bản sửa metadata/base `23bc6bfb`, CI `36201277638`/metadata `36201277627` đạt. Bump 10.2.0 được giữ; cần kiểm lại với base mới sau #41.
- #45 Ruff: bản sửa metadata/base `41f6821e`, CI `36201323368`/metadata `36201323328` đạt. Bump 0.16.8 cùng lockfile được giữ; cần kiểm lại với base mới sau #41.
- Không miễn kiểm tra CHANGELOG, không skip/xfail/giảm validation, không tự merge PR T4. HEAD/run mới nhất phải đọc GitHub.

## Bằng chứng và điểm tiếp tục

- [Task pack CI](docs/task-packs/2026-09-26-ci-repair.md), [checkpoint DATA](docs/sessions/2026-09-26-ci-repair.md), [UTF-8 repair](docs/sessions/2026-09-26-quality-ci-repair.md), [đồng bộ sau merge DATA](docs/sessions/2026-09-26-post-data-merge-sync.md).
- [Ma trận 27 mục](docs/implementation/2026-09-25/execution-matrix.md) là checkpoint lịch sử theo nhánh; session mới và GitHub xác định trạng thái PR/CI hiện hành. [Audit gốc](docs/audits/2026-09-25/README.md) giữ nguyên.
- Tiếp tục kiểm tất cả PR trên HEAD mới; sau human T4 từng diff mới tích hợp tuần tự, refresh stack sau squash và kiểm lại CI base.
- Analytics/ledger, operator form/CSV/inbox/bulk workflow, lịch sử giá, identity nhiều người dùng, server/TLS production và restore drill chưa hoàn tất. #42/#43 dùng manual/fake; không suy quyền API/account từ test mô phỏng.
- Django/PostgreSQL cần ADR được chấp nhận; chưa tự thay stdlib/SQLite. ADR0003/0004 có điều kiện, checklist/evidence vẫn bắt buộc trước cutover.

## Quy tắc resume

Đọc file này trước, đối chiếu base/PR/CI rồi đọc AGENTS/TRAPS/ARCHITECTURE/CODEMAP và quy ước subtask. Bảo toàn worktree; không push trực tiếp hoặc force base, không bypass test/review. Sau mỗi thay đổi cập nhật checkpoint và ghi session. Không dùng CI xanh thay human review, không gọi PR mở là đã merge hay fake receipt là live success.
