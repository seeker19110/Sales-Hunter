"""Kill switch theo adapter — in-memory, không side effect mạng."""

from __future__ import annotations


class KillSwitch:
    """Bật/tắt adapter theo tên. Mặc định mọi adapter enabled."""

    def __init__(self) -> None:
        self._disabled: set[str] = set()

    def disable(self, adapter_name: str) -> None:
        self._disabled.add(adapter_name)

    def enable(self, adapter_name: str) -> None:
        self._disabled.discard(adapter_name)

    def is_enabled(self, adapter_name: str) -> bool:
        return adapter_name not in self._disabled

    def assert_enabled(self, adapter_name: str) -> None:
        if not self.is_enabled(adapter_name):
            raise RuntimeError(f"adapter {adapter_name!r} đang bị kill switch")
