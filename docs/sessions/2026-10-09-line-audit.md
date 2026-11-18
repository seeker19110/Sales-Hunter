# Phiên 2026-10-09 — audit từng dòng và vá cứng

Task pack: [2026-10-09-audit-hardening](../task-packs/2026-10-09-audit-hardening.md). Baseline `a78da48` (#43 đã merge); PR mở khác: #44 setup-uv, #45 ruff, #46 DHCB pilot (không chạm).

## Đã hoàn thành

Đọc toàn bộ `src/s_n_sales` (domain, adapters, pipeline, quality, evidence, content, publishing, api, analytics), `tools/` và workflow CI. Mỗi phát hiện dưới đây được tái hiện bằng probe hoặc test đỏ trước khi sửa (`tests/test_audit_hardening.py`, 13 test vòng 1, 6 test vòng 2).

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

## Vòng 2 (cùng ngày, theo "hoàn thiện tiếp")

| # | Việc | Test |
|---|---|---|
| 13 | Store có API công khai `read()`, `in_transaction`, `decide_in_transaction`; `quality`, `evidence`, `publishing` thôi đọc `store._lock`/`store._conn` | `EncapsulationTests` quét `src/` |
| 14 | Đăng nhập dashboard: 10 token sai trong 5 phút → mọi lần thử trả 429 + `Retry-After` tới khi cửa sổ trôi; vài lần gõ sai không chặn | `LoginThrottleTests` |
| 15 | Trang đăng nhập có `viewport`, tiêu đề, CSS chung | `test_login_page_is_mobile_ready` |
| 16 | Lease thu hồi dùng `QueuePolicy.lease_seconds` thay vì 30 giây cố định | `RecallLeasePolicyTests` |
| 17 | `import_manual` chuẩn hóa actor trước khi ghi `captured_by` | `ProvenanceNormalizationTests` |
| 18 | `scheduled-audit.yml`: `pip_audit` hàng tuần trên `bootstrap/base`, quyền `contents: read` | chạy được bằng `workflow_dispatch` sau merge |

## Còn lại (cần ADR hoặc quyết định owner)

- Luồng legacy `pipeline/publication.build_publication_candidate` và `POST /api/v1/candidates` chỉ kiểm HTTPS cho `affiliate_url`; luồng grounded mới áp `UrlPolicy`. Publisher legacy đã khóa ở `FakePlatformClient`, queue bền vững chỉ nhận package đã qua `UrlPolicy`, nên chưa có đường gửi link ngoài allowlist. Bỏ hoặc siết luồng legacy là đổi hợp đồng API → cần ADR.
- `analytics` vẫn in-memory; lưu bền cần bảng/schema mới → ADR.
- Throttle đăng nhập nằm trong bộ nhớ tiến trình, đủ cho loopback; staging ngoài cần identity/roles theo ADR-0007.
- `upsert_candidate` lặp lại cùng nội dung vẫn đòi `expected_revision` (quyết định #41); giữ nguyên.

## PR đang mở

- [#47](https://github.com/seeker19110/Sales-Hunter/pull/47) target `bootstrap/base`; CI vòng 1 xanh trên `9cbdc15`. AUD-PUB/AUD-LOGIN/AUD-RECALL-LEASE là T4 → cần người duyệt trước merge.
- #44, #45 (dependabot) và #46 (DHCB pilot) không bị chạm.

## Bẫy mới

Đã ghi vào `TRAPS.md`: exception handler đóng kết nối, JSON khóa trùng, mã hóa URL hai lần, lỗ hổng dependency trôi vào base.

## Không được quên

- Không dùng CI xanh thay human T4. Không nói đã đăng/đã gửi thật: mọi transport vẫn là fake/local.
