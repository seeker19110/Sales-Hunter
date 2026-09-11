# Task pack 0006 — Phase 4 Staging + Operator UI

## 1. Mục tiêu
HTTP service + dashboard duyệt + deploy staging HTTPS.

## 2. Xong nghĩa là gì
- [ ] FastAPI (hoặc tương đương) + /healthz
- [ ] API candidates/approve/reject/publish
- [ ] UI list/detail tối giản
- [ ] Staging deploy theo DEPLOY-SALES-SUBDOMAIN
- [ ] Auth operator tạm thời

## 3. Phạm vi
Được chạm: `api/`, `web/`, deploy scripts, docs deploy  
Không được chạm: production DNS, SSO đầy đủ, analytics nâng cao

## 4. Bối cảnh
`docs/impl/PHASE-4-IMPLEMENTATION.md`, PLATFORM.md, DEPLOY-SALES-SUBDOMAIN.md

## 5. Ràng buộc
- Không dùng credential Learning
- Dry-run mặc định trên UI publish
- External side effects: publish chỉ khi bật tường minh

## 6. Bẫy
Lộ secret trong healthz/log; trỏ DNS production sớm

## 7. Kiểm và báo
TestClient + smoke HTTPS + PR deploy có bằng chứng
