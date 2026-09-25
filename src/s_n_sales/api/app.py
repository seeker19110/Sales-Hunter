"""Minimal HTTP API and Operator Web Dashboard (stdlib) for staging operator flows."""

from __future__ import annotations

import hmac
import html
import ipaddress
import json
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Protocol
from urllib.parse import parse_qs, quote, urlparse

from s_n_sales.api.read_model import CandidatePriceView
from s_n_sales.pipeline.approval import ApprovalError


class OperatorStoreProtocol(Protocol):
    def upsert_candidate(self, candidate: dict[str, Any]) -> dict[str, Any]: ...
    def list_candidates(self, status: str | None = None) -> list[dict[str, Any]]: ...
    def get_candidate(self, publication_id: str) -> dict[str, Any] | None: ...
    def approve(
        self,
        publication_id: str,
        *,
        decided_by: str,
        reason: str | None = None,
    ) -> dict[str, Any]: ...
    def reject(
        self,
        publication_id: str,
        *,
        decided_by: str,
        reason: str | None = None,
    ) -> dict[str, Any]: ...
    def get_approval(self, publication_id: str) -> dict[str, Any] | None: ...


def _json_response(handler: BaseHTTPRequestHandler, status: int, body: Any) -> None:
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def _html_response(handler: BaseHTTPRequestHandler, status: int, body: str) -> None:
    payload = body.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def _redirect_response(
    handler: BaseHTTPRequestHandler, location: str, cookie: str | None = None
) -> None:
    handler.send_response(303)
    handler.send_header("Location", location)
    if cookie:
        handler.send_header("Set-Cookie", cookie)
    handler.send_header("Content-Length", "0")
    handler.end_headers()


_CSS_COMMON = """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f9fafb; margin: 0; padding: 24px; color: #111827;
}
.container {
    max-width: 960px; margin: 0 auto; background: white;
    border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 24px;
}
h1 { margin-top: 0; font-size: 22px; color: #1f2937; }
.tabs { margin-bottom: 16px; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; }
.tab {
    margin-right: 12px; text-decoration: none; color: #4b5563;
    font-weight: 500; padding: 6px 12px; border-radius: 6px;
}
.tab.active { background: #eff6ff; color: #2563eb; font-weight: 600; }
table { width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }
th { background: #f9fafb; padding: 10px; border-bottom: 2px solid #e5e7eb; color: #4b5563; }
td { padding: 10px; border-bottom: 1px solid #e5e7eb; }
.back-link {
    display: inline-block; margin-bottom: 16px; color: #2563eb;
    text-decoration: none; font-size: 14px; font-weight: 500;
}
.field { margin-bottom: 16px; }
.label {
    font-size: 12px; font-weight: 600; text-transform: uppercase;
    color: #6b7280; margin-bottom: 4px;
}
.value { font-size: 15px; color: #111827; }
.content-box {
    background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px;
    padding: 12px; font-family: monospace; font-size: 14px; white-space: pre-wrap;
}
.actions {
    margin-top: 24px; border-top: 1px solid #e5e7eb;
    padding-top: 20px; display: flex; gap: 16px;
}
form {
    flex: 1; background: #f9fafb; padding: 16px;
    border-radius: 6px; border: 1px solid #e5e7eb;
}
input[type="text"] {
    width: 100%; box-sizing: border-box; padding: 8px;
    margin-top: 4px; margin-bottom: 12px; border: 1px solid #d1d5db; border-radius: 4px;
}
.btn-approve {
    background: #16a34a; color: white; padding: 10px 16px;
    border: none; border-radius: 4px; font-weight: 600; cursor: pointer; width: 100%;
}
.btn-reject {
    background: #dc2626; color: white; padding: 10px 16px;
    border: none; border-radius: 4px; font-weight: 600; cursor: pointer; width: 100%;
}
.table-scroll { overflow-x: auto; }
.value, .content-box { overflow-wrap: anywhere; }
.tabs { display: flex; flex-wrap: wrap; gap: 8px; }
:focus-visible { outline: 3px solid #2563eb; outline-offset: 3px; }
@media (max-width: 600px) {
    body { padding: 8px; }
    .container { padding: 12px; }
    .actions { flex-direction: column; }
    .tab { margin-right: 0; }
}
"""


