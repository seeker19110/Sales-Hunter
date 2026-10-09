# PROJECT STATUS — Sales-Hunter

> **Single source of truth cho tiến độ thực thi.** Đọc trước ROADMAP và đối chiếu GitHub trước mỗi phiên.

## Snapshot hiện tại

- Ngày cập nhật: 2026-10-09
- Base branch: `bootstrap/base`
- Base hiện tại: `7e00135063207bf0b38f0b62870c783708142f0e`
- Base đã có skeleton Phase 1–6, #35 audit, #36 packaging, #37 giá/dashboard, #38 integrity, #40 projection, #39 local auth, #41 revision/transaction/history, #42 facts/eligibility/grounded payload, #43 durable publishing (intent/lease/reconcile/recall, chỉ transport fake) và #47 audit từng dòng 2026-10-09 (ranh giới HTTP, JSON chặt, fencing worker/recall, urllib3 2.8.0, throttle đăng nhập, audit dependency hàng tuần).
- Chưa production/staging thực, chưa client nền tảng thật, chưa đổi DNS/secret hoặc chạy migration dữ liệu người dùng. Dry-run, pause toàn cục mặc định và review vẫn là cổng bắt buộc.

## Nhánh và PR còn mở

- [#48](https://github.com/seeker19110/Sales-Hunter/pull/48) allowlist URL ADR-0011 (nhánh `claude/affectionate-bohr-pk3fsx`, làm lại từ base `7e00135`, target `bootstrap/base`): hợp đồng `url-allowlist.v1`, `config/url-allowlist.v1.json` rỗng (fail-closed), builder/manual flow/`POST /api/v1/candidates` bắt buộc policy. T4 → cần người duyệt trước merge. Xem [session](docs/sessions/2026-10-09-url-allowlist.md).
- #46 DHCB read-only pilot [T4]: target `bootstrap/base` `a78da48`; chưa merge, cần human T4.
- #44 setup-uv 10.2.0 và #45 Ruff 0.16.8 (dependabot): base cũ `e458f21`, cần đồng bộ base mới và kiểm lại CI; nhãn `no-changelog` theo TRAPS.
- Không miễn kiểm tra CHANGELOG, không skip/xfail/giảm validation, không tự merge PR T4. HEAD/run mới nhất phải đọc GitHub.

## Bằng chứng và điểm tiếp tục

- [Audit từng dòng 2026-10-09](docs/sessions/2026-10-09-line-audit.md) với [task pack](docs/task-packs/2026-10-09-audit-hardening.md); [audit gốc 2026-09-25](docs/audits/2026-09-25/README.md) giữ nguyên; [ma trận 27 mục](docs/implementation/2026-09-25/execution-matrix.md) là checkpoint lịch sử.
- Việc còn lại cần ADR/owner: analytics bền vững, identity/roles trước staging ngoài; thêm domain nền tảng thật vào allowlist cần nguồn chính thức + ngày kiểm chứng (owner). Luồng legacy chỉ kiểm HTTPS được xử lý bởi ADR-0011 ([#48](https://github.com/seeker19110/Sales-Hunter/pull/48), đang mở).
- Analytics/ledger, operator form/CSV/inbox/bulk workflow, lịch sử giá, identity nhiều người dùng, server/TLS production và restore drill chưa hoàn tất. Publishing dùng manual/fake; không suy quyền API/account từ test mô phỏng.
- Django/PostgreSQL cần ADR được chấp nhận; chưa tự thay stdlib/SQLite. ADR0003/0004 có điều kiện, checklist/evidence vẫn bắt buộc trước cutover.

## Quy tắc resume

Đọc file này trước, đối chiếu base/PR/CI rồi đọc AGENTS/TRAPS/ARCHITECTURE/CODEMAP và quy ước subtask. Bảo toàn worktree; không push trực tiếp hoặc force base, không bypass test/review. Sau mỗi thay đổi cập nhật checkpoint và ghi session. Không dùng CI xanh thay human review, không gọi PR mở là đã merge hay fake receipt là live success.
