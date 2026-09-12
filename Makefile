.PHONY: sync lint format-check typecheck test schema dependency-audit status-freshness check

export PYTHONPATH := src:$(PYTHONPATH)

sync:
	uv sync --locked

lint:
	uv run ruff check src tools tests

format-check:
	uv run ruff format --check src tools tests

typecheck:
	uv run python -m pyright src tools tests

test:
	uv run python -m unittest discover -s tests -v

schema:
	uv run python tools/validate_repo.py

dependency-audit:
	uv run python -m pip_audit

status-freshness:
	uv run python tools/check_status_freshness.py

check: lint format-check typecheck test schema dependency-audit
