# Session handoff — 2026-09-19

## Đã hoàn tất

1. **Gỡ kẹt và hợp nhất PR Dependabot**:
   - Gắn nhãn `no-changelog` cho PR #30 (`ruff` 0.16.6 -> 0.16.7) và PR #31 (`setup-uv` 10.0.1 -> 10.1.0) theo đúng kinh nghiệm trong `TRAPS.md`.
   - Cả hai PR đạt 14/14 checks CI xanh và đã được merge lần lượt vào `bootstrap/base`.
   - Mở PR #32 đồng bộ `PROJECT-STATUS.md` và `CHANGELOG.md`, qua CI và merge vào base.

2. **Triển khai Phase 4 hoàn thiện theo ADR-0006**:
   - **ADR-0006**: Quy định kiến trúc lưu trữ bền vững SQLite (`sqlite3` stdlib, zero-dependency) và xác thực Bearer/Query Token cho Operator API & Web Dashboard.
   - **Tầng lưu trữ (`SqliteOperatorStore`)**:
     - Lưu trữ bảng `candidates`, `approvals`, `publish_receipts` trong `var/operator.db` (đã gitignored).
     - Bảo toàn chặt chẽ `draft_sha256` và các invariants domain.
     - Hỗ trợ transaction, thread-safe, persistence qua các lần restart.
   - **Operator Web Dashboard & Auth**:
     - Giao diện HTML server-side rendering chuẩn stdlib, lọc theo trạng thái (`pending`, `approved`, `rejected`), xem chi tiết claim snapshot và disclosure affiliate, form duyệt/từ chối deal trực quan, chống XSS (`html.escape`).
     - Bảo vệ bằng Token Auth (`Authorization: Bearer <token>` hoặc `?token=<token>`). Endpoint `/healthz` giữ nguyên public.
     - CLI entrypoint `python -m s_n_sales.api` hỗ trợ cấu hình `--db-path` và `--token`.
   - **Kiểm thử**:
     - Tuân thủ TDD: toàn bộ test đỏ trước khi viết code tối thiểu.
     - Thêm 9 unit tests cho `SqliteOperatorStore` (`tests/test_sqlite_store.py`).
     - Thêm 11 tests cho Auth, Web Dashboard và End-to-end integration (`tests/test_operator_api.py`).
     - Tổng test suite nâng từ 55 lên 75 tests, 100% PASS.

## Bằng chứng kiểm tra cục bộ

- `uv sync --locked`: OK
- `uv run ruff check src tools tests`: Pass (0 errors)
- `uv run ruff format --check src tools tests`: Pass (38 files already formatted)
- `uv run python -m pyright src tools tests`: Pass (0 errors, 0 warnings)
- `uv run python -m unittest discover -s tests -v`: 75/75 tests PASS
- `uv run python tools/validate_repo.py`: Repository contract OK
- `uv run python tools/check_status_freshness.py`: PROJECT-STATUS.md khớp git thật
- `uv run python -m pip_audit`: No known vulnerabilities found

## Việc tiếp theo

- Merge PR cho nhánh `feat/phase4-sqlite-operator-dashboard` vào `bootstrap/base`.
- Khi có hạ tầng và domain DNS cho `sales.donghanhcungban.org`, tiến hành deploy staging và kiểm tra HTTPS read-back theo `docs/PRODUCTION-CHECKLIST.md`.
