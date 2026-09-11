# Checklist an toàn affiliate

Checklist này là baseline kỹ thuật, không thay thế điều khoản của từng chương trình affiliate/kênh.

## Nguồn và quyền truy cập

- [ ] `source_method` chỉ là `official_api`, `authorized_export` hoặc `manual`.
- [ ] Có URL chính sách/điều khoản, khu vực áp dụng, ngày đọc và người chịu trách nhiệm.
- [ ] Không tự động hóa đăng nhập, CAPTCHA, cookie hoặc cơ chế chống bot.
- [ ] Có timeout, rate limit, retry có trần và kill switch theo adapter.
- [ ] Credential nằm ngoài repo; log chỉ dùng account reference/fingerprint.

## Tính trung thực của deal

- [ ] Giá, tồn kho, voucher và shipping có `observed_at` cùng evidence.
- [ ] Tách giá niêm yết, giá hiển thị, phí vận chuyển và ưu đãi phụ thuộc người mua.
- [ ] Không nói “rẻ nhất”, “sắp hết”, “chỉ hôm nay” nếu không có phép đo tương ứng.
- [ ] Eligibility, minimum spend, cap và stacking không bị bỏ qua.
- [ ] Observation quá freshness policy hoặc nguồn lỗi phải chặn claim, không quy thành “không có sale”.
- [ ] Có đường thu hồi/cập nhật nội dung khi deal hết hạn.

## Link và attribution

- [ ] Link chỉ do API/công cụ được ủy quyền hoặc thao tác manual có receipt tạo ra.
- [ ] Kiểm HTTPS, hostname allowlist và đích sau redirect.
- [ ] Không cloaking, cookie stuffing, click giả hoặc tự ghép tham số tracking chưa được phép.
- [ ] Link hết hạn/revoked không được đăng lại.
- [ ] Không đổi destination sau approval mà không duyệt lại.

## Nội dung và disclosure

- [ ] Disclosure affiliate/hoa hồng hiển thị rõ ràng.
- [ ] Mỗi claim thương mại truy được về snapshot/evidence.
- [ ] Sản phẩm hạn chế và claim sức khỏe/tài chính/trẻ em đi qua ruleset + người duyệt.
- [ ] Tài sản hình ảnh/video/nhạc có quyền sử dụng.
- [ ] Dùng disclosure hoặc nhãn AI gốc của nền tảng khi policy hiện hành yêu cầu.

## Dữ liệu và side effect

- [ ] Test dùng dữ liệu synthetic/fixture đã khử nhạy cảm.
- [ ] Mặc định chỉ lưu analytics tổng hợp; PII cần use case, căn cứ và retention riêng.
- [ ] Publisher kiểm approval hash, idempotency key và compliance trước khi gửi.
- [ ] Sau side effect, đọc lại đúng platform object/receipt trước khi báo thành công.
- [ ] Lần bật network adapter, tạo link thật hoặc publish đầu tiên phải có người duyệt.
