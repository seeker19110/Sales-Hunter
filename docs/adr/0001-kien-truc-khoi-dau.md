# ADR-0001: Kiến trúc khởi đầu cho S-N Sales

- Trạng thái: Chấp nhận
- Ngày: 2026-09-11

## Bối cảnh

Repository bắt đầu trống. Sản phẩm dự kiến săn sale và gắn link affiliate trên Shopee/TikTok Shop, nhưng chưa có đặc tả API, quyền nền tảng, tải, kênh đăng hay mô hình dữ liệu production. Bê nguyên runtime multi-agent từ Claude-Agents sẽ tạo hạ tầng chưa có consumer.

## Quyết định

1. Bắt đầu bằng modular monolith với adapter tách theo nền tảng và hợp đồng JSON version hóa.
2. Lưu quan sát nguồn theo kiểu chỉ-thêm; bản chuẩn hóa là dữ liệu dẫn xuất có thể tái tạo.
3. Code xác định chịu trách nhiệm tính toán, validate, link affiliate, idempotency và publish; model chỉ tạo/phân loại dữ liệu có schema.
4. Pipeline dừng ở draft + human approval. Auto-publish chỉ được bật bởi ADR sau khi có kill switch, audit, idempotency và read-back receipt.
5. Khung repo gồm luật, task pack, codemap, traps thật, session handoff, CI, gitleaks và schema contracts. Không mang bus SQLite, gateway model, console, hệ agent/topic/gate, golden/eval hay supervisor từ Claude-Agents ở giai đoạn này.

## Hệ quả

- Có thể thêm adapter đầu tiên mà không khóa stack triển khai quá sớm.
- Mọi breaking contract cần schema version mới và kế hoạch chuyển đổi.
- Chưa có sản phẩm chạy thật; README phải tiếp tục nói rõ trạng thái này.
- Nếu sau này cần hàng đợi bền vững, multi-agent hoặc tự động đăng, quyết định đó phải dựa trên số đo/sự cố thật thay vì sao chép kiến trúc nguồn.

## Phương án không chọn

- **Sao chép toàn bộ Claude-Agents:** bỏ vì phần lớn giải quyết orchestration phát triển phần mềm, không phải săn sale.
- **Microservices ngay:** bỏ vì chưa có tải/ranh giới đội ngũ và làm transaction/audit phức tạp sớm.
- **Model tự quyết định và đăng:** bỏ vì giá/link là dữ liệu thương mại biến động và side effect công khai cần kiểm soát tất định.
