"""Conservative URL policy; each redirect must pass the same explicit allowlist."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, unquote, urljoin, urlsplit

_HOST = re.compile(r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
_SECRET = re.compile(
    r"(?:token|secret|password|passwd|cookie|session|authorization|api[_-]?key)", re.I
)


@dataclass(frozen=True)
class UrlPolicy:
    allowed_hosts: frozenset[str] = frozenset()
    max_redirects: int = 3

    def __post_init__(self) -> None:
        if type(self.max_redirects) is not int or not 0 <= self.max_redirects <= 5:
            raise ValueError("invalid_redirect_limit")
        if any(not _HOST.fullmatch(host) for host in self.allowed_hosts):
            raise ValueError("invalid_allowlist_hostname")

    def validate(self, value: str) -> str:
        if not isinstance(value, str) or not value or len(value) > 4096:
            raise ValueError("url_invalid")
        decoded = value
        for _ in range(3):
            if any(ord(char) <= 32 or ord(char) == 127 for char in decoded) or "\\" in decoded:
                raise ValueError("url_control_or_whitespace")
            if re.search(r"%(?![0-9a-fA-F]{2})", decoded):
                raise ValueError("url_bad_percent_escape")
            decoded = unquote(decoded, errors="strict")
        try:
            parts = urlsplit(value)
            host = parts.hostname
            if (
                parts.scheme != "https"
                or not value.lower().startswith("https://")
                or not host
                or not host.isascii()
                or not _HOST.fullmatch(host)
                or host not in self.allowed_hosts
                or parts.username is not None
                or parts.password is not None
                or parts.port not in (None, 443)
                or parts.fragment
                or not parts.netloc
            ):
                raise ValueError("url_not_allowed")
            for key, _ in parse_qsl(parts.query, keep_blank_values=True, max_num_fields=100):
                if _SECRET.search(unquote(key)):
                    raise ValueError("url_contains_secret_parameter")
        except (UnicodeError, ValueError) as exc:
            raise ValueError("url_not_allowed") from exc
        return value

    def redirect(self, source: str, location: str, *, hop: int = 1) -> str:
        self.validate(source)
        if type(hop) is not int or hop < 1 or hop > self.max_redirects:
            raise ValueError("redirect_limit")
        if not isinstance(location, str) or not location:
            raise ValueError("redirect_location_invalid")
        return self.validate(urljoin(source, location))


def assert_public_addresses(addresses: list[str]) -> None:
    """A fetcher must pin one of these validated addresses instead of resolving again."""
    if not addresses:
        raise ValueError("dns_empty")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global or ip.is_multicast or ip.is_unspecified:
            raise ValueError("dns_non_public_address")
