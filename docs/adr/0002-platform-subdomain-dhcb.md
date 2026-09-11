# ADR-0002: Sales-Hunter là subdomain của Đồng Hành Cùng Bạn

- Trạng thái: Chấp nhận
- Ngày: 2026-09-11

## Bối cảnh

Platform [donghanhcungban.org](https://www.donghanhcungban.org) (repo `seeker19110/donghanh`) đã có domain production `en-vi.donghanhcungban.org` (Learning). Sales-Hunter săn sale + affiliate thuộc domain Career / Work / Startup, không thuộc Learning.

Cần chốt ranh giới deploy, auth và dữ liệu trước khi viết adapter thật hoặc UI.

## Quyết định

1. **Subdomain mục tiêu:** `sales.donghanhcungban.org` (operator + sau này user-facing deals).
2. **Repo độc lập:** giữ `seeker19110/Sales-Hunter` (Python), không gộp monorepo vào `donghanh` (Node) ở giai đoạn này.
3. **Auth:** ưu tiên SSO / session từ platform hub; operator role tách khỏi end-user Learning. Không dùng credential Learning để gọi Sales API.
4. **Dữ liệu:** isolated — không đọc mastery, billing, World Model Learning trừ khi có grant + purpose rõ và ADR riêng.
5. **Deploy:** cùng pattern VPS + Cloudflare như `en-vi`; CD vẫn dry-run cho tới ADR deploy.
6. **Invariant platform:** AI không tự sửa giá/link/publish; external write cần authority + audit (khớp AGENTS.md).

## Hệ quả

- README và branding phải nêu quan hệ DHCB.
- DNS/TLS/Cloudflare cấu hình ngoài repo; repo chỉ giữ đặc tả và (sau) config mẫu.
- Schema Sales không embed PII Learning.

## Phương án không chọn

- **Merge vào monorepo donghanh ngay:** khác runtime, tăng rủi ro regression Learning.
- **Domain riêng ngoài donghanhcungban.org:** làm loãng thương hiệu platform.
- **Chia sẻ DB với Learning:** vi phạm ranh giới nhạy cảm V2.
