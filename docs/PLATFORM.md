# PLATFORM — gắn Sales-Hunter với Đồng Hành Cùng Bạn

## Quan hệ

| Thành phần | URL / repo |
|------------|------------|
| Hub | https://www.donghanhcungban.org |
| Learning (prod) | https://en-vi.donghanhcungban.org — `seeker19110/donghanh` |
| Sales (mục tiêu) | **https://sales.donghanhcungban.org** — repo này |

Chi tiết quyết định: [ADR-0002](adr/0002-platform-subdomain-dhcb.md). Trạng thái triển khai và điều kiện mở domain: [DEPLOY-SALES-SUBDOMAIN](DEPLOY-SALES-SUBDOMAIN.md).

## Ranh giới

```text
Learning  ──✕──  không đọc/ghi Sales
Sales     ──✕──  không đọc mastery / billing Learning
Platform hub ──► SSO / identity (sau ADR auth chi tiết)
```

## Deploy

Mục tiêu là `sales.donghanhcungban.org` trên pattern Cloudflare + VPS, nhưng **chưa có HTTP service hay DNS/TLS production**. Không coi domain là đã tích hợp cho tới khi hoàn tất checklist deploy và read-back HTTPS.

## Vai trò người dùng (v1)

- **Operator:** duyệt draft, bật/tắt publish, xem audit.
- **System:** adapter, ranking, pipeline (không phải end-user Learning).

End-user deals UI là phase sau khi pipeline + approval ổn định.
