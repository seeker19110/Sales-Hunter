# ADR-0005: Canonical Content Hash (draft_sha256) cho Multi-Channel Publication Candidates

- Trạng thái: Chấp nhận
- Ngày: 2026-09-12
- Người chịu trách nhiệm: Sales-Hunter Core Team

## Bối cảnh

Trong Phase 1.5 và Phase 3, bản nháp ưu đãi (`publication-candidate.v1`) sử dụng trường `draft_sha256` để đại diện cho nội dung đã duyệt. Người duyệt (human hoặc automated policy) quyết định phê duyệt dựa trên `draft_sha256` này.

Tuy nhiên, hàm `compute_draft_sha256` trước đây bao gồm cả `target_channel` trong JSON object chuẩn hóa. Khi phát bản nháp đa kênh (`publish_multi_channel`), hệ thống tạo các bản sao của `publication_candidate` và thay đổi `target_channel` theo từng kênh (ví dụ: `telegram:channel_1`, `tiktok_shop:channel_2`).

Điều này dẫn đến mâu thuẫn bất biến:
1. Nếu không đổi `draft_sha256`, bản nháp có `target_channel` mới nhưng giữ hash cũ (hash không phản ánh đúng canonical object khi tính lại từ `target_channel` mới).
2. Nếu tính lại `draft_sha256` theo kênh mới, `approval.draft_sha256` sẽ không khớp với candidate `draft_sha256`, làm hỏng cơ chế kiểm duyệt (`assert_approval_matches_draft`).

## Quyết định

1. **Chuẩn hóa `draft_sha256` theo nội dung nháp (Channel-Agnostic Content Hash):**
   `draft_sha256` được định nghĩa là SHA-256 hex của canonical JSON gồm 5 trường nội dung cốt lõi:
   - `observation_id`
   - `content`
   - `affiliate_url`
   - `affiliate_disclosure`
   - `claim_snapshot`

2. **Tách biệt nội dung và kênh phân phối:**
   - Phê duyệt (`approval-record.v1`) được gắn trực tiếp vào `draft_sha256` của nội dung. Một nội dung đã duyệt được phép phân phối tới nhiều kênh mà không cần cấp lại approval record riêng nếu nội dung và link affiliate giữ nguyên.
   - Định danh lũy đẳng của phiên đăng theo kênh được xác định qua `idempotency_key = f"{observation_id}:{target_channel}:{draft_sha256}"`.

3. **Bảo toàn chữ ký hàm `compute_draft_sha256`:**
   Giữ tham số `target_channel: str | None = None` trong chữ ký hàm để tương thích ngược, nhưng không đưa `target_channel` vào đối tượng JSON canonical dùng để băm.

## Hệ quả

- **Lợi ích:**
  - Giải quyết dứt điểm mâu thuẫn bất biến hash giữa `publication-candidate.v1`, `approval-record.v1` và `publish_multi_channel`.
  - Phê duyệt nội dung có tính lũy đẳng và tái sử dụng nhất quán cho phát sóng đa kênh.
  - Khử hoàn toàn rủi ro phê duyệt bị invalidate sai khi chọn kênh xuất bản.
- **Rủi ro & Đã giảm thiểu:**
  - Các fixture JSON mẫu cần cập nhật lại giá trị SHA-256 tương ứng (`ddd61687fe4b53cea53a8ef94aba13c655914a96a8541027951738209e0893bd`).
  - Đã cập nhật unit test và contract test để kiểm chứng tính ổn định của hash.

## Phương án không chọn

- **Yêu cầu phê duyệt riêng từng kênh (Per-channel Candidate & Approval):** Tăng độ phức tạp cho người duyệt khi phải bấm duyệt N lần cho 1 nội dung giống hệt nhau phát lên N kênh.
- **Bỏ `draft_sha256` khỏi hợp đồng:** Vi phạm bất biến bảo vệ an toàn nội dung affiliate, không chấp nhận được.

## Bằng chứng và điều kiện xem xét lại

- Kiểm tra contract schema: `tools/validate_repo.py` đạt OK.
- Tất cả unit tests trong `test_publication.py`, `test_approval_publisher.py` và `test_multi_channel.py` trôi qua 100%.
- Xem xét lại nếu về sau một kênh yêu cầu format nội dung khác biệt về mặt bản thể (ví dụ: TikTok yêu cầu video metadata riêng thuộc về draft payload).
