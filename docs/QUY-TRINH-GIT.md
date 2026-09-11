# Quy trình Git — S-N Sales

Luồng chuẩn: **đặc tả → tách subtask + tier → một nhánh việc lớn (mô hình A) → TDD/commit theo subtask → PR → CI → squash merge → quan sát**.

Gắn [SUBAGENT-TASK-CONVENTION.md](SUBAGENT-TASK-CONVENTION.md):

- **Mặc định (A):** 1 việc lớn = 1 remote branch; mỗi subtask = commit trên cùng nhánh; 1 PR khi xong.
- **Ngoại lệ (B):** remote branch per subtask chỉ khi parallel thật + không overlap path.
- Nhiều việc lớn: nhiều nhánh → **rebase rồi merge tuần tự** theo phụ thuộc kế hoạch.

## 1. Đặc tả trước code

ADR trước khi đổi kiến trúc, schema breaking, nguồn thu thập, link affiliate, quyền đăng.

Việc lớn: bảng subtask + `model_tier` + `branching: A` trước khi mở nhánh.

## 2. Nhánh và worktree

- Không commit/push trực tiếp `main` / base được protect.
- Tên nhánh việc lớn: `feat/<slug>`, `fix/<slug>`, `docs/<slug>`, `chore/<slug>`.
- **Không** đặt tên `feat/1.5.a-...` cho từng subtask trừ khi branching B.
- Có thể ghi subtask trong **commit message**, ví dụ: `test(publication): 1.5.a đỏ compute_draft_sha256`.
- Một worktree cho một nhánh việc lớn khi làm tuần tự.

```bash
git fetch origin
git worktree add -b feat/<viec-lon> ../s-n-sales-wt-<viec-lon> origin/<base>
```

Sau khi việc lớn trước đã merge:

```bash
git fetch origin
git checkout feat/<viec-lon-sau>
git rebase origin/<base>
# make check → push --force-with-lease nếu đã push trước rebase
```

## 3. Commit

Conventional Commits. Một commit một ý (thường = một subtask).  
Trên mô hình A: nhiều commit trên cùng nhánh trước khi mở PR.

## 4. Trước khi push / PR

```bash
uv sync --locked
make check
git diff --check
git status --short
git diff origin/<base>...HEAD
```

Cập nhật CHANGELOG; body PR liệt kê `subtask_id` + `model_tier`.

## 5. Pull request

- Một PR cho một việc lớn (A), trừ khi tách draft PR giữa chừng có lý do review.
- Tiêu đề Conventional Commits.
- Không merge khi `quality` / `metadata` chưa xanh.
- T4: ghi nhận người duyệt.
- Mặc định **squash merge**, xóa nhánh.

## 6. Sau merge

Kiểm workflow trên base. Hồi quy production → kill switch + revert bằng PR mới.
