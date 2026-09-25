# Sales-Hunter — đánh giá kỹ thuật và kế hoạch nâng cấp

**Ngày đánh giá:** 25/09/2026.  
**Repository:** seeker19110/Sales-Hunter.  
**Nhánh:** bootstrap/base.  
**Commit cố định:** `0159c420ad8976939a98fb579bc9f5404bfcec89`.

## 1. Kết luận điều hành

Giữ lõi Python modular monolith và định hướng dữ liệu có bằng chứng, ranking xác định, người duyệt trước đăng. Chưa bật publish thật hoặc coi dashboard hiện tại là production-ready chỉ vì CI xanh. Ưu tiên khép kín một luồng đáng tin cậy thay vì thêm nền tảng, model hay microservices.

Đây là hệ thống săn sale/affiliate cho Shopee và TikTok Shop, không phải CRM tìm khách hàng. Đề xuất kiến trúc giả định nhóm vận hành nội bộ nhỏ; chưa giả định SaaS nhiều tenant hoặc lưu lượng lớn.

### Phạm vi và giới hạn

Đã đọc mã nguồn trọng yếu qua GitHub, hợp đồng JSON, các test liên quan, CI/CD, trạng thái và roadmap tại commit trên. GitHub ghi CI run `35422018948` thành công ngày 19/09/2026; log job Linux/Python 3.11 `105841334388` ghi 75 tests/OK. CD run `35422052134` chỉ là placeholder, không phải deployment. Không có PR đang mở tại thời điểm đọc.

Đã chạy **12 probe cục bộ** trên hai module approval/publisher và hai JSON schema. Bốn tệp dùng trong probe được đối chiếu Git blob SHA và khớp byte với upstream. Kết quả: **9 tình huống tái hiện rủi ro trong 6 nhóm**, **3 kiểm soát hiện hữu hoạt động**, không có probe lỗi. Bốn tình huống trong chín tình huống là các biến thể của cùng lỗi hash; không được diễn giải thành chín lỗ hổng độc lập.

Không clone/chạy được toàn bộ repo trong môi trường này vì giới hạn truy cập mạng của container. Không chạy full suite cục bộ, không cài wheel production để tái hiện lỗi đóng gói, không test tải/production/credential thật, không đăng bài ra ngoài, không thực hiện backup-restore thật. Các phát hiện chỉ đọc mã được ghi rõ bên dưới. Không chỉnh sửa GitHub hay tạo PR.

### Ý nghĩa mức ưu tiên

**P0** trong báo cáo là điều kiện chặn mốc phát hành/side effect nêu cụ thể, không phải kết luận đang có sự cố bảo mật trên hệ thống live. **P1** cần giải quyết để chạy pilot/production đáng tin cậy. **P2** là cải thiện chất lượng và khả năng mở rộng sau các chốt an toàn.

### Những nền tảng nên giữ

Domain tách khỏi adapter; Money và ranking không dùng LLM để tính giá; observation/claim/hash có schema; dry-run mặc định; fake client không gọi mạng; CI có lint/type/schema/tests/audit, lockfile, pin SHA actions và ma trận hệ điều hành/Python. Kiến trúc hiện tại đã chọn modular monolith và không dùng chung credential/dữ liệu Learning mặc định. Những điều này tốt hơn việc viết lại toàn bộ từ đầu.

Nguồn: [ARCHITECTURE.md](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/ARCHITECTURE.md) · [docs/ROADMAP.md](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/docs/ROADMAP.md) · [.github/workflows/ci.yml](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/.github/workflows/ci.yml) · [src/s_n_sales/pipeline/publisher.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publisher.py)

## 2. Danh mục phát hiện và nghiệm thu

### SH-001 — Hash lưu sẵn không bảo vệ nội dung đã duyệt

**Ưu tiên:** P0. **Bằng chứng:** Đã tái hiện.

**Hiện trạng:** assert_approval_matches_draft chỉ so sánh hash giữa hai object; không tính lại hash từ nội dung. Bốn thử nghiệm sửa content, affiliate_url, affiliate_disclosure hoặc claim_snapshot nhưng giữ hash đều qua publisher giả lập.

**Đề xuất:** Draft revision bất biến; tính lại canonical hash tại ingest, approve và publish; lấy approval có hiệu lực từ kho tin cậy thay vì object do caller tùy ý cung cấp.

**Nghiệm thu:** Sửa từng trường được bảo vệ phải bị từ chối trước khi gọi client. Approval cũ không dùng được sau sửa hoặc thu hồi.

**Mã nguồn:** [src/s_n_sales/pipeline/approval.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/approval.py) · [src/s_n_sales/pipeline/publisher.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publisher.py)

### SH-002 — Publisher nhận approval chưa đầy đủ

**Ưu tiên:** P0. **Bằng chứng:** Đã tái hiện + đọc mã.

**Hiện trạng:** Object chỉ có status, publication_id và draft_sha256 được publisher chấp nhận, thiếu người duyệt, thời điểm, định danh và phiên bản schema.

**Đề xuất:** Validate approval đầy đủ; authorization theo actor thật, bản ghi đã commit và revision/channel scope; không coi possession of hash là quyền duyệt.

**Nghiệm thu:** Approval thiếu actor/thời điểm, giả mạo hoặc đã revoked không gọi được client.

**Mã nguồn:** [src/s_n_sales/pipeline/approval.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/approval.py) · [src/s_n_sales/pipeline/publisher.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publisher.py)

### SH-003 — Xác thực tùy chọn và token trong URL/log

**Ưu tiên:** P0 trước external deploy. **Bằng chứng:** Đọc mã.

