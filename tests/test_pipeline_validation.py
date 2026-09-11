from __future__ import annotations

import json
import unittest
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from s_n_sales.pipeline.draft import ObservationValidationError, observation_to_rank

ROOT = Path(__file__).resolve().parents[1]


class PipelineValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.observation = json.loads(
            (ROOT / "schemas/examples/valid/offer-observation.v1.json").read_text(encoding="utf-8")
        )
        self.now = datetime(2026, 9, 11, 4, 0, tzinfo=UTC)

    def test_rejects_schema_invalid_observation_before_ranking(self) -> None:
        invalid = {"observation_id": "obs-invalid"}

        with self.assertRaises(ObservationValidationError):
            observation_to_rank(invalid, now=self.now)

    def test_rejects_invalid_domain_values_before_ranking(self) -> None:
        invalid = deepcopy(self.observation)
        invalid["sale_price_minor"] = True
        invalid["stock_status"] = "made_up"

        with self.assertRaises(ObservationValidationError):
            observation_to_rank(invalid, now=self.now)

    def test_rejects_naive_clock(self) -> None:
        with self.assertRaises(ValueError):
            observation_to_rank(self.observation, now=datetime(2026, 9, 11, 4, 0))

    def test_returns_result_that_validates_against_rank_contract(self) -> None:
        result = observation_to_rank(self.observation, now=self.now)
        schema = json.loads((ROOT / "schemas/rank-result.v1.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        errors = list(validator.iter_errors(result))

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
