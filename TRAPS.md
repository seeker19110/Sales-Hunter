# TRAPS.md — bẫy đã xảy ra trong Sales-Hunter

File này chỉ ghi sự cố **đã xảy ra thật trong repository này**, không sao chép lịch sử của Claude-Agents và không dùng như danh sách best practice chung.

## Sổ bẫy

Chưa có bẫy kỹ thuật sản phẩm: repository chưa có mã tích hợp nền tảng.

## 2026-09-13 — PR dependabot kẹt ở cổng `metadata` vì không tự sửa được CHANGELOG (#7)

- Triệu chứng: job `metadata` (`pr-policy.yml`) báo đỏ "PR không đổi CHANGELOG.md" trên PR dependabot bump `astral-sh/setup-uv`; các job còn lại (`static`, `typecheck`, `unit`…) đều xanh.
- Nguyên nhân gốc: `pr-policy.yml` đòi mọi PR đổi `CHANGELOG.md` trừ khi gắn nhãn `no-changelog`; dependabot mở PR tự động, không tự sửa `CHANGELOG.md` và không tự gắn nhãn miễn trừ đó (chỉ có nhãn `dependencies`, `github_actions` mặc định).
- Bằng chứng đỏ/xanh: check `metadata` đỏ trước khi gắn nhãn; xanh ngay sau khi gắn `no-changelog` và chạy lại (không sửa code/CHANGELOG).
- Rà cả họ: mọi PR do bot mở (dependabot, renovate, github-actions) mà cổng đòi thứ bot không tự làm được (CHANGELOG, checklist PR template, review con người) đều có nguy cơ kẹt vô thời hạn, trông giống "PR chưa đạt chuẩn" nhưng thực ra không bao giờ tự xanh được — hỏi trước khi tin cổng đỏ trên PR bot là do code sai: "bot này có khả năng tự sửa cái cổng đòi không?".
- Lần sau: gắn nhãn `no-changelog` cho PR dependabot/tool tự động trước khi tìm nguyên nhân sâu hơn ở code; cân nhắc thêm bot vào danh sách miễn trừ tự động trong `pr-policy.yml` nếu việc gắn tay lặp lại nhiều lần.

## Cách thêm một mục

Một mục cần có:

- ngày và PR/commit;
- triệu chứng quan sát được;
- nguyên nhân gốc đã tái hiện;
- test hoặc lệnh chứng minh lỗi trước/sau;
- câu hỏi rà cả họ lỗi;
- cách tránh lần sau.

Mẫu:

```markdown
## YYYY-MM-DD — <tên khuôn lỗi> (#PR)

- Triệu chứng:
- Nguyên nhân gốc:
- Bằng chứng đỏ/xanh:
- Rà cả họ:
- Lần sau:
```

Rủi ro dự đoán (giá cũ, coupon theo tài khoản, link redirect, quota, thay đổi API) thuộc threat model/ADR/test plan; chỉ chuyển vào đây sau khi nó thực sự gây sự cố và đã tìm được nguyên nhân.
