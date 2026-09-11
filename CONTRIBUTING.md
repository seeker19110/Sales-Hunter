# Đóng góp vào S-N Sales

## 1. Chuẩn bị

Cần Python 3.11+ và `uv`:

```bash
uv sync --locked
```

Cài hook tùy chọn:

```bash
uv tool install pre-commit
pre-commit install
```

## 2. Luồng thay đổi

1. Đọc `AGENTS.md`, `TRAPS.md`, `ARCHITECTURE.md` và `CODEMAP.md`.
2. Với việc nhiều file, điền `docs/TASK-PACK.md`.
3. Tạo nhánh riêng theo `docs/QUY-TRINH-GIT.md`.
4. Nếu đổi kiến trúc/schema/quyền xuất bản, viết ADR trước.
5. Viết test đỏ cho hành vi mới hoặc lỗi tái hiện được.
6. Viết code tối thiểu để xanh; sau đó mới refactor.
7. Chạy cổng, tự đọc diff, cập nhật tài liệu và changelog.
8. Push, mở PR, chờ `quality` và `metadata` xanh; chỉ squash merge sau đó.

## 3. Cổng chất lượng

```bash
uv run ruff check tools tests
uv run ruff format --check tools tests
uv run python -m unittest discover -s tests -v
uv run python tools/validate_repo.py
```

Hoặc `make check`.

CI jobs:

| Job | Việc |
|-----|------|
| `static` | ruff lint + ruff format --check |
| `schema` | `tools/validate_repo.py` (file bắt buộc, link markdown, schema + examples) |
| `unit` | unittest trên Ubuntu/Windows × Python 3.11/3.12 |
| `audit` | gitleaks toàn lịch sử |
| `quality` | tất cả job trên phải `success` |
| `metadata` (PR policy) | Conventional Commits title + CHANGELOG |

CD hiện là **placeholder dry-run** (`.github/workflows/cd.yml`). Không publish/deploy cho tới khi có ADR.

Khi đã có mã ứng dụng, PR thêm stack phải đồng thời bổ sung typecheck, unit/integration test, build và audit phụ thuộc vào `quality`; không thay các cổng hiện có bằng cổng yếu hơn.

## 4. Thay đổi hợp đồng

- Thêm trường optional tương thích: có thể cập nhật cùng version nếu semantics không đổi.
- Xóa/đổi tên/đổi nghĩa/siết kiểu: tạo file schema version mới và kế hoạch chuyển đổi.
- Mỗi adapter có contract test với fixture đã khử dữ liệu nhạy cảm.
- Mọi công thức giá/giảm giá/hoa hồng phải có test biên và không dùng float.

## 5. Definition of Done

- [ ] Phạm vi khớp task pack/ADR; không có sửa dọn ngoài lề.
- [ ] Test từng đỏ đúng lý do rồi xanh với bản sửa.
- [ ] Lint, format, test, repository contract và CI xanh.
- [ ] Không có secret, payload thật, log debug hoặc file sinh ngoài ý muốn.
- [ ] Hành động ngoài hệ thống có dry-run, idempotency và read-back khi áp dụng.
- [ ] `README.md`, `ARCHITECTURE.md`, `CODEMAP.md`, schema và changelog được cập nhật khi liên quan.
- [ ] PR nêu phần chưa kiểm được thay vì suy đoán.
