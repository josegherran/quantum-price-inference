"""Shared Pydantic request/response schemas for the quantum-price-inference API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared request body
# ---------------------------------------------------------------------------


class UncertaintyParams(BaseModel):
    """Parameters describing the uncertain variable."""

    mu: float = Field(..., description="Mean of the Normal distribution.", examples=[100.0])
    sigma: float = Field(
        ..., gt=0, description="Standard deviation (must be > 0).", examples=[15.0]
    )
    num_qubits: int = Field(
        3, ge=1, le=8, description="Qubits used to discretise the distribution (1–8)."
    )
    low: float | None = Field(None, description="Lower bound of the support (defaults to mu − 3σ).")
    high: float | None = Field(
        None, description="Upper bound of the support (defaults to mu + 3σ)."
    )


class PayoffParams(BaseModel):
    """Parameters describing the linear business payoff."""

    breakeven: float = Field(
        ..., description="Outcome value at which profit starts.", examples=[85.0]
    )
    slope: float = Field(
        ..., gt=0, description="Profit rate per unit above breakeven.", examples=[0.02]
    )
    max_value: float = Field(1.0, gt=0, description="Saturation cap (normalises payoff to [0, 1]).")


class EstimateRequest(BaseModel):
    """Common request body for both estimation endpoints."""

    uncertainty: UncertaintyParams
    payoff: PayoffParams


# ---------------------------------------------------------------------------
# Shared response fields
# ---------------------------------------------------------------------------


class ConfidenceInterval(BaseModel):
    lower: float
    upper: float


# ---------------------------------------------------------------------------
# Classical endpoint response
# ---------------------------------------------------------------------------


class ClassicalEstimateResponse(BaseModel):
    method: str = "classical_monte_carlo"
    value: float = Field(..., description="Estimated E[g(X)].")
    std_error: float
    confidence_interval: ConfidenceInterval
    n_samples: int


# ---------------------------------------------------------------------------
# Quantum endpoint response
# ---------------------------------------------------------------------------


class QuantumEstimateResponse(BaseModel):
    method: str = "quantum_amplitude_estimation"
    value: float = Field(..., description="Estimated E[g(X)].")
    confidence_interval: ConfidenceInterval
    epsilon: float
    num_oracle_calls: int