def _render_dashboard_list(
    candidates: list[dict[str, Any]],
    current_status: str | None,
    csrf_token: str,
) -> str:
    rows_html: list[str] = []
    for c in candidates:
        pub_id = html.escape(str(c.get("publication_id", "")))
        view = CandidatePriceView.from_candidate(c)
        platform = html.escape(view.platform)
        content = html.escape(str(c.get("content", "")))[:60]
        approval = c.get("approval", {})
        status = html.escape(str(approval.get("status", "pending")))

        color = (
            "#eab308" if status == "pending" else "#22c55e" if status == "approved" else "#ef4444"
        )
        detail_url = f"/dashboard/candidates/{quote(str(c.get('publication_id', '')), safe='')}"

        badge = (
            f'<span style="background: {color}; color: white; '
            f'padding: 3px 8px; border-radius: 9999px; font-size: 12px; font-weight: bold;">'
            f"{status}</span>"
        )
        link = (
            f'<a href="{detail_url}" '
            f'style="font-weight: 600; color: #2563eb; text-decoration: none;">{pub_id}</a>'
        )
        prices = (
            f"<strong>{view.sale}</strong> / "
            f'<span style="text-decoration: line-through; color: #6b7280;">{view.listed}</span>'
        )
        btn = (
            f'<a href="{detail_url}" style="background: #f3f4f6; padding: 4px 10px; '
            f'border-radius: 4px; text-decoration: none; color: #374151; font-size: 13px;">'
            f"Chi tiết</a>"
        )

        rows_html.append(f"""
        <tr data-publication-id="{pub_id}">
            <td>{link}</td>
            <td>{platform}</td>
            <td>{content}</td>
            <td>{prices}</td>
            <td style="font-weight: bold; color: #dc2626;">{view.discount}</td>
            <td>{badge}</td>
            <td>{btn}</td>
        </tr>
        """)

    empty_row = (
        '<tr><td colspan="7" style="padding: 20px; text-align: center; color: #6b7280;">'
        "Không có bản nháp nào phù hợp.</td></tr>"
    )
    rows_str = "".join(rows_html) or empty_row
    t_all = "active" if not current_status else ""
    t_pend = "active" if current_status == "pending" else ""
    t_appr = "active" if current_status == "approved" else ""
    t_rej = "active" if current_status == "rejected" else ""

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Sales-Hunter Operator Dashboard</title>
    <style>{_CSS_COMMON}</style>
</head>
<body>
    <div class="container">
        <h1>Sales-Hunter Operator Dashboard</h1>
        <div class="tabs">
            <a href="/dashboard" class="tab {t_all}">Tất cả</a>
            <a href="/dashboard?status=pending" class="tab {t_pend}">Chờ duyệt</a>
            <a href="/dashboard?status=approved" class="tab {t_appr}">Đã duyệt</a>
            <a href="/dashboard?status=rejected" class="tab {t_rej}">Từ chối</a>
        </div>
        <form method="POST" action="/dashboard/logout" style="max-width: 10em;">
            <input type="hidden" name="csrf_token" value="{html.escape(csrf_token)}">
            <button type="submit">Đăng xuất</button>
        </form>
        <div class="table-scroll" role="region" aria-label="Danh sách ưu đãi" tabindex="0">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nền tảng</th>
                    <th>Nội dung</th>
                    <th>Giá sale / Giá gốc</th>
                    <th>Giảm</th>
                    <th>Trạng thái</th>
                    <th>Thao tác</th>
                </tr>
            </thead>
            <tbody>
                {rows_str}
            </tbody>
        </table>
        </div>
    </div>
</body>
</html>"""


def _render_dashboard_detail(candidate: dict[str, Any], csrf_token: str) -> str:
    pub_id = html.escape(str(candidate.get("publication_id", "")))
    view = CandidatePriceView.from_candidate(candidate)
    platform = html.escape(view.platform)
    channel = html.escape(str(candidate.get("target_channel", "")))
    draft_sha256 = html.escape(str(candidate.get("draft_sha256", "")))
    content = html.escape(str(candidate.get("content", "")))
    affiliate_url = html.escape(str(candidate.get("affiliate_url", "")))
    affiliate_disclosure = html.escape(str(candidate.get("affiliate_disclosure", "")))

    approval = candidate.get("approval", {})
    status = html.escape(str(approval.get("status", "pending")))
    decided_by = html.escape(str(approval.get("decided_by", "")))
    reason = html.escape(str(approval.get("reason", "")))

    csrf_input = f'<input type="hidden" name="csrf_token" value="{html.escape(csrf_token)}">'

    approve_action = f"/dashboard/candidates/{pub_id}/approve"
    reject_action = f"/dashboard/candidates/{pub_id}/reject"

    history_box = ""
    if decided_by:
        history_box = f"""
        <div class="field" style="background: #f3f4f6; padding: 12px; border-radius: 6px;">
            <div class="label">Lịch sử duyệt</div>
            <div class="value">Người duyệt: <strong>{decided_by}</strong> | Lý do: {reason}</div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Duyệt Deal: {pub_id} — Sales-Hunter</title>
    <style>{_CSS_COMMON}</style>
