"""SH-010 browser acceptance: real builder -> SQLite -> HTTP -> headless Chrome.

Uses no browser-library dependency. Missing Chrome is a failure, never a skip.
Fixtures are synthetic; this proves display, not production identity or publishing.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
from pathlib import Path
from tempfile import TemporaryDirectory

from s_n_sales.api.app import make_server
from s_n_sales.api.store_sqlite import SqliteOperatorStore
from s_n_sales.pipeline.publication import build_publication_candidate

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    chrome = os.environ.get("CHROME_BIN") or next(
        (
            path
            for name in ("google-chrome", "chromium", "chromium-browser")
            if (path := shutil.which(name))
        ),
        None,
    )
    if not chrome:
        raise RuntimeError("Chrome/Chromium is required for browser acceptance")
    version = subprocess.run(
        [chrome, "--version"], check=True, capture_output=True, text=True, timeout=10
    )
    print(version.stdout.strip())
    cases = (
        (80000, 100000, "80.000 VND", "100.000 VND", "20%"),
        (80000, None, "80.000 VND", "Chưa xác minh", "Chưa xác minh"),
        (0, 100000, "0 VND", "100.000 VND", "100%"),
        (
            9007199254740993,
            10000000000000000,
            "9.007.199.254.740.993 VND",
            "10.000.000.000.000.000 VND",
            "9,93%",
        ),
    )
    with TemporaryDirectory(prefix="sales-hunter-browser-") as directory:
        store = SqliteOperatorStore(Path(directory) / "operator.db")
        server = make_server(store, allow_unauthenticated_local=True)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        browser_cases = []
        try:
            for index, (sale, listed, sale_label, list_label, discount) in enumerate(cases):
                observation = json.loads(
                    (ROOT / "schemas/examples/valid/offer-observation.v1.json").read_text(
                        encoding="utf-8"
                    )
                )
                observation.update(sale_price_minor=sale, list_price_minor=listed)
                candidate = build_publication_candidate(
                    observation,
                    {},
                    content="Minh họa <script>document.body.innerHTML='XSS_EXECUTED'</script>",
                    affiliate_url="https://example.com/affiliate",
                    target_channel="manual_export",
                    publication_id=f"browser-case-{index}",
                )
                store.upsert_candidate(candidate)
                for route in ("/dashboard", f"/dashboard/candidates/browser-case-{index}"):
                    expected = [sale_label, list_label, discount, "Shopee"]
                    if route != "/dashboard":
                        expected.extend(["#affiliate", "https://example.com/affiliate"])
                    browser_cases.append(
                        {
                            "url": f"http://127.0.0.1:{server.server_address[1]}{route}",
                            "expected": expected,
                            "row_id": f"browser-case-{index}" if route == "/dashboard" else None,
                        }
                    )
            cases_path = Path(directory) / "cases.json"
            cases_path.write_text(json.dumps(browser_cases), encoding="utf-8")
            subprocess.run(
                [
                    "node",
                    str(ROOT / "tools/browser/dashboard.mjs"),
                    chrome,
                    str(Path(directory) / "chrome"),
                    str(cases_path),
                ],
                check=True,
                timeout=75,
            )
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)
            store.close()
    print("8 browser pages passed; no live source, identity or publish claim")


if __name__ == "__main__":
    main()
