# Quantum Price Inference

A quantum price inference simulation system that uses quantum algorithms for estimating expected business value under uncertainty, with two delivery interfaces:

- **Jupyter Notebook** — researcher-facing demo for a 90-min workshop
- **REST API** — FastAPI service wrapping the same simulation logic

## General Approach

Pricing a product or service is fundamentally a **probability problem**. Instead of computing a fixed number, we estimate an expected value over uncertain outcomes:

$$
\text{Fair Price} = \mathbb{E}[g(X)]
$$

- $X$ — uncertain input (demand, cost, usage, FX, incidents)
- $g(X)$ — business payoff (revenue, margin, penalty, benefit)

This system implements two estimation paths side-by-side:

| Approach | Method | Error rate |
| --- | --- | --- |
| Classical | Monte Carlo simulation | $\mathcal{O}(1/\sqrt{N})$ |
| Quantum | Amplitude Estimation (QAE) | $\mathcal{O}(1/N)$ — quadratic speedup |

Both paths share the same **4-block model**:

1. **Uncertainty Model** — define what is uncertain (demand, cost, usage)
2. **Payoff Function** — map outcomes to business value (margin, loss, penalty)
3. **Encoding** — load probability distributions into the quantum circuit
4. **Estimation** — extract the expected value via amplitude estimation

The quantum approach does not change *what* is calculated — only *how efficiently* the expectation is estimated.

See [`docs/Quantum_Workshop_Facilitator_Script.md`](docs/Quantum_Workshop_Facilitator_Script.md) for the full 90-minute workshop guide.

---

## Features

- Classical Monte Carlo and Quantum Amplitude Estimation (QAE) side-by-side
- Normal and Log-Normal uncertainty models; Linear and Threshold payoff functions
- In-process LRU result cache — seeded classical calls and all quantum calls are served from cache on repeat requests
- Structured JSON logging with per-request UUID correlation (`X-Request-ID` header)
- Prometheus metrics at `/metrics` — request rates, latency histograms, oracle call counters
- Liveness (`/health/live`) and readiness (`/health/ready`) probes for Kubernetes / load balancers
- Per-IP rate limiting (30 req/min classical, 10 req/min quantum) with `Retry-After` headers
- Input validation with HTTP 422 on out-of-range parameters
- 30 s estimation timeout with HTTP 504 on the quantum endpoint
- CORS policy for Jupyter and local frontends
- IBM Quantum Composer export — view any circuit in the browser, no IBM account needed
- Docker image + full-stack Compose (API + Prometheus + Grafana) with a pre-built dashboard
- Makefile with targets for every common workflow

---

## API Endpoints

| Endpoint | Method | Rate limit | Key bounds | Timeout |
| --- | --- | --- | --- | --- |
| `/estimate/classical` | POST | 30 req/min per IP | `n_samples`: 100–100 000 | — |
| `/estimate/quantum` | POST | 10 req/min per IP | `epsilon`: 0.001–0.1; `alpha`: 0.01–0.5 | 30 s (HTTP 504) |
| `/health/live` | GET | — | — | — |
| `/health/ready` | GET | — | — | — |
| `/metrics` | GET | — | Prometheus text format | — |
| `/docs` | GET | — | OpenAPI / Swagger UI | — |

Exceeded rate limits return HTTP 429 with a `Retry-After` header. Out-of-range parameters return HTTP 422. CORS is enabled for `localhost:8888` (Jupyter) and `localhost:3000` by default.

---

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) — fast Python package and project manager
- Docker + Docker Compose *(for containerised deployment only)*

All Python dependencies are declared in [`pyproject.toml`](pyproject.toml):

| Package | Purpose | Extra |
| --- | --- | --- |
| `qiskit` | quantum circuit construction and simulation | core |
| `qiskit-algorithms` | amplitude estimation (IQAE) | core |
| `numpy` | classical Monte Carlo and numerical computation | core |
| `matplotlib` | circuit and distribution visualisations | core |
| `fastapi` | REST API server | core |
| `uvicorn[standard]` | ASGI server | core |
| `slowapi` | per-IP rate limiting | core |
| `prometheus-fastapi-instrumentator` | Prometheus metrics endpoint | core |
| `jupyter`, `ipykernel`, `pylatexenc` | interactive notebook interface | `notebook` |
| `qiskit-finance` | pre-built uncertainty distributions and payoff circuits | `notebook` |
| `pytest`, `httpx`, `ruff` | testing and linting | `dev` |