</head>
<body>
    <div class="container">
        <a href="/dashboard" class="back-link">&larr; Quay lại danh sách</a>
        <h2>Chi tiết bản nháp ưu đãi: {pub_id}</h2>

        <div style="display: flex; gap: 20px;">
            <div class="field" style="flex: 1;">
                <div class="label">Nền tảng</div>
                <div class="value">{platform}</div>
            </div>
            <div class="field" style="flex: 1;">
                <div class="label">Kênh phân phối</div>
                <div class="value">{channel}</div>
            </div>
            <div class="field" style="flex: 1;">
                <div class="label">Trạng thái hiện tại</div>
                <div class="value" style="font-weight: bold;">{status}</div>
            </div>
        </div>

        <div class="field">
            <div class="label">Claim Snapshot Giá</div>
            <div class="value">
                Giá khuyến mãi: <strong style="color: #dc2626; font-size: 18px;">
                    {view.sale}
                </strong> &nbsp;|&nbsp;
                Giá gốc: <span style="text-decoration: line-through; color: #6b7280;">
                    {view.listed}
                </span> &nbsp;|&nbsp;
                Giảm: <strong>{view.discount}</strong>
            </div>
        </div>

        <div class="field">
            <div class="label">Nội dung bài đăng (Content Draft)</div>
            <div class="content-box">{content}</div>
        </div>

        <div class="field">
            <div class="label">Link Affiliate</div>
            <div class="value">
                <a href="{affiliate_url}" target="_blank" rel="noopener noreferrer"
                   style="color: #2563eb;">{affiliate_url}</a>
            </div>
        </div>

        <div class="field">
            <div class="label">Công bố Affiliate (Disclosure bắt buộc)</div>
            <div class="value" style="font-style: italic; color: #4b5563;">
                {affiliate_disclosure}
            </div>
        </div>

        <div class="field">
            <div class="label">Canonical Content Hash (ADR-0005 draft_sha256)</div>
            <div class="value" style="font-family: monospace; font-size: 13px; color: #4b5563;">
                {draft_sha256}
            </div>
        </div>

        {history_box}

        <div class="actions">
            <form method="POST" action="{approve_action}">
                {csrf_input}
                <div style="font-weight: 600; color: #15803d; margin-bottom: 8px;">Duyệt Deal</div>
                <label style="font-size: 13px;">Lý do / Ghi chú:</label>
                <input type="text" name="reason" placeholder="Đã kiểm tra deal hợp lệ">
                <button type="submit" class="btn-approve">Approve Deal</button>
            </form>

            <form method="POST" action="{reject_action}">
                {csrf_input}
                <div style="font-weight: 600; color: #b91c1c; margin-bottom: 8px;">Từ chối</div>
                <label style="font-size: 13px;">Lý do từ chối:</label>
                <input type="text" name="reason" placeholder="Giá sale không thật hoặc link hỏng">
                <button type="submit" class="btn-reject">Reject Deal</button>
            </form>
        </div>
    </div>
