# Handoff — Sales-Hunter hardening, branding và trạng thái

- Nhánh: `chore/sales-hunter-hardening`.
- Chuẩn hóa mọi tên hiển thị còn lại thành Sales-Hunter; giữ `s_n_sales` và schema v1 để không phá contract.
- Đồng bộ roadmap/README/architecture/deploy với `PROJECT-STATUS`: skeleton đã merge, còn năng lực production/T4 chưa hoàn tất.
- Đổi Pyright và pip-audit sang `python -m` để tránh lỗi Windows console-script trampoline.
- Không có side effect mạng, deploy, affiliate link hoặc publish.
- Owner đã chấp nhận có điều kiện ADR-0003 và ADR-0004 ngày 2026-09-12; chưa có account/platform credential, owner hạ tầng hoặc auth/datastore ADR để chạy side effect.
