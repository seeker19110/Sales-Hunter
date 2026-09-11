# Prompt Phase 1.5 — mỗi file = một subtask (mô hình nhánh A)

**Parent:** task-pack `0003-phase1.5-publication-candidate`  
**Spec:** `docs/impl/PHASE-1.5-IMPLEMENTATION.md`  
**Convention:** `docs/SUBAGENT-TASK-CONVENTION.md` — **branching A**

## Nhánh Git (bắt buộc)

```text
Một remote branch cho cả Phase 1.5 code, ví dụ:
  feat/1.5-publication-candidate

Subtask 1.5.a → commit trên nhánh đó
Subtask 1.5.b → commit trên cùng nhánh
…
Một PR khi đủ DoD (hoặc draft PR giữa chừng nếu cần review)
```

**Không** tạo `feat/1.5.a`, `feat/1.5.b`, … trừ khi orchestrator bật branching B (parallel thật).

## Thứ tự khuyến nghị

| ID | File | Tier | Phụ thuộc |
|----|------|------|-----------|
| 1.5.a | `1.5.a-tests-draft-sha256.md` | T1 | — |
| 1.5.b | `1.5.b-impl-draft-sha256.md` | T2 | 1.5.a |
| 1.5.c | `1.5.c-tests-build-candidate.md` | T1 | 1.5.b |
| 1.5.d | `1.5.d-impl-build-minimal.md` | T2 | 1.5.c |
| 1.5.e | `1.5.e-validation-claim-https.md` | T2 | 1.5.d |
| 1.5.f | `1.5.f-fixture-contract.md` | T1 | 1.5.e |
| 1.5.g | `1.5.g-docs-changelog.md` | T0 | 1.5.f |

Cách dùng: copy khối prompt trong **một** file → một phiên agent → commit trên `feat/1.5-…` → subtask kế tiếp **cùng nhánh**.
