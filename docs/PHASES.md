# Đặc tả các Phase — Sales-Hunter

Tài liệu này mô tả chi tiết từng phase từ trạng thái hiện tại đến hệ thống hoàn chỉnh.
Mọi thay đổi kiến trúc, nguồn dữ liệu, quyền publish hoặc schema breaking **phải có ADR** trước khi code.

**Nguyên tắc chỉ đạo toàn bộ lộ trình:**

> Chứng minh được **một vòng kín hợp pháp và trung thực** trước khi mở rộng nền tảng hoặc tự động hóa.

**Vận hành agent (toàn cục):**

> Mỗi phase hoặc việc lớn **bắt buộc** tách thành subtask, giao subagent, chọn `model_tier` T0–T4 theo [SUBAGENT-TASK-CONVENTION.md](SUBAGENT-TASK-CONVENTION.md). Không giao cả phase cho một agent.

---

## Tổng quan lộ trình

| Phase | Tên | Mục tiêu chính | Ước lượng (1 người) | Phụ thuộc |
|-------|-----|----------------|---------------------|-----------|
| 0     | Khung vận hành | Luật + schema + CI | Đã xong | — |
| 0.5   | Platform DHCB | ADR subdomain | Đã xong | — |
| 1     | Domain core | Money + ranking + pipeline fake | Gần xong | — |
| **1.5** | Content draft đầy đủ | Publication-candidate + disclosure | 1–1.5 tuần | Phase 1 |
| **2** | Adapter + nguồn hợp pháp | Observation thật từ nguồn được phép | 3–6 tuần | Phase 1.5 |
| **3** | Approval + Publisher | Human approval + publish receipt | 2–3 tuần | Phase 2 |
| **4** | Staging + Operator UI | Deploy staging + dashboard duyệt | 2 tuần | Phase 3 |
| **5** | Analytics + Feedback | Tracking + cải thiện ranking | 2 tuần | Phase 4 |
| **6** | Production + Scale | Production, kill switch, multi-channel | 3–4 tuần+ | Phase 5 |

**MVP dùng được thực tế** = kết thúc Phase 4 (có vòng kín quan sát → draft → duyệt → đăng → theo dõi cơ bản).

**Trước khi code bất kỳ phase mở nào:** đọc `docs/impl/PHASE-x-IMPLEMENTATION.md` → task-pack phase → tách subtask (TEMPLATE-SUBTASK) → gán tier.

---

## Phase 1.5 — Content draft đầy đủ

### Mục tiêu
Hoàn thiện pipeline từ `rank-result` → `publication-candidate.v1` với đầy đủ bất biến an toàn.

### Phạm vi được làm
- Builder `publication-candidate` từ observation + rank result.
- `claim_snapshot` đóng băng dữ liệu dùng để viết nội dung.
- `draft_sha256` (canonicalization deterministic).
- Template disclosure affiliate bắt buộc.
- Unit test + contract test với schema.
- Cập nhật `docs/HOP-DONG-DU-LIEU.md` nếu cần làm rõ semantics.

### Phạm vi **không** được làm
- Adapter mạng, tạo link affiliate thật, publish, UI.

### Nghiệm thu (Definition of Done)
- [ ] Có hàm/module tạo `publication-candidate` hợp lệ theo schema v1.
- [ ] `draft_sha256` thay đổi khi nội dung / link / disclosure / claim_snapshot thay đổi.
- [ ] Disclosure luôn có mặt và không thể bỏ qua bằng tham số.
- [ ] Test đỏ → xanh theo TDD; `make check` xanh.
- [ ] CHANGELOG + session log cập nhật.
- [ ] Đã tách và hoàn thành subtask theo convention (không một PR “làm cả phase” thiếu bảng subtask).

### Ràng buộc kỹ thuật
- Không dùng float cho tiền.
- Claim phải truy được về observation_id + observed_at.
- External side effects: **none**.
- Subtask điển hình: T1–T2 (xem impl Phase 1.5).

### Rủi ro
Thấp. Chủ yếu là làm rõ canonicalization của `draft_sha256`.

---

