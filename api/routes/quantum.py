"""Quantum Amplitude Estimation endpoint."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Query, Request
from prometheus_client import Counter

from api.config import settings
from api.limiter import limiter
from quantum_price_inference import (
    NormalUncertaintyModel,
    LogNormalUncertaintyModel,
    LinearPayoff,
    ThresholdPayoff,
    quantum_estimate_async,
)
from api.schemas import (
    EstimateRequest,
    QuantumEstimateResponse,
    ConfidenceInterval,
)

_UNCERTAINTY_MODELS = {
    "normal": NormalUncertaintyModel,
    "lognormal": LogNormalUncertaintyModel,
}

log = logging.getLogger(__name__)

router = APIRouter(prefix="/estimate", tags=["quantum"])

# Timeout read from settings (QPI_ESTIMATION_TIMEOUT_SECONDS); defaults to 30 s.
_ESTIMATION_TIMEOUT_SECONDS = settings.estimation_timeout_seconds

# ---------------------------------------------------------------------------
# Prometheus counters
# ---------------------------------------------------------------------------

_ORACLE_CALLS_TOTAL = Counter(
    "quantum_oracle_calls_total",
    "Total number of Grover oracle evaluations across all quantum estimation requests.",
)


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
@limiter.limit(settings.quantum_rate_limit)
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
        "POST /estimate/quantum  distribution=%s payoff=%s mu=%s sigma=%s epsilon=%s alpha=%s",
        body.uncertainty.distribution_type,
        body.payoff.payoff_type,
        body.uncertainty.mu,
        body.uncertainty.sigma,
        epsilon,
        alpha,
    )
    try:
        ModelClass = _UNCERTAINTY_MODELS[body.uncertainty.distribution_type]
        model = ModelClass(
            mu=body.uncertainty.mu,
            sigma=body.uncertainty.sigma,
            num_qubits=body.uncertainty.num_qubits,
            low=body.uncertainty.low,
            high=body.uncertainty.high,
        )
        if body.payoff.payoff_type == "threshold":
            payoff = ThresholdPayoff(threshold=body.payoff.threshold)  # type: ignore[arg-type]
        else:
            payoff = LinearPayoff(
                breakeven=body.payoff.breakeven,
                slope=body.payoff.slope,
                max_value=body.payoff.max_value,
            )
        result = await asyncio.wait_for(
            quantum_estimate_async(model, payoff, epsilon=epsilon, alpha=alpha),
            timeout=_ESTIMATION_TIMEOUT_SECONDS,
        )
        _ORACLE_CALLS_TOTAL.inc(result.num_oracle_calls)
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
