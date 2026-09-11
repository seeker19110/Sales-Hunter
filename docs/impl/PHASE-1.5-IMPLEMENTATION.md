# Đặc tả triển khai chi tiết — Phase 1.5 (Content draft đầy đủ)

**Trạng thái:** Chưa bắt đầu.  
**Phụ thuộc:** Phase 1 (Money, ranking, observation → rank).  
**Tài liệu gốc:** [PHASES.md](../PHASES.md) · schema `publication-candidate.v1.json`

---

## 1. Mục tiêu

Hoàn thiện bước **rank-result + observation → publication-candidate.v1** với đầy đủ bất biến an toàn:

- `claim_snapshot` đóng băng dữ liệu dùng để viết nội dung.
- `draft_sha256` deterministic (canonical JSON).
- `affiliate_disclosure` bắt buộc, không thể tắt bằng tham số.
- `approval.status = "pending"` mặc định.
- Không side effect mạng / publish.

---

## 2. Phạm vi được làm

| Việc | Mô tả |
|------|--------|
| Module builder | `src/s_n_sales/pipeline/publication.py` (hoặc mở rộng `draft.py`) |
| Hàm chính | `build_publication_candidate(observation, rank_result, *, content, affiliate_url, target_channel, ...) → dict` |
| Canonicalization | Hàm `compute_draft_sha256(...)` pure, ổn định |
| Disclosure | Template cố định hoặc config version hóa, luôn non-empty |
| Validation | JSON Schema + invariant domain trước khi trả về |
| Test | Unit + contract test (schema + hash stability + thay đổi field làm hash đổi) |
| Tài liệu | Cập nhật HOP-DONG-DU-LIEU nếu cần làm rõ semantics hash |

## 3. Phạm vi **không** được làm

- Gọi model LLM để sinh `content` (có thể nhận `content` từ ngoài).
- Tạo affiliate link thật / gọi API nền tảng.
- Lưu approval thật, publish, UI, database.
- Sửa semantics schema v1 (chỉ thêm optional nếu thật sự cần → vẫn phải cập nhật fixture).

---

## 4. Hợp đồng kỹ thuật chi tiết

### 4.1. Input

```text
observation: dict          # đã validate (offer-observation.v1)
rank_result: dict          # đã có từ observation_to_rank
content: str               # nội dung bản nháp (do người hoặc model cung cấp)
affiliate_url: str         # URL đích (phải HTTPS; Phase 1.5 chưa enforce allowlist đầy đủ)
target_channel: str        # ví dụ "telegram:s-n-sales", "facebook:page-id"
publication_id: str | None # nếu None → sinh "pub-{observation_id}-{short_hash}"
idempotency_key: str | None
```

### 4.2. Output (`publication-candidate.v1`)

Phải thỏa schema `schemas/publication-candidate.v1.json` và các bất biến sau:

1. `schema_version == "publication-candidate.v1"`
2. `observation_id` lấy từ observation.
3. `claim_snapshot` chứa đúng:
   - `platform` từ observation
   - `observed_at` từ observation
   - `currency`, `sale_price_minor`, `list_price_minor` (nếu có)
   - `source_url` từ `evidence.source_url`