</body>
</html>"""


def create_handler_class(
    store: Any,
    auth_token: str | None = None,
    auth_actor: str = "operator",
    allow_unauthenticated_local: bool = False,
) -> type[BaseHTTPRequestHandler]:
    sessions: dict[str, tuple[float, str]] = {}
    sessions_lock = threading.Lock()
    session_duration = 8 * 60 * 60

    class OperatorHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return  # quiet in tests

        def _is_authorized(self) -> bool:
            if allow_unauthenticated_local:
                return True
            auth_header = self.headers.get("Authorization", "")
            return auth_header.startswith("Bearer ") and hmac.compare_digest(
                auth_header[len("Bearer ") :].encode("utf-8"), (auth_token or "").encode("utf-8")
            )

        def _session(self) -> tuple[str, str] | None:
            if allow_unauthenticated_local:
                return ("", "")
            for part in self.headers.get("Cookie", "").split(";"):
                key, sep, value = part.strip().partition("=")
                if sep and key == "operator_session":
                    with sessions_lock:
                        item = sessions.get(value)
                        if item and item[0] > time.monotonic():
                            return (value, item[1])
                        sessions.pop(value, None)
                    break
            return None

        def _dashboard_unauthorized(self) -> None:
            _html_response(
                self, 401, '<h1>401 Unauthorized</h1><a href="/dashboard/login">Đăng nhập</a>'
            )

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            query_params = parse_qs(parsed.query)

            if path == "/healthz":
                _json_response(self, 200, {"status": "ok", "service": "sales-hunter-operator"})
                return

            if path == "/dashboard/login":
                _html_response(
                    self,
                    200,
                    '<!doctype html><html lang="vi"><meta charset="utf-8">'
                    '<h1>Đăng nhập operator</h1><form method="POST" action="/dashboard/login">'
                    '<label>Token <input type="password" name="token" required></label>'
                    '<button type="submit">Đăng nhập</button></form></html>',
                )
                return

            if path.startswith("/dashboard"):
                session = self._session()
                if session is None:
                    self._dashboard_unauthorized()
                    return
            elif not self._is_authorized():
                _json_response(self, 401, {"error": "unauthorized"})
                return

            # Dashboard Web UI routes
            if path == "/dashboard":
                status_filter = query_params.get("status", [None])[0]
                candidates = store.list_candidates(status=status_filter)
                html_body = _render_dashboard_list(candidates, status_filter, session[1])
                _html_response(self, 200, html_body)
                return

            if path.startswith("/dashboard/candidates/"):
                pub_id = path[len("/dashboard/candidates/") :]
                candidate = store.get_candidate(pub_id)
                if candidate is None:
                    _html_response(self, 404, "<h1>404 Not Found</h1><p>Không tìm thấy deal.</p>")
                    return
                html_body = _render_dashboard_detail(candidate, session[1])
                _html_response(self, 200, html_body)
                return

            # REST API routes
            if path == "/api/v1/candidates":
                _json_response(self, 200, {"items": store.list_candidates()})
                return

            if path.startswith("/api/v1/candidates/"):
                pub_id = path[len("/api/v1/candidates/") :]
                if "/approval" in pub_id:
                    base_id, _, _ = pub_id.partition("/approval")
                    approval = store.get_approval(base_id)
                    if approval is None:
                        _json_response(self, 404, {"error": "approval_not_found"})
                        return
                    _json_response(self, 200, approval)
                    return
                candidate = store.get_candidate(pub_id)
                if candidate is None:
                    _json_response(self, 404, {"error": "candidate_not_found"})
                    return
                _json_response(self, 200, candidate)
                return

            if path == "/api/v1/receipts":
                receipts = store.list_receipts() if hasattr(store, "list_receipts") else []
                _json_response(self, 200, {"items": receipts})
                return

            _json_response(self, 404, {"error": "not_found"})

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            content_type = self.headers.get("Content-Type", "")
            is_dashboard = path.startswith("/dashboard")
            is_login = path == "/dashboard/login"
            if is_dashboard and not is_login and self._session() is None:
                self._dashboard_unauthorized()
                return
            if not is_dashboard and not self._is_authorized():
                _json_response(self, 401, {"error": "unauthorized"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = -1
            if length < 0 or length > 1024 * 1024:
                if is_dashboard:
                    _html_response(self, 413, "<h1>413 Payload Too Large</h1>")
                else:
                    _json_response(self, 413, {"error": "payload_too_large"})
                return
            raw = self.rfile.read(length) if length else b""

            if is_dashboard:
                if "application/x-www-form-urlencoded" not in content_type:
                    _html_response(self, 415, "<h1>415 Unsupported Media Type</h1>")
                    return
                form = parse_qs(raw.decode("utf-8"))
                if is_login:
                    supplied = form.get("token", [""])[0]
                    if not auth_token or not hmac.compare_digest(
                        supplied.encode("utf-8"), auth_token.encode("utf-8")
                    ):
                        self._dashboard_unauthorized()
                        return
                    session_id, csrf_token = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
                    with sessions_lock:
                        now = time.monotonic()
                        for key, (expiry, _) in list(sessions.items()):
                            if expiry <= now:
                                del sessions[key]
                        if len(sessions) >= 256:
                            _html_response(self, 429, "<h1>429 Too Many Sessions</h1>")
                            return
                        sessions[session_id] = (now + session_duration, csrf_token)
                    _redirect_response(
                        self,
                        "/dashboard",
                        f"operator_session={session_id}; Max-Age={session_duration}; "
                        "HttpOnly; SameSite=Strict; Path=/dashboard",
                    )
                    return

                session = self._session()
                if session is None:
                    self._dashboard_unauthorized()
                    return
                if not allow_unauthenticated_local and not hmac.compare_digest(
                    form.get("csrf_token", [""])[0], session[1]
                ):
                    _html_response(self, 403, "<h1>403 Forbidden</h1>")
                    return
                if path == "/dashboard/logout":
                    with sessions_lock:
                        sessions.pop(session[0], None)
                    _redirect_response(
                        self,
                        "/dashboard/login",
                        "operator_session=; Max-Age=0; HttpOnly; SameSite=Strict; Path=/dashboard",
                    )
                    return

                if path.startswith("/dashboard/candidates/") and path.endswith("/approve"):
                    pub_id = path[len("/dashboard/candidates/") : -len("/approve")]
                    reason = form.get("reason", [""])[0].strip() or None
                    try:
                        store.approve(pub_id, decided_by=auth_actor, reason=reason)
                    except KeyError:
                        _html_response(self, 404, "<h1>404 Not Found</h1>")
                        return
                    except ApprovalError as exc:
                        err_msg = f"<h1>400 Error</h1><p>{html.escape(str(exc))}</p>"
                        _html_response(self, 400, err_msg)
                        return
                    _redirect_response(self, f"/dashboard/candidates/{quote(pub_id, safe='')}")
                    return

                if path.startswith("/dashboard/candidates/") and path.endswith("/reject"):
                    pub_id = path[len("/dashboard/candidates/") : -len("/reject")]
                    reason = form.get("reason", [""])[0].strip() or None
                    try:
                        store.reject(pub_id, decided_by=auth_actor, reason=reason)
                    except KeyError:
                        _html_response(self, 404, "<h1>404 Not Found</h1>")
                        return
                    except ApprovalError as exc:
                        err_msg = f"<h1>400 Error</h1><p>{html.escape(str(exc))}</p>"
                        _html_response(self, 400, err_msg)
                        return
                    _redirect_response(self, f"/dashboard/candidates/{quote(pub_id, safe='')}")
                    return

                _html_response(self, 404, "<h1>404 Not Found</h1>")
                return

            # JSON REST API POST
            try:
                body = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                _json_response(self, 400, {"error": "invalid_json"})
                return
            if not isinstance(body, dict):
                _json_response(self, 400, {"error": "body_must_be_object"})
                return

            if path == "/api/v1/candidates":
                try:
                    saved = store.upsert_candidate(body)
                except ValueError as exc:
                    _json_response(self, 400, {"error": str(exc)})
                    return
                _json_response(self, 201, saved)
                return

            if path.endswith("/approve") and path.startswith("/api/v1/candidates/"):
                pub_id = path[len("/api/v1/candidates/") : -len("/approve")]
                try:
                    record = store.approve(
                        pub_id,
                        decided_by=auth_actor,
                        reason=body.get("reason") if isinstance(body.get("reason"), str) else None,
                    )
                except KeyError:
                    _json_response(self, 404, {"error": "candidate_not_found"})
                    return
                except ApprovalError as exc:
                    _json_response(self, 400, {"error": str(exc)})
                    return
                _json_response(self, 200, record)
                return

            if path.endswith("/reject") and path.startswith("/api/v1/candidates/"):
                pub_id = path[len("/api/v1/candidates/") : -len("/reject")]
                try:
                    record = store.reject(
                        pub_id,
                        decided_by=auth_actor,
                        reason=body.get("reason") if isinstance(body.get("reason"), str) else None,
                    )
                except KeyError:
                    _json_response(self, 404, {"error": "candidate_not_found"})
                    return
                except ApprovalError as exc:
                    _json_response(self, 400, {"error": str(exc)})
                    return
                _json_response(self, 200, record)
                return

            _json_response(self, 404, {"error": "not_found"})

    return OperatorHandler


def make_server(
    store: Any,
    host: str = "127.0.0.1",
    port: int = 0,
    auth_token: str | None = None,
    auth_actor: str = "operator",
    allow_unauthenticated_local: bool = False,
) -> ThreadingHTTPServer:
    try:
        local_bind = host == "localhost" or ipaddress.ip_address(host).is_loopback
    except ValueError as exc:
        raise ValueError("Operator server must bind to loopback") from exc
    if not local_bind:
        raise ValueError("Operator server must bind to loopback")
    if not auth_token and not allow_unauthenticated_local:
        raise ValueError("OPERATOR_TOKEN is required; local anonymous mode must be explicit")
    if auth_token and allow_unauthenticated_local:
        raise ValueError("Cannot combine auth_token with anonymous local mode")
    if not auth_actor.strip():
        raise ValueError("auth_actor must identify a configured reviewer")
    handler = create_handler_class(
        store,
        auth_token=auth_token,
        auth_actor=auth_actor,
        allow_unauthenticated_local=allow_unauthenticated_local,
    )
    return ThreadingHTTPServer((host, port), handler)
