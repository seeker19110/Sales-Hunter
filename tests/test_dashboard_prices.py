"""SH-010: list/detail render builder output, not fabricated UI-only fields."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from s_n_sales.api.app import _render_dashboard_detail, _render_dashboard_list
from s_n_sales.pipeline.publication import build_publication_candidate

ROOT = Path(__file__).resolve().parents[1]


def candidate_for_prices(sale: int = 80000, listed: int | None = 100000) -> dict[str, Any]:
    observation = json.loads(
        (ROOT / "schemas/examples/valid/offer-observation.v1.json").read_text(encoding="utf-8")
    )
    observation.update(sale_price_minor=sale, list_price_minor=listed)
    return build_publication_candidate(
        observation,
        {},
        content="Minh họa <script>alert(1)</script>",
        affiliate_url="https://example.com/affiliate",
        target_channel="manual_export",
    )


class DashboardPriceTests(unittest.TestCase):
    def render_both(self, candidate: dict[str, Any]) -> tuple[str, str]:
        return (
            _render_dashboard_list([candidate], None, ""),
            _render_dashboard_detail(candidate, ""),
        )

    def test_real_builder_fields_on_list_and_detail(self) -> None:
        for page in self.render_both(candidate_for_prices()):
            with self.subTest(page=page[:60]):
                self.assertIn("80.000 VND", page)
                self.assertIn("100.000 VND", page)
                self.assertIn("20%", page)
                self.assertIn("Shopee", page)
                self.assertNotIn("<script>alert(1)</script>", page)

    def test_unknown_list_price_is_not_zero_or_discount(self) -> None:
        for page in self.render_both(candidate_for_prices(listed=None)):
            self.assertIn("Chưa xác minh", page)
            self.assertNotRegex(page, r">-?0%</")
            self.assertNotIn("Giảm: <strong>0", page)

    def test_zero_sale_remains_verified_zero(self) -> None:
        for page in self.render_both(candidate_for_prices(sale=0)):
            self.assertIn("0 VND", page)
            self.assertIn("100%", page)

    def test_large_integer_is_exact(self) -> None:
        for page in self.render_both(candidate_for_prices(9007199254740993, 10000000000000000)):
            self.assertIn("9.007.199.254.740.993 VND", page)
            self.assertIn("9,93%", page)

    def test_untrusted_legacy_fields_are_not_used(self) -> None:
        candidate = candidate_for_prices()
        candidate["platform"] = "wrong-platform"
        candidate["claim_snapshot"].update(sale_price_units=1, discount_ratio=0.99)
        for page in self.render_both(candidate):
            self.assertIn("80.000 VND", page)
            self.assertNotIn("wrong-platform", page)
            self.assertNotIn("99%", page)

    def test_malformed_snapshot_renders_unknown_instead_of_crashing(self) -> None:
        candidate = candidate_for_prices()
        for snapshot in (None, [], {"sale_price_minor": True}, {"sale_price_minor": 1.5}):
            candidate["claim_snapshot"] = snapshot
            for page in self.render_both(candidate):
                self.assertIn("Chưa xác minh", page)

    def test_mobile_viewport_and_scroll_region_exist(self) -> None:
        listing, detail = self.render_both(candidate_for_prices())
        for page in (listing, detail):
            self.assertIn('name="viewport"', page)
        self.assertIn('aria-label="Danh sách ưu đãi"', listing)


if __name__ == "__main__":
    unittest.main()
