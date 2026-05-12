# A quantum price inference system

A quantum price inference simulation system that uses quantum algorithms for inferring asset prices using amplitude estimation and quantum Monte Carlo methods, with two interfaces:

- **Jupyter Notebook** — researcher interface with circuit visualizations, price simulations, and full physics derivations
- **REST API** — FastAPI service for programmatic access to quantum simulations.

## General approach

Pricing a product or service is fundamentally a **probability problem**. Instead of computing a fixed number, we estimate an expected value over uncertain outcomes:

$$
\text{Fair Price} = \mathbb{E}[g(X)]
$$

- $X$ — uncertain input (demand, cost, usage, FX, incidents)
- $g(X)$ — business payoff (revenue, margin, penalty, benefit)

This system implements two estimation paths side-by-side:

| Approach | Method | Notes |
| --- | --- | --- |
| Classical | Monte Carlo simulation | Error $\propto \mathcal{O}(1/\sqrt{N})$ |
| Quantum | Amplitude Estimation (QAE) | Error $\propto \mathcal{O}(1/N)$ — quadratic speedup |

Both paths share the same **4-block model**:

1. **Uncertainty Model** — define what is uncertain (variable demand, cost, usage)
2. **Payoff Function** — map outcomes to business value (margin, loss, penalty)
3. **Encoding** — load probability distributions into the quantum circuit
4. **Estimation** — extract the expected value via amplitude estimation

The quantum approach does not change *what* is calculated — only *how efficiently* the expectation is estimated. The same model applies across business domains: API pricing with variable usage, services with SLA penalties, subscriptions with churn uncertainty.

See [Quantum_Workshop_Facilitator_Script.md](Quantum_Workshop_Facilitator_Script.md) for the full 90-minute workshop guide designed for non-technical stakeholders.

## Features

- Simulate the price of a product or service using quantum amplitude estimation
- Model uncertainty over demand, cost, usage, or any continuous business variable
- Define custom payoff functions (margin, penalty, benefit) applied to simulated outcomes
- Run classical Monte Carlo and quantum QAE side-by-side for direct comparison
- Visualize quantum circuits and probability distributions in the notebook interface
- Expose all simulations via a REST API for programmatic and integration use

## API Behaviour

Both estimation endpoints share the same request schema (uncertainty + payoff parameters) and enforce the following constraints:

| Endpoint | Rate limit | Key bounds | Timeout |
| --- | --- | --- | --- |
| `POST /estimate/classical` | 30 req/min per IP | `n_samples`: 100–100 000 | — |
| `POST /estimate/quantum` | 10 req/min per IP | `epsilon`: 0.001–0.1; `alpha`: 0.01–0.5 | 30 s (HTTP 504) |

Exceeded rate limits return HTTP 429 with a `Retry-After` header. Out-of-range parameters return HTTP 422.

CORS is enabled for `localhost:8888` (Jupyter) and `localhost:3000` by default. Expand `allow_origins` in `api/main.py` for production deployments.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) — fast Python package and project manager

All other dependencies are declared in [pyproject.toml](pyproject.toml):

| Package | Purpose |
| --- | --- |
| `qiskit` | quantum circuit construction and simulation |
| `qiskit-algorithms` | amplitude estimation (QAE) |
| `numpy` | classical Monte Carlo and numerical computation |
| `matplotlib` | circuit and distribution visualizations |
| `fastapi` | REST API server |
| `uvicorn[standard]` | ASGI server for FastAPI |
| `slowapi` | per-IP rate limiting for FastAPI |
| `jupyter`, `ipykernel` | interactive notebook interface *(optional)* |
| `qiskit-finance` | pre-built uncertainty distributions and payoff circuits *(optional)* |

## Circuit Visualization

Circuits can be visualized locally (via Matplotlib) or interactively in **IBM Quantum Composer** — no IBM account needed to open a circuit in the visual editor.

```python
from qiskit import QuantumCircuit
from quantum_price_inference import configure_logging
from quantum_price_inference.composer import open_in_composer, composer_url

configure_logging(level="INFO")  # once at startup

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)

# open directly in the default browser
open_in_composer(qc)

# or just get the URL (useful in notebooks / CI)
url = composer_url(qc)
print(url)

# async variant — safe inside FastAPI handlers or async notebook cells
import asyncio
from quantum_price_inference import open_in_composer_async
await open_in_composer_async(qc)  # notebook
# asyncio.run(open_in_composer_async(qc))  # script
```

The utility exports the circuit to **OpenQASM 2.0** and encodes it as a `?code=` query parameter in the Composer URL. No upload, no credentials.

> Composer: <https://quantum.cloud.ibm.com/composer>

## Project Structure

```file
quantum-price-inference/
├── quantum_price_inference/      # core library — pure Python, no side effects
│   ├── _log.py                   # configure_logging() utility
│   ├── uncertainty.py            # NormalUncertaintyModel, LogNormalUncertaintyModel
│   ├── payoff.py                 # LinearPayoff, ThresholdPayoff
│   ├── classical.py              # classical Monte Carlo engine (estimate / estimate_async)
│   ├── quantum.py                # quantum QAE engine (estimate / estimate_async)
│   └── composer.py               # IBM Quantum Composer export utilities
├── api/                          # FastAPI REST service
│   ├── main.py                   # app factory, lifespan, CORS, rate-limit wiring
│   ├── limiter.py                # shared slowapi Limiter instance
│   ├── schemas.py                # shared Pydantic request/response models
│   └── routes/
│       ├── classical.py          # POST /estimate/classical  (30 req/min, n_samples 100–100 000)
│       └── quantum.py            # POST /estimate/quantum    (10 req/min, epsilon 0.001–0.1, 30 s timeout)
├── tests/
│   ├── conftest.py               # shared fixtures
│   ├── test_uncertainty.py
│   ├── test_payoff.py
│   ├── test_classical.py
│   ├── test_quantum.py           # 14 tests — unit + integration (skipped without qiskit-finance)
│   └── test_api.py
├── notebook/
│   └── quantum_price_inference.ipynb   # 90-min workshop demo notebook
├── docs/
│   ├── IMPROVEMENT_PLAN.md       # phased improvement roadmap (Wave 1 complete)
│   ├── EXPLAINER.md              # plain-language project explainer
│   └── STORYBOARD.md             # 15-min stakeholder presentation storyboard
├── pyproject.toml                # dependencies, build config, ruff settings
├── AGENTS.md                     # agent/AI coding instructions
└── Quantum_Workshop_Facilitator_Script.md
```

## Installation

```bash
# clone the repository
git clone https://github.com/your-org/quantum-price-inference.git
cd quantum-price-inference

# create virtual environment and install core dependencies
uv sync

# also install notebook extras (Jupyter + circuit drawing)
uv sync --extra notebook

# also install dev tools (pytest, ruff, httpx)
uv sync --extra dev
```

Activate the environment when running commands directly:

```bash
source .venv/bin/activate
```

Or prefix any command with `uv run` to use the project environment without activating:

```bash
uv run jupyter notebook
uv run uvicorn api.main:app --reload
```

### Run the Notebook

```bash
uv run jupyter notebook
```

Open `notebook/quantum_price_inference.ipynb`.

### Run the REST API

```bash
uv run uvicorn api.main:app --reload
```

API available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### License

License and documentation in this repository are licensed under the MIT License. See [LICENSE](LICENSE) for details.

### Author

@ 2026
Jose Giori Herran Escobar -  [GitHub](https://github.com/josegherran) - [LinkedIn](https://www.linkedin.com/in/joseherran/)
