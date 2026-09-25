# DEAL — bằng chứng source và giới hạn

Parent DATA #41 HEAD75c302b/tree6af8047, CI36156814136 success. Base protected0fea065;
không tự merge #39/41 hoặc coi ADR0009 đề xuất là được chấp nhận.

- Red new acceptance: 10 tests lỗi do chưa có quality/evidence/composer capabilities.
- Green core: 10 tests OK: retained evidence, stock/freshness/future/conditions/hash,
  integer money, allowlist/redirect, final payload và model output không tự sinh claims.
- Expanded integration: 16 tests ban đầu 1 failure (redaction làm rơi new_customer_only)
  và 1 error (payload style là list không trả ValueError). Fix tách PII fields khỏi điều
  kiện mua và validate toàn payload schema trước invariant. Cùng tests xanh.
- Hai regression bổ sung: sensitive source title không được sao vào facts/candidate;
  model input budget không tắt template/manual. 28 test DEAL, 161 tổng discovery.
- `PYTHONPATH=src:<baseline-wheel-for-metadata> python -m unittest discover -s tests -v`:
  161 tests OK, Python3.13.5/jsonschema4.26.0. Không gọi là locked environment.
- Ruff0.16.7 lint/format, repository/schema/examples validation, git diff --check OK.
- Runtime-only smoke mở rộng kiểm manual source→retained evidence→facts→eligibility→
  final payload/persistent binding bên ngoài checkout; phải qua CI đúng HEAD mới.

Schema v1 cũ giữ nguyên. Hai schema mới có valid/invalid fixtures và package copies khớp.
Evidence permission_ref là operator attestation; raw bytes được hash rồi khử nhạy cảm
trước lưu. Bản lưu có hash riêng, không giả rằng đó là raw source nguyên vẹn. Payload bị
retire có tombstone; source facts/history không bị âm thầm đổi. Không lưu credential thật.

AI chế độ ràng buộc, chỉ fact order/style đã định nghĩa; fake model không nhận raw source
instruction, không có tool publish. Không tự chạy benchmark/API tính phí.

Hiện tại legacy publisher chưa dùng durable queue/scoped approval; PUB tiếp theo là gate
bắt buộc trước tuyên bố end-to-end posting. Manual/fake không phải live provider evidence.
