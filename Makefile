.PHONY: sync lint format-check test schema check

export PYTHONPATH := src:$(PYTHONPATH)

sync:
	uv sync --locked

lint:
	uv run ruff check src tools tests

format-check:
	uv run ruff format --check src tools tests

test:
	uv run python -m unittest discover -s tests -v

schema:
	uv run python tools/validate_repo.py

check: lint format-check test schema
