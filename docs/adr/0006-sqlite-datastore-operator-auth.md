# ADR-0006: Lưu trữ bền vững SQLite và Xác thực Token cho Operator API / Dashboard

- Trạng thái: Chấp nhận
- Ngày: 2026-09-19
- Người chịu trách nhiệm: Sales-Hunter Core Team
- Phase: 4

## Bối cảnh

Tại Phase 4 (Staging + Operator UI), hệ thống cần một HTTP service tối thiểu phục vụ người vận hành duyệt bản nháp ưu đãi và kiểm soát quy trình xuất bản theo tài liệu đặc tả [PHASE-4-IMPLEMENTATION](../impl/PHASE-4-IMPLEMENTATION.md) và ghi chú mục 4 trong [PROJECT-STATUS.md](../../PROJECT-STATUS.md) (*"Trước API operator public cần ADR auth/authorization và datastore"*).

Hiện tại:
1. `OperatorStore` (`src/s_n_sales/api/store.py`) lưu trữ dữ liệu dạng in-memory dictionary. Mọi ứng viên (`publication-candidate`) và quyết định duyệt (`approval-record`) sẽ bị mất khi khởi động lại server.
2. Operator API chưa có cơ chế xác thực kiểm soát quyền truy cập, tiềm ẩn rủi ro thao tác trái phép khi bind vào môi trường staging.
3. Chưa có giao diện người dùng (Dashboard) trực quan để operator quan sát claim snapshot, affiliate disclosure và ra quyết định phê duyệt/từ chối.

## Quyết định

1. **Lưu trữ bền vững bằng SQLite (`sqlite3` stdlib):**
   - Sử dụng thư viện chuẩn `sqlite3` của Python, không thêm external dependencies (như ORM, SQLAlchemy).
   - Đường dẫn database mặc định đặt tại `var/operator.db` (thư mục `var/` và file `*.db` đã được định cấu hình trong `.gitignore`). Hỗ trợ cấu hình database path tùy chọn hoặc `:memory:` cho kiểm thử tự động.
   - Thiết kế 3 bảng dữ liệu chính:
     - `candidates`: lưu thông tin bản nháp với `publication_id` (PRIMARY KEY), `draft_sha256` (TEXT NOT NULL), `status` (TEXT NOT NULL: `pending`/`approved`/`rejected`), `candidate_json` (TEXT NOT NULL), `created_at` (TEXT NOT NULL), `updated_at` (TEXT NOT NULL).
     - `approvals`: lưu hồ sơ phê duyệt với `publication_id` (PRIMARY KEY), `draft_sha256` (TEXT NOT NULL), `status` (TEXT NOT NULL), `decided_by` (TEXT NOT NULL), `decided_at` (TEXT NOT NULL), `reason` (TEXT), `approval_json` (TEXT NOT NULL).
     - `publish_receipts`: lưu biên lai xuất bản với `receipt_id` (PRIMARY KEY), `idempotency_key` (TEXT UNIQUE NOT NULL), `target_channel` (TEXT NOT NULL), `published_at` (TEXT NOT NULL), `receipt_json` (TEXT NOT NULL).
   - Bảo toàn chặt chẽ bất biến `draft_sha256` từ ADR-0005: khi duyệt bản nháp, hàm `decide_approval` kiểm tra và gắn cứng `draft_sha256` của candidate vào bản ghi approval.

2. **Xác thực Token Auth cho Operator API & Dashboard:**
   - Xác thực qua Bearer Token: Header `Authorization: Bearer <token>`.
   - Hỗ trợ tham số query `?token=<token>` cho các yêu cầu `GET` từ trình duyệt web.
   - Token được cấu hình qua biến môi trường `OPERATOR_TOKEN` hoặc tham số `auth_token: str | None` trong application factory. Nếu `auth_token` là `None` (hoặc chuỗi rỗng), hệ thống vận hành ở chế độ dev/test mở.
   - Endpoint `/healthz` luôn là public endpoint, trả về trạng thái hoạt động mà tuyệt đối không lộ token, secret hay PII.

3. **Giao diện Web Operator Dashboard tối giản:**
   - Tích hợp trực tiếp trong HTTP handler của `app.py` bằng HTML server-side rendering chuẩn (sử dụng `html.escape` chống XSS).
   - Danh sách bản nháp `GET /dashboard`: bảng trực quan lọc theo trạng thái (`all`, `pending`, `approved`, `rejected`), hiển thị ID, nền tảng, giá bán, discount và trạng thái.
   - Chi tiết bản nháp `GET /dashboard/candidates/{id}`: hiển thị toàn bộ claim snapshot, nội dung nháp, disclosure affiliate, điểm và lý do ranking.
   - Form thao tác: `POST /dashboard/candidates/{id}/approve` và `POST /dashboard/candidates/{id}/reject`.

4. **Kỷ luật an toàn xuất bản:**
   - Tiếp tục giữ nguyên cờ `dry_run = True` mặc định và kill switch toàn hệ thống.
   - Không kích hoạt bất kỳ side effect mạng ngoài nào trong phạm vi này.

## Hệ quả

- **Ưu điểm:**
  - Bản nháp và biên bản duyệt được lưu trữ bền vững, sống qua các chu kỳ khởi động lại tiến trình.
  - Người vận hành có thể truy cập dashboard trên trình duyệt để kiểm tra và duyệt deal một cách thuận tiện, có trách nhiệm giải trình.
  - Zero-dependency: không làm phình `pyproject.toml` hay tăng diện tích tấn công của dependency chuỗi cung ứng.
- **Ranh giới:**
  - SQLite phục vụ mô hình modular monolith và tải đơn tiến trình hoặc đa luồng cục bộ. Khi mở rộng multi-node trong tương lai, việc chuyển sang Postgres sẽ tuân theo một ADR riêng.

## Bằng chứng và kiểm chứng

- Toàn bộ hành vi của `SqliteOperatorStore` được kiểm thử qua unit tests độc lập (`tests/test_sqlite_store.py`).
- Các kịch bản xác thực Token và Web Dashboard được kiểm thử qua `tests/test_operator_api.py`.
- TDD: Test đỏ trước khi code, toàn bộ test suite và linting đạt chuẩn 100%.
