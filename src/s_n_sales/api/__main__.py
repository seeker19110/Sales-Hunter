"""Chạy operator API local: PYTHONPATH=src python -m s_n_sales.api --port 8080"""

from __future__ import annotations

import argparse

from s_n_sales.api.app import make_server
from s_n_sales.api.store import OperatorStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sales-Hunter operator API (stdlib, staging skeleton)"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    store = OperatorStore()
    server = make_server(store, host=args.host, port=args.port)
    print(f"listening on http://{args.host}:{args.port}  GET /healthz")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("shutdown")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
