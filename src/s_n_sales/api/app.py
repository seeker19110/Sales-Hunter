"""Minimal HTTP API (stdlib) for staging operator flows."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from s_n_sales.api.store import OperatorStore
from s_n_sales.pipeline.approval import ApprovalError


def _json_response(handler: BaseHTTPRequestHandler, status: int, body: Any) -> None:
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def create_handler_class(store: OperatorStore) -> type[BaseHTTPRequestHandler]:
    class OperatorHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return  # quiet in tests

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path.rstrip("/") or "/"
            if path == "/healthz":
                _json_response(self, 200, {"status": "ok", "service": "s-n-sales-operator"})
                return
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
            _json_response(self, 404, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path.rstrip("/") or "/"
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b"{}"
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
                decided_by = body.get("decided_by")
                if not isinstance(decided_by, str) or not decided_by.strip():
                    _json_response(self, 400, {"error": "decided_by_required"})
                    return
                try:
                    record = store.approve(
                        pub_id,
                        decided_by=decided_by,
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
                decided_by = body.get("decided_by")
                if not isinstance(decided_by, str) or not decided_by.strip():
                    _json_response(self, 400, {"error": "decided_by_required"})
                    return
                try:
                    record = store.reject(
                        pub_id,
                        decided_by=decided_by,
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
    store: OperatorStore,
    host: str = "127.0.0.1",
    port: int = 0,
) -> ThreadingHTTPServer:
    handler = create_handler_class(store)
    return ThreadingHTTPServer((host, port), handler)
