# Quy ước Subagent Task — S-N Sales

**Trạng thái:** Chấp nhận (quy ước vận hành).  
**Áp dụng từ:** mọi phase và việc lớn sau khi merge tài liệu này.

---

## 1. Mục tiêu quy ước

Mỗi **phase** hoặc **việc lớn** phải được:

1. **Chia** thành các **task nhỏ** (subtask) có phạm vi rõ, nghiệm thu rõ.
2. **Giao** từng subtask cho **một subagent** (một phiên làm việc độc lập).
3. **Chọn model** theo **mức độ phức tạp** của subtask — không dùng model mạnh nhất cho mọi việc, không dùng model yếu cho việc rủi ro cao.

Orchestrator (người hoặc agent điều phối) chịu trách nhiệm chia việc, chọn tier, thu kết quả và merge — **không** để subagent tự mở rộng phạm vi.

---

## 2. Phân cấp công việc

```text
Phase (ROADMAP / PHASES.md)
  └── Việc lớn / epic (task-pack phase, ví dụ 0003, 0004…)
        └── Subtask (TEMPLATE-SUBTASK)  ← đơn vị giao subagent
              └── Commit / PR nhỏ (một logic review được)
```

| Cấp | Ai sở hữu | Đầu ra |
|-----|-----------|--------|
| Phase | Owner / ROADMAP | DoD phase trong `docs/impl/PHASE-x-IMPLEMENTATION.md` |
| Việc lớn | Task pack phase | PR hoặc chuỗi PR hoàn thành pack |
| **Subtask** | **Subagent** | Diff + test + báo cáo ngắn theo template |
| Commit | Subagent / orchestrator | Conventional commit, một ý |

---

## 3. Mức độ phức tạp (tier) và chọn model

Gán **một tier** cho mỗi subtask trước khi giao. Tier quyết định model tối thiểu và có cần review người hay không.

| Tier | Tên | Ví dụ việc | Model khuyến nghị | Review |
|------|-----|------------|-------------------|--------|
| **T0** | Cơ học | Sửa typo docs, changelog, rename theo CODEMAP, format | Model nhanh / rẻ | Orchestrator lướt |
| **T1** | Đơn giản** | Unit test thuần, fixture JSON, validate schema, hàm pure nhỏ | Model nhanh–trung bình | Orchestrator |
| **T2** | Chuẩn | Implement hàm domain theo spec có sẵn, pipeline glue, contract test | Model trung bình–mạnh | Orchestrator + CI |
| **T3** | Phức tạp | Thiết kế module mới, canonicalization/hash, ranking formula, adapter interface | Model mạnh | Orchestrator bắt buộc đọc diff |
| **T4** | Rủi ro cao | ADR, ToS/nguồn hợp pháp, approval/publish invariants, kill switch, secret/auth | Model mạnh nhất + **người** duyệt | **Human required** trước merge |

### Quy tắc chọn tier

- Có **side effect** (`ingest-network`, `affiliate-link-create`, `publish`, `account-change`) → tối thiểu **T3**, thường **T4**.
- Đụng schema breaking, ADR, GIA-DINH-NEN-TANG, AN-TOAN-AFFILIATE → **T4**.
- Chỉ đọc/sửa docs không đổi quyết định hệ thống → **T0–T1**.
- Subagent **không** được tự nâng tier để “làm thêm”; muốn mở rộng phải trả việc về orchestrator.

### Ghi chú model (trừu tượng, không gắn vendor)

Repo **không** hard-code tên model cụ thể (Claude/GPT/… thay đổi theo thời điểm). Orchestrator map tier → model hiện có trong môi trường, ví dụ:

- T0–T1 → model latency thấp, chi phí thấp
- T2 → model cân bằng
- T3–T4 → model reasoning mạnh; T4 thêm human gate

Ghi `model_tier: T2` (và optional `model_id` thực tế) trong subtask pack / session log.

---

## 4. Tiêu chí một subtask “đủ nhỏ”

Subtask **hợp lệ** khi thỏa **tất cả**:

1. **Một mục tiêu quan sát được** (một hành vi hoặc một artifact).
2. **Phạm vi path** liệt kê được (được chạm / không được chạm).
3. **Làm xong trong một phiên** hợp lý (hướng dẫn: ≤ ~1–2 giờ agent; tránh “làm cả Phase 2”).
4. **DoD checklist** ≤ 7 mục, có lệnh kiểm máy được.
5. **Side effect** khai báo một mức: `none | ingest-network | affiliate-link-create | publish | account-change`.
6. **Không** yêu cầu subagent vừa thiết kế ADR vừa implement vừa deploy.

Nếu việc lớn hơn → orchestrator **tách thêm** subtask, không giao một cục.

### Ví dụ tách (Phase 1.5)

