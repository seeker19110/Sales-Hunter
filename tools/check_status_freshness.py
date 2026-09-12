"""Đối chiếu PROJECT-STATUS.md với git thật.

Bẫy đang phòng: PROJECT-STATUS.md là văn xuôi tự do, không có gì đối chiếu nó với
git — nên nó có thể lệch thực tế (SHA cũ, nhánh đã xóa) mà không ai nhận ra. Script
này chỉ chạy được đáng tin trên `bootstrap/base` sau khi đã fetch đủ lịch sử
(``git fetch --unshallow`` hoặc checkout với ``fetch-depth: 0``).

Kiểm:
  PF-1: SHA ghi ở "Base hiện tại" phải là tổ tiên của (hoặc bằng) HEAD hiện tại.
  PF-2: nếu file có dòng "Nhánh đang làm: `<tên>`", nhánh đó phải còn tồn tại
        trên remote `origin` — nếu không, dòng đó là tàn dư của một nhánh đã merge.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

STATUS_FILE = Path("PROJECT-STATUS.md")
SHA_RE = re.compile(r"Base hiện tại:\s*`([0-9a-f]{7,40})`")
BRANCH_RE = re.compile(r"Nhánh đang làm:\s*`([^`]+)`")


def run_git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    return result.stdout.strip()


def fail(message: str) -> None:
    print(f"PROJECT-STATUS.md lỗi thời: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    if not STATUS_FILE.exists():
        print("PROJECT-STATUS.md không tồn tại — bỏ qua.")
        return 0

    text = STATUS_FILE.read_text(encoding="utf-8")

    sha_match = SHA_RE.search(text)
    if sha_match:
        sha = sha_match.group(1)
        check = subprocess.run(
            ["git", "merge-base", "--is-ancestor", sha, "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if check.returncode not in (0, 1):
            fail(
                f"không xác định được SHA `{sha}` trong lịch sử "
                "(fetch có đủ sâu không? cần fetch-depth: 0)."
            )
        if check.returncode == 1:
            fail(
                f"SHA `{sha}` ở mục 'Base hiện tại' không phải tổ tiên của HEAD — "
                "cập nhật lại PROJECT-STATUS.md với HEAD mới sau khi merge."
            )

    branch_match = BRANCH_RE.search(text)
    if branch_match:
        branch = branch_match.group(1)
        remote_branches = run_git("branch", "-r")
        if f"origin/{branch}" not in remote_branches.split():
            fail(
                f"nhánh `{branch}` ghi ở 'Nhánh đang làm' không còn tồn tại trên "
                "remote — có thể đã merge/xóa mà PROJECT-STATUS.md chưa cập nhật."
            )

    print("PROJECT-STATUS.md khớp git thật.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
