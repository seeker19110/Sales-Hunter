# ADR-0011 — Allowlist URL version hóa bắt buộc cho mọi đường tạo candidate

Trạng thái: chấp nhận — owner merge #48 ngày 2026-10-09 sau review T4. Phụ thuộc ADR0005/0009. Không thêm domain nền tảng thật.

## Bối cảnh

Audit 2026-10-09 (`docs/sessions/2026-10-09-line-audit.md`) thấy luồng grounded (ADR0009) đã áp `quality/urls.py::UrlPolicy`, nhưng `pipeline/publication.build_publication_candidate`, `pipeline/manual_draft_flow.py` và `POST /api/v1/candidates` chỉ kiểm `https`. Điều này trái `AGENTS.md` luật cấm 9 và luật bắt buộc 5: link affiliate phải qua allowlist config version hóa. Ngoài ra repo chưa có file allowlist nào; mọi `UrlPolicy` hiện được dựng trong test.

## Quyết định

1. Hợp đồng mới `schemas/url-allowlist.v1.json`: `version`, `max_redirects`, danh sách `hosts` với `host`, `purpose` (`affiliate`, `product`, `evidence`), `reference` (tài liệu/điều khoản chính thức, HTTPS) và `verified_on` (ngày kiểm chứng). Một host có thể có nhiều mục.
2. File cấu hình `config/url-allowlist.v1.json` được commit với `hosts: []`: mặc định fail-closed. Domain Shopee/TikTok chỉ được thêm bằng PR riêng có nguồn chính thức và ngày kiểm chứng (luật cấm 3); ADR này không thêm domain nào.
3. `quality/allowlist.py::load_url_policy(path)` parse chặt (`json_object` + schema), dựng `UrlPolicy` mang `version`. Không có giá trị mặc định ngầm.
4. `build_publication_candidate` bắt buộc tham số keyword `url_policy` và kiểm `affiliate_url` cùng `evidence.source_url` trước khi băm. `run_manual_to_publication_candidate` cũng bắt buộc `url_policy`.
5. Operator server nhận `url_policy` tùy chọn (`--url-allowlist`/`OPERATOR_URL_ALLOWLIST`). Không cấu hình → `POST /api/v1/candidates` trả 403 `url_allowlist_not_configured`; có cấu hình → URL ngoài allowlist trả 400 `url_not_allowed`. Đọc/duyệt/từ chối candidate đã có không đổi.
6. `validate_repo.py` kiểm mọi file `config/*.v1.json` khớp schema cùng tên.

## Hệ quả

- Caller cũ của builder phải truyền policy; test dùng `UrlPolicy(frozenset({"example.com"}))` (domain dành riêng cho tài liệu).
- Candidate legacy đã lưu không bị sửa hay migrate; kiểm chỉ áp cho đường tạo mới. Publish bền vững vẫn chỉ nhận package grounded (ADR0010).
- Allowlist rỗng nghĩa là chưa tạo được candidate thật cho tới khi owner duyệt domain có bằng chứng.

## Nghiệm thu

Test đỏ trước: builder/flow/API nhận URL ngoài allowlist; loader nhận file sai schema hoặc khóa trùng; config trong repo lệch schema. Test xanh sau, toàn bộ cổng `CONTRIBUTING.md`, browser và wheel smoke.
