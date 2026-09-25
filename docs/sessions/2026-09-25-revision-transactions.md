# DATA — bằng chứng thực thi

Base 0fea065, parent source PR39 f48346c. Local snapshot tree9479850 khớp upstream.
Không có subagent; local Python3.13.5/jsonschema4.26.0. `uv sync --locked` exit1 do DNS;
không gọi local suite là locked CI.

- Baseline: 110 tests OK.
- Input red: 4 tests/12 failures; import tự khai approved, thiếu claim, trường lạ, bool/float.
- Input green: 4 tests OK trên cùng regression.
- HTTP red: 17 tổng tests, 4 failures/1 error (missing revision, ETag, stale form, Host/UTF8).
- HTTP green: 17 tests OK; race dùng hai connection + barrier, không sleep giả.
- Migration red: preview API chưa tồn tại; 3 errors, rollback regression đã pass.
- Migration green: 4 tests OK; nguồn read-only, manifest khớp, schema rollback khi hash sai.
- Positive test fixtures và smoke cũ gửi revision đã đọc; test receipt cũ dùng payload ngoài
  schema đã được chuyển sang publish-receipt.v1 hợp lệ, không bỏ kiểm idempotency.
- Green diagnostic cuối: 133 tests OK (Python3.13.5); Ruff0.16.7 lint/format và validate_repo đều exit0.
- Full locked/type/browser/clean wheel phải đọc CI trên HEAD thực; chưa tuyên bố tại checkpoint này.

No live API/publish/credential/DNS/deploy/migration user data. ADR0008 đề xuất; human T4
bắt buộc trước merge. PostgreSQL/RBAC production và các epic PUB/DEAL/LEDGER/OPS chưa nằm
trong phạm vi nghiệm thu DATA. Rerun rollback bằng database fixture, không production.