---

## Project Structure

```
quantum-price-inference/
├── quantum_price_inference/      # core library — pure Python, no side effects
│   ├── _log.py                   # configure_logging(), JSON formatter, request-ID filter
│   ├── uncertainty.py            # NormalUncertaintyModel, LogNormalUncertaintyModel
│   ├── payoff.py                 # LinearPayoff, ThresholdPayoff
│   ├── classical.py              # Monte Carlo engine — estimate / estimate_async + LRU cache
│   ├── quantum.py                # QAE engine — estimate / estimate_async + LRU cache
│   └── composer.py               # IBM Quantum Composer export (circuit_to_qasm2, composer_url)
├── api/
│   ├── main.py                   # app factory, lifespan, CORS, rate-limit, Prometheus wiring
│   ├── limiter.py                # shared slowapi Limiter instance
│   ├── middleware.py             # RequestIDMiddleware — UUID4 per request, X-Request-ID header
│   ├── schemas.py                # Pydantic request/response models
│   └── routes/
│       ├── classical.py          # POST /estimate/classical
│       └── quantum.py            # POST /estimate/quantum
├── deploy/
│   ├── Dockerfile                # multi-stage build — Python 3.13-slim, non-root user
│   ├── docker-compose.yml        # API + Prometheus + Grafana
│   ├── .env.example              # environment variable template
│   ├── prometheus.yml            # scrape config
│   ├── prometheus-alerts.yml     # alert rules (error rate, latency, API down, idle)
│   └── grafana/provisioning/     # auto-provisioned datasource + dashboard
├── tests/
│   ├── conftest.py
│   ├── test_uncertainty.py
│   ├── test_payoff.py
│   ├── test_classical.py
│   ├── test_quantum.py           # unit + integration (auto-skipped without qiskit-finance)
│   ├── test_composer.py
│   └── test_api.py
├── notebook/
│   └── quantum_price_inference.ipynb   # 90-min workshop demo
├── docs/
│   ├── IMPROVEMENT_PLAN.md
│   ├── Quantum_Workshop_Facilitator_Script.md
│   ├── EXPLAINER.md
│   └── STORYBOARD.md
├── Makefile                      # all common workflows — see `make help`
└── pyproject.toml
```

---

## Quick Start

### 1. Install dependencies

```bash
# core + dev tools
uv sync --extra dev

# also install notebook extras (Jupyter, qiskit-finance, matplotlib)
uv sync --extra dev --extra notebook
```

### 2. Run the API

```bash
uv run uvicorn api.main:app --reload
# or
make api
```

API at `http://localhost:8000` · Swagger UI at `http://localhost:8000/docs` · Metrics at `http://localhost:8000/metrics`

### 3. Run the notebook

```bash
uv run jupyter notebook notebook/quantum_price_inference.ipynb
# or
make notebook
```

> **Kernel check:** the notebook must run on the kernel labelled **`python3`** pointing at `.venv` (top-right corner of the Jupyter UI). Switch via *Kernel → Change kernel → python3* if needed. Running without `--extra notebook` causes `ModuleNotFoundError: No module named 'matplotlib'` on the first cell.

### 4. Run tests

```bash
uv run pytest --tb=short
# or
make test
```

90 tests, 0 failures. Integration tests that require `qiskit-finance` are auto-skipped when the notebook extra is not installed.

### 5. Lint and format

```bash
make lint          # ruff check
make format        # ruff format (auto-fix)
make format-check  # ruff format --check (CI mode)
make ci            # lint + format-check + test
```

---

## Docker Deployment

### Single container

```bash
make docker-build   # builds quantum-price-inference:latest
make docker-run     # runs on port 8000
make docker-stop
make docker-logs
```

### Full stack (API + Prometheus + Grafana)

```bash
# first run — copies .env.example → .env automatically
make deploy-up

# verify
curl http://localhost:8000/health/live    # {"status":"alive"}
curl http://localhost:8000/health/ready   # {"status":"ready","checks":{...}}
curl http://localhost:8000/metrics        # Prometheus text

# open dashboards
open http://localhost:9090   # Prometheus
open http://localhost:3001   # Grafana  (admin / see deploy/.env)

make deploy-down
```

