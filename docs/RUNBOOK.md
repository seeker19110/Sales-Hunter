# Runbook vận hành S-N Sales

Tài liệu sự cố cho operator. **Không** chứa secret, token, IP nội bộ.

## 1. Kill switch nhanh

| Phạm vi | Cách (code hiện tại) | Ghi chú |
|---------|----------------------|---------|
| Adapter `manual` | `KillSwitch.disable("manual")` | Chặn nạp observation manual |
| Publish hệ thống | `Publisher.publish(..., system_kill_switch=True)` | Chặn mọi publish |
| Publish theo kênh | `channel_kill_switch=True` hoặc multi-channel map | Chặn một `target_channel` |
| Dry-run | `Publisher(dry_run=True)` **mặc định** | Không bao giờ publish thật nếu quên tắt |

Production: ghi nhận **ai** bật/tắt, **khi nào**, ticket/PR liên quan.

## 2. Deal / giá sai đã đăng

1. Bật kill switch publish (+ kênh liên quan).
2. Đánh dấu content cần thu hồi: `should_recall_content` / event `content_recalled`.
3. Gỡ hoặc sửa bài trên kênh (thao tác thủ công ngoài repo cho đến khi có client thật).
4. Không tin model; đối chiếu `claim_snapshot` + `observed_at` + evidence.
5. Ghi `TRAPS.md` nếu là lỗi tái diễn.

## 3. Nguồn / quota / “không thu thập được”

- Phân biệt metric: `ingest_no_sale` vs `ingest_source_unavailable`.
- Không fallback scraping.
- Nếu official API chưa xác minh → giữ **manual** (`ADR-0003`).

## 4. Approval / hash mismatch

- Sửa draft → `draft_sha256` đổi → approval cũ **vô hiệu**.
- Phải `decide_approval` lại trước publish.
- Publish trùng `idempotency_key` → trả cùng receipt (không tạo post thứ hai trong store).

## 5. API operator (`/healthz`)

```bash
curl -sS "http://127.0.0.1:8080/healthz"
# kỳ vọng: {"status":"ok",...}
```

Staging/production URL thật chỉ ghi trong PR deploy (không hard-code secret).

## 6. Rollback

1. Revert bằng PR mới (không force-push `main` / base protected).
2. Giữ dry-run publish = on.
3. Xác nhận `/healthz` và unittest trên artifact SHA đã rollback.

## 7. Liên hệ / trách nhiệm

Điền ngoài git: owner platform DHCB, người giữ credential affiliate, on-call.