**Hiện trạng:** Không có auth_token thì cho qua. Dashboard mang token trong query/form; CLI in URL có token. decided_by do caller nhập. Mặc định bind loopback có tác dụng giảm phơi lộ nhưng không có chốt cấu hình khi bind ra ngoài.

**Đề xuất:** Session cookie an toàn + CSRF; actor lấy từ phiên; vai trò viewer/reviewer/admin; scoped token cho máy. Không token trong URL/argv/log. Thiếu auth trong staging/prod phải từ chối khởi động.

**Nghiệm thu:** Test không đăng nhập, sai quyền, CSRF, đổi token, thu hồi phiên và rà log/redirect không có secret.

**Mã nguồn:** [src/s_n_sales/api/app.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/api/app.py) · [src/s_n_sales/api/__main__.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/api/__main__.py)

### SH-004 — Runtime dependency và schema không được đóng gói đúng

**Ưu tiên:** P0 trước phát hành artifact. **Bằng chứng:** Đọc mã + cấu hình.

**Hiện trạng:** dependencies rỗng trong khi runtime import jsonschema, đang đặt ở nhóm dev. Runtime đọc schema bằng parents[3]/schemas, ngoài package wheel. CI chạy môi trường dev và PYTHONPATH=src nên không chứng minh cài đặt production.

**Đề xuất:** Khai báo dependency runtime; đưa schemas thành package resources và đọc bằng importlib.resources; build wheel và smoke test trong môi trường sạch ngoài checkout.

**Nghiệm thu:** Cài chỉ wheel/runtime dependencies; không source tree, không PYTHONPATH, không dev dependencies vẫn tạo candidate, approve và dry-run được. Chạy bằng Python của môi trường đã tạo, tránh uv run tự bổ sung dev.

**Mã nguồn:** [pyproject.toml](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/pyproject.toml) · [src/s_n_sales/pipeline/approval.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/approval.py) · [src/s_n_sales/pipeline/publication.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publication.py) · [src/s_n_sales/pipeline/draft.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/draft.py) · [src/s_n_sales/pipeline/publisher.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publisher.py)

### SH-005 — Chống đăng trùng chỉ ở bộ nhớ publisher

**Ưu tiên:** P0 trước publish thật. **Bằng chứng:** Đã tái hiện một phần + đọc mã.

**Hiện trạng:** Publisher dùng dict _receipts_by_key, không nối với SQLite receipts. Hai Publisher mới gọi client hai lần. Trong mô phỏng provider không hỗ trợ dedup, tạo hai post. Chưa kiểm thử hành vi của provider thật.

**Đề xuất:** Outbox/intent bền vững, unique logical key, lease worker, lưu attempt và receipt; unknown outcome phải reconcile trước retry. Native idempotency của provider được dùng khi có nhưng không được giả định.

**Nghiệm thu:** Hai worker cùng nhận job, restart, lỗi sau remote accept/trước save và retry sau timeout không gây retry mù; trạng thái mơ hồ có đường xử lý rõ.

**Mã nguồn:** [src/s_n_sales/pipeline/publisher.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publisher.py) · [src/s_n_sales/api/store_sqlite.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/api/store_sqlite.py)

### SH-006 — API upsert bỏ qua hợp đồng và nhận trạng thái từ client

**Ưu tiên:** P1. **Bằng chứng:** Đọc mã.

**Hiện trạng:** upsert_candidate chủ yếu kiểm publication_id; không chạy candidate schema/domain validator. Nhận cả approval.status do người gửi đặt.

**Đề xuất:** Tách CreateDraftInput khỏi CandidateReadModel; trường actor, hash, approval, receipt chỉ do server sinh; validate schema và invariant ở application service.

**Nghiệm thu:** Payload sai kiểu, thiếu claim, status approved tự khai, hash sai và URL sai đều bị chặn có mã lỗi ổn định.

**Mã nguồn:** [src/s_n_sales/api/app.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/api/app.py) · [src/s_n_sales/api/store_sqlite.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/api/store_sqlite.py)

### SH-007 — Candidate sau approve không khớp schema candidate

**Ưu tiên:** P1. **Bằng chứng:** Đọc mã + đối chiếu schema.

**Hiện trạng:** Store đặt toàn bộ approval-record vào candidate.approval. Nested schema approval của candidate dùng additionalProperties:false và không cho các trường schema_version, approval_id, publication_id, policy_version.

**Đề xuất:** Lưu approval tách biệt; read model dùng approval reference hoặc schema dùng $ref/version mới một cách nhất quán. Có adapter dữ liệu cũ.

**Nghiệm thu:** Validate candidate sau create, approve, reject, reload database và trả API đều thành công.

**Mã nguồn:** [src/s_n_sales/api/store_sqlite.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/api/store_sqlite.py) · [schemas/publication-candidate.v1.json](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/schemas/publication-candidate.v1.json) · [schemas/approval-record.v1.json](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/schemas/approval-record.v1.json)

### SH-008 — Duyệt và cập nhật chưa nguyên tử

**Ưu tiên:** P1. **Bằng chứng:** Đọc mã.

**Hiện trạng:** approve/reject đọc candidate dưới lock rồi nhả lock, sau đó ghi lại dưới lock khác. UPDATE chỉ theo publication_id. Upsert xen giữa có thể bị ghi đè bằng JSON cũ, thậm chí hash ở cột và JSON khác nhau.

**Đề xuất:** Transaction và optimistic concurrency theo revision/version/hash; cập nhật có điều kiện; xung đột trả 409, không âm thầm ghi đè.

**Nghiệm thu:** Dùng barrier điều phối hai luồng update/approve; chỉ revision được hiển thị mới được duyệt; không lost update.

**Mã nguồn:** [src/s_n_sales/api/store_sqlite.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/api/store_sqlite.py)

### SH-009 — Lịch sử duyệt bị ghi đè và approval cũ chưa vô hiệu hóa

