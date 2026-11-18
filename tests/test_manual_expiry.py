"""Manual expiry is validated before evidence retention; null remains supported."""

import unittest

from s_n_sales.api.store import OperatorStore
from s_n_sales.domain.json_value import canonical
from s_n_sales.quality.repository import DealRepository
from s_n_sales.quality.urls import UrlPolicy
from test_grounded_flow import NOW, manual_request


class ManualExpiryTests(unittest.TestCase):
    def test_nullable_expiry_is_narrowed_before_evidence_is_retained(self) -> None:
        store = OperatorStore()
        self.addCleanup(store.close)
        repo = DealRepository(store, url_policy=UrlPolicy(frozenset({"example.com"})))
        request = manual_request()
        for invalid in (True, 0, [], {}):
            request["valid_until"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                repo.import_manual(canonical(request).encode(), actor="reviewer", now=NOW)
        count = store._conn.execute("SELECT COUNT(*) FROM evidence_manifests").fetchone()[0]
        self.assertEqual(count, 0)
        request["valid_until"] = None
        result = repo.import_manual(canonical(request).encode(), actor="reviewer", now=NOW)
        self.assertIsNone(result.facts["valid_until"])
