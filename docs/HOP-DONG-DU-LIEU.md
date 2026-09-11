# Hợp đồng dữ liệu v1

## `offer-observation.v1`

Một lần adapter nhìn thấy ưu đãi. Đây không phải “giá hiện tại mãi mãi”. Consumer phải dùng `observed_at`, chính sách độ mới và trạng thái nguồn trước khi tạo claim.

Bất biến ngoài khả năng biểu đạt đầy đủ của JSON Schema:

- `sale_price_minor <= list_price_minor` khi có giá niêm yết;
- số tiền là integer theo đơn vị nhỏ nhất của `currency`;
- giá niêm yết, giá sale và shipping là ba trường riêng; `null` nghĩa là chưa biết, không phải miễn phí;
- hash bằng SHA-256 của payload raw đã canonicalize theo quy ước adapter;
- `source_url` và `product_url` phải qua allowlist/redirect validation;
- coupon/eligibility có thể phụ thuộc tài khoản, khu vực và thời điểm; không tự áp vào mọi người dùng.
- `source_method` chỉ nhận nguồn chính thức, export được ủy quyền hoặc nhập tay; v1 không hợp thức hóa scraping.

## `publication-candidate.v1`

Bản nháp nội dung chuẩn bị duyệt. `claim_snapshot` đóng băng dữ liệu dùng để viết; `draft_sha256` bao phủ nội dung, link, disclosure và snapshot theo canonicalization sẽ được định nghĩa trong code triển khai.

Publisher tương lai phải từ chối khi:

- approval không ở trạng thái `approved`;
- approval không trỏ đúng `draft_sha256` hiện tại;
- observation quá cũ theo policy của nền tảng/kênh;
- URL ngoài allowlist hoặc redirect chưa kiểm;
- thiếu affiliate disclosure;
- idempotency key đã có receipt thành công.

## `approval-record.v1`

Quyết định duyệt/từ chối một bản nháp. Bắt buộc có `decided_by` + `decided_at`. Approval chỉ có hiệu lực khi `draft_sha256` khớp bản nháp hiện tại; sửa nội dung/link → approval cũ vô hiệu.

## `publish-receipt.v1`

Bằng chứng đăng thành công do **publisher đọc lại** từ nền tảng (`platform_post_id`, `platform_post_url`, `read_back_at`). Không được sinh từ model hay ghi cục bộ “đã đăng”.

## `rank-result.v1`

Kết quả xếp hạng **xác định**. `score` và `reasons` phải tái tạo được từ observation + `rank_version`. Không dùng model để sinh điểm số.

## Versioning

Thay đổi làm consumer cũ hiểu sai dữ liệu phải tạo `*.v2.json`; không sửa semantics âm thầm trong v1. Thêm trường optional vẫn phải cập nhật fixture/contract test và changelog.
