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
        "--token",
        default=os.environ.get("OPERATOR_TOKEN"),
        help="Token xác thực cho Operator API và Dashboard",
    )
    parser.add_argument(
        "--in-memory",
        action="store_true",
        help="Sử dụng in-memory store thay cho SQLite",
    )
    args = parser.parse_args()

    if args.in_memory:
        store = OperatorStore()
        store_desc = "in-memory"
    else:
        db_path = Path(args.db_path)
        store = SqliteOperatorStore(db_path=db_path)
        store_desc = f"sqlite ({db_path})"

    server = make_server(store, host=args.host, port=args.port, auth_token=args.token)
    print(f"Sales-Hunter Operator listening on http://{args.host}:{args.port}")
    print(f"  Store:     {store_desc}")
    print(f"  Health:    http://{args.host}:{args.port}/healthz")
    auth_suffix = f"?token={args.token}" if args.token else ""
    print(f"  Dashboard: http://{args.host}:{args.port}/dashboard{auth_suffix}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("shutdown")
    finally:
        server.server_close()
        store.close()


if __name__ == "__main__":
    main()
