"""Read-only, separately authenticated DHCB pilot. No publishing or DB migrations."""

from __future__ import annotations

import base64
import binascii
import hmac
import html
import json
import os
import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from s_n_sales.api.contracts import candidate_from_json, validate_candidate
from s_n_sales.api.read_model import CandidatePriceView
from s_n_sales.pipeline.publication import assert_candidate_integrity

PILOT_ORIGINS = frozenset(
    {"https://sales.donghanhcungban.org", "https://sales-staging.donghanhcungban.org"}
)
HUB_URL = "https://donghanhcungban.org"
MAX_PAGE_SIZE = 50


class PlatformPilot:
    """One operator, read-only SQLite view. Reverse proxy must enforce TLS and Access."""

    def __init__(self, *, origin: str, db_path: Path, actor: str, token: str) -> None:
        if origin not in PILOT_ORIGINS:
            raise ValueError("pilot_origin_not_allowed")
        if not actor.strip() or ":" in actor or any(ord(c) < 32 for c in actor):
            raise ValueError("invalid_operator_actor")
        if len(token) < 32 or len(token) > 512 or token != token.strip():
            raise ValueError("operator_token_must_be_32_to_512_characters")
        if not db_path.is_absolute() or not db_path.is_file():
            raise ValueError("existing_absolute_pilot_database_required")
        self.origin = origin
        self.host = urlsplit(origin).netloc
        self.db_uri = db_path.resolve().as_uri() + "?mode=ro"
        self.credentials = f"{actor}:{token}".encode()
        # Fail closed on an uninitialized database. Never create schema or run migrations here.
        self._read_page(0)

    def _read_page(self, page: int) -> list[dict[str, Any]]:
        connection = sqlite3.connect(self.db_uri, uri=True, timeout=2)
        try:
            connection.execute("PRAGMA query_only = ON")
            rows = connection.execute(
                "SELECT candidate_json FROM candidates "
                "ORDER BY updated_at DESC, publication_id LIMIT ? OFFSET ?",
                (MAX_PAGE_SIZE + 1, page * MAX_PAGE_SIZE),
            ).fetchall()
            candidates = [candidate_from_json(row[0]) for row in rows]
            for candidate in candidates:
                validate_candidate(candidate)
                assert_candidate_integrity(candidate)
            return candidates
        finally:
            connection.close()

    def _authorized(self, value: str) -> bool:
        if not value.startswith("Basic ") or len(value) > 2048:
            return False
        try:
            supplied = base64.b64decode(value[6:], validate=True)
        except (binascii.Error, ValueError):
            return False
        return hmac.compare_digest(supplied, self.credentials)

    @staticmethod
    def _response(
        start_response: Callable[..., Any],
        status: str,
        text: str,
        *,
        json_body: bool = False,
        challenge: bool = False,
    ) -> list[bytes]:
        payload = text.encode("utf-8")
        content_type = "application/json" if json_body else "text/html"
        headers = [
            ("Content-Type", f"{content_type}; charset=utf-8"),
            ("Content-Length", str(len(payload))),
            ("Cache-Control", "no-store"),
            ("Referrer-Policy", "no-referrer"),
            ("X-Content-Type-Options", "nosniff"),
            ("X-Robots-Tag", "noindex, nofollow"),
            (
                "Content-Security-Policy",
                "default-src 'none'; style-src 'unsafe-inline'; "
                "frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
            ),
            ("Permissions-Policy", "camera=(), microphone=(), geolocation=()"),
        ]
        if challenge:
            headers.append(
                ("WWW-Authenticate", 'Basic realm="Sales-Hunter pilot", charset="UTF-8"')
            )
        if status.startswith("405"):
            headers.append(("Allow", "GET"))
        start_response(status, headers)
        return [payload]

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]) -> list[bytes]:
        respond = self._response
        if environ.get("HTTP_HOST") != self.host:
            return respond(start_response, "400 Bad Request", "Invalid host")
        if environ.get("REQUEST_METHOD") != "GET":
            return respond(start_response, "405 Method Not Allowed", "Read-only pilot")
        path = environ.get("PATH_INFO", "/")
        if path == "/healthz" and not environ.get("QUERY_STRING"):
            try:
                self._read_page(0)
            except (sqlite3.Error, ValueError, KeyError, TypeError, AttributeError):
                return respond(
                    start_response,
                    "503 Service Unavailable",
                    '{"status":"unavailable"}',
                    json_body=True,
                )
            return respond(
                start_response,
                "200 OK",
                json.dumps(
                    {
                        "status": "ok",
                        "service": "sales-hunter-platform-pilot",
                        "mode": "read_only",
                        "live_publish": False,
                    }
                ),
                json_body=True,
            )
        if not self._authorized(environ.get("HTTP_AUTHORIZATION", "")):
            return respond(
                start_response,
                "401 Unauthorized",
                "Operator authentication required",
                challenge=True,
            )
        if path not in {"/", "/dashboard"}:
            return respond(start_response, "404 Not Found", "Not found")
        try:
            params = parse_qs(
                environ.get("QUERY_STRING", ""),
                keep_blank_values=True,
                strict_parsing=True,
                max_num_fields=1,
            )
            raw_page = params.get("page", ["0"])
            if set(params) - {"page"} or len(raw_page) != 1 or not raw_page[0].isascii():
                raise ValueError("invalid_query")
            page = int(raw_page[0])
            if not 0 <= page <= 10000:
                raise ValueError("invalid_page")
        except ValueError:
            return respond(start_response, "400 Bad Request", "Invalid page")
        try:
            candidates = self._read_page(page)
            body = self._render(candidates, page)
        except (sqlite3.Error, ValueError, KeyError, TypeError, AttributeError):
            return respond(start_response, "503 Service Unavailable", "Pilot data unavailable")
        return respond(start_response, "200 OK", body)

    @staticmethod
    def _render(candidates: list[dict[str, Any]], page: int) -> str:
        rows: list[str] = []
        for candidate in candidates[:MAX_PAGE_SIZE]:
            price = CandidatePriceView.from_candidate(candidate)
            fields = [
                candidate["publication_id"],
                price.platform,
                price.sale,
                candidate.get("claim_snapshot", {}).get("observed_at", ""),
                candidate.get("approval", {}).get("status", "pending"),
                str(candidate.get("content", ""))[:500],
            ]
            cells = "".join(f"<td>{html.escape(str(value))}</td>" for value in fields)
            rows.append(f"<tr>{cells}</tr>")
        if not rows:
            rows.append('<tr><td colspan="6">Chưa có bản nháp trong trang này.</td></tr>')
        links = []
        if page:
            links.append(f'<a href="?page={page - 1}">Trang trước</a>')
        if len(candidates) > MAX_PAGE_SIZE:
            links.append(f'<a href="?page={page + 1}">Trang sau</a>')
        return f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sales-Hunter | Đồng Hành Cùng Bạn</title>
