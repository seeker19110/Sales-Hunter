# Đặc tả triển khai chi tiết — Phase 2 (Adapter + nguồn hợp pháp)

**Trạng thái:** Chưa bắt đầu.  
**Phụ thuộc:** Phase 1.5 (publication-candidate builder).  
**Tài liệu gốc:** [PHASES.md](../PHASES.md) · [GIA-DINH-NEN-TANG.md](../GIA-DINH-NEN-TANG.md) · [AN-TOAN-AFFILIATE.md](../AN-TOAN-AFFILIATE.md)

---

## 1. Mục tiêu

Có **ít nhất một** nguồn observation thật, hợp pháp, lặp lại được → chạy end-to-end:

```text
nguồn hợp pháp → offer-observation.v1 → rank → publication-candidate (draft-only)
```

Ưu tiên **Shopee Việt Nam**. TikTok Shop chỉ sau khi Shopee ổn.

---

## 2. Thứ tự ưu tiên nguồn (bắt buộc tuân thủ)

1. **Official Affiliate / Product API** (nếu tài khoản + ToS cho phép).
2. **Authorized export / feed** từ chương trình affiliate.
3. **Manual / semi-manual** (`source_method=manual`) với audit rõ ràng.

**Cấm tuyệt đối:**
- Scraping, browser automation, CAPTCHA, cookie, hard-code domain ngoài allowlist.
- Biến phỏng đoán ToS thành code.

---

## 3. Việc phải làm trước khi viết adapter mạng

### 3.1. ADR bắt buộc

Tạo ADR mới (ví dụ `docs/adr/0003-shopee-source-and-allowlist.md`) gồm:

- URL / tên agreement + phiên bản + ngày đọc.
- Account/program, khu vực, scope.
- Auth flow (OAuth / API key / không auth).
- Quota, rate limit, pagination, timezone, currency.
- Trường dữ liệu được phép lưu + retention.
- Hành động read-only vs tạo link vs publish.
- Allowlist hostname/domain (version hóa).
- Người chịu trách nhiệm + ngày cần rà lại policy.

### 3.2. Cập nhật `GIA-DINH-NEN-TANG.md`

Chỉ đánh dấu “đã xác minh” sau khi ADR được chấp nhận và có bằng chứng.

### 3.3. Checklist `AN-TOAN-AFFILIATE.md`

Tick các mục liên quan nguồn trước khi merge adapter mạng.

---

## 4. Phạm vi được làm

| Thành phần | Mô tả |
|------------|--------|
| Config allowlist | File/config version hóa (không hard-code trong domain) |
| Adapter interface | Protocol/ABC: `fetch_observations(...) -> list[dict]` |
| Adapter Shopee (hoặc Manual) | Implement interface → `offer-observation.v1` |
| Rate limit + timeout + retry | Trần cố định, exponential backoff, dead-letter |
| Kill switch | Config/env: tắt adapter theo nền tảng hoặc toàn cục |
| Normalizer | Raw payload → observation (giữ raw hash + observed_at) |
| Contract test | Fixture khử nhạy cảm + schema validate |
| CLI / script | Chạy 1 lần ingest → rank → publication-candidate (dry) |

## 5. Phạm vi **không** được làm

- Auto-publish, approval UI, multi-platform song song.
- Lưu credential trong repo.
- Tạo affiliate link nếu chưa có quyền chính thức (ghi `source_method=manual` nếu operator dán link).

---

## 6. Thiết kế kỹ thuật đề xuất

### 6.1. Cấu trúc package

```text
src/s_n_sales/
  adapters/
    __init__.py
    base.py           # Protocol + common errors
    fake.py           # đã có
    manual.py         # MỚI: nhận observation dict / file từ operator
    shopee.py         # MỚI: chỉ sau ADR
  config/
    allowlist.py      # load domain allowlist version hóa
  pipeline/
    ingest.py         # optional: orchestration ingest → rank → draft
```

### 6.2. Interface gợi ý

```python
class OfferAdapter(Protocol):
    platform: str  # "shopee" | "tiktok_shop" | "manual"

    def fetch_observations(
        self,
        *,
        limit: int = 20,
        cursor: str | None = None,
    ) -> list[dict[str, Any]]: ...
```

### 6.3. Invariants khi map sang observation

- `source_method` ∈ {`official_api`, `authorized_export`, `manual`}.
- `observed_at` timezone-aware.
- `sale_price_minor` / `list_price_minor` integer ≥ 0; sale ≤ list nếu có list.
- `product_url` + `evidence.source_url` HTTPS và nằm trong allowlist.
- Raw payload (hoặc hash) được giữ để audit; không ghi đè raw bằng bản chuẩn hóa.

### 6.4. Rate limit & resilience

- Timeout mỗi request (ví dụ 10–30s).
- Retry tối đa N lần (ví dụ 3), exponential backoff + jitter.
- Sau trần → escalate / dead-letter, **không** lặp vô hạn.
- Kill switch đọc từ env/config trước mọi gọi mạng.

### 6.5. Manual adapter (nên làm trước hoặc song song)

Cho phép operator cung cấp JSON observation hợp lệ (hoặc form sau này).  
`source_method="manual"`. Vẫn phải qua schema + allowlist URL.

---

## 7. Test bắt buộc

- Contract: output adapter → schema `offer-observation.v1`.
- Allowlist: URL ngoài list → reject.
- Kill switch bật → không gọi mạng.
- Rate limit / retry behavior (mock).
- Manual path: file fixture → observation hợp lệ.
- End-to-end: observation thật (hoặc manual) → rank → publication-candidate.

---

## 8. Thứ tự triển khai khuyến nghị

1. Viết ADR + cập nhật GIA-DINH-NEN-TANG (chưa code mạng).
2. Implement `manual` adapter + allowlist config + test.
3. End-to-end manual → rank → publication-candidate.
4. Nếu ADR official API được duyệt → implement `shopee` adapter + mock/contract test.
5. Bật kill switch + rate limit thật.
6. PR riêng cho ADR, PR riêng cho code adapter.

---

## 9. Nghiệm thu (DoD)

- [ ] ADR nguồn/allowlist được merge.
- [ ] `GIA-DINH-NEN-TANG.md` phản ánh trạng thái xác minh.
- [ ] Có ít nhất một đường tạo observation hợp lệ (manual hoặc official).
- [ ] Pipeline observation → rank → publication-candidate chạy được.
- [ ] Checklist AN-TOAN-AFFILIATE (phần nguồn) được tick.
- [ ] `make check` + contract test xanh.
- [ ] Không có secret trong git.

---

## 10. Rủi ro

| Rủi ro | Xử lý |
|--------|--------|
| Không có API/feed hợp pháp | Giữ manual; dừng mở rộng platform |
| ToS thay đổi | Ngày rà lại trong ADR + GIA-DINH |
| Rate limit / khóa tài khoản | Kill switch + backoff + monitoring |
| Scope creep scrap | Từ chối PR; ghi TRAPS |

---

## 11. Liên kết

- Task pack: `docs/task-packs/0004-phase2-adapter-source.md`
- Schema: `offer-observation.v1.json`
