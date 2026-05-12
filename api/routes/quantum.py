"""Quantum Amplitude Estimation endpoint."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Query, Request

from api.limiter import limiter
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

# Timeout for a single IQAE run.  Configurable via QPI_ESTIMATION_TIMEOUT_SECONDS
# (Wave 3 environment config); hardcoded here for Wave 1.
_ESTIMATION_TIMEOUT_SECONDS = 30.0


@router.post(
    "/quantum",
    response_model=QuantumEstimateResponse,
    summary="Quantum Amplitude Estimation",
    description=(
        "Estimates E[g(X)] using Iterative Quantum Amplitude Estimation (IQAE). "
        "Runs on a statevector simulator — no IBM account required. "
        "Requires the `qiskit-finance` optional dependency (`uv sync --extra notebook`).\n\n"
        "**Bounds:** `epsilon` is in [0.001, 0.1]; `alpha` is in [0.01, 0.5]. "
        "Requests time out after 30 s."
    ),
)
@limiter.limit("10/minute")
async def estimate_quantum(
    request: Request,
    body: EstimateRequest,
    epsilon: float = Query(
        default=0.01,
        ge=0.001,
        le=0.1,
        description="Target precision for the amplitude estimate (0.001–0.1).",
    ),
    alpha: float = Query(
        default=0.05,
        ge=0.01,
        le=0.5,
        description="Significance level for the confidence interval (0.01–0.5).",
    ),
):
    """Run Quantum Amplitude Estimation and return the expected payoff.

    Query parameters:
    - **epsilon**: target precision (0.001–0.1, default 0.01)
    - **alpha**: significance level for the CI (0.01–0.5, default 0.05 → 95 % CI)
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
        result = await asyncio.wait_for(
            quantum_estimate_async(model, payoff, epsilon=epsilon, alpha=alpha),
            timeout=_ESTIMATION_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        log.warning(
            "Quantum estimation timed out after %.0f s (epsilon=%s)",
            _ESTIMATION_TIMEOUT_SECONDS,
            epsilon,
        )
        raise HTTPException(
            status_code=504,
            detail=(
                f"Quantum estimation did not complete within {_ESTIMATION_TIMEOUT_SECONDS:.0f} s. "
                "Try a larger epsilon value to reduce circuit depth."
            ),
        )
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
