"""FastAPI application for the quantum-price-inference REST API."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from quantum_price_inference import configure_logging
from api.limiter import limiter
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
# Middleware
# ---------------------------------------------------------------------------

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
# Routers
# ---------------------------------------------------------------------------
app.include_router(classical.router)
app.include_router(quantum.router)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health", tags=["meta"], summary="Health check")
async def health():
    """Returns service status."""
    return {"status": "ok"}
