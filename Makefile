.PHONY: install dev test lint fmt types ci

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest -v

lint:
	ruff check .

fmt:
	ruff format .
	ruff check --fix .

types:
	mypy brasil_cli/

ci: lint types test

run:
	brasil --help
