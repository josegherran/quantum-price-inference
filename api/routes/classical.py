"""Classical Monte Carlo estimation endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from quantum_price_inference import (
    NormalUncertaintyModel,
    LinearPayoff,
    classical_estimate_async,
)
from api.schemas import (
    EstimateRequest,
    ClassicalEstimateResponse,
    ConfidenceInterval,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/estimate", tags=["classical"])


@router.post(
    "/classical",
    response_model=ClassicalEstimateResponse,
    summary="Classical Monte Carlo estimation",
    description=(
        "Estimates E[g(X)] by drawing random samples from a Normal uncertainty model "
        "and averaging the linear payoff. Reference baseline for the quantum comparison."
    ),
)
async def estimate_classical(body: EstimateRequest, n_samples: int = 10_000, seed: int | None = None):
    """Run classical Monte Carlo and return the expected payoff.

    Query parameters:
    - **n_samples**: number of random samples (default 10 000)
    - **seed**: optional random seed for reproducibility
    """
    log.info(
        "POST /estimate/classical  mu=%s sigma=%s n_samples=%s",
        body.uncertainty.mu,
        body.uncertainty.sigma,
        n_samples,
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
        result = await classical_estimate_async(model, payoff, n_samples=n_samples, seed=seed)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("Unexpected error in classical estimation")
        raise HTTPException(status_code=500, detail="Estimation failed.") from exc

    return ClassicalEstimateResponse(
        value=result.value,
        std_error=result.std_error,
        confidence_interval=ConfidenceInterval(
            lower=result.confidence_interval[0],
            upper=result.confidence_interval[1],
        ),
        n_samples=result.n_samples,
    )
