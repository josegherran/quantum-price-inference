# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install
uv sync --extra dev                         # core + dev tools (pytest, ruff)
uv sync --extra dev --extra notebook        # + Jupyter, marimo, qiskit-finance

# Test
make test                                   # full suite (uv run pytest --tb=short)
make test-unit                              # unit tests only (no qiskit-finance needed)
make test-integration                       # requires --extra notebook
uv run pytest tests/test_api.py -k "health" # single test or module

# Lint / format
make lint                                   # ruff check
make format                                 # ruff format --fix
make ci                                     # lint + format-check + test

# Run
make api                                    # uvicorn api.main:app --reload on :8000
make notebook                               # Jupyter on notebook/
uv run marimo run notebook/00_calculating_orangejuice_price_app.py
uv run marimo run notebook/01_price_estimation_techniques_app.py
```

## Architecture

Three delivery interfaces share one core library:

```file structure
quantum_price_inference/   # pure-Python library — the only place business logic lives
api/                       # FastAPI service consuming the library
notebook/                  # Jupyter + marimo apps consuming the library
tests/                     # pytest suite
deploy/                    # Docker, docker-compose, Prometheus, Grafana
```

### 4-block simulation model

Every simulation — classical or quantum — follows the same four steps:

1. **Uncertainty Model** (`uncertainty.py`) — distribution over an unknown variable (Normal or LogNormal)
2. **Payoff Function** (`payoff.py`) — maps outcome → business value (Linear or Threshold)
3. **Encoding** — classical: draws samples; quantum: loads distribution into Qiskit circuit
4. **Estimation** — classical: Monte Carlo mean; quantum: `IterativeAmplitudeEstimation` from `qiskit-algorithms`

Each engine (`classical.py`, `quantum.py`) exposes both a sync `estimate()` and `estimate_async()` wrapping it with `asyncio.to_thread`. FastAPI routes always call the async variant.

### Key structural rules

- Business logic belongs in `quantum_price_inference/`, not in route handlers or notebook cells.
- The core library must be **import-safe**: no side effects at module level, no heavy I/O at import time.
- Optional dependencies (`qiskit-finance`, `jupyter`) are guarded with `try/import` inside functions — never at module top level.
- All Qiskit imports in `composer.py` are deferred inside functions.
- The shared `slowapi` Limiter lives in `api/limiter.py`; route modules import from there to avoid circular imports with `api/main.py`.
- `configure_logging()` is called exactly once: in the FastAPI lifespan or the first notebook cell.

See `AGENTS.md` for detailed conventions on rate limiting, async patterns, logging, and test fixtures.
