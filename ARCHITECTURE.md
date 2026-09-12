# ARCHITECTURE.md — bản đồ Sales-Hunter

## Trạng thái

Kiến trúc mục tiêu được chấp nhận ở [ADR-0001](docs/adr/0001-kien-truc-khoi-dau.md). Hiện có skeleton Phase 1–6: domain core, manual adapter, approval/publisher dry-run, operator HTTP API in-memory, analytics và runbook. Chưa có adapter mạng, tạo link affiliate, persistence production, client publish thật hoặc deploy subdomain.

## Luồng chính

```text
Shopee adapter ─┐
                ├─> raw observations ─> normalize ─> validate ─> rank
TikTok adapter ─┘                                           │
                                                            v
analytics <─ published receipt <─ publisher <─ approval <─ content draft
```

## Ranh giới module dự kiến

| Module | Trách nhiệm | Không được làm |
|---|---|---|
| `adapters` | Gọi nguồn được phép, giới hạn tốc độ, chuyển payload thành quan sát có bằng chứng | Tự xếp hạng hoặc tự đăng |
| `catalog` | Nhận diện sản phẩm/merchant giữa các lần quan sát | Gộp sản phẩm chỉ bằng tiêu đề gần giống |
| `offers` | Chuẩn hóa giá, coupon, tồn kho; kiểm invariants | Dùng model để tính số |
| `ranking` | Chấm điểm bằng hàm xác định, version hóa trọng số | Che giấu lý do chọn ưu đãi |
| `affiliate` | Tạo/kiểm link theo adapter và allowlist domain | Tin URL do model sinh |
| `content` | Tạo bản nháp có snapshot claim và disclosure affiliate | Đánh dấu đã đăng |
| `approval` | Lưu người duyệt, thời điểm, nội dung đã duyệt | Duyệt lại ngầm khi nội dung đổi |
| `publishing` | Đăng lũy đẳng, đọc lại receipt từ nền tảng | Đăng mặc định trong test/dev |
| `analytics` | Nhận click/conversion theo attribution có nguồn | Gắn danh tính người dùng nếu không cần thiết |

Bắt đầu bằng **modular monolith**: ranh giới là package/interface trong một ứng dụng và một kho dữ liệu. Chỉ tách service khi có số đo tải, cô lập lỗi hoặc quyền truy cập buộc phải tách.

## Dòng dữ liệu và sự thật

1. `raw observation` là dữ liệu chỉ thêm, giữ hash payload và thời điểm thu thập.
2. `normalized offer` là bản dẫn xuất; có thể tái tạo từ raw + phiên bản normalizer.
3. `content draft` đóng băng snapshot claim dùng khi viết nội dung.
4. Approval gắn với hash bản nháp. Sửa nội dung hoặc link làm approval cũ mất hiệu lực.
5. `published receipt` chỉ hợp lệ khi publisher nhận và đọc lại định danh từ nền tảng.

Hợp đồng hiện có:

- [`offer-observation.v1.json`](schemas/offer-observation.v1.json): quan sát ưu đãi từ adapter.
- [`rank-result.v1.json`](schemas/rank-result.v1.json): kết quả ranking từ observation đã validate.
- [`publication-candidate.v1.json`](schemas/publication-candidate.v1.json): bản nháp chuẩn bị duyệt/đăng.

## Yêu cầu xuyên suốt

- Mọi consumer lũy đẳng theo định danh sự kiện/bản nháp.
- Retry có trần, exponential backoff và dead-letter/escalation; không lặp vô hạn.
- Đồng hồ, timezone, currency và rounding được truyền tường minh.
- Metric tách “không có sale” khỏi “không thu thập được dữ liệu”.
- Có kill switch theo nền tảng và toàn hệ thống trước khi bật auto-publish.
- Sales được deploy độc lập tại `sales.donghanhcungban.org`; không chia sẻ dữ liệu/credential Learning mặc định.
