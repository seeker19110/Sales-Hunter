"""Versioned URL allowlist file (ADR-0011); an empty host list fails closed."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from s_n_sales.domain.json_value import json_object
from s_n_sales.quality.urls import UrlPolicy


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    resource = files("s_n_sales").joinpath("schemas", "url-allowlist.v1.json")
    return Draft202012Validator(
        json.loads(resource.read_text(encoding="utf-8")), format_checker=FormatChecker()
    )


def load_url_policy(path: str | Path) -> UrlPolicy:
    """Parse strictly, validate the contract, then build the policy; never default hosts."""
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise ValueError("url_allowlist_unreadable") from exc
    document = json_object(raw, max_bytes=256 * 1024)
    if not _validator().is_valid(document):
        raise ValueError("url_allowlist_contract_invalid")
    return UrlPolicy(
        allowed_hosts=frozenset(entry["host"] for entry in document["hosts"]),
        max_redirects=document["max_redirects"],
        version=document["version"],
    )
