# Đặc tả triển khai chi tiết — Phase 1 (Domain core + ranking)

**Trạng thái:** Gần hoàn thành (2026-09-11).  
**Phụ thuộc:** Phase 0, Phase 0.5.  
**Tài liệu gốc:** [PHASES.md](../PHASES.md), [task-packs/0002-phase1-domain-core.md](../task-packs/0002-phase1-domain-core.md)

---

## 1. Mục tiêu Phase 1

Xây dựng **domain core xác định** và pipeline an toàn từ observation thô → rank-result, không side effect mạng.

Kết quả bắt buộc:
- Value object `Money` (integer minor units, không float).
- Ranking deterministic có `rank_version` + `reasons`.
- Pipeline validate observation (schema + invariant) → rank.
- Fake adapter đọc fixture.
- Mọi test và `make check` xanh.

---

## 2. Hiện trạng code (đã có)

| Thành phần | Path | Trạng thái |
|------------|------|------------|
| Money | `src/s_n_sales/domain/money.py` | Hoàn thành |
| Ranking | `src/s_n_sales/domain/ranking.py` | Hoàn thành (`rank-v1.0.0`) |
| Pipeline observation → rank | `src/s_n_sales/pipeline/draft.py` | Hoàn thành (validate + rank) |
| Fake adapter | `src/s_n_sales/adapters/fake.py` | Hoàn thành (load fixture) |
| Schema | `schemas/offer-observation.v1.json`, `rank-result.v1.json` | Có |
| Package skeleton | `src/s_n_sales/` | Có |

### Hành vi đã có

```text
fixture JSON
  → load_observation_fixture()
  → observation_to_rank(observation, now=...)
       ├─ JSON Schema validate (Draft 2020-12)
       ├─ invariant: sale_price ≤ list_price (nếu có)
       ├─ HTTPS bắt buộc cho product_url + evidence.source_url
       ├─ timezone bắt buộc cho observed_at và now
       └─ rank_observation() → rank-result.v1 dict
```

### Ranking công thức hiện tại (`rank-v1.0.0`)

- Discount depth: weight 0.45 (ratio giảm so với list).
- Freshness: weight 0.35 (giảm tuyến tính về 0 sau 24h).
- In-stock bonus: 0.20.
- Trả `score` (0–1 khoảng), `reasons[]`, `features`, `rank_version`.

---

## 3. Phần còn lại của Phase 1 (phải đóng trước khi coi xong)

Phase 1 gốc còn mục “Publication-candidate builder đầy đủ”.  
**Quyết định:** chuyển phần đó sang **Phase 1.5** (xem `PHASE-1.5-IMPLEMENTATION.md`).

Việc còn lại **trong Phase 1** (nếu muốn đóng sạch):

1. **Bổ sung test thiếu** (nếu chưa đủ):
   - Money: biên âm, bool, currency mismatch, discount_ratio edge.
   - Ranking: out_of_stock, unknown stock, observed_at trong tương lai, age > 24h.
   - Pipeline: schema invalid, thiếu timezone, URL http, sale > list.
2. **Cập nhật CODEMAP.md** nếu path mới xuất hiện.
3. **Đánh dấu ROADMAP Phase 1** là xong (sau khi test xanh).

**Không làm trong Phase 1:**
- Tạo `publication-candidate` đầy đủ (disclosure, draft_sha256, claim_snapshot) → Phase 1.5.
- Adapter mạng, affiliate link, approval, publish.

---

## 4. Ràng buộc kỹ thuật bắt buộc (Phase 1)

- Không dùng `float` cho bất kỳ số tiền nào trong domain.
- Ranking phải pure function: cùng input + cùng `now` → cùng output.
- Mọi datetime đưa vào domain phải timezone-aware (UTC sau khi normalize).
- External side effects: **none**.
- Không hard-code domain Shopee/TikTok trong domain layer.

---

## 5. Kiểm tra nghiệm thu Phase 1

```bash
uv sync --locked
export PYTHONPATH=src
make check
# hoặc từng cổng:
uv run ruff check src tools tests
uv run ruff format --check src tools tests
uv run pyright src tools tests
uv run python -m unittest discover -s tests -v
uv run python tools/validate_repo.py
```

Pipeline thủ công:

```bash
uv run python -c "
from datetime import datetime, UTC
from pathlib import Path
from s_n_sales.adapters.fake import load_observation_fixture
from s_n_sales.pipeline.draft import observation_to_rank
p = Path('schemas/examples/valid/offer-observation.v1.json')  # điều chỉnh path nếu khác
obs = load_observation_fixture(p)
print(observation_to_rank(obs, now=datetime.now(UTC)))
"
```

---

## 6. Bàn giao sang Phase 1.5

Khi Phase 1 được coi là xong:
- `observation_to_rank` ổn định.
- Không còn thay đổi semantics ranking/Money trừ khi có ADR + `rank_version` mới.
- Mọi builder nội dung (publication-candidate) nằm ở Phase 1.5.

Chi tiết triển khai Phase 1.5: **[PHASE-1.5-IMPLEMENTATION.md](PHASE-1.5-IMPLEMENTATION.md)**.
