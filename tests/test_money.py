from __future__ import annotations

import unittest

from s_n_sales.domain.money import Money


class MoneyTests(unittest.TestCase):
    def test_rejects_float_amount(self) -> None:
        with self.assertRaises(TypeError):
            Money(1.5)  # type: ignore[arg-type]

    def test_rejects_boolean_amount(self) -> None:
        with self.assertRaises(TypeError):
            Money(True)  # type: ignore[arg-type]

    def test_rejects_negative(self) -> None:
        with self.assertRaises(ValueError):
            Money(-1)

    def test_discount_ratio(self) -> None:
        sale = Money(150_000)
        listed = Money(200_000)
        self.assertAlmostEqual(sale.discount_ratio(listed) or 0.0, 0.25)

    def test_sale_above_list_raises(self) -> None:
        with self.assertRaises(ValueError):
            Money(300_000).discount_ratio(Money(200_000))


if __name__ == "__main__":
    unittest.main()