<style>body{{font-family:system-ui,sans-serif;max-width:1100px;margin:auto;padding:24px}}
a{{color:#155e75}}td,th{{padding:12px;text-align:left;border-bottom:1px solid #ddd}}
table{{border-collapse:collapse;width:100%}}td{{overflow-wrap:anywhere;max-width:32rem}}
.notice{{background:#f1f5f9;padding:16px}}.scroll{{overflow:auto}}nav a{{margin-right:24px}}
:focus-visible{{outline:3px solid #155e75;outline-offset:3px}}</style></head>
<body><header><a href="{HUB_URL}" rel="noreferrer">← Đồng Hành Cùng Bạn</a>
<h1>Sales-Hunter</h1><p>Săn ưu đãi và quản lý nội dung affiliate.</p></header>
<p class="notice"><strong>Thử nghiệm riêng — chỉ đọc.</strong> Không có quyền duyệt,
nhập dữ liệu hoặc đăng bài qua trang này. Trạng thái duyệt bản nháp không phải xác nhận
đã đăng. Nội dung dưới đây chỉ là trích đoạn tối đa 500 ký tự, không phải payload để đăng.
Giá và điều kiện có thể đã thay đổi; đây là ảnh chụp dữ liệu.</p>
<main><h2>Bản nháp từ cơ sở dữ liệu Sales riêng</h2>
<div class="scroll" role="region" aria-label="Danh sách bản nháp" tabindex="0">
<table><thead><tr><th>ID</th><th>Nền tảng</th><th>Giá đã ghi nhận</th>
<th>Thời điểm quan sát</th><th>Duyệt bản nháp</th><th>Trích đoạn nội dung</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
<nav aria-label="Phân trang">{" ".join(links)}</nav></main>
<footer><p>Không chia sẻ dữ liệu, cookie đăng nhập hay quyền thanh toán của Learning.</p></footer>
</body></html>"""


def create_app() -> PlatformPilot:
    """Gunicorn factory; mandatory, separate operator credentials; no permissive defaults."""
    return PlatformPilot(
        origin=os.environ["SALES_PUBLIC_ORIGIN"],
        db_path=Path(os.environ["SALES_PILOT_DB_PATH"]),
        actor=os.environ["SALES_OPERATOR_ACTOR"],
        token=os.environ["SALES_OPERATOR_TOKEN"],
    )
