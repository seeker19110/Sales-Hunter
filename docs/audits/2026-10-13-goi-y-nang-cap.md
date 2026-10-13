# Gợi ý nâng cấp — rà soát 2026-10-13

> Lấy từ đợt rà soát chéo 19 repo của chủ sở hữu (ma trận vệ sinh ở [seeker19110/stored, mục 23 §8.1](https://github.com/seeker19110/stored/blob/main/23-own-repos-lessons/README.md); gợi ý tích hợp ở §7b của cùng file). Số liệu đo bằng lệnh trên HEAD (đếm `uses:` ghim SHA 40 ký tự, khối `permissions:`, `dependabot.yml`, `.claude/settings.json`), không suy ra từ văn xuôi. Đây là **đề xuất**, chưa sửa code. Mỗi mục kèm bằng chứng để kiểm lại trước khi làm; mục nào đã xử lý thì đánh dấu hoặc xoá.

## Hiện trạng đo được

| HEAD đọc | Action ghim SHA | Workflow thiếu `permissions:` cấp đầu | Dependabot | LICENSE · SECURITY | File test |
|---|---|---|---|---|---|
| `a3201f0` (2026-10-09) | 23/23 | – | uv, github-actions | có · có | 27 |

## Đề xuất (🔴 cao · 🟠 trung bình · 🟢 nhẹ)

| # | Mức | Đề xuất | Bằng chứng | Kiểm xong khi |
|---|---|---|---|---|
| 1 | 🟢 | Khi nối client mạng thật (Phase sau): thêm **egress allowlist** (chỉ cho phép domain Shopee / TikTok API) và guardrails cho output trước khi publish | `AGENTS.md:9` ghi hiện chưa có client mạng thật và publisher mặc định dry-run; đây là thời điểm rẻ nhất để đặt ranh giới | Có test chứng minh domain ngoài allowlist bị chặn |

## Giữ nguyên (điểm mạnh)

- Ghim SHA 23/23, Dependabot uv + github-actions, pre-commit, status-freshness CI, repo contract validator, `model_tier` T0–T4, outbox / lease / fencing. **Không có lỗ hổng vệ sinh đáng kể.**

## Gợi ý tích hợp từ catalog `stored`

- Mẫu egress allowlist của Decepticon (stored mục 12 §3g); guardrails output (mục 12 §2).

## Ghi chú chung

- Ghim action theo SHA bằng [pinact](https://github.com/suzuki-shunsuke/pinact) hoặc [ratchet](https://github.com/sethvargo/ratchet), giữ comment tag (`# v7.0.1`), rồi để Dependabot `github-actions` tự nâng SHA. Đây là cách projects-template, xboss và Sales-Hunter đang làm.
- Chuẩn tham chiếu là `seeker19110/projects-template`: 25/25 action ghim SHA, mọi workflow có `permissions:` cấp đầu, Dependabot cho npm, github-actions và pip.
