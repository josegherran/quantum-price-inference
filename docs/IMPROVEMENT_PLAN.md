# Improvement Plan — quantum-price-inference

## Executive Summary

`quantum-price-inference` is a well-structured simulation system with a clean 4-block architecture,
clear separation between the core library and its three delivery interfaces (REST API, Jupyter,
marimo), and a solid foundation of 90 tests. Waves 1 (security/correctness), 2 (observability/
performance), and 3.1 (Docker + Compose + Grafana) are complete. The system is now safe to
expose beyond localhost, fully observable, and deployable as a container with a pre-built
Grafana dashboard.

The remaining gaps fall into four themes:

1. **Automation** (Wave 3): No CI pipeline, no environment-based config, no async job pattern,
   no mypy enforcement — the system requires manual process for every quality gate.
2. **API feature completeness** (Wave 4): Both route handlers hardcode `NormalUncertaintyModel +
   LinearPayoff`, silently ignoring `LogNormalUncertaintyModel` and `ThresholdPayoff` that already
   exist in the library. The classical CI level is hardcoded at 95 % while the quantum endpoint
   exposes a configurable `alpha`. There is no API versioning.
3. **Production hardening** (Wave 5): No authentication, in-process LRU caches fragment across
   workers when `QPI_WORKERS > 1`, no Qiskit 3.0 migration path, no Kubernetes manifests.
4. **Qiskit 3.0 migration** (Wave 5): `LinearAmplitudeFunction`, `BlueprintCircuit`,
   `GroverOperator`, and `MCXGate` are deprecated in Qiskit 2.x and will be removed in 3.0.
   The migration window is closing.

This plan extends the original three waves with two additional waves (4 and 5) ordered by business
value relative to implementation effort.

---

## Implementation Progress

| Wave | Status | Completed | Remaining |
|---|---|---|---|
| Wave 1 — Correctness, Security, Reliability | ✅ Complete | 1.1, 1.2, 1.3, 1.4, 1.5, 1.6 | — |
| Wave 2 — Observability and Performance | ✅ Complete | 2.1, 2.2, 2.3, 2.4, 2.5 | — |
| Wave 3 — Portability, Scalability, Maintainability | 🔧 In progress | 3.1 | 3.2, 3.3, 3.4, 3.5 |
| Wave 4 — API Feature Completeness | ✅ Complete | 4.1, 4.2, 4.3, 4.4 | — |
| Wave 5 — Production Hardening | 📋 Planned | — | 5.1, 5.2, 5.3, 5.4 |

---

## Current State and Gaps

### What works well

- Clean layered architecture: `quantum_price_inference/` is a pure library; API and notebooks are
  thin consumers.
- Async pattern applied consistently: every engine exposes both `estimate` and `estimate_async`;
  route handlers are `async def` and call the `_async` variant.
- Logging correctly deferred: modules declare `log = logging.getLogger(__name__)` at module level;
  `configure_logging()` is called once in the lifespan.
- LRU caching in both engines: quantum always cached (deterministic); classical cached when `seed`
  is provided.
- Full observability stack: structured JSON logs, per-request `X-Request-ID`, Prometheus counters,
  pre-built Grafana dashboard with 9 panels.
- Container packaging: multi-stage Docker image, docker-compose with Prometheus + Grafana, alert
  rules, `deploy/.env.example`.

### Remaining gaps by quality attribute

| Attribute | Gap | Wave |
|---|---|---|
| **Maintainability** | No CI pipeline — all quality gates (lint, format, tests) are manual. | 3 |
| **Cost** | Config (log level, CORS, rate limits, timeout) is hardcoded; changing requires a code edit. | 3 |
| **Scalability** | No async job pattern for long-running quantum jobs; clients hold HTTP connections open for up to 30 s. | 3 |
| **Maintainability** | `mypy` not in dev deps and not enforced; `estimate()` parameters in `classical.py` and `quantum.py` are untyped. | 3 |
| **Maintainability** | API route handlers hardcode `NormalUncertaintyModel + LinearPayoff`; `LogNormalUncertaintyModel` and `ThresholdPayoff` are inaccessible via the API despite existing in the library. | 4 |
| **Maintainability** | Classical endpoint CI is hardcoded at 95 % (1.96 × stderr); quantum endpoint exposes configurable `alpha`. Inconsistent interfaces. | 4 |
| **Maintainability** | No API versioning — any breaking schema change breaks all existing clients. | 4 |
| **Observability** | No OpenTelemetry tracing spans around estimation calls — Prometheus shows rates/latency but not circuit depth or IQAE iteration count per span. | 4 |
| **Security** | No authentication — any caller can hit the API; rate limiting constrains frequency but does not identify or authorize callers. | 5 |
| **Scalability** | In-process LRU caches fragment across workers when `QPI_WORKERS > 1` — the same parameter tuple may be recomputed N times on an N-worker deployment. | 5 |
| **Maintainability** | `LinearAmplitudeFunction`, `BlueprintCircuit`, `GroverOperator`, and `MCXGate` are deprecated in Qiskit 2.x. No migration plan before Qiskit 3.0 removal. | 5 |
| **Portability** | No Kubernetes manifests (Deployment, Service, HPA, ConfigMap) — only docker-compose is provided. | 5 |