## Phase 2 — Adapter + nguồn hợp pháp (bottleneck)

### Mục tiêu
Có ít nhất **một** nguồn observation thật, hợp pháp, có thể chạy lặp lại được (ưu tiên Shopee Việt Nam).

### Thứ tự ưu tiên nguồn
1. Official Affiliate / Product API (nếu có và được phép).
2. Authorized export / feed từ chương trình affiliate.
3. Manual / semi-manual (`source_method=manual`) với quy trình rõ ràng.

**Cấm tuyệt đối:** scraping, browser automation, CAPTCHA solving, cookie stuffing, hard-code domain ngoài allowlist.

### Phạm vi được làm
- ADR mới: ToS + allowlist domain + rate limit + auth flow (nếu có).
- Cập nhật `docs/GIA-DINH-NEN-TANG.md` → đánh dấu “đã xác minh” với bằng chứng.
- Adapter Shopee (hoặc manual pipeline chất lượng cao) → `offer-observation.v1`.
- Rate limit, timeout, retry có trần, kill switch theo adapter.
- Contract test + fixture đã khử dữ liệu nhạy cảm.
- Cho phép chạy end-to-end observation → rank → publication-candidate (vẫn draft-only).

### Phạm vi **không** được làm
- Auto-publish, multi-platform song song, UI phức tạp.

### Nghiệm thu
- [ ] ADR ToS/allowlist được chấp nhận (**T4 + human**).
- [ ] `GIA-DINH-NEN-TANG.md` ghi rõ nguồn, ngày đọc, người chịu trách nhiệm.
- [ ] Có thể tạo observation hợp lệ từ nguồn thật (hoặc manual có audit).
- [ ] Pipeline observation → rank → publication-candidate chạy được với dữ liệu thật.
- [ ] Checklist `AN-TOAN-AFFILIATE.md` được tick cho phần nguồn.
- [ ] `make check` + contract test xanh.
- [ ] Subtask đã tách (ADR / manual / official / e2e) theo convention.

### Ràng buộc kỹ thuật
- `source_method` chỉ nhận giá trị được schema cho phép.
- Mọi URL phải qua allowlist + HTTPS.
- Credential ngoài repo; log chỉ dùng reference.
- External side effects: `ingest-network` (nếu có) hoặc `none` (manual).

### Rủi ro
**Rất cao.** Nếu không tìm được nguồn hợp pháp ổn định → dừng mở rộng, giữ manual pipeline và đánh giá lại sản phẩm.

---

## Phase 3 — Approval + Publisher

### Mục tiêu
Vòng kín draft → người duyệt → publish có receipt đọc lại từ nền tảng.

### Phạm vi được làm
- Lưu `approval-record.v1` (decided_by, decided_at, draft_sha256).
- Publisher idempotent: chỉ publish khi approval còn hiệu lực và hash khớp.
- Read-back `publish-receipt.v1` từ nền tảng (platform_post_id, url, read_back_at).
- Kill switch theo nền tảng và toàn hệ thống.
- Dry-run mặc định; bật publish thật cần cấu hình tường minh.

### Phạm vi **không** được làm
- Auto-publish không người duyệt (cần ADR riêng sau này).
- UI phức tạp (có thể dùng CLI / file-based trước).

### Nghiệm thu
- [ ] Sửa draft → approval cũ vô hiệu.
- [ ] Publish trùng idempotency key không tạo post thứ hai.
- [ ] Receipt chỉ được ghi khi đọc lại thành công từ nền tảng.
- [ ] Test phủ các ca biên (hash mismatch, expired, already published).
- [ ] ADR (nếu cần) cho cơ chế publish và kill switch.
- [ ] Subtask publish/kill-switch = **T4**.

### Ràng buộc
- External side effects: `publish` (có kiểm soát).
- Mọi hành động ra ngoài hệ thống phải có audit log.

### Rủi ro
Trung bình (phụ thuộc kênh đăng và khả năng đọc lại).

---

## Phase 4 — Staging + Operator UI

### Mục tiêu
Deploy staging tại `sales.donghanhcungban.org` và có giao diện tối thiểu để operator duyệt draft.

