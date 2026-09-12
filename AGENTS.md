# AGENTS.md — luật làm việc trong Sales-Hunter

Đọc **[PROJECT-STATUS.md](PROJECT-STATUS.md) trước tiên** để biết tiến độ thực tế và điểm resume. Sau đó đọc [TRAPS.md](TRAPS.md), [ARCHITECTURE.md](ARCHITECTURE.md) và dòng liên quan trong [CODEMAP.md](CODEMAP.md). `docs/ROADMAP.md` mô tả lộ trình; không dùng ROADMAP thay cho trạng thái thực thi hiện tại.

Khi làm **phase hoặc việc lớn**: đọc thêm [docs/SUBAGENT-TASK-CONVENTION.md](docs/SUBAGENT-TASK-CONVENTION.md) — chia subtask, giao subagent, chọn `model_tier` T0–T4.

## Phạm vi hiện tại

Phase 1 → Phase 6 skeleton đã được hợp nhất vào `bootstrap/base`. Hệ thống vẫn ở chế độ an toàn: chưa có client mạng thật, chưa cutover production và publisher mặc định dry-run. Trạng thái mới nhất, blocker và việc tiếp theo nằm trong `PROJECT-STATUS.md`.

## Luật cấm

1. Không commit hoặc push trực tiếp lên `main`; mọi thay đổi đi qua nhánh riêng, PR và CI xanh.
2. Không commit token, cookie, khóa API, webhook secret, thông tin tài khoản affiliate, dữ liệu khách hàng hay payload thương mại thật.
3. Không dùng scraping/endpoint không được nền tảng cho phép. Mỗi adapter phải dẫn tài liệu hoặc điều khoản chính thức và có ngày kiểm chứng.
4. Không để model tự tính giá, phần trăm giảm, hoa hồng, thời hạn hoặc chọn URL đích. Model output luôn là dữ liệu chưa tin cậy.
5. Không biến một lần quan sát giá/tồn kho thành khẳng định “đang sale” nếu chưa kiểm tra độ mới và bằng chứng nguồn.
6. Không tự động đăng nội dung công khai khi chưa có ADR nêu rõ phạm vi, cơ chế dừng và phê duyệt.
7. Không sửa ngoài phạm vi task pack **hoặc subtask** đã giao; thấy việc khác thì ghi lại, không tiện tay dọn.
8. Không nói “đã chạy/đã đăng/đã kiểm” nếu không có output hoặc định danh do công cụ sinh ra.
9. Không hard-code domain/redirect của Shopee/TikTok trong code ứng dụng; phải qua allowlist config version hóa.
10. Không dùng float cho tiền tệ ở bất kỳ tầng domain nào.
11. Không giao cả phase cho một subagent; không để subagent tự nâng tier hoặc tự mở side effect.

## Luật bắt buộc

1. Thay đổi code phải theo TDD: test đỏ đúng lý do → code tối thiểu → test xanh → refactor.
2. Input ngoài hệ thống phải được lưu nguyên bản hoặc có dấu vết, sau đó parse qua schema có version trước khi vào domain.
3. Mọi số tiền dùng số nguyên theo đơn vị nhỏ nhất của tiền tệ (value object `Money`); thời gian dùng ISO 8601 có múi giờ.
4. Bản ghi ưu đãi phải mang `platform`, định danh ngoài, `observed_at` và bằng chứng nguồn. Dữ liệu chuẩn hóa không được ghi đè dữ liệu thô.
5. Link affiliate chỉ được tạo bởi adapter/code với allowlist domain và quy tắc nền tảng; không lấy link cuối từ văn bản do model hoặc trang nguồn chỉ dẫn.
6. Hành động ra ngoài hệ thống phải lũy đẳng, có audit log và mặc định ở chế độ dry-run/draft.
7. Đổi ranh giới module, schema, chiến lược thu thập hoặc quyền tự động đăng phải có ADR trước code.
8. Mỗi PR cập nhật `CHANGELOG.md`; cuối phiên ghi điều cần bàn giao trong `docs/sessions/`.
9. Trước push chạy đúng các cổng trong [CONTRIBUTING.md](CONTRIBUTING.md). Không hạ cổng để làm CI xanh.
10. Sửa một lỗi phải rà các adapter/luồng cùng cơ chế và thêm bẫy vào `TRAPS.md` nếu đó là sự cố mới có khả năng tái diễn.
11. Ranking phải deterministic, có `rank_version` và `reasons` giải thích được; không dùng model để sinh score.
12. Phase/việc lớn: tách subtask theo [SUBAGENT-TASK-CONVENTION.md](docs/SUBAGENT-TASK-CONVENTION.md); mỗi subtask có `model_tier`; T4 cần người duyệt trước merge.
13. Mỗi phiên phải đọc `PROJECT-STATUS.md` trước khi làm việc; sau mỗi merge, thay đổi phase, blocker hoặc quyết định kiến trúc phải cập nhật `PROJECT-STATUS.md` trong cùng PR. Nếu file này mâu thuẫn với trạng thái GitHub, đối chiếu GitHub rồi sửa file ngay. Job CI `status-freshness` (`tools/check_status_freshness.py`, chạy khi push `bootstrap/base`) đối chiếu máy: SHA ở "Base hiện tại" phải là tổ tiên của HEAD.

## Ranh giới tin cậy

```text
nguồn ngoài -> raw observation -> schema parser -> validator tất định -> domain
model       -> draft JSON      -> schema parser -> policy validator  -> bản nháp
người duyệt -> approval record -> publisher lũy đẳng                 -> kênh
```

Trạng thái “đã đăng”, URL bài đăng và mã giao dịch phải do publisher đọc lại từ nền tảng, không do model khai.

## Cổng cục bộ

```bash
uv sync --locked
uv run ruff check src tools tests
uv run ruff format --check src tools tests
uv run python -m pyright src tools tests
uv run python -m unittest discover -s tests -v
uv run python tools/validate_repo.py
uv run python -m pip_audit
```

## Khi cần dừng hỏi

Chỉ dừng khi thiếu thông tin làm thay đổi kiến trúc/quyền truy cập, có hành động không đảo ngược, liên quan bí mật/thanh toán/đăng công khai, hoặc nguồn chính thức không cho phép cách tích hợp dự kiến. Các trường hợp khác: nêu giả định và tiếp tục trong phạm vi an toàn.