---

## Quality Characteristics Matrix

| Characteristic | Baseline (1–5) | Wave 1 | Wave 2 | Wave 3 | Wave 4 Target | Wave 5 Target |
|---|---|---|---|---|---|---|
| Security | 2 | **4** ✅ | 4 | 4 | 4 | **5** |
| Availability | 2 | **3** ✅ | **4** ✅ | 4 | 4 | **5** |
| Performance | 2 | 2 | **4** ✅ | 4 | 4 | **5** |
| Observability | 1 | 1 | **4** ✅ | 4 | **5** | 5 |
| Maintainability | 3 | **4** ✅ | **4** ✅ | **5** | **5** | 5 |
| Portability | 1 | 1 | 1 | **4** ✅ | 4 | **5** |
| Scalability | 2 | 2 | 2 | **3** | 3 | **4** |
| Cost | 2 | **3** ✅ | **4** ✅ | **5** | 5 | 5 |

---

## Detailed Waves

---

### Wave 1 — Correctness, Security, and Baseline Reliability ✅ Complete

**Goal:** Make the system safe to expose beyond localhost.
**Actual effort:** ~1 day. All 6 items delivered; 56 tests passing.

| Item | Description | Delivered |
|---|---|---|
| 1.1 | Fix `composer.py` module-level import violation | All `qiskit` imports moved inside functions |
| 1.2 | Add API-layer input bounds | `n_samples` 100–100 000; `epsilon` 0.001–0.1; `alpha` 0.01–0.5 via `fastapi.Query` |
| 1.3 | Add rate limiting | `slowapi` 30 req/min classical, 10 req/min quantum; shared `api/limiter.py` |
| 1.4 | Add CORS policy | `CORSMiddleware` with restrictive localhost defaults |
| 1.5 | Add estimation timeout | `asyncio.wait_for(timeout=30.0)` → HTTP 504 on timeout |
| 1.6 | Add missing quantum engine tests | `tests/test_quantum.py` with 14 tests |

---

### Wave 2 — Observability and Performance ✅ Complete

**Goal:** Make the system operable in a shared environment.
**Actual effort:** ~3 days. All 5 items delivered; 90 tests passing.

| Item | Description | Delivered |
|---|---|---|
| 2.1 | Structured logging with request IDs | `_JsonFormatter`, `_RequestIDFilter`, `RequestIDMiddleware` (UUID4 per request) |
| 2.2 | Prometheus metrics endpoint | `prometheus-fastapi-instrumentator`; `/metrics`; `quantum_oracle_calls_total`, `classical_samples_total` counters |
| 2.3 | Result caching for deterministic simulations | LRU cache 256 (classical, seeded) + 128 (quantum, always) |
| 2.4 | `/health` liveness vs readiness split | `/health/live`, `/health/ready` (checks qiskit importability) |
| 2.5 | Expanded test coverage | 34 new tests; `ThresholdPayoff.circuit()`, `LogNormalUncertaintyModel`, `composer_url`, API quantum endpoint, cache behaviour, `/metrics` |

---

### Wave 3 — Portability, Scalability, and Baseline Maintainability 🔧 In progress

**Goal:** Package the system for deployment, add CI, and externalise configuration.
**Estimated effort for remaining items:** 3–4 days.

---

#### 3.1 Dockerfile and docker-compose ✅ Complete

