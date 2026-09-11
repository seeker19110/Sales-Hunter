# Quy ước Subagent Task — S-N Sales

**Trạng thái:** Chấp nhận (quy ước vận hành).  
**Áp dụng từ:** mọi phase và việc lớn sau khi merge tài liệu này.

---

## 1. Mục tiêu quy ước

Mỗi **phase** hoặc **việc lớn** phải được:

1. **Chia** thành các **task nhỏ** (subtask) có phạm vi rõ, nghiệm thu rõ.
2. **Giao** từng subtask theo thứ tự (một subagent / một subtask tại một thời điểm trên cùng việc lớn — trừ parallel hợp lệ ở §8).
3. **Chọn model** theo **mức độ phức tạp** (`model_tier` T0–T4).

Orchestrator chịu trách nhiệm chia việc, chọn tier, thu kết quả và mở PR — **không** để subagent tự mở rộng phạm vi.

---

## 2. Phân cấp công việc

```text
Phase (ROADMAP / PHASES.md)
  └── Việc lớn / epic (task-pack phase)  ← 1 remote branch + 1 PR (mặc định)
        └── Subtask (TEMPLATE-SUBTASK)   ← 1 commit (hoặc vài commit nhỏ) trên CÙNG nhánh
              └── Không mở remote branch riêng cho mỗi subtask (mặc định)
```

| Cấp | Ai sở hữu | Đầu ra |
|-----|-----------|--------|
| Phase | Owner / ROADMAP | DoD phase trong `docs/impl/PHASE-x-IMPLEMENTATION.md` |
| Việc lớn | Task pack phase | **Một** nhánh remote + **một** PR (sau khi đủ subtask) |
| **Subtask** | Subagent / phiên tuần tự | Commit Conventional trên nhánh việc lớn + báo cáo |
| Commit | — | Một ý review được; message có thể ghi `subtask_id` |

---

## 2.1. Mô hình nhánh **A** (mặc định toàn cục)

**Phương án A — bắt buộc trừ khi thỏa ngoại lệ §2.2:**

| Quy tắc | Chi tiết |
|---------|----------|
| 1 việc lớn → 1 remote branch | Ví dụ `feat/1.5-publication-candidate`, `feat/2-manual-adapter` |
| Nhiều subtask trên **cùng** nhánh | `1.5.a` → commit; `1.5.b` → commit; … rồi **một** PR |
| Subagent tuần tự | Giao subtask k+1 sau khi k xong (cùng worktree/nhánh) |
| Tiết kiệm token | Không cold-start N agent × full AGENTS/spec nếu không cần parallel |
| Nhiều việc lớn | Nhiều nhánh song song **được**, rồi **rebase/merge tuần tự** theo phụ thuộc kế hoạch |

```text
origin/<base>
  └── feat/viec-lon-X          ← remote branch duy nhất cho X
        commit subtask X.a
        commit subtask X.b
        commit subtask X.c
        └── PR → squash merge vào base
```

**Không** mặc định tạo `feat/1.5.a`, `feat/1.5.b`, … trừ khi §2.2.

---

## 2.2. Ngoại lệ — mô hình **B** (nhánh theo subtask)

Chỉ khi **tất cả** đúng:

1. Hai (trở lên) agent/người chạy **song song thật**, và
2. **Không overlap** path/module, và
3. Orchestrator ghi rõ trong task pack / session: `branching: B` + bảng path.

Khi đó mỗi subtask parallel có thể có remote branch riêng, merge/rebase vào nhánh việc lớn hoặc base theo thứ tự phụ thuộc.

Nếu chỉ có **một** agent làm tuần tự → **luôn A**.

---

## 3. Mức độ phức tạp (tier) và chọn model

Gán **một tier** cho mỗi subtask trước khi giao.

| Tier | Tên | Ví dụ việc | Model khuyến nghị | Review |
|------|-----|------------|-------------------|--------|
| **T0** | Cơ học | Typo docs, changelog, format | Nhanh / rẻ | Orchestrator lướt |
| **T1** | Đơn giản | Unit test, fixture, schema validate | Nhanh–TB | Orchestrator |
| **T2** | Chuẩn | Implement theo spec, contract test | TB–mạnh | Orchestrator + CI |
| **T3** | Phức tạp | Module mới, hash, ranking, adapter interface | Mạnh | Đọc diff bắt buộc |
| **T4** | Rủi ro cao | ADR, ToS, publish, secret/auth | Mạnh nhất + **người** | **Human** trước merge |

### Quy tắc chọn tier

- Side effect `ingest-network` / `affiliate-link-create` / `publish` / `account-change` → tối thiểu **T3**, thường **T4**.
- Schema breaking, ADR, GIA-DINH, AN-TOAN-AFFILIATE → **T4**.
- Docs không đổi quyết định hệ thống → **T0–T1**.
- Subagent không tự nâng tier / mở rộng phạm vi.

Repo **không** hard-code tên model vendor; chỉ bắt buộc `model_tier` (optional `model_id` trong session log).

---