### Phạm vi được làm
- HTTP service tối thiểu (FastAPI hoặc tương đương).
- Dashboard đơn giản: list draft, xem claim_snapshot, approve/reject, xem receipt.
- Deploy staging theo checklist `DEPLOY-SALES-SUBDOMAIN.md`.
- DNS/TLS, health check, log cơ bản.
- Phân quyền Operator (chưa cần SSO đầy đủ).

### Nghiệm thu
- [ ] Staging accessible qua HTTPS.
- [ ] Operator có thể duyệt và (nếu bật) publish từ UI.
- [ ] Không leak dữ liệu/credential sang Learning.
- [ ] Checklist deploy được tick.
- [ ] Subtask tách API / UI / deploy; deploy DNS = T3–T4.

### Rủi ro
Trung bình (vận hành, bảo mật cơ bản).

---

## Phase 5 — Analytics + Feedback loop

### Mục tiêu
Đo được hiệu quả và cải thiện ranking/freshness dựa trên dữ liệu thật.

### Phạm vi được làm
- Tracking click (UTM / short link / platform event).
- Lưu conversion cơ bản (nếu affiliate program cung cấp).
- Metric tách “không có sale” vs “không thu thập được”.
- Feedback vào ranking (vẫn deterministic, version hóa).
- Cảnh báo deal hết hạn / cần thu hồi nội dung.

### Nghiệm thu
- [ ] Có dashboard hoặc export số liệu cơ bản.
- [ ] Ranking có thể điều chỉnh trọng số qua `rank_version` mới.
- [ ] Có quy trình thu hồi nội dung khi deal hết hạn.
- [ ] Subtask theo convention; đổi rank_version có test regression.

---

## Phase 6 — Production + Scale

### Mục tiêu
Chạy production ổn định, có thể mở thêm kênh/nền tảng.

### Phạm vi được làm
- ADR auth/SSO (nếu cần chia sẻ identity với hub DHCB).
- Production deploy + monitoring + alerting.
- Kill switch production đã kiểm chứng.
- Thêm adapter thứ hai (TikTok Shop) chỉ sau khi Shopee ổn.
- Multi-channel publish (Telegram, Facebook, …) theo cùng quy trình approval.
- Tài liệu vận hành cho operator.

### Nghiệm thu
- [ ] Production chạy ≥ 2 tuần không sự cố nghiêm trọng.
- [ ] Có runbook sự cố (khóa tài khoản, deal sai, rate limit).
- [ ] Mọi nền tảng mới đều đi qua `GIA-DINH-NEN-TANG.md` + ADR.
- [ ] Cutover production = **T4 + human**; diễn tập kill switch.

---

## Quy tắc chung cho mọi phase

1. **TDD bắt buộc** với thay đổi code.
2. Mọi side effect ra ngoài hệ thống mặc định dry-run / draft.
3. Cập nhật `CHANGELOG.md`, session log, và (nếu có) task-pack.
4. Không hạ cổng CI để “xanh”.
5. Khi nghi ngờ ToS / quyền → dừng và hỏi, không đoán.
6. Ưu tiên **một vòng kín chất lượng** hơn nhiều nền tảng nửa vời.
7. **Tách subtask + `model_tier`** trước khi giao agent ([SUBAGENT-TASK-CONVENTION.md](SUBAGENT-TASK-CONVENTION.md)).

---

## Tài liệu liên quan

- [ROADMAP.md](ROADMAP.md)
- [SUBAGENT-TASK-CONVENTION.md](SUBAGENT-TASK-CONVENTION.md)
- [ARCHITECTURE.md](../ARCHITECTURE.md)
- [HOP-DONG-DU-LIEU.md](HOP-DONG-DU-LIEU.md)
- [AN-TOAN-AFFILIATE.md](AN-TOAN-AFFILIATE.md)
- [GIA-DINH-NEN-TANG.md](GIA-DINH-NEN-TANG.md)
- [PLATFORM.md](PLATFORM.md)
- `docs/impl/PHASE-*-IMPLEMENTATION.md`
- ADR trong `docs/adr/`
