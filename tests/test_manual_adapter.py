from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from s_n_sales.adapters.kill_switch import KillSwitch
from s_n_sales.adapters.manual import ManualAdapterError, load_manual_observation
from s_n_sales.pipeline.manual_draft_flow import run_manual_to_publication_candidate

ROOT = Path(__file__).resolve().parents[1]


class ManualAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = ROOT / "schemas/examples/valid/offer-observation.v1.json"
        self.now = datetime(2026, 9, 11, 4, 0, tzinfo=UTC)

    def test_load_manual_fixture(self) -> None:
        data = load_manual_observation(self.fixture, now=self.now)
        self.assertEqual(data["source_method"], "manual")
        self.assertEqual(data["observation_id"], "obs-demo-001")

    def test_rejects_non_manual_source_method(self) -> None:
        raw = json.loads(self.fixture.read_text(encoding="utf-8"))
        raw["source_method"] = "official_api"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "obs.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(ManualAdapterError):
                load_manual_observation(path, now=self.now)

    def test_rejects_missing_file(self) -> None:
        with self.assertRaises(ManualAdapterError):
            load_manual_observation(Path("/no/such/obs.json"), now=self.now)

    def test_kill_switch_blocks_flow(self) -> None:
        switch = KillSwitch()
        switch.disable("manual")
        with self.assertRaises(RuntimeError):
            run_manual_to_publication_candidate(
                self.fixture,
                content="Deal demo",
                affiliate_url="https://example.com/aff/x",
                target_channel="telegram:demo",
                now=self.now,
                kill_switch=switch,
            )

    def test_e2e_manual_to_publication_candidate(self) -> None:
        candidate = run_manual_to_publication_candidate(
            self.fixture,
            content="Sản phẩm minh họa đang giảm — kiểm tra link.",
            affiliate_url="https://example.com/aff/item-demo-001",
            target_channel="telegram:s-n-sales-demo",
            now=self.now,
        )
        self.assertEqual(candidate["schema_version"], "publication-candidate.v1")
        self.assertEqual(candidate["approval"]["status"], "pending")
        self.assertEqual(candidate["observation_id"], "obs-demo-001")
        self.assertRegex(candidate["draft_sha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
