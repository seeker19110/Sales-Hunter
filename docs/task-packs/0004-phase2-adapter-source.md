# Task pack 0004 — Phase 2 Adapter + nguồn hợp pháp

## 1. Mục tiêu
Có ít nhất một đường tạo `offer-observation.v1` hợp pháp (manual trước, official API sau ADR).

## 2. Xong nghĩa là gì
- [ ] ADR nguồn/allowlist được merge
- [ ] `GIA-DINH-NEN-TANG.md` cập nhật
- [ ] Manual adapter + allowlist + test xanh
- [ ] End-to-end observation → rank → publication-candidate
- [ ] (Optional) Shopee adapter sau khi ADR official được duyệt
- [ ] CHANGELOG + session log

## 3. Phạm vi
Được chạm: `adapters/`, `config/`, docs ADR/GIA-DINH, tests, pipeline ingest nhẹ  
Không được chạm: publish, UI, scrap, secret trong git

## 4. Bối cảnh phải đọc
`docs/impl/PHASE-2-IMPLEMENTATION.md`, AGENTS.md, AN-TOAN-AFFILIATE.md, GIA-DINH-NEN-TANG.md

## 5. Ràng buộc
- source_method chỉ official_api | authorized_export | manual
- URL HTTPS + allowlist
- Kill switch + rate limit nếu có mạng
- External side effects: none (manual) hoặc ingest-network (sau ADR)

## 6. Bẫy
ToS chưa đọc mà code mạng; hard-code domain; nhầm “không có sale” với “fetch lỗi”

## 7. Kiểm và báo
ADR review → test contract → make check → PR
