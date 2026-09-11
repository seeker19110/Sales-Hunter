# PLATFORM — gắn Sales-Hunter với Đồng Hành Cùng Bạn

## Quan hệ

| Thành phần | URL / repo |
|------------|------------|
| Hub | https://www.donghanhcungban.org |
| Learning (prod) | https://en-vi.donghanhcungban.org — `seeker19110/donghanh` |
| Sales (mục tiêu) | **https://sales.donghanhcungban.org** — repo này |

Chi tiết quyết định: [ADR-0002](adr/0002-platform-subdomain-dhcb.md).

## Ranh giới

```text
Learning  ──✕──  không đọc/ghi Sales
Sales     ──✕──  không đọc mastery / billing Learning
Platform hub ──► SSO / identity (sau ADR auth chi tiết)
```

## Deploy (đặc tả, chưa thực hiện)

1. Cloudflare DNS: `sales` CNAME/A → VPS
2. TLS qua Cloudflare
3. Reverse proxy (nginx) path `/` → app Sales
4. Environment `staging` rồi `production` + kill switch
5. Secrets chỉ qua env/secret manager — không commit

## Vai trò người dùng (v1)

- **Operator:** duyệt draft, bật/tắt publish, xem audit
- **System:** adapter, ranking, pipeline (không phải end-user Learning)

End-user deals UI là phase sau khi pipeline + approval ổn định.
