# Prompt Phase 1.5 — mỗi file = một subagent / một subtask

**Parent:** task-pack `0003-phase1.5-publication-candidate`  
**Spec:** `docs/impl/PHASE-1.5-IMPLEMENTATION.md`  
**Convention:** `docs/SUBAGENT-TASK-CONVENTION.md`

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

Cách dùng: mở đúng file subtask → copy toàn bộ khối prompt → dán vào một phiên subagent mới. **Không** dán nhiều file vào cùng một agent.