4. `affiliate_disclosure` **không rỗng** và chứa ít nhất một cụm từ nhận diện (ví dụ “#affiliate” hoặc câu disclosure chuẩn).
5. `approval.status == "pending"` và `approval.draft_sha256 == draft_sha256`.
6. `draft_sha256` = SHA-256 hex của canonical payload (xem 4.3).
7. `idempotency_key` ổn định theo (observation_id + target_channel + draft_sha256) nếu không truyền vào.

### 4.3. Canonicalization cho `draft_sha256`

**Yêu cầu:** cùng nội dung logic → cùng hash, bất kể thứ tự key khi serialize.

Đề xuất thuật toán (ghi rõ trong code + test):

```text
canonical_object = {
  "content": content,
  "affiliate_url": affiliate_url,
  "affiliate_disclosure": affiliate_disclosure,
  "claim_snapshot": claim_snapshot,   # đã sort key
  "target_channel": target_channel,
  "observation_id": observation_id,
}
canonical_json = json.dumps(canonical_object, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
draft_sha256 = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
```

- Không bao gồm `publication_id`, `approval`, `idempotency_key` vào hash (vì chúng phụ thuộc hash hoặc là metadata).
- Thay đổi bất kỳ field trong canonical_object → hash đổi.

### 4.4. Disclosure mặc định

```text
DISCLOSURE_TEMPLATE = (
  "#affiliate — Bài viết có thể chứa liên kết tiếp thị liên kết. "
  "Giá và tồn kho được quan sát tại thời điểm ghi nhận, có thể đã thay đổi."
)
```

- Cho phép override bằng tham số `disclosure: str | None = None`.
- Nếu `disclosure` là `None` hoặc rỗng sau khi strip → dùng template.
- **Cấm** đường tắt “không disclosure”.

### 4.5. Validation sau khi build

- Chạy JSON Schema validator (`publication-candidate.v1`).
- Kiểm `approval.draft_sha256 == draft_sha256`.
- Kiểm `affiliate_url` scheme == `https`.
- Ném exception domain rõ ràng nếu fail (không trả partial object).

---

## 5. Cấu trúc code đề xuất

```text
src/s_n_sales/
  pipeline/
    draft.py              # giữ observation_to_rank (đã có)
    publication.py        # MỚI: build_publication_candidate + compute_draft_sha256
  domain/
    money.py
    ranking.py
```

Public API gợi ý:

```python
def compute_draft_sha256(
    *,
    content: str,
    affiliate_url: str,
    affiliate_disclosure: str,
    claim_snapshot: dict[str, Any],
    target_channel: str,
    observation_id: str,
) -> str: ...

def build_publication_candidate(
    observation: dict[str, Any],
    rank_result: dict[str, Any],
    *,
    content: str,
    affiliate_url: str,
    target_channel: str,
    disclosure: str | None = None,
    publication_id: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]: ...
```

`rank_result` được nhận để sau này có thể gắn score vào metadata (không bắt buộc vào schema v1 hiện tại).

---

## 6. Test bắt buộc (TDD)

### 6.1. Unit test

- `test_compute_draft_sha256_stable` — cùng input → cùng hash.
- `test_compute_draft_sha256_changes_on_content` — đổi content → hash đổi.
- `test_compute_draft_sha256_changes_on_disclosure`.
- `test_compute_draft_sha256_changes_on_claim_snapshot`.
- `test_build_sets_pending_approval`.
- `test_build_requires_https_affiliate_url`.
- `test_build_uses_default_disclosure_when_none`.
- `test_build_rejects_empty_content`.
- `test_build_claim_snapshot_matches_observation`.

### 6.2. Contract test

- Output của `build_publication_candidate` validate được bởi schema `publication-candidate.v1.json`.
- Fixture ví dụ hợp lệ nằm trong `schemas/examples/valid/`.

### 6.3. Lệnh kiểm

```bash
uv run python -m unittest discover -s tests -v
make check
```

---

## 7. Thứ tự triển khai khuyến nghị (TDD)

1. Viết test `compute_draft_sha256_*` (đỏ).
2. Implement `compute_draft_sha256` (xanh).
3. Viết test `build_publication_candidate` cơ bản (đỏ).
4. Implement builder tối thiểu + default disclosure (xanh).
5. Thêm validation schema + HTTPS + claim_snapshot (xanh).
6. Thêm fixture example + contract test.
7. Cập nhật CODEMAP, HOP-DONG-DU-LIEU (nếu cần), CHANGELOG, session log.
8. PR theo QUY-TRINH-GIT.

---

## 8. Nghiệm thu (Definition of Done)

- [ ] `build_publication_candidate` trả object khớp schema v1.
- [ ] `draft_sha256` deterministic và thay đổi đúng khi input canonical thay đổi.
- [ ] Disclosure luôn có mặt.
- [ ] `approval.status == "pending"` và hash khớp.
- [ ] Không có side effect mạng.
- [ ] `make check` xanh.
- [ ] CHANGELOG + session log + CODEMAP cập nhật.
- [ ] Task-pack 0003 được đánh dấu hoàn thành sau merge.

---

## 9. Rủi ro & lưu ý

| Rủi ro | Cách xử lý |
|--------|------------|
| Canonicalization không ổn định giữa Python version | Dùng `sort_keys=True` + `separators=(",", ":")` + UTF-8; thêm test lock |
| Người dùng quên disclosure | Default template + cấm chuỗi rỗng |
| Affiliate URL giả / không HTTPS | Validate scheme ngay trong builder |
| Scope creep (LLM, publish) | Giữ đúng phạm vi Phase 1.5 |

---

## 10. Liên kết

- Schema: `schemas/publication-candidate.v1.json`
- Hợp đồng dữ liệu: `docs/HOP-DONG-DU-LIEU.md`
- An toàn affiliate: `docs/AN-TOAN-AFFILIATE.md`
- Task pack: `docs/task-packs/0003-phase1.5-publication-candidate.md`
