# Handoff — chuẩn hóa branding Sales-Hunter

- Nhánh: `fix/sales-hunter-branding`.
- Đã đổi mọi tên hiển thị cũ trong tài liệu, prompt và docstring thành `Sales-Hunter`.
- Đã đổi package metadata từ `s-n-sales` sang `sales-hunter` trong `pyproject.toml` và `uv.lock`.
- Giữ nguyên package Python `s_n_sales` và schema `$id` `s-n-sales.local`: đây là định danh kỹ thuật/contract v1; đổi chúng cần migration và rà toàn bộ consumer, không nằm trong chuẩn hóa branding hiển thị.
- Cần chạy `make check`, kiểm markdown/repository contract và xem diff trước khi mở PR.
