.PHONY: audit format lint run sync typecheck

audit:
	uvx pip-audit

format:
	uv run ruff format src/

lint:
	uv run ruff check src/

run:
	uv run src/main.py

sync:
	uv sync

typecheck:
	uv run pyright src/
