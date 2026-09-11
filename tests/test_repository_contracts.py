from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryHarnessTests(unittest.TestCase):
    def test_repository_contract_is_clean(self) -> None:
        from tools.validate_repo import validate_repository

        self.assertEqual(validate_repository(ROOT), [])

    def test_absolute_and_traversal_links_are_reported(self) -> None:
        from tools.validate_repo import validate_repository

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_minimum_repository(root)
            # Absolute path (could exist on CI host but is not a valid repo link)
            (root / "README.md").write_text(
                "[absolute](/etc/hosts)\n[traversal](../../outside.md)\n", encoding="utf-8"
            )

            errors = validate_repository(root)

        self.assertTrue(any("tuyệt đối" in error for error in errors), errors)
        self.assertTrue(any("thoát ra ngoài" in error for error in errors), errors)

    def test_broken_local_markdown_link_is_reported(self) -> None:
        from tools.validate_repo import validate_repository

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_minimum_repository(root)
            (root / "README.md").write_text("[không tồn tại](docs/missing.md)\n", encoding="utf-8")

            errors = validate_repository(root)

        self.assertTrue(any("docs/missing.md" in error for error in errors), errors)

    def test_schema_missing_required_property_is_reported(self) -> None:
        from tools.validate_repo import validate_repository

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_minimum_repository(root)
            schema_path = root / "schemas" / "broken.v1.json"
            schema_path.parent.mkdir(parents=True, exist_ok=True)
            schema_path.write_text(
                json.dumps(
                    {
                        "$schema": "https://json-schema.org/draft/2020-12/schema",
                        "$id": "https://schemas.s-n-sales.local/broken.v1.json",
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["missing"],
                        "properties": {},
                    }
                ),
                encoding="utf-8",
            )

            errors = validate_repository(root)

        self.assertTrue(any("missing" in error for error in errors), errors)

    def test_schema_with_wrong_collection_types_is_reported(self) -> None:
        from tools.validate_repo import validate_repository

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_minimum_repository(root)
            schema_path = root / "schemas" / "broken.v1.json"
            schema_path.parent.mkdir(parents=True, exist_ok=True)
            schema_path.write_text(
                json.dumps(
                    {
                        "$schema": "https://json-schema.org/draft/2020-12/schema",
                        "$id": "https://schemas.s-n-sales.local/broken.v1.json",
                        "type": "object",
                        "additionalProperties": False,
                        "required": "not-a-list",
                        "properties": [],
                    }
                ),
                encoding="utf-8",
            )

            errors = validate_repository(root)

        self.assertTrue(any("properties phải là object" in error for error in errors), errors)
        self.assertTrue(any("required phải là array" in error for error in errors), errors)

    def test_invalid_draft_2020_schema_is_reported(self) -> None:
        from tools.validate_repo import validate_repository

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_minimum_repository(root)
            schema_path = root / "schemas" / "broken.v1.json"
            schema_path.write_text(
                json.dumps(
                    {
                        "$schema": "https://json-schema.org/draft/2020-12/schema",
                        "$id": "https://schemas.s-n-sales.local/broken.v1.json",
                        "type": "not-a-json-schema-type",
                        "additionalProperties": False,
                        "required": [],
                        "properties": {},
                    }
                ),
                encoding="utf-8",
            )

            errors = validate_repository(root)

        self.assertTrue(any("Draft 2020-12" in error for error in errors), errors)

    def test_valid_example_with_bad_format_is_reported(self) -> None:
        from tools.validate_repo import validate_repository

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_minimum_repository(root)
            schema_path = root / "schemas" / "offer-observation.v1.json"
            schema_path.write_text(
                json.dumps(
                    {
                        "$schema": "https://json-schema.org/draft/2020-12/schema",
                        "$id": "https://schemas.s-n-sales.local/offer-observation.v1.json",
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["source_url"],
                        "properties": {"source_url": {"type": "string", "format": "uri"}},
                    }
                ),
                encoding="utf-8",
            )
            valid_path = root / "schemas" / "examples" / "valid" / schema_path.name
            valid_path.parent.mkdir(parents=True)
            valid_path.write_text(json.dumps({"source_url": "not a URI"}), encoding="utf-8")
            invalid_path = (
                root
                / "schemas"
                / "examples"
                / "invalid"
                / "offer-observation.v1.missing-url.json"
            )
            invalid_path.parent.mkdir(parents=True)
            invalid_path.write_text("{}", encoding="utf-8")

            errors = validate_repository(root)

        self.assertTrue(any("mẫu valid bị từ chối" in error for error in errors), errors)

    def test_schema_without_examples_is_reported(self) -> None:
        from tools.validate_repo import validate_repository

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_minimum_repository(root)

            errors = validate_repository(root)

        self.assertTrue(any("thiếu mẫu valid" in error for error in errors), errors)
        self.assertTrue(any("thiếu mẫu invalid" in error for error in errors), errors)

    def test_missing_contract_file_is_reported(self) -> None:
        from tools.validate_repo import validate_repository

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_minimum_repository(root)
            missing_path = root / "schemas" / "offer-observation.v1.json"
            missing_path.unlink()

            errors = validate_repository(root)

        self.assertTrue(any("offer-observation.v1.json" in error for error in errors), errors)

    @staticmethod
    def _write_minimum_repository(root: Path) -> None:
        required_files = (
            "README.md",
            "AGENTS.md",
            "ARCHITECTURE.md",
            "CODEMAP.md",
            "TRAPS.md",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "docs/TASK-PACK.md",
            "docs/PROMPT-SHEET.md",
            "docs/QUY-TRINH-GIT.md",
            "docs/adr/0001-kien-truc-khoi-dau.md",
            "docs/adr/TEMPLATE.md",
            "docs/AN-TOAN-AFFILIATE.md",
            "docs/GIA-DINH-NEN-TANG.md",
            "docs/sessions/README.md",
            ".github/pull_request_template.md",
            ".github/workflows/ci.yml",
            ".github/workflows/pr-policy.yml",
            "pyproject.toml",
            "uv.lock",
            "schemas/offer-observation.v1.json",
            "schemas/publication-candidate.v1.json",
        )
        for relative_path in required_files:
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == ".json":
                path.write_text(
                    json.dumps(
                        {
                            "$schema": "https://json-schema.org/draft/2020-12/schema",
                            "$id": f"https://schemas.s-n-sales.local/{path.name}",
                            "type": "object",
                            "additionalProperties": False,
                            "required": [],
                            "properties": {},
                        }
                    ),
                    encoding="utf-8",
                )
            else:
                path.write_text("# test\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
