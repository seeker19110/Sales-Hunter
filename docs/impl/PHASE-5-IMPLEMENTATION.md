# Đặc tả triển khai chi tiết — Phase 5 (Analytics + Feedback loop)

**Trạng thái:** Chưa bắt đầu.  
**Phụ thuộc:** Phase 4 (có publish thật hoặc semi-thật + staging).

---

## 1. Mục tiêu

- Đo click / conversion cơ bản.
- Tách metric “không có sale” vs “không thu thập được dữ liệu”.
- Cải thiện ranking qua `rank_version` mới (vẫn deterministic).
- Quy trình thu hồi / cập nhật khi deal hết hạn.

---

## 2. Phạm vi được làm

| Thành phần | Mô tả |
|------------|--------|
| Click tracking | UTM / short-link / redirect có log |
| Conversion ingest | Nếu affiliate program cung cấp postback/report |
| Metrics store | Tổng hợp theo ngày/channel/platform |
| Ranking feedback | Điều chỉnh trọng số → `rank-v1.1.0` (ADR nhỏ) |
| Expiry / recall | Đánh dấu candidate hết hạn; cảnh báo operator |
| Dashboard số liệu | Bảng đơn giản hoặc export CSV |

## 3. Phạm vi **không** được làm

- ML ranking / model chấm điểm.
- PII người dùng cuối không cần thiết.
- Tối ưu real-time phức tạp.

---

## 4. Thiết kế kỹ thuật

### 4.1. Tracking

- Khi build publication-candidate: gắn `idempotency_key` / tracking id vào affiliate_url (nếu chương trình cho phép).
- Redirect service hoặc platform insight → ghi sự kiện `click` (timestamp, publication_id, channel).
- Không lưu IP/user-agent đầy đủ trừ khi có ADR privacy.

### 4.2. Metrics

```text
observations_fetched
observations_valid
observations_invalid / source_error
candidates_created
candidates_approved / rejected
publish_attempts / published / failed
clicks
conversions (nếu có)
```

Tách rõ:
- `no_deal` (nguồn OK, không có ưu đãi)
- `fetch_error` (nguồn lỗi / quota / kill switch)

### 4.3. Ranking feedback

- Phân tích correlaton đơn giản: score vs click/conversion.
- Đề xuất trọng số mới → ADR + `RANK_VERSION = "rank-v1.1.0"`.
- Giữ `reasons` giải thích được; không dùng model để sinh score.

### 4.4. Expiry & recall

- Policy freshness (ví dụ observation > 24–48h → không publish mới).
- Job/flag: candidate đã publish nhưng deal có thể hết → nhắc operator gỡ/sửa bài.
- Không tự xóa bài trên nền tảng trừ khi có ADR + quyền API.

---

## 5. Test & nghiệm thu

- Ghi nhận click → metric tăng.
- Export/dashboard hiển thị số liệu đúng fixture.
- Rank version mới có test regression với golden input.
- Quy trình recall được mô tả trong runbook ngắn.

**DoD:**
- [ ] Có số liệu click (và conversion nếu khả dụng).
- [ ] Metric tách no_deal vs fetch_error.
- [ ] Có thể ship rank_version mới an toàn.
- [ ] Có quy trình thu hồi nội dung.

---

## 6. Liên kết

- Task pack: `docs/task-packs/0007-phase5-analytics.md`
