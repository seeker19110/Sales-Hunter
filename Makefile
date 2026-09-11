.PHONY: sync lint test check

sync:
	uv sync --locked

lint:
	uv run ruff check tools tests

test:
	uv run python -m unittest discover -s tests -v

check: lint test
	uv run python tools/validate_repo.py