**Delivered:**
- `deploy/Dockerfile` — multi-stage, Python 3.13-slim, `uv` pinned, non-root `qpi` user,
  `curl` HEALTHCHECK on `/health/live`, `QPI_WORKERS` env var
- `deploy/docker-compose.yml` — API + Prometheus v3.4.0 + Grafana v12.0.1
- `deploy/.env.example` — config template; `deploy/.env` gitignored
- `deploy/prometheus.yml` + `deploy/prometheus-alerts.yml` — 4 alert rules
- `deploy/grafana/provisioning/` — auto-provisioned datasource + 9-panel dashboard
- `Makefile` — all docker/deploy targets; `ci` target chains lint + format-check + test

**Verified:** image builds; `curl http://localhost:8000/health/live` returns `{"status":"alive"}`.

---

#### 3.2 CI pipeline (GitHub Actions)

**Problem:** No automated checks. Regressions are caught only when a developer manually runs
`uv run pytest`. The `make ci` target exists but is never triggered automatically.

**Fix:** Add `.github/workflows/ci.yml` with three jobs:

1. **lint** — `uv run ruff check . && uv run ruff format --check .`
2. **type-check** — `uv run mypy quantum_price_inference/ api/` (after 3.5 adds mypy)
3. **test** — `uv run pytest --tb=short` matrix: Python 3.10 + 3.12

Trigger on `push` to any branch and `pull_request` to `main`. Cache the uv download and
`.venv` by hashing `uv.lock` to keep runs under 60 s.

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true
          cache-dependency-glob: "uv.lock"
      - run: uv sync --extra dev --extra notebook
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run pytest --tb=short
```

**Effort:** 0.5 days. **Risk:** Low — additive, no runtime impact.

---

#### 3.3 Environment-based configuration

**Problem:** Log level, CORS origins, rate limits, and the 30 s quantum timeout are hardcoded.
Changing any value requires a code edit and redeploy. The `deploy/.env.example` documents several
`QPI_*` variables but the application never reads them — `api/main.py` calls
`configure_logging(level="INFO")` directly, ignoring `QPI_LOG_LEVEL`.

**Fix:** Add `api/config.py` using `pydantic-settings`. Replace all hardcoded values.

```python
# api/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    log_level: str = "INFO"
    log_json: bool = False
    cors_origins: list[str] = ["http://localhost:8888", "http://localhost:3000",
                                "http://127.0.0.1:8888", "http://127.0.0.1:3000"]
    classical_rate_limit: str = "30/minute"
    quantum_rate_limit: str = "10/minute"
    estimation_timeout_seconds: float = 30.0
    quantum_cache_maxsize: int = 128
    classical_cache_maxsize: int = 256

    class Config:
        env_prefix = "QPI_"

settings = Settings()
```

Add `pydantic-settings>=2.0` to the core dependencies in `pyproject.toml`. Replace the
`_ESTIMATION_TIMEOUT_SECONDS` constant in `api/routes/quantum.py` with `settings.estimation_timeout_seconds`.
Update `deploy/.env.example` to list every `QPI_*` variable with its default.

**Effort:** 1 day. **Risk:** Low — backward-compatible; defaults match current hardcoded values.

---

#### 3.4 Async job pattern for long-running quantum estimation

**Problem:** For small `epsilon` values, IQAE can take tens of seconds. Holding an HTTP connection
open that long is fragile: client timeouts, load balancer idle timeouts, and poor UX in the
workshop demo (the browser spinner runs until the 30 s timeout fires or the result arrives).

**Fix:** Add an async job variant alongside the existing synchronous endpoint:

- `POST /estimate/quantum/async` — returns `202 Accepted` with a `job_id` immediately.
- `GET /jobs/{job_id}` — returns `{"status": "pending"}` or the completed result.

Jobs are stored in an in-process `dict[str, asyncio.Task]` initially (acceptable for single-process
workshop use; replace with Redis in Wave 5 for multi-worker deployments). The existing synchronous
`POST /estimate/quantum` is preserved unchanged.

```python
# api/routes/quantum.py — async job variant (addition)
_jobs: dict[str, asyncio.Task] = {}

