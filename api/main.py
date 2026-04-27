"""FastAPI application for the quantum-price-inference REST API."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from quantum_price_inference import configure_logging
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

app.include_router(classical.router)
app.include_router(quantum.router)


@app.get("/health", tags=["meta"], summary="Health check")
async def health():
    """Returns service status."""
    return {"status": "ok"}
