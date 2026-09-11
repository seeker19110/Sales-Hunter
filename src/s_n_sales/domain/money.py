"""Money value object — chỉ số nguyên đơn vị nhỏ nhất, không float."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Money:
    amount_minor: int
    currency: str = "VND"

    def __post_init__(self) -> None:
        if isinstance(self.amount_minor, bool) or not isinstance(self.amount_minor, int):
            raise TypeError("amount_minor phải là int, không phải bool")
        if self.amount_minor < 0:
            raise ValueError("amount_minor không được âm")
        if not self.currency or not isinstance(self.currency, str):
            raise ValueError("currency không hợp lệ")

    def discount_ratio(self, list_price: Money | None) -> float | None:
        """Tỷ lệ giảm so với list; None nếu không có list hoặc list = 0."""
        if list_price is None:
            return None
        if list_price.currency != self.currency:
            raise ValueError("currency không khớp")
        if list_price.amount_minor <= 0:
            return None
        if self.amount_minor > list_price.amount_minor:
            raise ValueError("sale_price không được lớn hơn list_price")
        return (list_price.amount_minor - self.amount_minor) / list_price.amount_minor
