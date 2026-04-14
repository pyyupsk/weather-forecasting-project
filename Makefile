.PHONY: audit check format lint run sync test typecheck

audit:
	uvx pip-audit

check: lint typecheck test

format:
	uv run ruff format src/ tests/

lint:
	uv run ruff check src/ tests/

run:
	uv run src/main.py

sync:
	uv sync

test:
	uv run pytest

typecheck:
	uv run pyright src/
