# Đặc tả triển khai chi tiết — Phase 3 (Approval + Publisher)

**Trạng thái:** Chưa bắt đầu.  
**Phụ thuộc:** Phase 2 (có observation thật hoặc manual ổn định).  
**Schema:** `approval-record.v1.json`, `publish-receipt.v1.json`, `publication-candidate.v1.json`

---

## 1. Mục tiêu

Vòng kín:

```text
publication-candidate (pending)
  → human approval (approved/rejected)
  → publisher (idempotent)
  → read-back từ nền tảng
  → publish-receipt.v1
```

Mặc định **dry-run**. Publish thật chỉ khi cấu hình tường minh + kill switch mở.

---

## 2. Phạm vi được làm

| Thành phần | Mô tả |
|------------|--------|
| Approval service | Tạo/lưu `approval-record.v1`; gắn `draft_sha256` |
| Invalidation | Sửa draft → approval cũ vô hiệu |
| Publisher interface | Protocol theo `target_channel` |
| Publisher implementations | Ít nhất 1 kênh (ví dụ file/log dry-run + 1 kênh thật nếu có) |
| Idempotency store | Key = `idempotency_key`; chống publish trùng |
| Read-back | Chỉ ghi receipt khi đọc lại được `platform_post_id` + URL |
| Kill switch | Global + per-channel |
| Audit log | Mọi quyết định approve/reject/publish |

## 3. Phạm vi **không** được làm

- Auto-approve / auto-publish không người duyệt (cần ADR riêng sau).
- UI đầy đủ (Phase 4).
- Multi-channel phức tạp trước khi 1 kênh ổn.

---

## 4. Thiết kế kỹ thuật

### 4.1. Package đề xuất

```text
src/s_n_sales/
  approval/
    service.py          # approve / reject
    store.py            # interface lưu approval (file/sqlite/memory cho dev)
  publishing/
    base.py             # Protocol Publisher
    dry_run.py          # luôn safe
    <channel>.py        # ví dụ telegram.py / facebook.py
    receipt.py          # build publish-receipt sau read-back
  audit/
    log.py              # append-only audit events
```

### 4.2. Approval flow

```python
def approve(
    publication: dict,          # publication-candidate
    *,
    decided_by: str,
    reason: str | None = None,
    policy_version: str | None = None,
    now: datetime,
) -> dict:  # approval-record.v1
    ...
```

Invariants:
- `status ∈ {"approved", "rejected"}`.
- `draft_sha256` **phải** khớp `publication["draft_sha256"]` tại thời điểm duyệt.
- Nếu publication đã đổi hash → từ chối approve (yêu cầu duyệt lại).

### 4.3. Publisher flow

```python
def publish(
    publication: dict,
    approval: dict,
    *,
    dry_run: bool = True,
    now: datetime,
) -> dict:  # publish-receipt.v1
    ...
```

Điều kiện được publish:
1. `approval.status == "approved"`.
2. `approval.draft_sha256 == publication.draft_sha256`.
3. Kill switch mở cho channel.
4. Idempotency key chưa có receipt `status=published`.
5. Observation còn đủ freshness (policy).
6. Disclosure + URL hợp lệ.

Sau khi gọi API nền tảng:
- **Bắt buộc read-back** (GET post / tương đương).
- Chỉ khi read-back thành công mới ghi `status="published"` + `platform_post_id` + `platform_post_url` + `read_back_at`.
- Thất bại → `status="failed"` hoặc `"unknown"` + error fields; **không** bịa post id.

### 4.4. Idempotency

- Key lấy từ `publication["idempotency_key"]`.
- Store phải atomic (check-then-set hoặc unique constraint).
- Gọi lại cùng key khi đã published → trả receipt cũ, không tạo post mới.

### 4.5. Dry-run

- `dry_run=True` (mặc định): không gọi mạng; trả receipt giả lập với `status` rõ là dry-run hoặc không ghi receipt published.
- Config/env `PUBLISH_DRY_RUN=true/false`.

---

## 5. Test bắt buộc

- Approve với hash khớp → record hợp lệ.
- Approve khi hash lệch → lỗi.
- Reject → không publish được.
- Publish khi chưa approve → lỗi.
- Publish trùng idempotency key → không tạo post thứ hai.
- Read-back fail → không đánh dấu published.
- Kill switch off → không publish.
- Dry-run → không side effect mạng.

---

## 6. Thứ tự triển khai

1. Approval service + in-memory/file store + test.
2. Dry-run publisher + receipt schema validate.
3. Idempotency store.
4. Một publisher thật (nếu đã có credential + ADR kênh).
5. Audit log.
6. ADR kill switch / publish policy nếu chưa có.

---

## 7. Nghiệm thu (DoD)

- [ ] Approval gắn hash; sửa draft làm approval cũ vô hiệu.
- [ ] Publisher idempotent + read-back bắt buộc.
- [ ] Dry-run mặc định.
- [ ] Kill switch hoạt động.
- [ ] Test biên đầy đủ; `make check` xanh.
- [ ] Không secret trong git.

---

## 8. Rủi ro

| Rủi ro | Xử lý |
|--------|--------|
| Nền tảng không cho read-back | Không đánh dấu published; status unknown/failed |
| Double publish | Idempotency store + test |
| Operator duyệt nhầm | Audit + lý do reject/approve; thu hồi ở Phase 5 |

---

## 9. Liên kết

- Task pack: `docs/task-packs/0005-phase3-approval-publisher.md`
