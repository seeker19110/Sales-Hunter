# Quy trình Git — S-N Sales

Luồng chuẩn: **đặc tả → (tách subtask + tier) → nhánh/worktree → TDD → PR → CI/review → squash merge → quan sát**.

Gắn với [SUBAGENT-TASK-CONVENTION.md](SUBAGENT-TASK-CONVENTION.md): mỗi subtask (hoặc nhóm subtask không overlap) map sang nhánh/PR review được.

## 1. Đặc tả trước code

Cần ADR trước khi đổi kiến trúc, schema breaking, nguồn thu thập, cách tạo link hoặc quyền đăng. Sửa lỗi cục bộ và tài liệu không cần ADR nếu không đổi quyết định hệ thống.

Việc lớn / phase: tách subtask + `model_tier` trước khi mở nhánh implement.

## 2. Nhánh và worktree

- Không commit/push trực tiếp `main`.
- Tên nhánh: `feat/<slug>`, `fix/<slug>`, `docs/<slug>`, `chore/<slug>`.
- Có thể gắn slug subtask: `feat/1.5.b-draft-sha256`.
- Mỗi phiên đồng thời dùng một worktree riêng; không checkout qua lại trong clone phiên khác.
- Hai subagent **không** dùng cùng nhánh/file overlap.

```bash
git fetch origin
git worktree add -b feat/<slug> ../s-n-sales-wt-<slug> origin/main
```

## 3. Commit

Dùng Conventional Commits: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`, `perf`, `build`, `ci`, `revert`. Một commit chứa một thay đổi logic có thể review/revert độc lập.

## 4. Trước khi push

```bash
uv sync --locked
make check
git diff --check
git status --short
git diff origin/main...HEAD
```

Kiểm toàn repo cho tên/schema vừa đổi, cập nhật `CHANGELOG.md`, và tìm PR/issue trùng trước khi mở PR.

## 5. Pull request

- Tiêu đề theo regex: `^(feat|fix|refactor|docs|test|chore|style|perf|build|ci|revert)(\([a-z0-9._/-]+\))?!?: .+`.
- Thân PR nêu mục tiêu, phạm vi, **subtask id + model_tier** (nếu có), ADR/schema liên quan, test đỏ/xanh, bằng chứng manual/read-back và phần chưa kiểm.
- Không merge khi `quality` hoặc `metadata` chưa xanh; không dùng admin bypass.
- T4 (publish, ToS, secret, cutover): cần ghi nhận người duyệt trong PR/body.
- Mặc định squash merge và xóa nhánh.
- Sau push, so `HEAD` với `origin/<nhánh>` và kiểm commit hiện trong PR.

## 6. Sau merge

Kiểm workflow trên `main`. Nếu có hồi quy production, ưu tiên dừng publisher/adapter liên quan và revert qua PR mới; không vá trực tiếp `main`.