**Ưu tiên:** P1. **Bằng chứng:** Đọc mã.

**Hiện trạng:** Bảng approvals khóa theo publication_id và ON CONFLICT UPDATE ghi đè lịch sử; upsert candidate không tự vô hiệu bản ghi approvals riêng.

**Đề xuất:** ApprovalEvent append-only; trạng thái hiện hành là projection từ sự kiện, gắn revision. Sửa nội dung tạo revision mới và invalidate phê duyệt tương ứng trong cùng transaction.

**Nghiệm thu:** Lưu được approve→reject→reapprove theo actor/time; hai endpoint candidate và approval không mâu thuẫn.

**Mã nguồn:** [src/s_n_sales/api/store_sqlite.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/api/store_sqlite.py)

### SH-010 — Dashboard hiển thị sai giá và nền tảng

**Ưu tiên:** P1. **Bằng chứng:** Đọc mã + đối chiếu builder.

**Hiện trạng:** UI đọc sale_price_units/list_price_units/discount_ratio và platform ở cấp ngoài. Builder sinh sale_price_minor/list_price_minor và claim_snapshot.platform; các field UI đang đọc trả mặc định 0 hoặc rỗng.

**Đề xuất:** Một view model chuẩn; dùng Money/Decimal cho hiển thị và tính phần trăm; giá chưa biết hiện Chưa xác minh, không hiện 0.

**Nghiệm thu:** Browser test lấy candidate từ builder thực: giá 80.000/100.000, giảm 20%, đúng nền tảng; test cả list_price null, giá 0 và giá lớn.

**Mã nguồn:** [src/s_n_sales/api/app.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/api/app.py) · [src/s_n_sales/pipeline/publication.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publication.py) · [schemas/publication-candidate.v1.json](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/schemas/publication-candidate.v1.json)

### SH-011 — Link/disclosure có trong metadata nhưng thiếu ở payload gửi

**Ưu tiên:** P1 trước publish thật. **Bằng chứng:** Đã tái hiện.

**Hiện trạng:** Publisher chỉ truyền candidate.content. Không compose hoặc kiểm tra affiliate_url/disclosure trong nội dung. Đây không có nghĩa mọi content đều thiếu; caller có thể tự chèn, nhưng hệ thống chưa bảo đảm.

**Đề xuất:** Renderer theo channel tạo payload cuối; validate link/disclosure/commercial flags/độ dài; duyệt đúng payload cuối và kiểm receipt/readback theo capability thực.

**Nghiệm thu:** Payload thực gửi có đủ trường bắt buộc, preview trùng payload đã hash; sửa nội dung theo kênh bắt duyệt lại.

**Mã nguồn:** [src/s_n_sales/pipeline/publication.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publication.py) · [src/s_n_sales/pipeline/publisher.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publisher.py)

### SH-012 — Không có freshness gate ngay trước khi đăng

**Ưu tiên:** P1 trước publish thật. **Bằng chứng:** Đã tái hiện + đọc mã.

**Hiện trạng:** Publisher chấp nhận observation từ năm 2000 trong probe. Hàm recall chỉ so tuổi 24 giờ, không có worker thật tự kiểm/gỡ bài.

**Đề xuất:** Freshness policy theo nguồn/loại deal, valid_until và last_verified_at; revalidate ngay trước publish; queue recall có thực thi/xác nhận, không đồng nhất quyết định recall với đã gỡ bài.

**Nghiệm thu:** Hết hạn khi đang chờ duyệt, hết hàng sau duyệt và nguồn không xác minh được đều có xử lý an toàn; thu hồi có bằng chứng.

**Mã nguồn:** [src/s_n_sales/pipeline/publisher.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publisher.py) · [src/s_n_sales/analytics/recall.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/analytics/recall.py)

### SH-013 — Ranking chưa tách điều kiện đủ và mức hấp dẫn

**Ưu tiên:** P1. **Bằng chứng:** Đọc mã.

**Hiện trạng:** Điểm cộng tồn kho chứ không loại hết hàng; giá quan sát ở tương lai bị clamp age=0. Builder bỏ qua rank_result. Vì vậy điểm cao không chứng minh đủ điều kiện xuất bản.

**Đề xuất:** Eligibility gate riêng trước ranking và publish; kiểm sai lệch đồng hồ, quyền nguồn, điều kiện coupon/variant/stock. Score chỉ xếp thứ tự các deal đã đủ điều kiện.

**Nghiệm thu:** Deal hết hàng/tương lai/thiếu điều kiện không vào hàng xuất bản dù điểm discount cao.

**Mã nguồn:** [src/s_n_sales/domain/ranking.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/domain/ranking.py) · [src/s_n_sales/pipeline/publication.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publication.py)

### SH-014 — Snapshot claim làm rơi các điều kiện mua quan trọng

**Ưu tiên:** P1. **Bằng chứng:** Đọc mã.

**Hiện trạng:** Observation có variant, shipping, coupon, eligibility, evidence hash; claim_snapshot chỉ giữ nhóm giá/thời điểm/nguồn. Thiếu bằng chứng cho giá cuối hoặc điều kiện tài khoản.

**Đề xuất:** Version snapshot đủ product/variant, điều kiện tài khoản/vùng, coupon, phí ship, bằng chứng và thời hạn; unknown là trạng thái rõ. Không gọi giá chưa cộng phí là giá cuối.

**Nghiệm thu:** Cùng sản phẩm khác biến thể hoặc coupon chỉ cho tài khoản mới không bị mô tả như ưu đãi chung.

**Mã nguồn:** [src/s_n_sales/pipeline/publication.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publication.py) · [schemas/offer-observation.v1.json](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/schemas/offer-observation.v1.json)