@router.post("/quantum/async", status_code=202, tags=["quantum"])
async def estimate_quantum_async_job(request: Request, body: EstimateRequest,
                                     epsilon: float = Query(default=0.01, ge=0.001, le=0.1),
                                     alpha: float = Query(default=0.05, ge=0.01, le=0.5)):
    job_id = str(uuid.uuid4())
    model = NormalUncertaintyModel(...)
    payoff = LinearPayoff(...)
    _jobs[job_id] = asyncio.create_task(
        quantum_estimate_async(model, payoff, epsilon=epsilon, alpha=alpha)
    )
    return {"job_id": job_id, "status": "pending", "poll_url": f"/jobs/{job_id}"}

@router.get("/jobs/{job_id}", tags=["jobs"])
async def get_job(job_id: str):
    task = _jobs.get(job_id)
    if task is None:
        raise HTTPException(404, "Job not found")
    if not task.done():
        return {"status": "pending"}
    if task.exception():
        raise HTTPException(500, str(task.exception()))
    result = task.result()
    del _jobs[job_id]  # clean up on first retrieval
    return {"status": "complete", "result": result}
```

**Effort:** 1.5 days. **Risk:** Medium — in-process job store is lost on restart; documented
limitation.

---

#### 3.5 mypy strict mode and type annotations

**Problem:** `.mypy_cache/3.13/` exists but `mypy` is not in `pyproject.toml` dev dependencies
and is not run anywhere. `estimate()` in `classical.py` and `quantum.py` accepts untyped `model`
and `payoff` parameters — type errors in callers are invisible until runtime.

**Fix:**
1. Add `mypy>=1.10` to the `dev` extra in `pyproject.toml`.
2. Add `[tool.mypy]` to `pyproject.toml`:
   ```toml
   [tool.mypy]
   python_version = "3.10"
   disallow_untyped_defs = true
   warn_return_any = true
   ignore_missing_imports = true
   ```
3. Add Protocol types in `quantum_price_inference/` for `UncertaintyModel` and `PayoffFunction`
   so `estimate()` signatures are typed without importing concrete classes.
4. Wire `uv run mypy quantum_price_inference/ api/` into the CI job from 3.2.

**Effort:** 1 day. **Risk:** Low — type errors are surfaced incrementally; fix before gating CI.

---

### Wave 4 — API Feature Completeness ✅ Complete

**Goal:** Close the gap between the library's capabilities and what the API exposes. Make the
API consistent and versionable.

**Actual effort:** ~1 day. All 4 items delivered; 102 tests passing.

---

#### 4.1 Expose `LogNormalUncertaintyModel` in the API ✅

**Delivered:** Added `distribution_type: Literal["normal", "lognormal"]` discriminator to
`UncertaintyParams` in `api/schemas.py` (default `"normal"` — backward-compatible). Both route
handlers dispatch via `_UNCERTAINTY_MODELS = {"normal": NormalUncertaintyModel, "lognormal":
LogNormalUncertaintyModel}`. The quantum LRU cache key in `quantum.py._estimate_cached` now
includes `distribution_type` and `payoff_type` to prevent Normal/LogNormal collisions on
identical numeric parameters. Cache detection uses `type(model).__name__` rather than importing
concrete classes, keeping `quantum.py` import-clean.

---

#### 4.2 Expose `ThresholdPayoff` in the API ✅

**Delivered:** Added `payoff_type: Literal["linear", "threshold"]` (default `"linear"`) and
`threshold: float | None` to `PayoffParams`. A `@model_validator(mode="after")` enforces that
`threshold` is present when `payoff_type == "threshold"` and that `slope > 0` when
`payoff_type == "linear"`, returning HTTP 422 otherwise. Both route handlers dispatch via
`if body.payoff.payoff_type == "threshold": ThresholdPayoff(...) else: LinearPayoff(...)`.

---

#### 4.3 Consistent `alpha` / confidence level on the classical endpoint ✅

**Delivered:** Added `alpha: float = Query(default=0.05, ge=0.01, le=0.5)` to
`POST /estimate/classical`. The hardcoded `1.96` in `_estimate_uncached` was replaced with
`_z_score(alpha)`, a helper that uses `math.erfinv` (Python ≥ 3.12), falls back to
`scipy.special.erfinv` (Python 3.10–3.11, scipy already transitively installed by
qiskit-algorithms), or falls back to an Abramowitz & Stegun rational approximation as a
last resort. `alpha` is threaded through `_estimate_cached` / `_estimate_uncached` /
`estimate_async` signatures and included in the LRU cache key.

---

#### 4.4 API versioning prefix ✅

**Delivered:** All estimation routers are now mounted under `/v1` prefix in `api/main.py`.
Un-prefixed routes are preserved as deprecated aliases (`include_in_schema=False`) so existing
clients (workshop notebooks, curl examples) continue working without change. The canonical
OpenAPI schema at `/docs` shows only `/v1` routes.

**Test suite after Wave 4:** 102 passed, 0 failed. Ruff clean on all source files.

---

### Wave 5 — Production Hardening

**Goal:** Secure, scale, and future-proof the system for real-world deployments beyond the
workshop context.

**Estimated effort:** 5–7 days.

---

#### 5.1 API key authentication

**Problem:** The API has no authentication. Rate limiting constrains request frequency per IP
but does not identify callers, prevent credential sharing, or allow per-client quota management.
For a workshop deployment accessible over a network, any attendee who discovers the URL can
exhaust the quantum endpoint for other attendees (10 req/min per IP is easily circumvented
from multiple machines).

**Fix:** Add optional API key authentication via an `X-API-Key` header:

```python
# api/auth.py
from fastapi import Header, HTTPException, Security
from fastapi.security import APIKeyHeader

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str | None = Security(_API_KEY_HEADER)) -> str | None:
    if settings.api_key is None:
        return None  # auth disabled; open access for local dev
    if api_key != settings.api_key:
        raise HTTPException(401, "Invalid or missing X-API-Key")
    return api_key
