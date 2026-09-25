"""SH-004: contracts must be usable from an installed runtime-only wheel."""

import unittest
from importlib.metadata import requires
from importlib.resources import files
from pathlib import Path


class RuntimePackagingTests(unittest.TestCase):
    def test_jsonschema_is_a_runtime_dependency(self) -> None:
        requirements = requires("sales-hunter") or []
        self.assertTrue(
            any(
                item.lower().startswith("jsonschema") and "extra ==" not in item
                for item in requirements
            ),
            "jsonschema must be declared in project.dependencies, not only dev",
        )

    def test_packaged_contracts_match_repository_contracts(self) -> None:
        root = Path(__file__).resolve().parents[1]
        schemas = sorted((root / "schemas").glob("*.json"))
        self.assertTrue(schemas)
        for schema in schemas:
            with self.subTest(schema=schema.name):
                resource = files("s_n_sales").joinpath("schemas", schema.name)
                self.assertTrue(resource.is_file(), f"schema missing from package: {schema.name}")
                self.assertEqual(resource.read_bytes(), schema.read_bytes())


if __name__ == "__main__":
    unittest.main()
