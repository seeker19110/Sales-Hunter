# Subtask: <subtask_id> — <động từ + kết quả ngắn>

```yaml
subtask_id: "1.5.b"           # phase.stt hoặc slug
parent_phase: "1.5"
parent_task_pack: "0003-phase1.5-publication-candidate"
model_tier: "T2"              # T0 | T1 | T2 | T3 | T4
model_id_optional: ""         # điền khi orchestrator đã chọn model cụ thể
external_side_effects: "none" # none | ingest-network | affiliate-link-create | publish | account-change
```

## 1. Mục tiêu

<Một câu: việc gì phải có sau subtask này.>

## 2. Xong nghĩa là gì (DoD)

- [ ] <hành vi hoặc artifact quan sát được>
- [ ] <lệnh test/check cụ thể>
- [ ] <file docs tối thiểu nếu có — thường để subtask T0 riêng>

## 3. Phạm vi

**Được chạm:**
- `path/file` …

**Không được chạm:**
- `path/…`
- Mọi hành động ngoài hệ thống trừ mức `external_side_effects` đã khai

## 4. Bối cảnh phải đọc (theo thứ tự)

1. `AGENTS.md`
2. `docs/SUBAGENT-TASK-CONVENTION.md` (hiểu tier + cấm mở rộng phạm vi)
3. <impl spec / schema / ADR liên quan — liệt kê cụ thể>
4. <file code hiện có sẽ sửa>

## 5. Ràng buộc kỹ thuật

- TDD: <có / không — mặc định có nếu đụng code>
- Schema/version: <nếu có>
- Không float tiền; timezone-aware; …
- Policy snapshot: <nếu liên quan nguồn ngoài>

## 6. Bẫy cần tránh

- <từ TRAPS.md hoặc đặc tả phase>
- Không mở rộng sang subtask kế

## 7. Kiểm

- **Đỏ trước (nếu TDD):** `<lệnh>`
- **Xanh sau:** `<lệnh>`
- **Orchestrator:** `make check` trên nhánh tích hợp trước PR

## 8. Cấm làm

- Sửa ngoài mục 3
- Commit secret / dữ liệu thương mại thật
- Tự merge, tự bật publish, tự đổi ADR
- Tự nâng tier hoặc “tiện tay” làm subtask khác

## 9. Báo cáo trả orchestrator (bắt buộc)

```markdown
### Kết quả subtask <id>
- Trạng thái: xong | dở | chặn
- Diff chính: <file>
- Lệnh đã chạy + kết quả:
- Phát hiện ngoài phạm vi (nếu có):
- Rủi ro / cần người:
```
