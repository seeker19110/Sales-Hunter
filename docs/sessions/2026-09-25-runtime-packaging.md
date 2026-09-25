# SH-004 — runtime packaging

PR #36 được bắt đầu với test đỏ cho runtime dependency và 5 schema resource. Bản sửa khai báo `jsonschema[format-nongpl]` trong dependencies, chuyển loader sang `importlib.resources` và đóng gói bản sao byte-for-byte của năm schema v1. Job artifact đã có ở commit đỏ, kiểm một wheel trong runtime venv ngoài checkout.

Kiểm tại môi trường local: test đỏ xác nhận thiếu dependency/resources; `uv lock --check --offline`, `uv export --locked --offline --no-dev --no-emit-project`, `compileall` và `git diff --check` đã chạy sau sửa. Chưa cài được dependency từ PyPI tại container này; full suite, Ruff, Pyright và wheel smoke cần CI trên đúng HEAD. Không diễn giải kết quả local thành nghiệm thu hoàn chỉnh.

Nhánh này không sửa logic approval/publish, schema semantics, auth hoặc database. Chưa deploy và chưa gọi nền tảng thật. Bước tiếp: đối chiếu CI/PR #36, giải quyết lỗi nếu có rồi merge khi các cổng xanh; PR #38 cần human T4 review riêng.
