"""Quy tắc thu hồi nội dung khi observation quá hạn freshness."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


def should_recall_content(
    *,
    observed_at: datetime,
    now: datetime,
    max_age: timedelta = timedelta(hours=24),
) -> bool:
    """True nếu observation đã cũ hơn max_age — nên thu hồi / ngừng claim."""
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("observed_at phải có timezone")
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now phải có timezone")
    age = now.astimezone(UTC) - observed_at.astimezone(UTC)
    return age > max_age
