"""Shared Pydantic request/response schemas for the quantum-price-inference API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Shared request body
# ---------------------------------------------------------------------------


class UncertaintyParams(BaseModel):
    """Parameters describing the uncertain variable."""

    distribution_type: Literal["normal", "lognormal"] = Field(
        "normal",
        description=(
            "Distribution family. "
            "'normal' uses NormalUncertaintyModel (symmetric bell-curve, e.g. cost or FX). "
            "'lognormal' uses LogNormalUncertaintyModel (right-skewed, always-positive, "
            "e.g. demand or equity price). "
            "mu and sigma are the log-space parameters for 'lognormal'."
        ),
    )
    mu: float = Field(
        ...,
        description="Mean of the distribution (log-space mean for lognormal).",
        examples=[100.0],
    )
    sigma: float = Field(
        ...,
        gt=0,
        description="Standard deviation (must be > 0; log-space std for lognormal).",
        examples=[15.0],
    )
    num_qubits: int = Field(
        3, ge=1, le=8, description="Qubits used to discretise the distribution (1–8)."
    )
    low: float | None = Field(
        None,
        description="Lower bound of the support (defaults to mu − 3σ for normal, exp(mu − 3σ) for lognormal).",
    )
    high: float | None = Field(
        None,
        description="Upper bound of the support (defaults to mu + 3σ for normal, exp(mu + 3σ) for lognormal).",
    )


class PayoffParams(BaseModel):
    """Parameters describing the business payoff function."""

    payoff_type: Literal["linear", "threshold"] = Field(
        "linear",
        description=(
            "Payoff family. "
            "'linear' — g(x) = slope × (x − breakeven) clipped to [0, max_value]; "
            "models margin or benefit linear in the outcome. "
            "'threshold' — g(x) = 1 if x ≥ threshold else 0; "
            "models binary events (SLA breach, churn, cost overrun)."
        ),
    )
    breakeven: float = Field(
        ..., description="Outcome value at which profit starts (linear payoff).", examples=[85.0]
    )
    slope: float = Field(
        0.02,
        ge=0,
        description="Profit rate per unit above breakeven (linear payoff only; ignored for threshold).",
        examples=[0.02],
    )
    threshold: float | None = Field(
        None,
        description="Outcome value above which the binary event fires (threshold payoff only).",
        examples=[100.0],
    )
    max_value: float = Field(1.0, gt=0, description="Saturation cap (normalises payoff to [0, 1]).")

    @model_validator(mode="after")
    def _check_payoff_params(self) -> "PayoffParams":
        if self.payoff_type == "linear" and self.slope <= 0:
            raise ValueError("slope must be positive for linear payoff")
        if self.payoff_type == "threshold" and self.threshold is None:
            raise ValueError("threshold is required when payoff_type is 'threshold'")
        return self


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
