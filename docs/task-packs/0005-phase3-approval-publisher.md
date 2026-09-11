# Task pack 0005 — Phase 3 Approval + Publisher

## 1. Mục tiêu
Draft → approve/reject → publish idempotent → read-back receipt.

## 2. Xong nghĩa là gì
- [ ] Approval service gắn draft_sha256
- [ ] Publisher dry-run mặc định + idempotency
- [ ] Receipt chỉ khi read-back thành công
- [ ] Kill switch
- [ ] Test biên + make check

## 3. Phạm vi
Được chạm: `approval/`, `publishing/`, `audit/`, tests  
Không được chạm: UI đầy đủ, auto-publish không duyệt, multi-channel ồ ạt

## 4. Bối cảnh
`docs/impl/PHASE-3-IMPLEMENTATION.md`, schemas approval-record + publish-receipt

## 5. Ràng buộc
- Hash mismatch → không approve/publish
- Dry-run mặc định
- External side effects: publish (có kiểm soát)

## 6. Bẫy
Double publish; bịa platform_post_id; quên kill switch

## 7. Kiểm và báo
TDD → make check → PR có kịch bản dry-run vs real
