# Task pack 0007 — Phase 5 Analytics + Feedback

## 1. Mục tiêu
Click/conversion tracking, metric rõ ràng, rank_version mới khi có dữ liệu, quy trình recall.

## 2. Xong nghĩa là gì
- [ ] Ghi nhận click theo publication_id
- [ ] Metric no_deal vs fetch_error
- [ ] Export/dashboard cơ bản
- [ ] (Nếu đủ dữ liệu) ADR + rank-v1.1.0
- [ ] Runbook thu hồi nội dung

## 3. Phạm vi
Được chạm: tracking, metrics store, ranking version mới, docs  
Không được chạm: ML ranking, PII không cần thiết

## 4. Bối cảnh
`docs/impl/PHASE-5-IMPLEMENTATION.md`

## 5. Ràng buộc
Ranking vẫn deterministic; side effect tracking tối thiểu

## 6. Bẫy
Gộp fetch_error vào “không có sale”; thay ranking không version hóa

## 7. Kiểm và báo
Fixture metrics + PR
