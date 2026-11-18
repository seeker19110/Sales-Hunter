"""Vietnamese fixtures must not depend on the runner's locale encoding."""

from __future__ import annotations

import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import patch

from test_deal_quality import observation
from test_grounded_flow import manual_request


class FixtureEncodingTests(unittest.TestCase):
    def check_windows_locale(self, loader: Callable[[], dict[str, Any]]) -> None:
        # Simulate Windows cp1252 even on Linux without changing the fixture or
        # the process locale. Explicit UTF-8 passes through unchanged.
        original = Path.read_text
        expected = loader()

        def windows_read_text(
            path: Path,
            encoding: str | None = None,
            errors: str | None = None,
        ) -> str:
            if encoding in (None, "locale"):
                encoding = "cp1252"
            return original(path, encoding=encoding, errors=errors)

        with patch.object(Path, "read_text", windows_read_text):
            actual = loader()
        self.assertEqual(actual, expected)

    def test_deal_observation_is_locale_independent(self) -> None:
        self.check_windows_locale(observation)

    def test_manual_request_is_locale_independent(self) -> None:
        self.check_windows_locale(manual_request)


if __name__ == "__main__":
    unittest.main()