```

Add `api_key: str | None = None` to `Settings` in `api/config.py` (3.3 prerequisite). When
`QPI_API_KEY` is unset, authentication is disabled (preserving existing local-dev behaviour).
When set, all `/estimate/*` routes require the header.

**Effort:** 1 day. **Risk:** Low — opt-in via env var; disabled by default.

---

#### 5.2 Redis-backed shared cache

**Problem:** The in-process LRU caches in `classical.py` and `quantum.py` fragment across
workers. With `QPI_WORKERS=4`, the same parameter tuple may be computed 4 times — once per
worker — before any worker warms its cache. The `deploy/docker-compose.yml` uses the default
single-worker configuration, masking this issue, but the `Dockerfile` exposes `QPI_WORKERS`.

**Fix:** Extract the cache into a pluggable backend:

1. Add an abstract `CacheBackend` protocol with `get(key: str)` and `set(key: str, value)`.
2. Implement `LRUBackend` (current behaviour) and `RedisBackend` (using `redis-py` async client).
3. Select backend in `api/config.py`:
   ```python
   redis_url: str | None = None  # QPI_REDIS_URL; if None, use in-process LRU
   ```
4. Add `redis[asyncio]>=5.0` to a new `cache` optional extra.
5. Update `deploy/docker-compose.yml` to include a `redis:7-alpine` service when
   `QPI_REDIS_URL` is set.

This change is scoped to the API layer — `classical.py` and `quantum.py` keep their
in-process LRU caches for notebook and CLI use.

**Effort:** 2 days. **Risk:** Medium — introduces Redis as an optional infrastructure dependency;
existing deployments are unaffected (default `LRUBackend`).

---

#### 5.3 Qiskit 3.0 migration

**Problem:** Multiple classes used in `payoff.py` are deprecated in Qiskit 2.x and will be
removed in Qiskit 3.0. The `uv.lock` pins current versions, but the migration window is open
now. Delaying until Qiskit 3.0 is released creates a forced breaking change with no runway.

Affected symbols (from `payoff.py`):
- `LinearAmplitudeFunction` → use `qiskit_finance.circuit.library.LinearAmplitudeFunction` v2
  API or a hand-rolled `RealAmplitudeEstimation` circuit.
- `BlueprintCircuit` → use `QuantumCircuit` directly.
- `MCXGate` → use `MCXGrayCode` or the standard `MCXGate` via `qiskit.circuit.library`.
- `GroverOperator` → migrate to `qiskit.circuit.library.GroverOperator` (moved, not removed).

**Fix:**
1. Run `python -W error::DeprecationWarning -m pytest` and capture the full deprecation report.
2. For each warning, identify the replacement in the Qiskit 3.0 migration guide.
3. Update `payoff.py` and the relevant integration tests.
4. Pin `qiskit>=2.0,<3.0` in `pyproject.toml` during migration; remove the upper bound once
   all tests pass on 3.0.
5. Add a CI matrix entry for `qiskit==2.*` and `qiskit==3.*` after the migration.

**Effort:** 2–3 days (uncertainty: depends on `qiskit-finance` migration completeness).
**Risk:** High — `qiskit-finance` may not have a Qiskit 3.0-compatible release yet; track
the `qiskit-finance` issue tracker and plan a fallback (hand-rolled circuits).

---

#### 5.4 Kubernetes manifests

**Problem:** Only docker-compose is provided. Teams deploying on Kubernetes (EKS, GKE, AKS)
must write their own manifests. Without an HPA, the system cannot scale horizontally in
response to workshop traffic spikes; without a `ConfigMap`, the `QPI_*` environment variables
have no declarative home.

**Fix:** Add `deploy/k8s/` with:

- `deployment.yaml` — 2-replica `Deployment` with `QPI_WORKERS=1` (let HPA handle parallelism
  at the pod level rather than within a pod), `livenessProbe` on `/health/live`,
  `readinessProbe` on `/health/ready`.
- `service.yaml` — `ClusterIP` Service, port 8000.
- `configmap.yaml` — `QPI_LOG_LEVEL`, `QPI_LOG_JSON=true`, `QPI_CORS_ORIGINS` for prod.
- `hpa.yaml` — `HorizontalPodAutoscaler` targeting 70 % CPU, min 2 / max 10 replicas.
- `ingress.yaml` — annotation-driven TLS termination (cert-manager).

**Effort:** 1.5 days. **Risk:** Low — additive artefacts; no runtime changes.

---

## Wave Dependencies

```
Wave 1 (correctness/security) ✅ Complete
  ├── 1.1–1.6  ✅

Wave 2 (observability/performance) ✅ Complete
  ├── 2.1–2.5  ✅

Wave 3 (portability/scalability) — 3.1 done; 3.2–3.5 pending
  ├── 3.1 (Docker)         ✅ — gates 3.2 CI (image build step)
  ├── 3.2 (CI)             — requires 1.6 ✅ + 2.5 ✅; gates 3.5 (mypy in CI)
  ├── 3.3 (env config)     — requires 1.3 ✅ + 1.5 ✅; gates 5.1 (api_key setting)
  ├── 3.4 (async jobs)     — requires 2.2 ✅ (metrics for job queue depth)
  └── 3.5 (mypy)           — requires 3.2 (CI to enforce); gates 4.x (typed dispatch)

Wave 4 (API feature completeness) — blocked on 3.5 for type safety
  ├── 4.1 (LogNormal API)  — requires 3.5 (typed dispatch); gates cache key update
  ├── 4.2 (ThresholdPayoff API) — requires 4.1 (discriminator pattern established)
  ├── 4.3 (classical alpha) — independent; no blockers
  └── 4.4 (API versioning) — requires 4.1 + 4.2 (stable schema before versioning)

Wave 5 (production hardening) — blocked on Wave 3 completion
  ├── 5.1 (API key auth)   — requires 3.3 (settings module)
  ├── 5.2 (Redis cache)    — requires 3.3 (redis_url setting) + 3.4 (multi-worker awareness)
  ├── 5.3 (Qiskit 3.0)     — independent; time-sensitive (Qiskit 3.0 release date)
  └── 5.4 (K8s manifests)  — requires 3.1 ✅ + 3.3 (ConfigMap values)
```

**Critical path to production:** 3.3 → 5.1 → 5.2 (security + multi-worker cache).
**Critical path for maintenance:** 3.2 → 3.5 → 5.3 (CI + mypy + Qiskit 3.0 migration).

---

## Follow-up Metrics

| Metric | Baseline | Wave 1 | Wave 2 | Wave 3 | Wave 4 | Wave 5 |
|---|---|---|---|---|---|---|
| Test count | 42 | **56** ✅ | **90** ✅ | 100+ | **102** ✅ | 115+ |
| Test coverage (core library) | ~70 % | **~85 %** ✅ | **~90 %** ✅ | 92 % | **~92 %** ✅ | 95 % |
| Import-safe without extras | No | **Yes** ✅ | Yes | Yes | Yes | Yes |
| API input validation (422) | Partial | **Full** ✅ | Full | Full | Full | Full |
| Rate-limited 429 responses | No | **Yes** ✅ | Yes | Yes | Yes | Yes |
| Estimation timeout enforced | No | **Yes (30 s)** ✅ | Yes | **Configurable** | Configurable | Configurable |
| Structured log lines per request | 0 | 0 | **≥ 3 with request_id** ✅ | ≥ 3 | ≥ 3 | ≥ 3 |
| Prometheus scrape endpoint | No | No | **Yes** ✅ | Yes | Yes + tracing | Yes |
| Docker image builds cleanly | No | No | No | **Yes** ✅ | Yes | Yes |
| CI passes on PR (lint + test) | No | No | No | **Yes** | Yes | Yes |
| mypy errors in core library | Unknown | Unknown | Unknown | **0** | 0 | 0 |
| LogNormal + ThresholdPayoff via API | No | No | No | No | **Yes** ✅ | Yes |
| Consistent `alpha` on both endpoints | No | No | No | No | **Yes** ✅ | Yes |
| Authentication (API key) | No | No | No | No | No | **Yes** |
| Shared cache across workers | No | No | No | No | No | **Yes (Redis)** |
| Qiskit 3.0 compatibility | Unknown | Unknown | Unknown | Unknown | Unknown | **Yes** |
| Kubernetes manifests | No | No | No | No | No | **Yes** |
| p95 quantum latency (ε=0.01) cached | Unmeasured | Unmeasured | **Measured** ✅ | Measured | Measured | Measured |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Status | Mitigation |
|---|---|---|---|---|
| `qiskit-algorithms` API changes break `quantum.py` | Medium | High | Open | Pin exact versions in `uv.lock`; integration tests in 1.6 ✅ catch regressions. Abstract `StatevectorSampler` behind a factory function (Wave 3.5 typing work). |
| `LinearAmplitudeFunction` / `MCXGate` removed in Qiskit 3.0 | High | High | **Time-sensitive** | Start 5.3 migration now; `qiskit-finance` may not be Qiskit-3.0-ready — prepare hand-rolled circuit fallback. |
| LRU cache grows unbounded in long-running single-worker process | Low | Medium | Mitigated — maxsize set ✅ | Add `/admin/cache/clear` endpoint protected by `X-Admin-Key` header (Wave 5.1 builds the auth infrastructure). |
| Multi-worker cache fragmentation (`QPI_WORKERS > 1`) | High | Medium | Open (Wave 5.2) | Document that `QPI_WORKERS > 1` defeats in-process caching; mitigate with Redis backend (5.2). |
| Rate limiter blocks legitimate workshop participants sharing an IP | Low | Medium | Mitigated ✅ | Per-IP limits with generous burst; document how to whitelist IPs for workshop environments. After 5.1, rate-limit per API key instead of per IP. |
| Async job store (3.4) lost on restart | High | Low (demo context) | Open (Wave 3.4) | Document clearly; provide Redis-backed store in Wave 5.2. |
| Classical CI hardcoded at 95 % inconsistent with quantum | Medium | Low | Open (Wave 4.3) | Fix in 4.3; until then, document that classical CI is always 95 %. |
| API schema changes break distributed notebook copies | Medium | Medium | Open (Wave 4.4) | Introduce `/v1` prefix (4.4) before any breaking schema change (4.1, 4.2). |
| `configure_logging` replaces all root handlers | Low | Low | Open | Add `replace_handlers: bool = True` param so callers can opt out (useful when integrating with logging frameworks). |
| No request body size limit | Low | Low | Open | FastAPI/uvicorn default is 1 MB; document and consider lowering to 64 KB for estimation endpoints (bodies are tiny). |

---

## Conclusion

The project has reached a strong operational baseline: it is secure, observable, and
containerised. The 90-test suite provides confidence for ongoing changes.

**Recommended next steps in priority order:**

1. **3.2 CI** — highest leverage; prevents regressions from all previous waves automatically.
2. **3.3 Environment config** — unblocks 5.1 (auth) and makes the deployed container actually
   respect `QPI_*` variables that are already documented but ignored.
3. **5.3 Qiskit 3.0 migration** — time-sensitive; the deprecation window is open and the
   removal date is fixed by the Qiskit upstream release schedule.
4. **4.1 + 4.2** (LogNormal + ThresholdPayoff in API) — closes the gap between library
   capability and API exposure; high workshop value, low risk.
5. **5.1 API key auth** — required before any internet-accessible deployment.
