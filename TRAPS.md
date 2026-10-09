# TRAPS.md — bẫy đã xảy ra trong Sales-Hunter

File này chỉ ghi sự cố **đã xảy ra thật trong repository này**, không sao chép lịch sử của Claude-Agents và không dùng như danh sách best practice chung.

## Sổ bẫy

Chưa có bẫy tích hợp nền tảng thật (chưa có client mạng). Các bẫy mã ứng dụng đầu tiên được ghi từ audit 2026-10-09 bên dưới.

## 2026-09-13 — PR dependabot kẹt ở cổng `metadata` vì không tự sửa được CHANGELOG (#7)

- Triệu chứng: job `metadata` (`pr-policy.yml`) báo đỏ "PR không đổi CHANGELOG.md" trên PR dependabot bump `astral-sh/setup-uv`; các job còn lại (`static`, `typecheck`, `unit`…) đều xanh.
- Nguyên nhân gốc: `pr-policy.yml` đòi mọi PR đổi `CHANGELOG.md` trừ khi gắn nhãn `no-changelog`; dependabot mở PR tự động, không tự sửa `CHANGELOG.md` và không tự gắn nhãn miễn trừ đó (chỉ có nhãn `dependencies`, `github_actions` mặc định).
- Bằng chứng đỏ/xanh: check `metadata` đỏ trước khi gắn nhãn; xanh ngay sau khi gắn `no-changelog` và chạy lại (không sửa code/CHANGELOG).
- Rà cả họ: mọi PR do bot mở (dependabot, renovate, github-actions) mà cổng đòi thứ bot không tự làm được (CHANGELOG, checklist PR template, review con người) đều có nguy cơ kẹt vô thời hạn, trông giống "PR chưa đạt chuẩn" nhưng thực ra không bao giờ tự xanh được — hỏi trước khi tin cổng đỏ trên PR bot là do code sai: "bot này có khả năng tự sửa cái cổng đòi không?".
- Lần sau: gắn nhãn `no-changelog` cho PR dependabot/tool tự động trước khi tìm nguyên nhân sâu hơn ở code; cân nhắc thêm bot vào danh sách miễn trừ tự động trong `pr-policy.yml` nếu việc gắn tay lặp lại nhiều lần.

## 2026-10-09 — Exception trong handler HTTP đóng kết nối không phản hồi (audit)

- Triệu chứng: `GET /dashboard?status=bogus` hoặc store ném lỗi integrity → client nhận `RemoteDisconnected`, server in traceback ra stderr.
- Nguyên nhân gốc: `BaseHTTPRequestHandler` không bắt exception của `do_GET`/`do_POST`; mọi `ValueError`/`StoreIntegrityError` chưa liệt kê rơi xuống `socketserver.handle_error`.
- Bằng chứng đỏ/xanh: `tests/test_audit_hardening.py::OperatorHttpBoundaryTests` đỏ trước, xanh sau khi thêm ranh giới exception trả 500 `internal_error` và 400 cho bộ lọc sai.
- Rà cả họ: mọi server stdlib/route mới phải có ranh giới exception và không echo `str(exc)` của lỗi không lường trước.
- Lần sau: route mới thêm test cho input sai và lỗi store giả lập trước khi merge.

## 2026-10-09 — JSON khóa trùng: giá trị cuối thắng (audit)

- Triệu chứng: `{"expected_revision": 99, "expected_revision": 1}` được duyệt ở revision 1; file manual có hai `sale_price_minor` lặng lẽ lấy giá trị sau.
- Nguyên nhân gốc: API và adapter dùng `json.loads` mặc định thay cho `domain.json_value.json_object` (đã từ chối khóa trùng/NaN).
- Bằng chứng đỏ/xanh: `test_duplicate_json_keys_are_rejected_before_any_decision`, `test_manual_adapter_rejects_duplicate_keys`.
- Rà cả họ: mọi điểm parse input ngoài (HTTP body, file manual, fixture, payload transport tương lai) phải qua `json_object`; `grep -rn "json.loads" src` chỉ còn đọc dữ liệu do chính hệ thống ghi.
- Lần sau: adapter/endpoint mới không được gọi `json.loads` trên byte từ ngoài.

## 2026-10-09 — URL path mã hóa sai số lần (audit)

- Triệu chứng: form duyệt trên dashboard của `publication_id` có `/`, `?`, `#` post sai đường dẫn; redirect sau quyết định thành `%252F`.
- Nguyên nhân gốc: `action` dùng `html.escape` (không phải URL-encode); redirect `quote` lại đoạn path đã percent-encode.
- Bằng chứng đỏ/xanh: `test_detail_form_actions_url_encode_publication_id`, `test_dashboard_decision_round_trips_reserved_publication_id`.
- Rà cả họ: mọi URL dựng từ định danh: `quote(raw_id, safe="")` đúng một lần trên giá trị đã giải mã; HTML attribute escape là bước riêng.
- Lần sau: test định danh có ký tự dành riêng cho mọi route có ID trong path.

## 2026-10-09 — Lỗ hổng dependency trôi vào base dù lockfile không đổi (audit)

- Triệu chứng: `pip_audit` đỏ trên `bootstrap/base` `a78da48` (urllib3 2.7.0: PYSEC-2026-4175/4176/4177) dù không commit nào đổi `uv.lock`.
- Nguyên nhân gốc: cơ sở dữ liệu lỗ hổng cập nhật sau merge; CI chỉ chạy khi có push/PR nên base đỏ âm thầm.
- Bằng chứng đỏ/xanh: `uv run python -m pip_audit` 3 lỗ hổng → sạch sau `uv lock --upgrade-package urllib3` (2.8.0).
- Rà cả họ: dependency gián tiếp của nhóm dev (`pip-audit` → `requests` → `urllib3`) không được Dependabot gom nếu chỉ theo dõi dependency trực tiếp.
- Lần sau: cân nhắc chạy `dependency-audit` theo lịch (schedule) trên base; PR đầu tiên thấy cổng này đỏ phải bump transitive dependency trong cùng PR.

## Cách thêm một mục

Một mục cần có:

- ngày và PR/commit;
- triệu chứng quan sát được;
- nguyên nhân gốc đã tái hiện;
- test hoặc lệnh chứng minh lỗi trước/sau;
- câu hỏi rà cả họ lỗi;
- cách tránh lần sau.

Mẫu:

```markdown
## YYYY-MM-DD — <tên khuôn lỗi> (#PR)

- Triệu chứng:
- Nguyên nhân gốc:
- Bằng chứng đỏ/xanh:
- Rà cả họ:
- Lần sau:
```

Rủi ro dự đoán (giá cũ, coupon theo tài khoản, link redirect, quota, thay đổi API) thuộc threat model/ADR/test plan; chỉ chuyển vào đây sau khi nó thực sự gây sự cố và đã tìm được nguyên nhân.
