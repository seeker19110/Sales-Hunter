# ADR-0009 — Facts, evidence và payload cuối có version

Trạng thái: đề xuất; human T4 trên diff cuối trước merge. Ngày 25/09/2026.
Phụ thuộc ADR-0008 và PR dữ liệu; giữ publication-candidate.v1/approval-record.v1 và
canonical content hash channel-agnostic hiện có, không thêm trường lén vào v1.

## Quyết định đề xuất

Thêm deal-facts.v1 chứa toàn bộ observation, variant scope, thời hạn, evidence_id,
adapter/normalizer version và actor đã ghi nhận. Facts bất biến, ID là hash canonical;
candidate v1 vẫn là read model tương thích. Publish mới phải có facts/evidence đầy đủ,
payload cuối có version/hash/channel và approval riêng gắn đúng revision đã xem.
Không coi candidate cũ thiếu facts là đủ điều kiện đăng.

Evidence là bản JSON được phép lưu, không chỉ digest. Giữ digest nguồn trước khử nhạy cảm
và digest bản thực lưu riêng; metadata và tombstone bất biến; payload có thể bị xóa theo
hạn quyền/thu hồi nhưng không âm thầm đổi nội dung. Không lưu credential/PII theo trường
nhạy cảm đã biết. Quyền lưu là attestation có người chịu trách nhiệm, không giả platform
permission. Expired/revoked/tampered evidence chặn nghiệp vụ.

Eligibility độc lập ranking: thời gian aware UTC, tuổi mặc định pilot 6 giờ, skew tối đa
5 phút, còn hàng, variant rõ, điều kiện/coupon không bị làm rơi, evidence còn hiệu lực.
Đây là policy cấu hình, không phải SLA hay quy định nền tảng. Coupon không được tự trừ
vào giá. Giá cuối không được gọi là xác minh nếu không có evidence riêng cho tổng giá.

Renderer tạo văn bản từ facts và disclosure/link đã kiểm; payload hash bao gồm channel,
facts_id, renderer_version, draft hash và nội dung cuối. Manual-export/fake capability
không chứng minh quyền Telegram/Shopee/TikTok live. Preview chính là text/hash sẽ duyệt.
AI tùy chọn chỉ sắp thứ tự/cách giới thiệu các fact IDs đã khóa bằng schema chặt, không
sinh số/link hoặc có công cụ đăng. Thiếu model/credential/budget hay output sai -> fallback
xác định. Không benchmark tính phí hoặc gọi provider thật trong phiên này.

URL: HTTPS, host allowlist chính xác, không credentials/địa chỉ IP/control/fragment hoặc
tham số secret; kiểm từng redirect. Không coi URL validation đơn thuần là chứng minh
DNS-rebinding-safe fetch. Ranh giới network chỉ được bật khi capability/permission được
xác minh riêng; toàn bộ test ở đây là nội bộ/manual.

## Nghiệm thu

Stock/stale/future/variant/coupon/unknown/zero/float/bool; evidence raw/retained hashes,
redaction/expiry/immutability; allowlist URL và redirect; final payload giữ đúng mọi điều
kiện/link/disclosure; AI schema/numeric/injection/budget/fallback; package contracts đồng
nhất và manual observation→eligible rank→candidate→preview không dùng API trả phí.
