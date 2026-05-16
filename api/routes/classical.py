"""Classical Monte Carlo estimation endpoint."""

from __future__ import annotations

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
    classical_estimate_async,
)
from api.schemas import (
    EstimateRequest,
    ClassicalEstimateResponse,
    ConfidenceInterval,
)

_UNCERTAINTY_MODELS = {
    "normal": NormalUncertaintyModel,
    "lognormal": LogNormalUncertaintyModel,
}

log = logging.getLogger(__name__)

router = APIRouter(prefix="/estimate", tags=["classical"])

# ---------------------------------------------------------------------------
# Prometheus counters
# ---------------------------------------------------------------------------

_SAMPLES_TOTAL = Counter(
    "classical_samples_total",
    "Total number of Monte Carlo samples drawn across all requests.",
)


@router.post(
    "/classical",
    response_model=ClassicalEstimateResponse,
    summary="Classical Monte Carlo estimation",
    description=(
        "Estimates E[g(X)] by drawing random samples from the uncertainty model "
        "and averaging the payoff function. Reference baseline for the quantum comparison.\n\n"
        "**Bounds:** `n_samples` is capped at 100 000 to prevent CPU exhaustion. "
        "`alpha` controls the confidence interval width (default 0.05 → 95 % CI, "
        "consistent with the quantum endpoint)."
    ),
)
@limiter.limit(settings.classical_rate_limit)
async def estimate_classical(
    request: Request,
    body: EstimateRequest,
    n_samples: int = Query(
        default=10_000,
        ge=100,
        le=100_000,
        description="Number of random samples to draw (100–100 000).",
    ),
    seed: int | None = Query(
        default=None,
        description="Optional random seed for reproducibility.",
    ),
    alpha: float = Query(
        default=0.05,
        ge=0.01,
        le=0.5,
        description="Significance level for the confidence interval (0.01–0.5, default 0.05 → 95 % CI).",
    ),
):
    """Run classical Monte Carlo and return the expected payoff.

    Query parameters:
    - **n_samples**: number of random samples (100–100 000, default 10 000)
    - **seed**: optional random seed for reproducibility
    - **alpha**: significance level for the CI (0.01–0.5, default 0.05 → 95 % CI)
    """
    log.info(
        "POST /estimate/classical  distribution=%s payoff=%s mu=%s sigma=%s n_samples=%s alpha=%s",
        body.uncertainty.distribution_type,
        body.payoff.payoff_type,
        body.uncertainty.mu,
        body.uncertainty.sigma,
        n_samples,
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
        result = await classical_estimate_async(
            model, payoff, n_samples=n_samples, seed=seed, alpha=alpha
        )
        _SAMPLES_TOTAL.inc(n_samples)
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
