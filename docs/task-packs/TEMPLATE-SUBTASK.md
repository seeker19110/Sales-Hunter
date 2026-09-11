# Subtask: <subtask_id> — <động từ + kết quả ngắn>

```yaml
subtask_id: "1.5.b"
parent_phase: "1.5"
parent_task_pack: "0003-phase1.5-publication-candidate"
model_tier: "T2"              # T0 | T1 | T2 | T3 | T4
model_id_optional: ""
branching: "A"                # A = mặc định (cùng nhánh việc lớn); B = nhánh riêng (chỉ khi parallel)
parent_branch: "feat/1.5-publication-candidate"  # bắt buộc với A
external_side_effects: "none" # none | ingest-network | affiliate-link-create | publish | account-change
```

## 1. Mục tiêu

<Một câu: việc gì phải có sau subtask này.>

## 2. Xong nghĩa là gì (DoD)

- [ ] <hành vi hoặc artifact quan sát được>
- [ ] <lệnh test/check cụ thể>
- [ ] <commit trên parent_branch nếu branching A>

## 3. Phạm vi

**Được chạm:**
- `path/file` …

**Không được chạm:**
- `path/…`
- Tạo remote branch mới (trừ khi branching B được orchestrator cho phép)
- Mọi side effect ngoài mức đã khai

## 4. Bối cảnh phải đọc (theo thứ tự)

1. `AGENTS.md`
2. `docs/SUBAGENT-TASK-CONVENTION.md` (mô hình A mặc định)
3. <impl spec / schema / ADR liên quan>
4. <file code hiện có sẽ sửa>

## 5. Ràng buộc kỹ thuật

- TDD: <có / không>
- Schema/version: <nếu có>
- Không float tiền; timezone-aware khi đụng thời gian

## 6. Bẫy cần tránh

- Không mở rộng sang subtask kế
- Không mở nhánh remote riêng khi branching A

## 7. Kiểm

- **Đỏ trước (nếu TDD):** `<lệnh>`
- **Xanh sau:** `<lệnh>`
- **Orchestrator:** `make check` trên nhánh việc lớn trước PR

## 8. Cấm làm

- Sửa ngoài mục 3
- Commit secret / dữ liệu thương mại thật
- Tự merge, tự publish, tự đổi ADR
- Tự nâng tier hoặc làm subtask khác

## 9. Báo cáo trả orchestrator

```markdown
### Kết quả subtask <id>
- Trạng thái: xong | dở | chặn
- Branch: <parent_branch>
- Commit (nếu có): <sha hoặc message>
- Diff chính: <file>
- Lệnh đã chạy + kết quả:
- Phát hiện ngoài phạm vi:
- Rủi ro / cần người:
```