### SH-015 — URL chỉ được kiểm scheme HTTPS

**Ưu tiên:** P1 trước tích hợp mạng. **Bằng chứng:** Đọc mã.

**Hiện trạng:** Builder kiểm scheme, chưa allowlist host/chương trình affiliate; API upsert có thể bỏ qua luôn builder. Chưa có client mạng thật nên không kết luận đang tồn tại SSRF khai thác được trên production.

**Đề xuất:** Allowlist theo adapter, validate hostname/credentials/redirects và các đích nội bộ khi fetch; đường tạo affiliate link thuộc adapter được cấp quyền, không thuộc LLM.

**Nghiệm thu:** Domain không thuộc chương trình, URL thiếu host, scheme không cho phép, redirect tới private network bị chặn tại ranh giới phù hợp.

**Mã nguồn:** [src/s_n_sales/pipeline/publication.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publication.py) · [src/s_n_sales/pipeline/draft.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/draft.py) · [src/s_n_sales/api/store_sqlite.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/api/store_sqlite.py)

### SH-016 — Ghi sai UTC khi now có offset

**Ưu tiên:** P1. **Bằng chứng:** Đã tái hiện.

**Hiện trạng:** Publisher dùng strftime(...Z) mà không astimezone(UTC). Đầu vào 10:00+07:00 thành read_back_at=10:00Z thay vì 03:00Z. FakePlatformClient có kiểu lỗi tương tự.

**Đề xuất:** Chuẩn hóa UTC trước serialize; một hàm timestamp dùng chung; thời gian hiển thị mới đổi sang Asia/Ho_Chi_Minh.

**Nghiệm thu:** Test offset +07, -05, UTC và timestamp đúng cùng instant.

**Mã nguồn:** [src/s_n_sales/pipeline/publisher.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publisher.py)

### SH-017 — Kill switch chưa là công cụ vận hành bền vững

**Ưu tiên:** P1. **Bằng chứng:** Đọc mã.

**Hiện trạng:** Đang là tham số boolean/call trong mã; chưa có trạng thái pause bền vững dùng chung cho nhiều worker hay màn hình thao tác và audit.

**Đề xuất:** Pause toàn hệ thống/nguồn/kênh trong DB, audit actor/reason/time; worker đọc sát trước side effect và kiểm lại khi retry. Ghi rõ yêu cầu in-flight có thể đã tới provider.

**Nghiệm thu:** Pause còn hiệu lực sau restart, worker cũ và worker mới đều thấy; việc resume có xác nhận và không tự retry unknown.

**Mã nguồn:** [src/s_n_sales/pipeline/publisher.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publisher.py) · [src/s_n_sales/pipeline/multi_channel.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/multi_channel.py) · [docs/RUNBOOK.md](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/docs/RUNBOOK.md)

### SH-018 — HTTP handler tự viết còn thiếu kiểm soát production

**Ưu tiên:** P1 trước external deploy. **Bằng chứng:** Đọc mã + tài liệu Python.

**Hiện trạng:** Dùng http.server; đọc Content-Length trước xác thực và không thấy giới hạn body; xử lý lỗi input chưa đầy đủ. log_message bị tắt và healthz luôn ok, không thể đại diện trạng thái DB/worker.

**Đề xuất:** Framework/server production; auth middleware, body/time limits, mã lỗi rõ, log cấu trúc che secret, readiness và liveness riêng.

**Nghiệm thu:** Body quá lớn, length không hợp lệ, UTF-8 lỗi, DB down và worker mất heartbeat được kiểm tra có giới hạn.

**Mã nguồn:** [src/s_n_sales/api/app.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/api/app.py) · [src/s_n_sales/api/__main__.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/api/__main__.py)

### SH-019 — Analytics chưa bền vững/chống trùng/đối soát hoa hồng

**Ưu tiên:** P1 trước đo hiệu quả thật. **Bằng chứng:** Đọc mã.

**Hiện trạng:** Event list nằm trong bộ nhớ, chưa có provider_event_id để dedup; conversion/click tổng đơn giản, chưa vòng đời đơn hoặc hoa hồng xác nhận/hoàn/hủy.

**Đề xuất:** Event log bền vững, event ID và webhook verification, attribution có nguồn, commission ledger và đối soát; tối thiểu dữ liệu cá nhân.

**Nghiệm thu:** Webhook lặp không tăng conversion; refund điều chỉnh đúng; restart không mất event; dashboard tách ước tính, xác nhận, đã nhận.

**Mã nguồn:** [src/s_n_sales/analytics/events.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/analytics/events.py) · [src/s_n_sales/analytics/metrics.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/analytics/metrics.py)

### SH-020 — CD xanh chưa phải deploy; runbook chưa có bằng chứng phục hồi

**Ưu tiên:** P1 trước cutover. **Bằng chứng:** Đọc mã.

**Hiện trạng:** CD hiện chỉ echo gate. Runbook có hướng dẫn tham số code/revert git; chưa có pipeline artifact/deploy và bằng chứng backup-restore thực tế trong phạm vi đọc.

**Đề xuất:** Artifact bất biến theo SHA, staging smoke, approval cutover, migrations, rollback artifact tương thích schema, backup ngoài máy và restore drill.

**Nghiệm thu:** Khôi phục vào môi trường sạch; kiểm số lượng/hash/approval/outbox; giữ publish paused và reconcile giao dịch remote sau thời điểm backup trước resume.

**Mã nguồn:** [.github/workflows/cd.yml](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/.github/workflows/cd.yml) · [docs/RUNBOOK.md](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/docs/RUNBOOK.md)

### SH-021 — Tài liệu kiến trúc lệch hiện trạng

**Ưu tiên:** P2. **Bằng chứng:** Đọc tài liệu.

