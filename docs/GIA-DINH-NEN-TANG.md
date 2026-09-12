# Giả định và nguồn nền tảng

File này ngăn mã nguồn biến phỏng đoán về Shopee/TikTok thành “sự thật”. Chỉ đánh dấu `đã xác minh` sau khi đọc tài liệu/agreement áp dụng cho đúng tài khoản, khu vực và ngày hiện tại.

| Nền tảng | Năng lực | Trạng thái | Nguồn chính thức | Ngày đọc | Người chịu trách nhiệm | Ghi chú |
|---|---|---|---|---|---|---|
| Shopee Việt Nam | đọc catalog/giá/promotion | chưa xác minh | — | — | — | chưa được viết adapter mạng |
| Shopee Việt Nam | tạo link affiliate | chưa xác minh | — | — | — | chưa được tự ghép tracking parameter |
| Shopee Việt Nam | publish nội dung | chưa xác minh | — | — | — | draft-only |
| TikTok Shop Việt Nam | đọc catalog/giá/promotion | chưa xác minh | — | — | — | chưa được viết adapter mạng |
| TikTok Shop Việt Nam | tạo link affiliate | chưa xác minh | — | — | — | chưa được tự ghép tracking parameter |
| TikTok | publish/disclosure nội dung | chưa xác minh | — | — | — | draft-only |

## Khi xác minh một năng lực

Ghi rõ:

- URL/tên agreement và phiên bản;
- account/program, khu vực và scope OAuth liên quan;
- auth flow, quota, rate limit, pagination, timezone/currency;
- trường dữ liệu được lưu và thời hạn giữ;
- hành động nào là read-only, tạo link, publish hoặc account-change;
- fixture đã khử dữ liệu nhạy cảm và contract test;
- ngày cần rà lại policy.

Không fallback sang scraping hoặc browser automation chỉ vì API chính thức thiếu capability. Trường hợp manual phải được ghi `source_method=manual` và không giả là dữ liệu live tự động.


## Manual observation pipeline (Phase 2)

| Năng lực | Trạng thái | Ghi chú |
|----------|------------|---------|
| Nạp observation từ file JSON (`source_method=manual`) | **đã xác minh (kỹ thuật repo)** | Adapter `src/s_n_sales/adapters/manual.py`; không mạng |
| Giá trị thương mại / claim public | **chưa** — phụ thuộc người cung cấp file | Operator chịu trách nhiệm độ trung thực của file |
| Official API Shopee/TikTok | chưa xác minh | Xem bảng trên; cần ADR riêng khi có nguồn |

Ngày ghi: 2026-09-11. ADR liên quan: `docs/adr/0003-manual-first-observation.md`.
