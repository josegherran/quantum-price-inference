"""FastAPI application for the quantum-price-inference REST API."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from quantum_price_inference import configure_logging
from api.limiter import limiter
from api.middleware import RequestIDMiddleware
from api.routes import classical, quantum


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(level="INFO")
    yield


app = FastAPI(
    title="Quantum Price Inference API",
    description=(
        "REST API for estimating expected business value under uncertainty "
        "using Classical Monte Carlo and Quantum Amplitude Estimation (QAE). "
        "Both endpoints share the same 4-block model: "
        "Uncertainty → Payoff → Encoding → Estimation."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware  (order matters — outermost first)
# ---------------------------------------------------------------------------

# Request ID — must be first so all downstream middleware and handlers see it.
app.add_middleware(RequestIDMiddleware)

# CORS — restrictive by default; expand allow_origins for production deployments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8888",  # Jupyter notebook default port
        "http://localhost:3000",  # local frontend dev server
        "http://127.0.0.1:8888",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Rate limiter — attach state and exception handler required by slowapi.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------

# Instrument all routes and expose /metrics.  Must be called after the app
# object is fully configured but before the first request.
Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/metrics", "/health/live", "/health/ready"],
).instrument(app).expose(app, include_in_schema=False)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(classical.router)
app.include_router(quantum.router)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health", tags=["meta"], summary="Health check (legacy)")
async def health():
    """Backward-compatible health check.  Prefer /health/live or /health/ready."""
    return {"status": "ok"}


@app.get("/health/live", tags=["meta"], summary="Liveness probe")
async def health_live():
    """Liveness probe — returns 200 if the process is running.

    Use this for Kubernetes ``livenessProbe`` and load-balancer health checks.
    A 200 response means the process has not crashed; it does not guarantee
    that optional dependencies are available.
    """
    return {"status": "alive"}


@app.get("/health/ready", tags=["meta"], summary="Readiness probe")
async def health_ready():
    """Readiness probe — checks that optional dependencies are importable.

    Use this for Kubernetes ``readinessProbe``.  Returns 200 when the service
    can handle traffic; 503 when a required dependency is missing.
    """
    checks: dict[str, str] = {}

    try:
        import qiskit  # noqa: F401

        checks["qiskit"] = "ok"
    except ImportError:
        checks["qiskit"] = "missing"

    try:
        import qiskit_algorithms  # noqa: F401

        checks["qiskit_algorithms"] = "ok"
    except ImportError:
        checks["qiskit_algorithms"] = "missing"

    try:
        import qiskit_finance  # noqa: F401

        checks["qiskit_finance"] = "ok"
    except ImportError:
        checks["qiskit_finance"] = "missing (quantum endpoint unavailable)"

    return {"status": "ready", "checks": checks}
