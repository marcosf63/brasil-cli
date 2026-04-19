# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_bacen.py

# Run a single test
uv run pytest tests/test_bacen.py::test_consultar_serie_ultimos

# Lint
uv run ruff check brasil_cli/ tests/

# Format
uv run ruff format brasil_cli/ tests/

# Type check
uv run mypy brasil_cli/

# Run the CLI (after install)
brasil --help
```

## Architecture

The CLI bridges sync Typer commands with async providers using `asyncio.run()` via the `_run()` helper in `cli.py`. This lets providers be reused outside the CLI (bots, scripts, APIs).

**Data flow:** `cli.py` command → `_run(provider_function(...))` → `http_client.fetch_json()` → `output.py` formatting

### Key modules

- [brasil_cli/cli.py](brasil_cli/cli.py) — Entry point. All Typer sub-apps (`bacen_app`, `ibge_app`, `camara_app`, `br_app`, `transparencia_app`) registered here. Commands call providers via `_run()`.
- [brasil_cli/http_client.py](brasil_cli/http_client.py) — Single `fetch_json()` async function used by all providers. Implements exponential backoff retry (3 attempts, factor 1.5).
- [brasil_cli/output.py](brasil_cli/output.py) — Rich formatting helpers: `print_table`, `print_kv`, `print_series`, `print_list`, `print_error`, `print_info`.
- [brasil_cli/providers/](brasil_cli/providers/) — One module per data source. All functions are async and use `fetch_json`.

### Adding a new provider

1. Create `brasil_cli/providers/novo.py` with async functions using `fetch_json`
2. Add a `typer.Typer()` sub-app in `cli.py`
3. Register with `app.add_typer(novo_app, name="novo")`

### Tests

Tests use `respx` to mock `httpx` HTTP calls. All async tests use `@pytest.mark.asyncio` (mode is set to `auto` in `pyproject.toml`, so the decorator can be omitted).

### Portal da Transparência

Requires an API key passed via `--key` or env var `TRANSPARENCIA_API_KEY`.
