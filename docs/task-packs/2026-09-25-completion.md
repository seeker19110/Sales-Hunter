# Hoàn thiện audit — task pack thực thi 25/09/2026

Baseline đã đọc: base `0fea06578b04b832c07df6b31c60444510d25c79` (#40), CI 36150453741.
Stack web bắt đầu tại PR #39 HEAD `f48346c8596073a464c8289605945e9617ce9c4f`, tree
`947985091fd4d20ed56b09190d7ed53674a67ea7` (đối chiếu tree local khớp); CI 36150731331.
Snapshot git cục bộ không phải lịch sử upstream. Không reset/ghi đè base. Không có subagent;
một integrator làm tuần tự, branching A mỗi epic. Các PR phụ thuộc không auto-merge khi
parent chưa tích hợp hoặc thiếu human T4. Audit lịch sử giữ nguyên.

| Epic/parent_branch | Subtask/tier | Dependency | File được sửa | Nghiệm thu |
|---|---|---|---|---|
| feat/audit-revision-transactions-20260925 | DATA-SPEC T4, DATA-RED T1, DATA-STORE T3, DATA-HTTP T4, DATA-CHECK T1, DATA-TOOLS T2 | #39 trước tích hợp | api/contracts.py, store*.py, app.py, pipeline/approval/publisher, tests data/API, docs ADR-0008, CI artifact | input không tự duyệt, schema, revision/CAS, history immutable, race/restart, migration rollback/manifest |
| feat/audit-deal-quality-20260925 | DEAL-SPEC T4, DEAL-RED T1, DEAL-CORE T3, DEAL-CONTENT T3, DEAL-CHECK T1 | DATA interface | quality/ + content/ + evidence/vault.py + domain/json_value.py, manual import, schema/examples/package contracts, tests | eligibility độc lập score; snapshot/evidence/variant/URL; deterministic final payload; AI không có tool/secret |
| feat/audit-durable-publishing-20260925 | PUB-SPEC T4, PUB-RED T1, PUB-QUEUE T4, PUB-WORKER T4, PUB-CHECK T1 | DATA/DEAL | publishing/, tests worker/lease/crash/pause | intent trước send, atomic claim, unknown không retry mù, revision/payload scope, pause/restart, receipt bền |
| feat/audit-ledger-evidence-20260925 | LEDGER-SPEC T4, LEDGER-RED T1, LEDGER-CORE T3, LEDGER-CHECK T1 | DB transaction helper | analytics/, evidence/, tests | dedup immutable events, conversion lifecycle, commission; evidence hash/redaction/retention; không doanh thu live |
| feat/audit-operator-operations-20260925 | OPS-SPEC T4, OPS-RED T1, OPS-CLI T3, OPS-UI T3, OPS-RESTORE T4, OPS-CHECK T1 | DATA/DEAL/PUB/LEDGER | operations/, api UI, tools/, docs runbooks | import preview/errors, inbox/version diff, bulk per-item, command doctor/migrate/pause/reconcile/export/backup/restore; luồng offline hoàn chỉnh |

Mỗi epic: test đỏ -> code -> test xanh -> đọc diff -> CHANGELOG/PROJECT-STATUS/session
-> PR và đúng HEAD CI -> human review T4 -> merge thông thường khi đủ cổng. Không thay
CI/review permissions, không gọi live API, không đổi credential/DNS/mua dịch vụ/deploy.
Chưa có ADR được chấp nhận cho Django/PostgreSQL: giữ domain tách khỏi web và SQLite
pilot đã chấp nhận trong ADR-0006; quyết định production phải được duyệt riêng.

Baseline cục bộ: Python 3.13.5, jsonschema 4.26.0; PYTHONPATH=src plus wheel metadata;
110 tests OK. `uv sync --locked` exit 1 do DNS PyPI; không gọi diagnostic là locked suite.
Git/uv/node có, gh không có, git ls-remote exit128 do DNS. CI từ connector là cổng đầy đủ.
Có thể thao tác PR/branch qua GitHub connector; giữ default contents/review gates.

Mỗi subtask cấm chạm path epic khác trừ điểm nối ghi rõ; integrator quản lý migration
numbering và docs chung. Side effect scope: filesystem/worktree/CI và SQLite fixture cục bộ.
Source đang kiểm, staging chưa kiểm, production chưa triển khai. Không giả provider capability.

DATA-TOOLS T2: lưu binary Ruff đã cài từ lockfile trong artifact review của PR để format
trong môi trường không có DNS. Không thêm quyền repo, không thay gate, không xuất secret
hay toàn bộ môi trường. Artifact công cụ giữ 1 ngày, runtime wheel gate giữ nguyên.

DEAL triển khai evidence value/store trước PUB để mọi approval có chứng cứ thực và scope
ổn định. LEDGER sẽ thêm price/conversion events, không sửa lại payload evidence. Runtime
smoke và docs chung do một integrator quản lý, không có parallel overlap. DDL additive
chỉ chạy fixture; không chạy migration hoặc delete payload của người dùng thật.
