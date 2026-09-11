# Sales-Hunter

Khung phát triển cho hệ thống **săn sale và tạo nội dung affiliate đa nền tảng**, trước mắt nhắm tới Shopee và TikTok Shop.

**Platform:** subdomain của [Đồng Hành Cùng Bạn](https://www.donghanhcungban.org) — mục tiêu **`sales.donghanhcungban.org`** (xem [docs/PLATFORM.md](docs/PLATFORM.md), [ADR-0002](docs/adr/0002-platform-subdomain-dhcb.md)).

> Trạng thái: khung vận hành + schema v1 + **domain core Phase 1** (Money, ranking, fake pipeline). Chưa có crawler API thật hay auto-publish.

## Mục tiêu

```text
nguồn chính thức / adapter
  -> quan sát có bằng chứng
  -> chuẩn hóa + validate
  -> xếp hạng deterministic
  -> bản nháp + link affiliate
  -> người duyệt
  -> đăng kênh
  -> đo chuyển đổi
```

## Bắt đầu

Python 3.11+ và [uv](https://docs.astral.sh/uv/).

```bash
uv sync
export PYTHONPATH=src
make check
```

## Tài liệu

- [AGENTS.md](AGENTS.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [CODEMAP.md](CODEMAP.md)
- [ROADMAP](docs/ROADMAP.md) · [PHASES](docs/PHASES.md) · [PLATFORM](docs/PLATFORM.md)
- [Hợp đồng dữ liệu](docs/HOP-DONG-DU-LIEU.md)
- **[Quy ước subagent task](docs/SUBAGENT-TASK-CONVENTION.md)** — mọi phase/việc lớn: tách subtask + `model_tier` T0–T4 trước khi giao agent

## Giấy phép

[Apache License 2.0](LICENSE).