**Hiện trạng:** ARCHITECTURE vẫn nói in-memory/no persistence trong khi status/roadmap đã ghi SQLite và token dashboard. Một số checkbox skeleton dễ bị hiểu nhầm là năng lực production.

**Đề xuất:** Tách rõ implemented, verified staging, verified production; ít tài liệu nguồn chuẩn; cập nhật cùng PR thay đổi, không thêm nhiều checklist trùng lặp.

**Nghiệm thu:** README/status/architecture cùng mô tả đúng khả năng chạy hiện tại và blocker; release evidence gắn SHA.

**Mã nguồn:** [ARCHITECTURE.md](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/ARCHITECTURE.md) · [PROJECT-STATUS.md](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/PROJECT-STATUS.md) · [docs/ROADMAP.md](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/docs/ROADMAP.md)

### SH-022 — Tính khả thi TikTok Direct Post cần chốt trước

**Ưu tiên:** P1 trước đầu tư connector. **Bằng chứng:** Chính sách nguồn chính thức.

**Hiện trạng:** Tài liệu TikTok Direct Post ngày 04/08/2026 nêu công cụ chỉ upload cho tài khoản của cá nhân/đội nội bộ là use case không chấp nhận. Client chưa audit bị hạn chế. Không suy rộng quy định này thành cấm toàn bộ TikTok Shop affiliate.

**Đề xuất:** Lập ma trận riêng quyền lấy dữ liệu, affiliate, media, content posting, analytics; chứng minh account/scope/app review cho use case thật. Giữ manual/export khi chưa được phép.

**Nghiệm thu:** Mỗi connector có owner/account/scope/quota/tài liệu áp dụng và bằng chứng quyền; không fallback scraping hoặc endpoint không cho phép.

**Mã nguồn:** [docs/ROADMAP.md](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/docs/ROADMAP.md) · [docs/GIA-DINH-NEN-TANG.md](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/docs/GIA-DINH-NEN-TANG.md)

### SH-023 — Lỗi đa kênh chưa được phân loại nhất quán

**Ưu tiên:** P2. **Bằng chứng:** Đọc mã.

**Hiện trạng:** multi_channel bắt PublishError, còn ApprovalError là ValueError riêng; một số lỗi integrity có thể thoát ngoài cơ chế result từng kênh. Cần xác định lỗi toàn cục và lỗi theo kênh thay vì bắt Exception mù.

**Đề xuất:** Integrity/auth thất bại là dừng toàn request; lỗi provider cục bộ là outcome theo kênh; chuẩn hóa error taxonomy.

**Nghiệm thu:** Hai kênh: một lỗi tạm thời không chặn kênh hợp lệ; hash sai chặn tất cả trước side effect; kết quả giải thích rõ.

**Mã nguồn:** [src/s_n_sales/pipeline/multi_channel.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/multi_channel.py) · [src/s_n_sales/pipeline/approval.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/approval.py)

### SH-024 — Danh sách và giao diện thiếu quy mô vận hành

**Ưu tiên:** P2. **Bằng chứng:** Đọc mã.

**Hiện trạng:** list_candidates/list_receipts đọc toàn bộ; UI tập trung approve/reject, chưa inbox lỗi nguồn, deal quá hạn, kết quả unknown hay lô nhập.

**Đề xuất:** Pagination, index theo status/time; inbox có filter/search, bulk review với kiểm revision riêng, responsive mobile, keyboard, empty/error/loading states.

**Nghiệm thu:** Dataset lớn hơn pilot thực tế vẫn có giới hạn query/payload; mobile duyệt đúng dữ liệu; thao tác bulk không bỏ qua gate.

**Mã nguồn:** [src/s_n_sales/api/app.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/api/app.py) · [src/s_n_sales/api/store_sqlite.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/api/store_sqlite.py)

### SH-025 — Chưa chứng minh được chuỗi lưu bằng chứng raw

**Ưu tiên:** P2. **Bằng chứng:** Đọc schema và adapter.

**Hiện trạng:** Có trường payload_sha256 trong observation nhưng chỉ có hash không thay thế việc lưu payload nguồn được phép và đối chiếu hash. Manual adapter đọc JSON operator cung cấp.

**Đề xuất:** Evidence record bất biến: raw hợp lệ theo điều khoản, hash, nguồn, fetched_at, adapter_version, normalizer_version; policy lưu trữ/xóa; không lưu credential trong raw.

**Nghiệm thu:** Rebuild normalized offer từ evidence và version cho cùng kết quả; evidence thiếu hoặc không kiểm được có nhãn confidence rõ.

**Mã nguồn:** [src/s_n_sales/adapters/manual.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/adapters/manual.py) · [schemas/offer-observation.v1.json](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/schemas/offer-observation.v1.json)

### SH-026 — Kiểu dữ liệu rộng khiến contract dễ lệch

**Ưu tiên:** P2. **Bằng chứng:** Đọc mã + pyproject.

**Hiện trạng:** Nhiều dict[str, Any], store:Any dù có Protocol; typecheck basic không bắt nhầm tên trường như lỗi UI.

**Đề xuất:** Typed input/domain/read model, strict ở các module integrity trước; một nguồn sinh schema/DTO hoặc contract test hai chiều. Không cần đổi ngôn ngữ.

**Nghiệm thu:** Sai tên field/thiếu trường quan trọng bị phát hiện trước runtime; code adapter không truy cập dict tùy ý ngoài boundary.

**Mã nguồn:** [src/s_n_sales/api/app.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/api/app.py) · [src/s_n_sales/pipeline/publication.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publication.py) · [pyproject.toml](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/pyproject.toml)

### SH-027 — Idempotency kỹ thuật chưa giải quyết spam cùng deal

