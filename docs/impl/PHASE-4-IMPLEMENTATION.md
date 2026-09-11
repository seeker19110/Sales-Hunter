# Đặc tả triển khai chi tiết — Phase 4 (Staging + Operator UI)

**Trạng thái:** Chưa bắt đầu.  
**Phụ thuộc:** Phase 3 (approval + publisher hoạt động ở mức CLI/file).  
**Tài liệu:** [DEPLOY-SALES-SUBDOMAIN.md](../DEPLOY-SALES-SUBDOMAIN.md) · [PLATFORM.md](../PLATFORM.md)

---

## 1. Mục tiêu

- HTTP service tối thiểu phục vụ operator.
- Dashboard duyệt draft (list / xem / approve / reject).
- Deploy **staging** tại `sales.donghanhcungban.org` (hoặc subdomain staging rõ ràng).
- HTTPS + health check + không leak sang Learning.

---

## 2. Phạm vi được làm

| Thành phần | Mô tả |
|------------|--------|
| HTTP app | FastAPI (hoặc tương đương) |
| Auth tạm | Basic / token / simple password (SSO để Phase 6) |
| API | List candidates, get detail, approve, reject, list receipts |
| UI | HTML tối giản (Jinja/HTMX) hoặc SPA nhẹ — ưu tiên đơn giản |
| Health | `GET /healthz` không lộ secret/PII |
| Deploy staging | Theo checklist DEPLOY-SALES-SUBDOMAIN |
| Logging | Structured log, không ghi credential |

## 3. Phạm vi **không** được làm

- Production traffic / DNS production trước khi smoke test staging xong.
- SSO đầy đủ / chia sẻ session Learning.
- Analytics nâng cao (Phase 5).

---

## 4. Thiết kế kỹ thuật

### 4.1. Cấu trúc đề xuất

```text
src/s_n_sales/
  api/
    app.py              # FastAPI factory
    routes/
      health.py
      candidates.py
      approvals.py
      receipts.py
    auth.py             # dependency operator auth
  web/
    templates/          # nếu server-render
    static/
```

### 4.2. API tối thiểu

| Method | Path | Mô tả |
|--------|------|--------|
| GET | `/healthz` | 200 + version/commit |
| GET | `/api/candidates` | List publication-candidate (pending trước) |
| GET | `/api/candidates/{id}` | Chi tiết + claim_snapshot |
| POST | `/api/candidates/{id}/approve` | Body: reason? → approval-record |
| POST | `/api/candidates/{id}/reject` | Body: reason |
| GET | `/api/receipts` | List publish receipts |
| POST | `/api/candidates/{id}/publish` | Chỉ khi approved + kill switch; tôn trọng dry-run |

Mọi route (trừ healthz) yêu cầu operator auth.

### 4.3. UI tối thiểu

- Trang list: bảng draft (id, platform, giá, observed_at, status).
- Trang detail: content, disclosure, claim_snapshot, rank score/reasons.
- Nút Approve / Reject (có form reason).
- Nút Publish (chỉ hiện khi approved + dry-run flag rõ ràng).

### 4.4. Lưu trữ tạm (Phase 4)

- Có thể dùng SQLite / file store cho candidate, approval, receipt.
- Schema migration đơn giản; chưa cần Postgres trừ khi ADR yêu cầu.

### 4.5. Deploy staging

Tuân thủ `DEPLOY-SALES-SUBDOMAIN.md`:

1. ADR runtime/hosting nếu chưa có.
2. Build artifact có version/SHA.
3. Deploy origin cô lập.
4. Kiểm `/healthz` + HTTPS read-back.
5. DNS/TLS chỉ sau khi staging ổn.
6. Bằng chứng trong PR deploy (URL, SHA, thời điểm, rollback plan).

Ranh giới: **không** đọc/ghi dữ liệu Learning; credential tách biệt.

---

## 5. Test

- API auth: không token → 401.
- Approve/reject cập nhật store đúng hash.
- Healthz không chứa secret.
- Integration test với TestClient (FastAPI).
- Smoke script sau deploy.

---

## 6. Thứ tự triển khai

1. FastAPI skeleton + healthz + auth stub.
2. API candidates + approvals (nối Phase 3 services).
3. UI list/detail tối giản.
4. Wire publish endpoint (dry-run mặc định).
5. Dockerfile / deploy script staging.
6. PR deploy + bằng chứng checklist.

---

## 7. Nghiệm thu (DoD)

- [ ] Staging HTTPS reachable.
- [ ] Operator đăng nhập được và duyệt draft.
- [ ] Publish từ UI tôn trọng dry-run + kill switch.
- [ ] Không leak credential/data Learning.
- [ ] Checklist deploy được tick trong PR.
- [ ] `make check` + test API xanh.

---

## 8. Liên kết

- Task pack: `docs/task-packs/0006-phase4-staging-ui.md`
