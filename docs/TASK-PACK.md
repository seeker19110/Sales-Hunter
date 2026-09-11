# Task pack — gói việc cho một phiên / việc lớn

Điền đủ bảy mục trước mọi thay đổi nhiều file. Chỗ để trống là chỗ agent sẽ tự đoán.

**Cấp dưới task pack:** khi việc lớn hoặc cả phase, **bắt buộc** tách thành subtask và giao subagent theo [SUBAGENT-TASK-CONVENTION.md](SUBAGENT-TASK-CONVENTION.md) + [task-packs/TEMPLATE-SUBTASK.md](task-packs/TEMPLATE-SUBTASK.md).

- **Task pack** = việc lớn / phase (orchestrator sở hữu).
- **Subtask** = đơn vị giao một subagent + một `model_tier` (T0–T4).

```markdown
# Task pack: <động từ + kết quả>

## 1. Mục tiêu
<Việc gì thiếu/sai, ảnh hưởng người dùng hay số liệu nào.>

## 2. Xong nghĩa là gì
- [ ] <hành vi quan sát được>
- [ ] <test/lệnh/bằng chứng máy sinh>
- [ ] <tài liệu, changelog, PR>

## 3. Phạm vi
Được chạm: <path/module>
Không được chạm: <path/hành động ngoài hệ thống>

## 4. Bối cảnh phải đọc
1. `AGENTS.md`, mục liên quan trong `TRAPS.md`
2. `CODEMAP.md`, `ARCHITECTURE.md`
3. `docs/SUBAGENT-TASK-CONVENTION.md` nếu sẽ tách subagent
4. <schema/ADR/tài liệu nền tảng chính thức>

## 5. Ràng buộc kỹ thuật
- <schema/version, tiền tệ, timezone, idempotency, rate limit>
- <độ mới của dữ liệu và bằng chứng nguồn>
- <dry-run/human approval nếu có side effect>
- External side effects: none | ingest-network | affiliate-link-create | publish | account-change
- Policy snapshot: <nguồn chính thức, ngày đọc, phạm vi, người chịu trách nhiệm>

## 6. Bẫy và ca biên
- nguồn hết quota khác với không có sale;
- giá/coupon thay đổi theo tài khoản, khu vực, thời điểm;
- redirect/link hết hạn;
- retry trùng và publish hai lần;
- <bẫy thật từ TRAPS.md nếu có>.

## 7. Kiểm và báo
- Đỏ: <test phải fail trước code>
- Xanh: <lệnh cục bộ/CI>
- Đối chiếu: <read-back hoặc nguồn độc lập>
- Báo: <PR, changelog, session log, phần chưa kiểm được>

## 8. Subtask (khi áp dụng quy ước subagent)

Liệt kê trước khi giao việc:

| ID | Tier | Mục tiêu một dòng | Side effect |
|----|------|-------------------|-------------|
| x.a | T1 | … | none |
| x.b | T2 | … | none |

Chi tiết từng dòng: copy `TEMPLATE-SUBTASK.md`.
```