| Subtask | Tier | Nội dung |
|---------|------|----------|
| 1.5.a | T1 | Test đỏ cho `compute_draft_sha256` (chưa có impl) |
| 1.5.b | T2 | Implement `compute_draft_sha256` + test xanh |
| 1.5.c | T1 | Test đỏ cho `build_publication_candidate` happy path |
| 1.5.d | T2 | Implement builder tối thiểu + default disclosure |
| 1.5.e | T2 | Validation schema + HTTPS + claim_snapshot từ observation |
| 1.5.f | T1 | Fixture example + contract test |
| 1.5.g | T0 | CODEMAP + CHANGELOG + session log |

---

## 5. Vai trò Orchestrator vs Subagent

### Orchestrator (bắt buộc)

- Đọc phase impl spec + task pack phase.
- Tách subtask, gán tier, điền `TEMPLATE-SUBTASK`.
- Chọn model theo tier.
- Giao **một** subtask / một subagent / một thời điểm (tránh hai subagent sửa cùng file).
- Thu kết quả: diff, output test, phần chưa xong.
- Chạy `make check` trên tích hợp; mở PR hoặc chuỗi PR.
- Quyết định dừng / hỏi người khi T4 hoặc mơ hồ ToS.

### Subagent

- Chỉ làm đúng subtask đã giao.
- Đọc đúng danh sách “bối cảnh phải đọc” trong subtask (thường gồm AGENTS.md).
- TDD nếu có code.
- **Không** sửa ngoài phạm vi; thấy việc khác → ghi “phát hiện thêm” rồi dừng phần đó.
- Trả về: tóm tắt, lệnh đã chạy, kết quả, rủi ro, file đụng.

---

## 6. Template giao subtask (bắt buộc)

Dùng `docs/task-packs/TEMPLATE-SUBTASK.md`. Mỗi lần giao copy thành file hoặc block trong session, ví dụ:

`docs/task-packs/active/1.5.b-compute-draft-sha256.md`

Trường bắt buộc:

- `subtask_id`, `parent_phase`, `parent_task_pack`
- `model_tier` (T0–T4)
- Mục tiêu, DoD, phạm vi, ràng buộc, side effect
- Lệnh kiểm (đỏ/xanh)
- “Cấm làm”

---

## 7. Luồng chuẩn (gắn QUY-TRINH-GIT)

```text
1. Orchestrator: phase / việc lớn → danh sách subtask + tier
2. (Nếu T4 hoặc đổi kiến trúc) ADR / người duyệt trước
3. Với mỗi subtask:
     a. Điền TEMPLATE-SUBTASK
     b. Chọn model theo tier
     c. Subagent làm (nhánh feat/fix theo slug subtask nếu cần)
     d. Subagent báo cáo + orchestrator review
     e. make check (cục bộ)
4. Gộp logic liên quan → PR (một hoặc vài subtask/PR tùy reviewability)
5. CI xanh → squash merge
6. Session log: subtask xong / dở, tier, model_id (nếu có)
7. Subtask cuối của phase đạt → đánh dấu DoD phase
```

Vẫn cấm push thẳng `main`. Vẫn Conventional Commits.

---

## 8. Parallelism (làm song song)

Được phép **chỉ khi**:

- Không overlap file/module, và
- Không phụ thuộc dữ liệu lẫn nhau, và
- Orchestrator đã phân path rõ.

Ví dụ an toàn: subtask docs T0 song song với subtask test T1 ở package khác.  
Ví dụ **cấm**: hai subagent cùng sửa `pipeline/publication.py`.

---

## 9. Definition of Done cấp subtask

Subtask chỉ “xong” khi:

- [ ] DoD trong template được tick
- [ ] Không vượt phạm vi
- [ ] Lệnh kiểm đã chạy và kết quả được ghi
- [ ] Side effect đúng mức đã khai (thường `none`)
- [ ] Orchestrator chấp nhận báo cáo (T3+ đọc diff; T4 có human)

---

## 10. Liên kết tài liệu

| Tài liệu | Quan hệ |
|----------|---------|
| [TASK-PACK.md](TASK-PACK.md) | Gói việc lớn / phase; subtask là cấp dưới |
| [TEMPLATE-SUBTASK.md](task-packs/TEMPLATE-SUBTASK.md) | Mẫu giao từng subagent |
| [PHASES.md](PHASES.md) + `docs/impl/*` | Nguồn tách subtask |
| [QUY-TRINH-GIT.md](QUY-TRINH-GIT.md) | Nhánh, PR, merge |
| [AGENTS.md](../AGENTS.md) | Luật cấm/bắt buộc mọi subagent |
| [PROMPT-SHEET.md](PROMPT-SHEET.md) | Câu lệnh chuẩn orchestrator / subagent |

---

## 11. Vi phạm quy ước

- Giao cả phase cho một subagent một lần.
- Không ghi tier / side effect.
- Subagent tự làm publish/ADR/ToS khi task là T1–T2.
- Dùng model yếu cho T4 rồi merge không human review.

→ Orchestrator từ chối nhận kết quả; tách lại subtask đúng chuẩn.
