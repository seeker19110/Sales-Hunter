# ADR-0008 — Revision giao dịch và lịch sử bất biến cho pilot SQLite

Trạng thái: đề xuất, cần human T4 trên diff cuối trước merge. Ngày 25/09/2026.
Bổ sung ADR-0006, giữ nguyên schema publication-candidate.v1 và approval-record.v1.
Không thay database production hoặc cấp quyền network/publish.

## Quyết định đề xuất trước code

Mỗi candidate có revision số nguyên tăng sau create/edit/approve/reject. Đây là version
của trạng thái operator (bao gồm quyết định), không thay canonical hash channel-agnostic.
Mọi version lưu thành snapshot chỉ-thêm; sự kiện giữ actor/time/previous revision và
approval đầy đủ. Không giả tạo lịch sử trước thời điểm migration.

Client phải gửi revision đã nhìn thấy khi sửa/duyệt, qua If-Match hoặc form hidden.
Thiếu -> 428; cũ -> 409. Server sinh revision; caller không tự khai approval state. API
nhập candidate v1 chỉ chấp nhận pending đúng schema/hash; service tạo draft từ input
không có trường server. Hai đường đều không cho phép caller tự duyệt.

SQLite transaction BEGIN IMMEDIATE gom đọc so revision, cập nhật projection, snapshot,
current approval và event. Không giữ transaction qua lời gọi network. Hai connection
tranh cùng revision chỉ một ghi thành công. Revert nội dung A->B->A không hồi sinh
approval cũ; mọi edit invalidates current approval trong cùng transaction.

OperatorStore dùng cùng implementation SQLite :memory: thay hai bộ luật khác nhau.
Read snapshot trả candidate và revision từ cùng SELECT. Publisher đọc candidate/approval
trong cùng snapshot; outbox tiếp theo còn phải kiểm trước send và xử lý outcome_unknown.

Migration thêm column/table/trigger chỉ-thêm. Trước backfill kiểm schema/hash/status liên
quan. Dữ liệu cũ lỗi -> rollback toàn transaction, không âm thầm đổi approved thành hợp lệ.
Manifest lưu count và SHA256 dữ liệu đầu vào; chạy lại không thêm lịch sử giả. Có preview
chỉ đọc; không chạy migration trên database người dùng ở phiên này. Rollback code nên dùng
phiên bản tương thích hoặc restore kiểm soát; không drop history để rollback.

Nguồn kiểm chứng 25/09/2026:
- https://www.sqlite.org/lang_transaction.html (BEGIN IMMEDIATE, một writer)
- https://docs.python.org/3.11/library/sqlite3.html (isolation_level=None, backup, executescript)
Không dùng executescript bên trong transaction bảo toàn vì nó có thể implicit commit.

## Cổng nghiệm thu

Regression input/schema, revision thiếu/cũ, ABA, approve/reject/edit/reload đúng schema,
thread + hai connection, trigger không cho sửa history, migration dữ liệu lỗi rollback,
HTTP 409/428 và form revision. PostgreSQL/concurrency multi-node và RBAC production không
được tuyên bố đạt từ các test SQLite pilot.