## 4. Tiêu chí subtask “đủ nhỏ”

1. Một mục tiêu quan sát được.
2. Phạm vi path rõ (được / không được chạm).
3. Làm xong trong một phiên hợp lý (hướng dẫn ≤ ~1–2 giờ agent).
4. DoD ≤ 7 mục + lệnh kiểm máy được.
5. Một mức side effect được khai.
6. Không gộp ADR + implement mạng + deploy trong một subtask.

### Ví dụ tách (Phase 1.5) — vẫn **một** nhánh `feat/1.5-…`

| Subtask | Tier | Nội dung |
|---------|------|----------|
| 1.5.a | T1 | Test đỏ `compute_draft_sha256` |
| 1.5.b | T2 | Implement hash + test xanh |
| 1.5.c | T1 | Test đỏ builder |
| 1.5.d | T2 | Implement builder + disclosure |
| 1.5.e | T2 | Validation schema + HTTPS + claim |
| 1.5.f | T1 | Fixture + contract |
| 1.5.g | T0 | CODEMAP + CHANGELOG + session |

---

## 5. Orchestrator vs Subagent

### Orchestrator

- Tách subtask + tier; chọn **branching A** (mặc định).
- Tạo **một** nhánh việc lớn từ base.
- Giao subtask tuần tự trên nhánh đó; mỗi lần xong → commit (message có `subtask_id` nếu hữu ích).
- `make check` trước khi mở PR.
- Một PR cho việc lớn khi DoD các subtask đạt (hoặc PR sớm dạng draft nếu cần review giữa chừng).

### Subagent

- Chỉ làm đúng subtask; commit trên nhánh việc lớn đã cho (không tự tạo remote branch mới trừ khi orchestrator ghi `branching: B`).
- TDD nếu có code; báo cáo theo TEMPLATE-SUBTASK.

---

## 6. Template subtask

`docs/task-packs/TEMPLATE-SUBTASK.md`.

Thêm trường khuyến nghị:

```yaml
branching: "A"   # A = cùng nhánh việc lớn (mặc định); B = nhánh riêng subtask (parallel)
parent_branch: "feat/1.5-publication-candidate"  # bắt buộc với A
```

---

## 7. Luồng chuẩn (A + Git)

```text
1. Orchestrator: việc lớn → bảng subtask + tier + branching A
2. Tạo nhánh feat/<viec-lon> từ base (một lần)
3. ADR/human nếu T4 trước code rủi ro
4. Lặp subtask k = 1..n:
     a. Giao prompt subtask (cùng nhánh)
     b. Subagent làm + báo cáo
     c. Commit trên feat/<viec-lon>
     d. make check cục bộ
5. Một PR từ feat/<viec-lon> → base (body liệt kê subtask_id + tier)
6. CI xanh → squash merge → xóa nhánh
7. Session log
```

Nhiều việc lớn: nhiều nhánh song song → **rebase lên base mới** rồi merge **tuần tự theo phụ thuộc** (Phase 1.5 rồi 2…).

---

## 8. Parallelism

- **Trong một việc lớn (A):** mặc định **không** parallel subtask đụng cùng module; tuần tự trên một nhánh.
- **Giữa các việc lớn:** parallel nhánh được nếu path không đụng nhau.
- **B trong một việc lớn:** chỉ khi §2.2.

Cấm: hai subagent cùng sửa một file trên hai nhánh không phối hợp.

---

## 9. DoD subtask

- [ ] DoD template đạt
- [ ] Không vượt phạm vi
- [ ] Có bằng chứng lệnh kiểm
- [ ] Side effect đúng mức khai
- [ ] Commit nằm trên `parent_branch` (A) hoặc nhánh B đã khai
- [ ] T3+ orchestrator đọc diff; T4 human trước merge PR việc lớn

---

## 10. Token / chi phí (hệ quả A)

- **A** giảm lặp context (AGENTS, spec) so với mỗi subtask một agent cold-start + remote branch.
- Chấp nhận B khi cần song song thời gian, không phải để “rẻ token”.

---

## 11. Liên kết

| Tài liệu | Quan hệ |
|----------|---------|
| [QUY-TRINH-GIT.md](QUY-TRINH-GIT.md) | Nhánh, PR, rebase tuần tự |
| [TASK-PACK.md](TASK-PACK.md) / [TEMPLATE-SUBTASK.md](task-packs/TEMPLATE-SUBTASK.md) | Gói việc + subtask |
| [PROMPT-SHEET.md](PROMPT-SHEET.md) / [prompts/](prompts/) | Prompt orchestrator & subagent |
| [AGENTS.md](../AGENTS.md) | Luật cấm/bắt buộc |

---

## 12. Vi phạm

- Giao cả phase một lần không tách subtask.
- Tạo remote branch per subtask khi chỉ có một agent tuần tự (phải dùng A).
- Không ghi tier / side effect.
- Subagent tự publish/ADR khi không phải T4 + human.
- Parallel overlap file.

→ Orchestrator từ chối; làm lại đúng A hoặc B có kiểm soát.
