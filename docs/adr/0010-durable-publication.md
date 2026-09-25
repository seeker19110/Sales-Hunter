# ADR-0010 — Payload approval và durable publication cho pilot

Trạng thái: đề xuất; cần human T4 trước merge. Phụ thuộc ADR0008/0009 và PR DATA/DEAL.
Không chấp nhận quyền nền tảng, production cutover hoặc exactly-once xuyên mạng.

Duyệt payload cuối phải nhận revision đã xem và payload_sha256 từ preview. Ghi quyết định
candidate + scope (facts/hash/channel/renderer/revision/actor/time) trong cùng transaction.
Queue chỉ nhận scope còn hiện hành, không nhận approval/payload JSON do caller tự gửi.

Intent được commit trước side effect; key duy nhất theo scope. Claim nguyên tử có lease
và fencing token; attempt/send-start lưu trước gọi transport. Không giữ transaction qua
network. Claimed chưa send có thể claim lại; lease đã sending hết hạn -> outcome_unknown,
không ready/retry mù. Chỉ lỗi được transport xác nhận chưa gửi mới retry hữu hạn/backoff.
Readback phải khớp payload thực, channel, identifier/time. Lỗi sau accept hoặc readback
không đủ bằng chứng -> unknown và reconcile/manual review, không coi là failed chưa đăng.

Global/source/channel pause và nhật ký bền vững, mặc định paused. Kiểm trước claim/send/
retry; scope/revision/eligibility/evidence kiểm lại ngay trước send. Race sau send-start
không thể thu hồi thời gian: giữ receipt đúng payload cũ và tạo recall khi cần; không mất
bằng chứng remote chỉ vì local draft đổi trong lúc gọi transport.

Business cooldown theo đúng platform/shop/product/variant/conditions/channel, giữ qua
restart. Unknown và active intents chặn duplicate vô thời hạn tới khi reconcile. Multi-
request enqueue preflight toàn bộ rồi commit nguyên tử, không side effect trước khi kiểm.

Manual export là bản xuất có chứng cứ duyệt, không là bài đã đăng. Transport triển khai
ở epic này chỉ fake SQLite cục bộ với remote-state riêng, fault injection trước/sau accept,
lookup và recall/readback. Live capability disabled đến khi account/policy/endpoint được
xác minh. Legacy Publisher chỉ cho FakePlatformClient để không mở đường vòng network.

Restore luôn pause; mọi sending chưa rõ kết quả phải reconcile. Quy trình sau backup cần
đối soát remote phát sinh sau snapshot, thiếu receipt không chứng minh chưa đăng.

Nghiệm thu: hai worker/connections, restart, timeout/crash sau accept, stale fencing token,
retry giới hạn, unknown không retry mù, pause/restart, scope/revision/payload tamper, freshness,
readback lệch, business duplicate, manual export không count published, recall có xác nhận.
