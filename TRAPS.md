# TRAPS.md — bẫy đã xảy ra trong S-N Sales

File này chỉ ghi sự cố **đã xảy ra thật trong repository này**, không sao chép lịch sử của Claude-Agents và không dùng như danh sách best practice chung.

## Sổ bẫy

Chưa có bẫy kỹ thuật sản phẩm: repository chưa có mã tích hợp nền tảng.

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
