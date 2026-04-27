# quantum-price-inference — Agent Instructions

## Project Overview

Quantum price inference simulation system. Two delivery interfaces:

- **Jupyter Notebook** — researcher-facing demo for a 90-min workshop ([Quantum_Workshop_Facilitator_Script.md](Quantum_Workshop_Facilitator_Script.md))
- **REST API** — FastAPI service wrapping the same simulation logic

See [README.md](README.md) for architecture, dependency table, and run commands.

## Architecture

```
quantum_price_inference/   # core library (pure Python, no side effects)
│  _log.py                 # configure_logging() utility
│  composer.py             # IBM Quantum Composer export (circuit_to_qasm2, composer_url)
│  uncertainty.py          # NormalUncertaintyModel, LogNormalUncertaintyModel
│  payoff.py               # LinearPayoff, ThresholdPayoff
│  classical.py            # classical Monte Carlo engine (estimate / estimate_async)
│  quantum.py              # quantum QAE engine (estimate / estimate_async)
notebook/
│  quantum_price_inference.ipynb   # 90-min workshop demo
api/
│  main.py                 # FastAPI app, lifespan, health endpoint
│  schemas.py              # Pydantic request/response models
│  routes/
│     classical.py         # POST /estimate/classical
│     quantum.py           # POST /estimate/quantum
tests/
│  conftest.py             # shared fixtures
│  test_uncertainty.py
│  test_payoff.py
│  test_classical.py
│  test_api.py
```

### 4-block model (every simulation follows this)

1. **Uncertainty Model** — what is uncertain (demand, cost, usage); use `qiskit-finance` `NormalDistribution` / `LogNormalDistribution`
2. **Payoff Function** — business value mapping; use `qiskit-finance` `LinearAmplitudeFunction`
3. **Encoding** — probability distributions loaded into quantum circuit
4. **Estimation** — expected value extracted via `qiskit-algorithms` `IterativeAmplitudeEstimation`

## Build & Test

```bash
# install all groups
uv sync --extra notebook --extra dev

# run tests
uv run pytest

# lint / format
uv run ruff check .
uv run ruff format .

# start API
uv run uvicorn api.main:app --reload

# open notebook
uv run jupyter notebook
```

## Key Conventions

- **Python 3.10+**, line length 100 (`ruff` enforces, see `pyproject.toml`)
- **`uv`** only — never `pip install` or `python -m venv` directly
- Core library (`quantum_price_inference/`) must remain **import-safe** with no side effects at module level; no `webbrowser.open` or heavy I/O at import time
- Quantum circuits are exported as **OpenQASM 2.0** for Composer; use `qiskit.qasm2.dumps()` (not the deprecated `circuit.qasm()` method)
- API and notebook are consumers of the core library — keep business logic in `quantum_price_inference/`, not in route handlers or notebook cells
- Optional dependencies (`qiskit-finance`, `jupyter`) must be **guarded with try/import** inside functions, not at module top level, so the core library installs without extras

### Logging

Every module declares its own logger at module level — never configure logging inside the core library:

```python
import logging
log = logging.getLogger(__name__)
```

Call `configure_logging()` exactly once at startup — in `api/main.py` lifespan or the first notebook cell:

```python
from quantum_price_inference import configure_logging
configure_logging(level="DEBUG")   # or logging.INFO for production
```

### Async

Quantum and classical simulation engines are **CPU-bound**. Expose both a sync entry point and an async wrapper in every engine module:

```python
import asyncio

def estimate(model, payoff, **kwargs) -> float:
    ...  # synchronous implementation

async def estimate_async(model, payoff, **kwargs) -> float:
    return await asyncio.to_thread(estimate, model, payoff, **kwargs)
```

FastAPI route handlers must be `async def` and call the `_async` variant so the event loop is never blocked. Notebook cells can use either form.

## Workshop Context

The notebook is a **live demo for non-technical stakeholders** (see facilitator script). Keep notebook cells observable and interpretable — avoid raw math; prefer plain-language annotations alongside results. Side-by-side comparison (classical MC vs. quantum QAE) is the centerpiece of the demo.
