# S-N Sales

Khung phát triển cho hệ thống **săn sale và tạo nội dung affiliate đa nền tảng**, trước mắt nhắm tới Shopee và TikTok Shop.

> Trạng thái hiện tại: repository mới chỉ có **khung vận hành, hợp đồng dữ liệu và cổng CI**. Chưa có crawler, tích hợp API, tạo link affiliate hay tự động đăng nội dung. Các phần đó chỉ được triển khai sau khi có đặc tả và nguồn API hợp lệ.

## Mục tiêu

Luồng sản phẩm dự kiến:

```text
nguồn chính thức / adapter nền tảng
  -> quan sát ưu đãi có bằng chứng
  -> chuẩn hóa và kiểm định tất định
  -> xếp hạng
  -> tạo bản nháp nội dung + link affiliate
  -> người duyệt
  -> đăng kênh
  -> đo chuyển đổi
```

Ba bất biến từ ngày đầu:

1. Giá, mức giảm, thời hạn và trạng thái tồn kho là dữ liệu có thời điểm; không biến một quan sát cũ thành lời khẳng định hiện tại.
2. Model chỉ hỗ trợ phân loại/soạn nội dung. Code xác định tính tiền, xác thực schema, tạo link và thực hiện hành động ngoài hệ thống.
3. Mặc định chỉ tạo bản nháp. Đăng công khai cần phê duyệt của người vận hành cho tới khi có ADR cho phép tự động hóa một phạm vi cụ thể.

## Bắt đầu cho lập trình viên

Yêu cầu: Python 3.11+ và [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run ruff check tools tests
uv run python -m unittest discover -s tests -v
uv run python tools/validate_repo.py
```

Nếu có `make`:

```bash
make check
```

## Bản đồ tài liệu

- [AGENTS.md](AGENTS.md): luật bắt buộc cho mọi agent/lập trình viên.
- [ARCHITECTURE.md](ARCHITECTURE.md): ranh giới hệ thống và luồng dữ liệu dự kiến.
- [CODEMAP.md](CODEMAP.md): muốn thay đổi gì thì đọc/sửa ở đâu.
- [ROADMAP.md](docs/ROADMAP.md): lộ trình Phase 0 → 4.
- [TRAPS.md](TRAPS.md): chỉ ghi bẫy đã xảy ra thật trong repo này.
- [CONTRIBUTING.md](CONTRIBUTING.md): cài đặt, kiểm thử, PR và Definition of Done.
- [SECURITY.md](SECURITY.md): bí mật, dữ liệu nhạy cảm và ranh giới nguồn ngoài.
- [Task pack](docs/TASK-PACK.md): mẫu giao việc không để agent tự đoán.
- [Prompt sheet](docs/PROMPT-SHEET.md): câu lệnh chuẩn cho việc lặp lại.
- [Quy trình Git](docs/QUY-TRINH-GIT.md): nhánh → PR → CI → squash merge.
- [ADR-0001](docs/adr/0001-kien-truc-khoi-dau.md): quyết định kiến trúc khởi đầu.
- [Hợp đồng dữ liệu](docs/HOP-DONG-DU-LIEU.md): ý nghĩa và bất biến của schema v1.
- [Checklist an toàn affiliate](docs/AN-TOAN-AFFILIATE.md): nguồn, claim, link, disclosure và side effect.
- [Giả định nền tảng](docs/GIA-DINH-NEN-TANG.md): năng lực Shopee/TikTok chưa xác minh, không được biến thành code.

## Nguồn khung vận hành

Khung này được rút gọn và điều chỉnh từ [seeker19110/Claude-Agents](https://github.com/seeker19110/Claude-Agents), chỉ giữ những phần có ích trực tiếp cho S-N Sales: luật repo, bản đồ kiến trúc/code, task pack, nhật ký phiên, schema-first, CI, quét bí mật và bằng chứng kiểm thử. Runtime multi-agent, bus, gateway, console, eval/golden prompt và các quy trình phát hành của “công ty AI” không được mang sang vì chưa có nhu cầu sản phẩm tương ứng.

## Giấy phép

[Apache License 2.0](LICENSE). Nguồn điều chỉnh được ghi trong [NOTICE](NOTICE).
