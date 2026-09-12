# ADR-0003 — Manual-first observation trước official API

- **Trạng thái:** Đề xuất (chờ người duyệt — T4)
- **Ngày:** 2026-09-11
- **Phase:** 2

## Bối cảnh

Phase 2 cần observation để chứng minh vòng kín rank → publication-candidate.
API affiliate/catalog Shopee–TikTok **chưa xác minh** trong `GIA-DINH-NEN-TANG.md`.
Scraping / browser automation **bị cấm** bởi AGENTS.md.

## Quyết định

1. **Ưu tiên** pipeline **manual**: operator cung cấp file JSON `offer-observation.v1` với `source_method=manual`.
2. Adapter `manual` **không** gọi mạng; chỉ đọc file + validate schema/domain.
3. Kill switch theo tên adapter (`manual`, sau này `shopee`, …).
4. Chỉ mở adapter `official_api` / `authorized_export` sau khi có tài liệu chính thức + ngày đọc + người chịu trách nhiệm trong `GIA-DINH-NEN-TANG.md`.

## Hệ quả

- E2E draft-only với dữ liệu do người cung cấp, không thu thập tự động.
- Không quảng cáo observation manual như “giá live từ API”.
- Publication vẫn `approval.pending`; không auto-publish.

## Lựa chọn thay thế

| Phương án | Lý do không chọn ngay |
|-----------|------------------------|
| Official API | Chưa xác minh quyền/ToS trong repo |
| Authorized export | Chưa có feed được phép |
| Scraping | Cấm tuyệt đối |

## Kiểm chứng

- `load_manual_observation` + `run_manual_to_publication_candidate` + unit test
- Fixture synthetic trong `schemas/examples/valid/`
