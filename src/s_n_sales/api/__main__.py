"""Chạy operator API local: python -m s_n_sales.api --port 8080"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from s_n_sales.api.app import make_server
from s_n_sales.api.store import OperatorStore
from s_n_sales.api.store_sqlite import SqliteOperatorStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sales-Hunter operator API & Web Dashboard (stdlib)"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument(
        "--db-path",
        default=os.environ.get("OPERATOR_DB_PATH", "var/operator.db"),
        help="Đường dẫn SQLite database file (mặc định var/operator.db)",
    )
    parser.add_argument(
        "--allow-unauthenticated-local",
        action="store_true",
        help="Chỉ dùng phát triển/kiểm thử trên loopback; không có xác thực",
    )
    parser.add_argument(
        "--in-memory",
        action="store_true",
        help="Sử dụng in-memory store thay cho SQLite",
    )
    args = parser.parse_args()
    auth_token = os.environ.get("OPERATOR_TOKEN")
    auth_actor = os.environ.get("OPERATOR_ACTOR", "operator")
    if bool(auth_token) == args.allow_unauthenticated_local:
        parser.error("Set OPERATOR_TOKEN or --allow-unauthenticated-local (choose one)")
    # Validate authentication/bind before opening the SQLite database.
    if args.host != "localhost":
        try:
            from ipaddress import ip_address

            if not ip_address(args.host).is_loopback:
                parser.error("--host must be loopback")
        except ValueError:
            parser.error("--host must be loopback")

    if args.in_memory:
        store = OperatorStore()
        store_desc = "in-memory"
    else:
        db_path = Path(args.db_path)
        store = SqliteOperatorStore(db_path=db_path)
        store_desc = f"sqlite ({db_path})"

    server = make_server(
        store,
        host=args.host,
        port=args.port,
        auth_token=auth_token,
        auth_actor=auth_actor,
        allow_unauthenticated_local=args.allow_unauthenticated_local,
    )
    print(f"Sales-Hunter Operator listening on http://{args.host}:{args.port}")
    print(f"  Store:     {store_desc}")
    print(f"  Health:    http://{args.host}:{args.port}/healthz")
    print(f"  Dashboard: http://{args.host}:{args.port}/dashboard/login")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("shutdown")
    finally:
        server.server_close()
        store.close()


if __name__ == "__main__":
    main()
