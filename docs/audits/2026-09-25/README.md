# Audit 25/09/2026 — chất lượng và dễ vận hành

## Đọc trước

[Báo cáo đầy đủ](SALES-HUNTER-AUDIT-2026-09-25.md) có 27 hạng mục SH-001–SH-027, mức ưu tiên, nguồn theo commit, cách sửa và tiêu chí nghiệm thu; kèm kiến trúc đề xuất và lộ trình A–G.

**Đây là PR bàn giao báo cáo và bằng chứng, không phải PR đã sửa 27 hạng mục.** Không thay đổi runtime, schema, dependency, CI, credential, DNS/TLS hoặc quyền đăng bài. Publisher vẫn dry-run mặc định. Django/PostgreSQL trong báo cáo là đề xuất; phải có ADR và PR triển khai riêng trước khi chuyển kiến trúc.

## Bằng chứng được lưu

- [audit_probes.py](audit_probes.py): script quan sát bằng client giả cục bộ, không request ra nền tảng.
- [audit-results.json](audit-results.json): kết quả lịch sử của lần audit, gồm môi trường và manifest nguồn.
- [source-verification.json](source-verification.json): Git blob SHA của bốn tệp nguồn được dùng trong lần kiểm chứng.

Báo cáo, script và JSON giữ nguyên nội dung từ audit pack. Các câu như “không tạo PR” và “không có PR đang mở” trong báo cáo mô tả **thời điểm audit trước PR bàn giao này**, không mô tả trạng thái GitHub hiện tại. Kết quả 12 probe gồm 9 tình huống rủi ro thuộc 6 nhóm và 3 kiểm soát hoạt động; không gọi chúng là 12 test đạt hoặc 9 lỗ hổng độc lập.

## Chạy lại có kiểm soát

Từ thư mục gốc repo, chỉ diễn giải kết quả như baseline ngày 25/09 khi bốn Git blob SHA nguồn còn khớp manifest. Script có nhãn `REVIEWED_COMMIT` cố định; không dùng nhãn đó để khẳng định đã kiểm tra một commit mới sau khi sửa code. Không ghi đè JSON bằng chứng lịch sử khi chạy lại.

```bash
uv sync --locked
PYTHONPATH=src uv run python docs/audits/2026-09-25/audit_probes.py --output var/audit-rerun.json
```

```powershell
uv sync --locked
$env:PYTHONPATH = "src"
uv run python docs/audits/2026-09-25/audit_probes.py --output var/audit-rerun.json
```

Script tạo báo cáo quan sát, **không có exit code quality gate cho số rủi ro**. Sau khi sửa từng lỗi phải thêm regression test với kỳ vọng an toàn trong `tests/`, không chỉ chạy script rồi coi exit 0 là đạt. Full suite, security checks và điều kiện phê duyệt của repo vẫn giữ nguyên.

## Thứ tự tiếp tục

A: integrity/approval, runtime packaging và auth fail-closed. B: identity, revision và transaction. C: operator workflow/giá/evidence/payload. D: outbox, idempotency, pause và đối soát. E: staging/backup/restore. F: pilot một nguồn, một kênh đã xác minh quyền. G: tối ưu ranking/analytics/AI bằng dữ liệu.

Ưu tiên PR nhỏ, TDD và kiểm thử xuyên luồng; schema, migration và lockfile có người điều phối duy nhất. Không bật side effect khi chỉ mới lưu kế hoạch. Tiến độ thực thi hiện hành nằm ở [PROJECT-STATUS.md](../../../PROJECT-STATUS.md); lịch sử bàn giao ở [session note](../../sessions/2026-09-25-audit-pr.md).
