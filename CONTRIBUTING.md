# Đóng góp vào S-N Sales

## 1. Chuẩn bị

Python 3.11+ và `uv`:

```bash
uv sync --locked
```

Hook tùy chọn: `pre-commit install`.

## 2. Luồng thay đổi

1. Đọc `AGENTS.md`, `TRAPS.md`, `ARCHITECTURE.md`, `CODEMAP.md`.
2. Việc lớn / phase: `docs/SUBAGENT-TASK-CONVENTION.md` — tách subtask + `model_tier`; **mô hình nhánh A** (1 việc lớn = 1 remote branch; subtask = commit tuần tự).
3. Tạo **một** nhánh việc lớn theo `docs/QUY-TRINH-GIT.md`.
4. ADR trước nếu đổi kiến trúc/schema/nguồn/publish (T4 + người).
5. Từng subtask: test đỏ → code → xanh → commit trên cùng nhánh.
6. `make check`, changelog, PR **một lần** cho việc lớn (body: danh sách subtask + tier).
7. CI xanh → squash merge.

**Cấm:** mỗi subtask một remote branch khi chỉ làm tuần tự; giao cả phase không tách subtask; overlap parallel.

## 3. Cổng chất lượng

```bash
uv run ruff check src tools tests
uv run ruff format --check src tools tests
uv run pyright src tools tests
uv run python -m unittest discover -s tests -v
uv run python tools/validate_repo.py
uv run pip-audit
```

Hoặc `make check`.

## 4. Thay đổi hợp đồng

- Optional tương thích: có thể cùng version schema nếu semantics không đổi.
- Breaking: schema version mới + kế hoạch chuyển.
- Không float cho tiền; contract test fixture đã khử nhạy cảm.

## 5. Definition of Done

- [ ] Khớp task pack + subtask; branching A (hoặc B đã khai)
- [ ] Commit trên đúng parent_branch
- [ ] Test đỏ→xanh; CI xanh
- [ ] Không secret / payload thật
- [ ] Side effect dry-run / approval khi cần
- [ ] CHANGELOG / CODEMAP khi liên quan
