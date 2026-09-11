# Task pack 0002 — Phase 1 Domain core + ranking

## Mục tiêu

Triển khai domain core (Money, ranking deterministic) và skeleton package theo ROADMAP Phase 1, dựa trên schema mới đã có.

## Phạm vi

**Trong phạm vi:**
- Tạo `src/s_n_sales/` với package domain + interface adapter
- Value object Money (integer minor units)
- Ranking service deterministic + trả `rank-result.v1`
- Fake adapter đọc fixture JSON → observation → rank → publication-candidate (draft)
- Unit + contract test

**Ngoài phạm vi:**
- Kết nối API Shopee/TikTok thật
- Auto-publish
- Model LLM gọi trả phí trong CI

## Nghiệm thu

1. `uv sync --locked && make check` xanh
2. Pipeline từ `schemas/examples/valid/offer-observation.v1.json` chạy ra rank-result + publication-candidate hợp lệ
3. Mọi phép tính tiền dùng Money; không có float tiền tệ
4. Ranking có `reasons` giải thích được và `rank_version`
5. Cập nhật CODEMAP + session log

## Ghi chú

- Đọc `AGENTS.md`, `ARCHITECTURE.md`, `docs/HOP-DONG-DU-LIEU.md` trước khi code.
- Schema đã có sẵn; không sửa semantics v1 cũ.
