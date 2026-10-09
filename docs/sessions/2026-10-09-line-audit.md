# Phiên 2026-10-09 — audit từng dòng và vá cứng

Task pack: [2026-10-09-audit-hardening](../task-packs/2026-10-09-audit-hardening.md). Baseline `a78da48` (#43 đã merge); PR mở khác: #44 setup-uv, #45 ruff, #46 DHCB pilot (không chạm).

## Đã hoàn thành

Đọc toàn bộ `src/s_n_sales` (domain, adapters, pipeline, quality, evidence, content, publishing, api, analytics), `tools/` và workflow CI. Mỗi phát hiện dưới đây được tái hiện bằng probe hoặc test đỏ trước khi sửa (`tests/test_audit_hardening.py`, 13 test).

| # | Phát hiện | Tái hiện trước sửa | Sửa |
|---|---|---|---|
| 1 | Exception trong handler HTTP làm server đóng kết nối không phản hồi (vd. `/dashboard?status=bogus`, lỗi integrity của store) | `RemoteDisconnected` | ranh giới exception trả 500 ổn định, không lộ chi tiết; bộ lọc sai trả 400 |
| 2 | JSON API chấp nhận khóa trùng, giá trị cuối thắng (`{"expected_revision":99,"expected_revision":1}` duyệt revision 1) | HTTP 200 + approval | parse bằng `json_object` (từ chối khóa trùng/NaN), 400 `invalid_json` |
| 3 | Adapter manual/fake dùng `json.loads` lỏng: khóa trùng `sale_price_minor` lặng lẽ ghi đè | không lỗi | `json_object` + `ManualAdapterError` |
| 4 | `json_object` để lọt `JSONDecodeError` với thông điệp thô | thông điệp không ổn định | mã `invalid_json` |
| 5 | Form duyệt/từ chối dashboard chèn `publication_id` chưa URL-encode vào `action`; redirect sau quyết định mã hóa hai lần (`%252F`) | test đỏ | `quote` cho action, `quote(unquote())` cho redirect |
| 6 | `/api/v1/candidates/<id>/history` của ID không tồn tại trả 200 `[]` | 200 | 404 `candidate_not_found` |
| 7 | Worker publish ném `LeaseLost` ra ngoài `run_once` khi lease hết hạn sau khi provider đã nhận | exception | trả `{"status":"lease_lost"}`; intent ở `outcome_unknown`, reconcile đọc lại, không gửi lại |
| 8 | `RecallService.reconcile` crash khi transport `lookup` timeout (queue reconcile thì không) | `TimeoutError` | coi output transport là không tin cậy, giữ `outcome_unknown` |
| 9 | `RecallService.scan` chỉ xét 1000 publication confirmed mới nhất | bỏ sót | quét toàn bộ confirmed theo thứ tự tạo |
| 10 | `Publisher` trả chính dict receipt trong cache; caller sửa được receipt lần sau | test đỏ | deepcopy khi lưu và trả |
| 11 | `timestamp()` bỏ phần micro giây khi bằng 0 nên `ORDER BY created_at` sai thứ tự (`…00Z` > `…00.5Z`) | thứ tự đảo | `timespec="microseconds"` |
| 12 | Cổng `pip_audit` đỏ trên base: urllib3 2.7.0 (PYSEC-2026-4175/4176/4177) | 3 lỗ hổng | `uv lock --upgrade-package urllib3` → 2.8.0 |

Kiểm định cục bộ: ruff, format, pyright 0 lỗi, 210 unit test, `validate_repo.py`, `pip_audit` sạch, `browser_dashboard_smoke.py` (8 trang, Chromium cục bộ), wheel runtime-only ngoài checkout OK. CI GitHub trên HEAD cuối là bằng chứng chính thức.

## Đã rà nhưng không đổi (ghi lại, ngoài phạm vi hoặc cần quyết định)

- `quality/repository.py`, `evidence/vault.py`, `publishing/*` đọc thẳng `store._lock`/`store._conn`. Hoạt động đúng nhờ `RLock`, nhưng nên có API đọc công khai của store trước khi đổi sang PostgreSQL (cần ADR).
- `pipeline/publication.build_publication_candidate` (luồng legacy) chỉ kiểm HTTPS cho `affiliate_url`; luồng grounded (`content/render.py`) mới áp `UrlPolicy`. Legacy publisher đã khóa ở `FakePlatformClient`, nên chưa có rủi ro gửi thật; khi bỏ luồng legacy cần ADR.
- Đăng nhập dashboard chưa có giới hạn số lần thử; chấp nhận được vì server bắt buộc loopback (ADR-0007). Bắt buộc trước staging ngoài.
- `analytics` vẫn in-memory, recall lease 30 giây hard-code (bằng `QueuePolicy.lease_seconds` mặc định). Không đổi để tránh mở rộng PR.
- `upsert_candidate` lặp lại cùng nội dung vẫn đòi `expected_revision` (quyết định #41); giữ nguyên.

## PR đang mở

- Nhánh audit này (chưa mở PR, target dự kiến `bootstrap/base`); AUD-PUB là T4 → cần người duyệt trước merge.
- #44, #45 (dependabot) và #46 (DHCB pilot) không bị chạm.

## Bẫy mới

Đã ghi vào `TRAPS.md`: exception handler đóng kết nối, JSON khóa trùng, mã hóa URL hai lần, lỗ hổng dependency trôi vào base.

## Không được quên

- Không dùng CI xanh thay human T4. Không nói đã đăng/đã gửi thật: mọi transport vẫn là fake/local.
