# PROJECT STATUS — Sales-Hunter

## Snapshot đối chiếu GitHub

- Ngày: 2026-09-26
- Base branch: `bootstrap/base`
- Base hiện tại: `a78da48eac625621fd22371563eb5a828db2bf39`
- #39 AUTH, #41 DATA, #42 DEAL và #43 PUB đã merge. CI push base `36203934535` success.
- #44 setup-uv và #45 Ruff còn mở tại lần kiểm tra; không replay hoặc tự merge trong đợt này.
- Chưa có bằng chứng deploy staging/production, DNS/TLS, quyền API nền tảng hoặc đăng thật.

## Nhánh tích hợp Đồng Hành

- `feat/dhcb-platform-pilot-20260926`: WSGI pilot riêng, dashboard chỉ đọc với xác thực
  độc lập, cấu hình systemd/Access và hợp đồng lối vào từ website Đồng Hành.
- Đây là implementation nguồn trên nhánh, không phải đã merge hoặc đã online.
- 12 test mới; bản chạy chẩn đoán local phải đối chiếu session. CI khóa dependency,
  human T4 trên diff cuối và ADR0011 chưa được thay bằng kết quả local.
- Xem [runbook](docs/PLATFORM-PILOT.md), [ADR0011](docs/adr/0011-platform-read-only-pilot.md)
  và [task pack](docs/task-packs/2026-09-26-platform-pilot.md).
- Pilot mở snapshot Sales bằng SQLite read-only; không migration/ghi DB, không endpoint
  approve/publish, không cấp quyền từ cookie/identity/billing Learning. API operator cũ
  tiếp tục loopback-only. Không gọi view này là operator production đầy đủ.

## Việc còn lại

Human review, khóa/audit dependency triển khai, xác nhận VPS/Cloudflare, cài staging,
HTTPS/Access read-back và restore/rollback drill còn là cổng trước kích hoạt. Lối vào
website mặc định chưa mở. Mở subdomain không đồng nghĩa bật publisher.

Analytics/ledger, operator form/CSV/inbox/bulk workflow, lịch sử giá, identity nhiều người,
full production operator và connector nền tảng thật chưa hoàn tất. Django/PostgreSQL
vẫn cần ADR riêng; không viết lại lõi trong đợt tích hợp này.

## Bằng chứng lịch sử và resume

[Ma trận audit](docs/implementation/2026-09-25/execution-matrix.md) và
[audit gốc](docs/audits/2026-09-25/README.md) là lịch sử theo checkpoint, không dùng trạng
thái PR cũ trong đó thay GitHub hiện hành. Đọc AGENTS/TRAPS/ARCHITECTURE/CODEMAP trước khi
đổi code. Không push/force base, không bypass test/human review, không giả live receipt.