**Ưu tiên:** P2. **Bằng chứng:** Đề xuất dựa trên khóa hiện tại.

**Hiện trạng:** Khóa mặc định theo observation, channel và hash. Quan sát mới của cùng ưu đãi có thể có khóa mới dù người đọc coi là bài trùng; đây là nhu cầu business dedup riêng.

**Đề xuất:** Chính sách cooldown theo product+variant+channel+campaign; chỉ repost khi thay đổi có ý nghĩa hoặc operator cho phép. Tách business dedup khỏi retry idempotency.

**Nghiệm thu:** Hai observation không đổi giá không tạo hai bài trong cửa sổ; giảm giá mới có bằng chứng được xử lý theo policy.

**Mã nguồn:** [src/s_n_sales/pipeline/publication.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/publication.py) · [src/s_n_sales/pipeline/multi_channel.py](https://github.com/seeker19110/Sales-Hunter/blob/0159c420ad8976939a98fb579bc9f5404bfcec89/src/s_n_sales/pipeline/multi_channel.py)

## 3. Kiến trúc đích: ít thành phần nhưng đúng ranh giới

**Lựa chọn đề xuất:** Python modular monolith + Django 5.2 LTS (bản vá bảo mật đang được hỗ trợ) + giao diện server-rendered + PostgreSQL cho môi trường có web/worker vận hành thật. Một web process/service và một worker dùng cùng artifact/version; một database; TLS/reverse proxy hiện hữu hoặc được quản lý. Chưa cần Redis, Kafka, Elasticsearch, Kubernetes hay frontend SPA riêng.

Django được đề xuất vì nhu cầu hiện tại xoay quanh tài khoản, phiên, quyền, biểu mẫu duyệt và dữ liệu quan hệ. Không phải thay framework là tự hết lỗi nghiệp vụ. Giữ domain/validation/ranking độc lập, thêm adapter Django thay dần HTTP handler và storage glue. Sửa regression integrity/packaging ngay, không chờ migration framework xong mới sửa.

SQLite vẫn hợp lý cho pilot đơn máy, ít ghi; không phải nguyên nhân tự thân của lost update trong store. Nếu tiếp tục pilot bằng SQLite, phải giới hạn deployment, sửa transaction, kiểm backup đúng và tránh filesystem mạng. Đích PostgreSQL nên dùng cả trong integration test; không dùng kết quả SQLite để suy ra concurrency PostgreSQL đã đúng. Chuyển dữ liệu bằng importer có manifest/count/hash, giữ nguồn SQLite read-only để kiểm tra, không dual-write kéo dài.

Nếu ngân sách cho phép, ưu tiên database/backup được quản lý để giảm công chăm sóc; không cần tự host cả một bộ observability lớn. Nếu tự vận hành, phải chỉ định người chịu trách nhiệm restore, dung lượng và cập nhật.

### Luồng nghiệp vụ đề xuất

```text
Nguồn được phép hoặc nhập liệu có bằng chứng
→ lưu evidence/observation bất biến
→ chuẩn hóa + validate + eligibility gate
→ ranking có lý do
→ canonical draft revision
→ payload từng kênh + kiểm điều kiện/disclosure
→ người có quyền duyệt đúng revision/payload
→ durable outbox
→ worker publish / reconcile
→ receipt xác nhận
→ theo dõi hết hạn, thu hồi và đối soát conversion
```

### Canonical hash và approval

Giữ canonical content hash không phụ thuộc kênh để nhận diện nội dung gốc. Nhưng nếu thay caption, link, disclosure, media hay metadata thương mại khi render theo kênh, payload đó cần hash/version và phạm vi phê duyệt riêng. Không dùng một hash bất biến của nội dung gốc để ngầm cho phép mọi biến thể hoặc mọi kênh mới.

### Dữ liệu tối thiểu

Các thực thể đề xuất: Product/Variant, Observation, Evidence, OfferEligibility, DraftRevision, ChannelPayload, ApprovalEvent, PublishIntent, PublishAttempt, PublishReceipt, KillSwitch, AttributionEvent và CommissionLedger. Đây là bảng/module logic trong một ứng dụng, không phải mỗi thực thể là một service.

PublishIntent cần revision, channel/account, idempotency key, status, attempts, next_attempt_at, lease_owner/lease_until và last_error_code. Receipt cần liên hệ với intent/attempt và bằng chứng remote. Draft/approval/evidence bất biến; view/dashboard là projection có thể tái tạo.

### Trạng thái publish

```text
queued → claimed → sending → confirmed
                       ↘ outcome_unknown → reconciling → confirmed / manual_review
                       ↘ retryable_failed → queued (có giới hạn)
                       ↘ terminal_failed
```

Không gọi mọi timeout là failed. Không hứa exactly-once xuyên mạng khi provider không cung cấp idempotency/đối soát phù hợp. Mục tiêu thực tế là không retry mù, phát hiện trùng và giải quyết outcome không rõ theo capability của từng provider.

## 4. Nâng cấp sản phẩm theo chất lượng deal

### Deal Inbox thay vì chỉ danh sách approve/reject

Một màn hình mặc định tập trung vào việc operator phải quyết định: deal tốt và còn đủ mới, bản nháp chờ duyệt, giá/coupon cần xác minh, lỗi nguồn, bài có nguy cơ sai, tác vụ chưa biết đã đăng hay chưa. Filter theo nền tảng, danh mục, mức tin cậy, thời gian hết hạn và người xử lý. Cần nhập form/CSV có preview, validate từng dòng và lịch sử import, không yêu cầu operator sửa JSON.

Trang duyệt hiển thị ảnh được phép sử dụng, sản phẩm/biến thể, giá và điều kiện mua, bằng chứng, thời điểm xác minh, lý do ranking, thay đổi so với lần quan sát trước, link đúng đích, disclosure và preview payload cuối. Giá chưa biết không biến thành 0. Đổi revision trong lúc màn hình đang mở phải báo xung đột, không approve nhầm bản mới.

Thao tác di động và bàn phím, trạng thái tải/lỗi/trống rõ ràng, ngôn ngữ tiếng Việt nhất quán, không chỉ dùng màu để thể hiện trạng thái. Duyệt hàng loạt vẫn phải kiểm từng revision và từng eligibility gate.

### Chất lượng giá

Tách giá niêm yết, giá hiện bán, giá có điều kiện coupon, phí ship và giá cuối đã xác minh. Điều kiện người mua mới, tài khoản/vùng, đơn tối thiểu, số lượng, phương thức thanh toán và khả năng cộng dồn phải là dữ liệu, không chỉ là câu văn.

Xây lịch sử giá theo đúng product/merchant/variant. Khi chưa đủ lịch sử hoặc không đủ quyền dữ liệu, không tuyên bố rẻ nhất/lịch sử thấp nhất. Không so các biến thể khác nhau chỉ vì tiêu đề tương tự. Đưa mức đầy đủ của bằng chứng vào điều kiện xếp hạng; điểm hoa hồng không được lấn át độ đúng của claim.

### Nguồn và chi phí khai thác

Bắt đầu một nguồn hợp lệ, một kênh phát hành, ít danh mục, người duyệt. Refresh có ưu tiên: ưu đãi đang chờ đăng/gần hết hạn được kiểm trước; observation không đổi không cần tạo draft/LLM lại. Có ngân sách request theo nguồn, backoff, Retry-After, circuit breaker và cảnh báo credential hết hạn. Không dùng scraping làm fallback mặc định.

### Đo hiệu quả thật

Bảng điều hành tách lượt click, conversion pending/confirmed/refunded, hoa hồng ước tính/xác nhận/đã trả, theo kênh và nội dung. Có đối soát nguồn, cửa sổ attribution và chống event trùng. Chỉ tối ưu A/B hoặc ranking dựa trên conversion sau khi đối soát đủ tin cậy.

Chỉ số đề xuất: tỷ lệ claim có bằng chứng, tỷ lệ bài quá hạn, publish chưa rõ kết quả, bài trùng, thời gian operator xử lý một deal, tỷ lệ sửa/gỡ bài và hoa hồng xác nhận trên chi phí vận hành. Đây là metric cần đo, không phải kết quả hiện tại hay cam kết lợi nhuận.

## 5. AI: tăng chất lượng nội dung, không nắm sự thật và quyền đăng

Tác vụ phù hợp: tạo vài biến thể diễn đạt tiếng Việt từ claim đã khóa, rút gọn theo kênh, gợi ý tiêu đề/tag, tóm tắt khác biệt giá, giải thích rejection, phân loại hỗ trợ có người xác nhận. Không giao AI tính tiền, tạo link affiliate, suy đoán còn hàng, xác nhận coupon, tuyên bố khan hiếm hoặc quyết định quyền publish.

Pipeline đề xuất: facts allowlist → model output có schema → renderer → kiểm số/link/điều kiện/disclosure → preview → approval. Dữ liệu nguồn là dữ liệu không tin cậy, không được trở thành chỉ thị cấp quyền hay tool call. AI không được đọc secret/token hoặc tự chạy công cụ đăng bài. Nội dung/media dùng phải có quyền; không biến metadata chưa xác minh thành claim đã xác minh.

Dùng template deterministic làm baseline và fallback khi model lỗi/quá ngân sách. Chọn model qua benchmark bộ deal tiếng Việt của dự án, không theo tên mới nhất. Version model/prompt/policy; lưu chi phí theo task; cache theo content hash + prompt version; đặt trần token/cost/retry từng job và toàn ngày. Tạo ít biến thể rồi đo chất lượng, không cho các agent tự sửa qua lại vô hạn.

Bộ đánh giá nên có coupon điều kiện, hết hàng, biến thể, giá null/0, sai đơn vị, stale data, nội dung nguồn mang chỉ thị độc hại và trường hợp không đủ bằng chứng. Những lỗi sai giá/link/điều kiện là tiêu chí chặn, không được bù bằng điểm văn phong.

## 6. Vận hành ít thao tác

Các khả năng cần đóng gói thành lệnh hoặc màn hình (chưa phải lệnh đã tồn tại): doctor, migrate, backup, restore-check, pause, resume, retry-safe, reconcile, export-evidence. Operator không phải mở Python để đặt boolean kill switch.

Cấu hình có kiểu và kiểm khi khởi động: môi trường, database, secret, allowed hosts, publish mode, credentials/scopes từng adapter, giới hạn ngân sách và endpoint cảnh báo. .env.example chỉ chứa giá trị giả; secret thật ngoài Git. Thiếu điều kiện an toàn thì fail closed, không âm thầm chuyển qua chế độ ít bảo vệ.

Deploy từ artifact bất biến và SHA, không git pull trực tiếp rồi chạy mã mới chưa kiểm. Build một lần, dùng cùng artifact ở staging và production. Có server production thay http.server, TLS, non-root, giới hạn request/process, migration tương thích và đường rollback đã thử. Không dùng phiên/credential dùng chung mặc định với Learning ở domain cha.

Health nên tách liveness (process sống), readiness (DB/schema sẵn sàng), worker heartbeat, tuổi job chờ, quota/credential của nguồn và độ mới backup. Log JSON có request/job/publication ID và error code, che token/PII. Chỉ cảnh báo việc cần người xử lý; không tạo một tin nhắn cho mỗi retry nhỏ.

Backup có mã hóa và bản sao ngoài máy, lịch retention, restore drill vào môi trường sạch. Sau restore giữ publish paused, đối soát các side effect remote sau thời điểm backup; backup mất receipt cục bộ không đồng nghĩa bài remote chưa được đăng. RPO/RTO phải chọn theo rủi ro và được đo bằng bài phục hồi, chưa có số đo ở đợt audit này.

## 7. Lộ trình theo cổng nghiệm thu

| Đợt | Phạm vi | Cổng ra |
|---|---|---|
| A — Baseline và chặn lỗi | Regression hash/approval, runtime packaging, schema contract, token/log fail-closed | Các lỗi integrity đã có regression; runtime-only artifact chạy được; chưa bật mạng |
| B — Identity và transaction | Lớp web chuẩn, session/roles, actor thật, immutable revision, approval event, migration | Duyệt đúng phiên bản, chống giả actor và lost update; schema sau approve hợp lệ |
| C — Operator workflow | Giá/nền tảng đúng, nhập liệu, evidence, eligibility, channel renderer, preview | Một luồng manual từ bằng chứng tới nội dung đã duyệt, không cần sửa JSON |
| D — Side effects bền vững | Outbox, worker, idempotency, lease, persistent pause, reconcile | Restart/concurrency/timeout/unknown/freshness tests đạt bằng fake có các kiểu lỗi |
| E — Staging có thể phục hồi | Artifact deploy, readiness/logging, backup/restore, rollback | Restore thử và rollback thành công; có owner/on-call; không suy CI xanh thành live |
| F — Pilot thật hẹp | Một nguồn và một kênh đã xác minh quyền; human approval | Đăng/đọc lại/đối soát/thu hồi có bằng chứng thật; không mở kênh thứ hai trước cổng này |
| G — Tối ưu có dữ liệu | Conversion/commission, chất lượng ranking, AI benchmark | Hiệu quả và chất lượng được đo; mở rộng chỉ khi không tăng gánh nặng vận hành |

Bắt đầu bằng các PR nhỏ theo ranh giới trên, không gom một PR thay toàn bộ framework, schema và business rules. Công việc độc lập có thể chạy song song; contracts/schema, lockfile và migration có người điều phối duy nhất. Người tích hợp chịu trách nhiệm test xuyên luồng. Publish path, security, chính sách nền tảng và cutover cần review kỹ hơn công việc tài liệu/format.

### Bộ test bổ sung bắt buộc

Test content đổi nhưng hash cũ; approval thiếu/giả/revoked; channel payload khác bản duyệt; candidate sau mọi transition khớp schema; hai operator sửa/duyệt đồng thời; body quá lớn/UTF-8 lỗi; token không xuất hiện trong URL/log; cùng job hai worker; restart/crash sau remote accept; partial readback; timeout không rõ; retry quá trần; kill switch qua restart; stale/stock/coupon thay đổi; timezone +07; webhook trùng/sai chữ ký; wheel-only/runtime-only; restore database và reconcile remote; browser render đúng số thật.

## 8. Quyền nền tảng và tham chiếu chính thức

Ma trận connector phải tách quyền đọc sản phẩm/ưu đãi, tạo affiliate link, dùng media, đăng nội dung và đọc conversion. Không suy rằng đã tham gia affiliate là có mọi API cần thiết. Chính sách TikTok Direct Post bên dưới liên quan một sản phẩm API cụ thể; cần đánh giá đúng use case, không dùng nó để kết luận cấm toàn bộ hoạt động affiliate TikTok Shop. Cho tới khi có bằng chứng account/scope/app review, giữ manual hoặc export được phép.

Nguồn chính thức tra cứu ngày 25/09/2026:

- Python: http.server không được khuyến nghị cho production: https://docs.python.org/3/library/http.server.html
- Django supported releases: 5.2 LTS được liệt kê với extended support đến 04/2028: https://www.djangoproject.com/download/
- Django authentication/session/permissions: https://docs.djangoproject.com/en/5.2/topics/auth/
- Django deployment/security checks: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
- uv: nhóm dev không phải dependency runtime được công bố của project: https://docs.astral.sh/uv/concepts/projects/dependencies/
- SQLite: phù hợp ít writer; chỉ một writer cùng thời điểm, client/server phù hợp khi cần concurrency cao: https://www.sqlite.org/whentouse.html
- TikTok Direct Post intended use và yêu cầu review/UX, cập nhật 04/08/2026: https://developers.tiktok.com/docs/en/content-sharing-guidelines

Các lựa chọn kiến trúc, thứ tự triển khai, bộ test và metric là đề xuất của báo cáo; không phải xác nhận chúng đã tồn tại trong repo.

## 9. Tệp kiểm chứng đi kèm

`audit_probes.py`: 12 probe read-only dùng fake local; không thực hiện request ra nền tảng.  
`audit-results.json`: kết quả chạy và environment, kèm manifest SHA nguồn dùng trong lần kiểm chứng.  
`source-verification.json`: Git blob SHA kỳ vọng/thực tế của bốn tệp, tất cả khớp.

Chạy trên checkout đã được xem xét, trong môi trường có jsonschema và dependency của repo:

```bash
# POSIX, từ thư mục gốc Sales-Hunter
PYTHONPATH=src python /path/to/audit_probes.py --output audit-results.json
```

```powershell
# PowerShell, từ thư mục gốc Sales-Hunter
$env:PYTHONPATH = "src"
python C:\path\to\audit_probes.py --output audit-results.json
```

Script là công cụ quan sát rủi ro, không phải toàn bộ suite và không tự chuyển các kết quả thành CI gate. Sau khi sửa, cần chuyển từng tình huống sang regression test với kỳ vọng an toàn rõ. Probe không chứng minh behavior thật của provider.
