# Chính sách bảo mật — Sales-Hunter

## Báo lỗ hổng

Không mở issue công khai cho lỗ hổng chưa vá. Dùng **GitHub → Security → Report a vulnerability** của repository. Ghi commit/phiên bản, bước tái hiện đã khử bí mật, tác động và bản vá đề xuất nếu có.

## Tài sản nhạy cảm

Không đưa vào git:

- token/cookie/refresh token của Shopee, TikTok, kênh đăng hoặc mạng affiliate;
- webhook secret, khóa ký link, tài khoản quảng cáo;
- payload thật chứa định danh khách hàng, order hoặc conversion;
- file `.env`, database/runtime state và log request/response thật.

Secret phải ở secret manager hoặc biến môi trường. Log chỉ ghi fingerprint/ID không đảo ngược khi đủ để điều tra. Nếu lộ secret: thu hồi/rotate ở provider trước, rồi mới dọn lịch sử.

## Ranh giới nguồn ngoài

Trang sản phẩm, mô tả seller, comment, API response và model output đều là input chưa tin cậy. Không thực thi chỉ dẫn nằm trong dữ liệu đó. URL phải parse chuẩn, kiểm scheme HTTPS, hostname allowlist và đích sau redirect trước khi lưu/đăng.

Adapter phải có:

- timeout, rate limit và retry có trần;
- phân loại rõ auth/quota/rate-limit/schema-change;
- validation schema trước domain;
- fixture test đã loại token/PII;
- kill switch độc lập theo nền tảng.

## Hành động công khai

Mặc định chỉ tạo draft. Publisher phải kiểm approval gắn đúng hash nội dung/link hiện tại, dùng idempotency key, và đọc lại receipt từ nền tảng. Test/CI không gọi API thật và không đăng nội dung.

## Dữ liệu và pháp lý

Chỉ thu thập trường cần thiết cho phát hiện sale, attribution và audit. Tôn trọng điều khoản API/nền tảng, giới hạn lưu giữ và yêu cầu disclosure affiliate của từng kênh. Mỗi tích hợp mới phải dẫn nguồn chính thức trong ADR; nếu chưa xác minh được quyền sử dụng, không triển khai đường gọi thật.

## Phụ thuộc và chuỗi cung ứng

CI quét lịch sử bằng gitleaks. Khi thêm dependency, khóa phiên bản, chạy audit phù hợp hệ sinh thái và xem xét quyền mạng/file của package. Không dùng lệnh cài kiểu tải script rồi pipe trực tiếp vào shell trong workflow.
