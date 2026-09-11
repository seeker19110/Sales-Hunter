# Task pack 0008 — Phase 6 Production + Scale

## 1. Mục tiêu
Production ổn định, monitoring, runbook, mở channel/adapter mới có kiểm soát.

## 2. Xong nghĩa là gì
- [ ] Production HTTPS + monitoring + alerting
- [ ] Kill switch đã diễn tập
- [ ] Runbook sự cố
- [ ] (Optional) SSO theo ADR
- [ ] Adapter/channel mới chỉ sau ADR + GIA-DINH

## 3. Phạm vi
Deploy production, ops docs, adapter #2, multi-channel  
Không được chạm: auto-publish không kiểm soát, scrap

## 4. Bối cảnh
`docs/impl/PHASE-6-IMPLEMENTATION.md`, DEPLOY-SALES-SUBDOMAIN.md

## 5. Ràng buộc
ADR-first cho auth và nền tảng mới; secret ngoài git

## 6. Bẫy
Mở TikTok trước khi Shopee ổn; quên rollback

## 7. Kiểm và báo
Checklist production + diễn tập kill switch + PR