The Grafana dashboard is pre-provisioned at startup — no manual import needed. It includes panels for request rate, error rate, p50/p95/p99 latency, quantum oracle calls, and classical MC sample throughput.

To customise the deployment, copy `deploy/.env.example` to `deploy/.env` and edit:

```bash
cp deploy/.env.example deploy/.env
# edit QPI_LOG_LEVEL, QPI_WORKERS, QPI_GRAFANA_PASSWORD, etc.
```

`deploy/.env` is gitignored — never commit credentials.

---

## Observability

### Logging

Every log line includes a `request_id` field that matches the `X-Request-ID` response header, enabling end-to-end request tracing across log aggregators.

```python
# plain text (default — local dev and notebook)
configure_logging(level="INFO")

# JSON lines (production — CloudWatch, Datadog, Loki, etc.)
configure_logging(level="INFO", json=True)
```

Pass a client-supplied `X-Request-ID` header to propagate your own trace ID:

```bash
curl -H "X-Request-ID: my-trace-42" http://localhost:8000/health/live
# response header: X-Request-ID: my-trace-42
```

### Metrics

`/metrics` exposes Prometheus-format metrics including:

| Metric | Description |
| --- | --- |
| `http_requests_total` | Request count by endpoint and status code |
| `http_request_duration_seconds` | Latency histogram (p50/p95/p99) |
| `classical_samples_total` | Total Monte Carlo samples drawn |
| `quantum_oracle_calls_total` | Total Grover oracle evaluations |

### Health probes

| Endpoint | Use case | Returns |
| --- | --- | --- |
| `GET /health/live` | Kubernetes `livenessProbe`, load balancer | `{"status":"alive"}` |
| `GET /health/ready` | Kubernetes `readinessProbe` | `{"status":"ready","checks":{...}}` |
| `GET /health` | Legacy backward-compat | `{"status":"ok"}` |

---

## Result Caching

Classical and quantum estimations are deterministic for fixed inputs. Results are served from an in-process LRU cache on repeat calls:

- **Classical** — cached when `seed` is provided (maxsize 256, keyed on all scalar params + seed)
- **Quantum** — always cached (IQAE on StatevectorSampler is fully deterministic; maxsize 128)

The cache is in-process and lost on restart. For multi-worker deployments a shared cache (Redis) is needed.

---

## Circuit Visualisation

Export any circuit to **IBM Quantum Composer** — no IBM account needed to view.

```python
from quantum_price_inference.composer import composer_url, open_in_composer

# get a URL
url = composer_url(circuit)
print(url)

# open directly in the default browser
open_in_composer(circuit)

# async variant — safe inside FastAPI handlers or async notebook cells
from quantum_price_inference.composer import open_in_composer_async
await open_in_composer_async(circuit)
```

The circuit is exported to **OpenQASM 2.0** and encoded as a `?code=` query parameter. No upload, no credentials.

> Composer: <https://quantum.cloud.ibm.com/composer>

---

## Makefile Reference

```
make help              show all targets
make install           uv sync (core only)
make install-dev       uv sync --extra dev
make install-notebook  uv sync --extra dev --extra notebook
make lint              ruff check
make format            ruff format (auto-fix)
make format-check      ruff format --check (CI mode)
make test              pytest --tb=short
make test-unit         unit tests only (no qiskit-finance needed)
make test-integration  integration tests (requires --extra notebook)
make ci                lint + format-check + test
make api               uvicorn --reload on port 8000
make notebook          jupyter notebook
make docker-build      build quantum-price-inference:latest
make docker-run        run container on port 8000
make docker-stop       stop the container
make docker-logs       tail container logs
make deploy-up         start full stack (API + Prometheus + Grafana)
make deploy-down       stop full stack
make deploy-logs       tail all compose service logs
make deploy-ps         show compose service status
make clean             remove __pycache__, .pytest_cache, .ruff_cache, .mypy_cache
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.

## Author

Jose Giori Herran Escobar · [GitHub](https://github.com/josegherran) · [LinkedIn](https://www.linkedin.com/in/joseherran/) · © 2026
