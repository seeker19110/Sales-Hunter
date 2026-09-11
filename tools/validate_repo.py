"""Kiểm tra các bất biến tối thiểu của khung vận hành repository."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

REQUIRED_FILES = (
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
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")
IGNORED_DIRECTORIES = {".git", ".venv", "__pycache__"}


def _markdown_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if not any(part in IGNORED_DIRECTORIES for part in path.parts)
    )


def _validate_markdown_links(root: Path) -> list[str]:
    errors: list[str] = []
    for markdown_path in _markdown_files(root):
        content = markdown_path.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK.findall(content):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if (
                not target
                or target.startswith(("#", "http://", "https://", "mailto:"))
                or "<" in target
                or ">" in target
            ):
                continue
            relative_target = unquote(target.split("#", maxsplit=1)[0])
            if relative_target.startswith("/"):
                source = markdown_path.relative_to(root).as_posix()
                errors.append(f"{source}: liên kết tuyệt đối không hợp lệ trong repo: {target}")
                continue
            resolved = (markdown_path.parent / relative_target).resolve()
            if not resolved.is_relative_to(root.resolve()):
                source = markdown_path.relative_to(root).as_posix()
                errors.append(f"{source}: liên kết thoát ra ngoài repo root: {target}")
                continue
            if not resolved.exists():
                source = markdown_path.relative_to(root).as_posix()
                errors.append(f"{source}: liên kết nội bộ không tồn tại: {target}")
    return errors


def _validate_schemas(root: Path) -> list[str]:
    errors: list[str] = []
    schema_root = root / "schemas"
    if not schema_root.exists():
        return errors

    for schema_path in sorted(schema_root.glob("*.json")):
        relative = schema_path.relative_to(root).as_posix()
        try:
            document = json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"{relative}: JSON không hợp lệ: {exc}")
            continue
        if not isinstance(document, dict):
            errors.append(f"{relative}: schema gốc phải là object")
            continue
        validator: Draft202012Validator | None = None
        try:
            Draft202012Validator.check_schema(document)
            validator = Draft202012Validator(document, format_checker=FormatChecker())
        except SchemaError as exc:
            errors.append(f"{relative}: không hợp lệ Draft 2020-12: {exc.message}")
        for key in ("$schema", "$id", "type", "properties", "required"):
            if key not in document:
                errors.append(f"{relative}: thiếu khóa bắt buộc {key}")
        if document.get("type") != "object":
            errors.append(f"{relative}: type gốc phải là object")
        if document.get("additionalProperties") is not False:
            errors.append(f"{relative}: additionalProperties gốc phải là false")
        properties = document.get("properties")
        required = document.get("required")
        if not isinstance(properties, dict):
            errors.append(f"{relative}: properties phải là object")
        if not isinstance(required, list):
            errors.append(f"{relative}: required phải là array")
        if isinstance(properties, dict) and isinstance(required, list):
            for name in required:
                if name not in properties:
                    errors.append(f"{relative}: required '{name}' không có trong properties")

        valid_example = schema_root / "examples" / "valid" / schema_path.name
        invalid_examples = sorted(
            (schema_root / "examples" / "invalid").glob(f"{schema_path.stem}.*.json")
        )
        if not valid_example.is_file():
            errors.append(f"{relative}: thiếu mẫu valid {valid_example.name}")
        elif validator is not None:
            try:
                instance = json.loads(valid_example.read_text(encoding="utf-8"))
                validation_errors = list(validator.iter_errors(instance))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                errors.append(f"{relative}: mẫu valid không đọc được: {exc}")
            else:
                if validation_errors:
                    errors.append(
                        f"{relative}: mẫu valid bị từ chối: {validation_errors[0].message}"
                    )
        if not invalid_examples:
            errors.append(f"{relative}: thiếu mẫu invalid {schema_path.stem}.*.json")
        elif validator is not None:
            for invalid_example in invalid_examples:
                try:
                    instance = json.loads(invalid_example.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    errors.append(f"{relative}: mẫu invalid không đọc được: {exc}")
                    continue
                if validator.is_valid(instance):
                    errors.append(
                        f"{relative}: mẫu invalid lại được chấp nhận: {invalid_example.name}"
                    )
    return errors


def validate_repository(root: Path) -> list[str]:
    """Trả về danh sách lỗi; danh sách rỗng nghĩa là đạt cổng."""
    root = root.resolve()
    errors = [
        f"thiếu file vận hành bắt buộc: {relative_path}"
        for relative_path in REQUIRED_FILES
        if not (root / relative_path).is_file()
    ]
    errors.extend(_validate_markdown_links(root))
    errors.extend(_validate_schemas(root))
    return sorted(errors)


def main() -> int:
    errors = validate_repository(Path.cwd())
    if errors:
        print("Repository contract: FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Repository contract: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
