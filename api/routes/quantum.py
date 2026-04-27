"""Quantum Amplitude Estimation endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from quantum_price_inference import (
    NormalUncertaintyModel,
    LinearPayoff,
    quantum_estimate_async,
)
from api.schemas import (
    EstimateRequest,
    QuantumEstimateResponse,
    ConfidenceInterval,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/estimate", tags=["quantum"])


@router.post(
    "/quantum",
    response_model=QuantumEstimateResponse,
    summary="Quantum Amplitude Estimation",
    description=(
        "Estimates E[g(X)] using Iterative Quantum Amplitude Estimation (IQAE). "
        "Runs on a statevector simulator — no IBM account required. "
        "Requires the `qiskit-finance` optional dependency (`uv sync --extra notebook`)."
    ),
)
async def estimate_quantum(
    body: EstimateRequest,
    epsilon: float = 0.01,
    alpha: float = 0.05,
):
    """Run Quantum Amplitude Estimation and return the expected payoff.

    Query parameters:
    - **epsilon**: target precision for the amplitude estimate (default 0.01)
    - **alpha**: significance level for the confidence interval (default 0.05 → 95% CI)
    """
    log.info(
        "POST /estimate/quantum  mu=%s sigma=%s epsilon=%s alpha=%s",
        body.uncertainty.mu,
        body.uncertainty.sigma,
        epsilon,
        alpha,
    )
    try:
        model = NormalUncertaintyModel(
            mu=body.uncertainty.mu,
            sigma=body.uncertainty.sigma,
            num_qubits=body.uncertainty.num_qubits,
            low=body.uncertainty.low,
            high=body.uncertainty.high,
        )
        payoff = LinearPayoff(
            breakeven=body.payoff.breakeven,
            slope=body.payoff.slope,
            max_value=body.payoff.max_value,
        )
        result = await quantum_estimate_async(model, payoff, epsilon=epsilon, alpha=alpha)
    except ImportError as exc:
        raise HTTPException(
            status_code=501,
            detail=(
                "qiskit-finance is required for the quantum endpoint. "
                "Install it with: uv sync --extra notebook"
            ),
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("Unexpected error in quantum estimation")
        raise HTTPException(status_code=500, detail="Estimation failed.") from exc

    return QuantumEstimateResponse(
        value=result.value,
        confidence_interval=ConfidenceInterval(
            lower=result.confidence_interval[0],
            upper=result.confidence_interval[1],
        ),
        epsilon=result.epsilon,
        num_oracle_calls=result.num_oracle_calls,
    )
