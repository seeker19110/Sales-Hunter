# Prompt sheet — câu lệnh chuẩn

**Bộ prompt sẵn:**
- Orchestrator: [docs/prompts/ORCHESTRATOR.md](prompts/ORCHESTRATOR.md)
- Phase 1.5: [docs/prompts/phase-1.5/](prompts/phase-1.5/) — **một nhánh việc lớn, nhiều commit (mô hình A)**

## Bắt đầu phiên

```text
Đọc AGENTS.md, docs/SUBAGENT-TASK-CONVENTION.md (mô hình nhánh A mặc định), TRAPS.md, ARCHITECTURE.md, CODEMAP.md. Kiểm git status/worktree. Việc lớn → một remote branch; subtask → commit tuần tự trên nhánh đó. Gán model_tier T0–T4. Không tạo branch per subtask trừ khi parallel thật (branching B).
```

## Orchestrator — tách việc + nhánh A

```text
Bạn là orchestrator Sales-Hunter. Đọc impl phase + task-pack. Tách subtask + model_tier. Mặc định branching A: một remote branch cho cả việc lớn; mỗi subtask là commit trên nhánh đó; một PR khi xong. Chỉ đề xuất branching B khi cần parallel + path không overlap. Xuất bảng subtask + tên parent_branch rồi dừng để duyệt.
```

## Giao một subagent (trên nhánh việc lớn)

```text
Bạn là subagent Sales-Hunter. Chỉ làm đúng subtask trong block sau. Làm việc trên parent_branch đã cho (branching A) — không tạo remote branch mới. Đọc AGENTS.md và mục bối cảnh. TDD nếu có code. Kết thúc bằng báo cáo TEMPLATE-SUBTASK (kèm gợi ý commit message có subtask_id).

<dán TEMPLATE-SUBTASK hoặc docs/prompts/phase-... đã điền>
```

## Thêm adapter nền tảng

```text
Trước khi code adapter: ADR + tài liệu chính thức + ngày đọc. Không scrap. Tối thiểu T4 + human trước mạng. Một nhánh feat/2-... cho việc lớn adapter; subtask commit tuần tự trên nhánh đó.
```

## Chuẩn bị đăng nội dung

```text
Kiểm publication candidate, freshness, disclosure, allowlist, approval hash. Dry-run mặc định. Publish thật = T4. Không nhận "đã đăng" từ model.
```

## Kết thúc phiên

```text
make check / unittest; đọc diff. Session log: subtask_id, tier, parent_branch, commit. Không quên phần dở cho phiên sau trên CÙNG nhánh việc lớn nếu chưa mở PR.
```
