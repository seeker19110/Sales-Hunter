# Session 2026-10-09 — Allowlist URL version hóa (ADR-0011)

Tiếp theo [audit từng dòng](2026-10-09-line-audit.md) sau khi [#47](https://github.com/seeker19110/Sales-Hunter/pull/47) merge vào `bootstrap/base` (`7e00135`). Task pack: [2026-10-09-url-allowlist](../task-packs/2026-10-09-url-allowlist.md).

## Đã làm

- [ADR-0011](../adr/0011-versioned-url-allowlist.md) (đề xuất, T4): mọi đường tạo candidate kiểm URL qua allowlist config version hóa, đóng mục "luồng legacy chỉ kiểm HTTPS" (trái luật cấm 9 và luật bắt buộc 5).
- Hợp đồng `url-allowlist.v1` + `config/url-allowlist.v1.json` rỗng. Repo không chứa domain nền tảng thật; mẫu valid dùng `example.com` (RFC 2606).
- `load_url_policy` parse chặt; builder, manual flow và `POST /api/v1/candidates` bắt buộc policy; `--url-allowlist`/`OPERATOR_URL_ALLOWLIST` cho server.
- `validate_repo.py` kiểm `config/*.json` theo schema cùng tên; smoke wheel nạp config commit sẵn.

## Kiểm định cục bộ

`tests/test_url_allowlist.py` (loader, builder, manual flow, API, contract config) đỏ trước bản sửa. Sau bản sửa: ruff/format/pyright sạch, unittest discover, `validate_repo`, `pip_audit`, browser smoke và smoke wheel runtime-only đều xanh (output trong PR).

## Còn lại

- Owner thêm domain thật: một PR riêng, mỗi host có `reference` tới tài liệu/điều khoản chính thức và `verified_on`; tới lúc đó API không nhập được candidate thật (fail-closed có chủ ý).
- `analytics` bền vững và identity/roles trước staging ngoài vẫn cần ADR riêng.
- PR: [#48](https://github.com/seeker19110/Sales-Hunter/pull/48), đã merge vào `bootstrap/base` (`98c4677`).
- #44, #45, #46 không bị chạm.

## Không được quên

Không dùng CI xanh thay human T4. Mọi transport vẫn fake/local; không có side effect ngoài.
