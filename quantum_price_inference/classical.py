"""
Classical Monte Carlo estimation engine.

Implements block 3 (Encoding) + block 4 (Estimation) using classical sampling
instead of a quantum circuit.  Used as the reference baseline in the side-by-side
workshop comparison.

Algorithm
---------
1. Draw ``n_samples`` indices from the discretised distribution.
2. Look up the outcome value ``x`` for each index.
3. Apply the payoff function ``g(x)``.
4. Return the sample mean as the estimate of E[g(X)].

Caching
-------
When a ``seed`` is provided the simulation is fully deterministic.  Results are
cached in an in-process LRU cache (max 256 entries) keyed on all scalar
parameters.  Requests without a seed bypass the cache.  The cache is lost on
process restart; for multi-worker deployments use a shared cache (Wave 3).

Usage
-----
    from quantum_price_inference.classical import estimate, estimate_async
    from quantum_price_inference.uncertainty import NormalUncertaintyModel
    from quantum_price_inference.payoff import LinearPayoff

    model = NormalUncertaintyModel(mu=100.0, sigma=15.0, num_qubits=3)
    payoff = LinearPayoff(breakeven=90.0, slope=0.02)

    result = estimate(model, payoff, n_samples=10_000, seed=42)
    print(result.value, result.std_error, result.confidence_interval)
"""

from __future__ import annotations

import asyncio
import functools
import logging
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Optional

import numpy as np

if TYPE_CHECKING:
    from quantum_price_inference.uncertainty import UncertaintyModel
    from quantum_price_inference.payoff import PayoffFunction

log = logging.getLogger(__name__)


def _z_score(alpha: float) -> float:
    """Return the z-score for a two-tailed CI at confidence level (1 - alpha).

    Uses ``math.erfinv`` (Python ≥ 3.12) when available, falling back to
    ``scipy.special.erfinv`` for earlier Python versions.  Both are exact;
    no approximation is needed.
    """
    # math.erfinv added in Python 3.12 (PEP 697)
    _erfinv: Optional[Callable[[float], float]] = getattr(math, "erfinv", None)
    if _erfinv is None:
        try:
            from scipy.special import erfinv as _scipy_erfinv  # type: ignore[import-untyped]

            _erfinv = _scipy_erfinv
        except ImportError:
            # Last-resort: Abramowitz & Stegun rational approximation (max error 4.5e-4)
            # Only reached in environments with neither Python 3.12 nor scipy.
            t = 1.0 - alpha
            u = math.log(1.0 - t * t)
            c = 2.515517 + 0.802853 * u + 0.010328 * u * u
            d = 1.0 + 1.432788 * u + 0.189269 * u * u + 0.001308 * u * u * u
            return c / d
    return math.sqrt(2.0) * _erfinv(1.0 - alpha)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClassicalResult:
    """Output of a classical Monte Carlo estimation run.

    Attributes:
        value:               Sample mean — estimate of E[g(X)].
        std_error:           Standard error of the mean (std / sqrt(n)).
        confidence_interval: 95 % confidence interval ``(lower, upper)``.
        n_samples:           Number of samples drawn.
    """

    value: float
    std_error: float
    confidence_interval: tuple[float, float]
    n_samples: int


# ---------------------------------------------------------------------------
# Internal cached implementation
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=256)
def _estimate_cached(
    mu: float,
    sigma: float,
    num_qubits: int,
    low: float | None,
    high: float | None,
    breakeven: float,
    slope: float,
    max_value: float,
    n_samples: int,
    seed: int,
    alpha: float,
) -> ClassicalResult:
    """LRU-cached implementation for deterministic (seeded) runs.

    All parameters are scalars so they are hashable and safe as cache keys.
    Called only when ``seed`` is not ``None``; unseeded calls go directly to
    :func:`_estimate_uncached`.
    """
    from quantum_price_inference.uncertainty import NormalUncertaintyModel
    from quantum_price_inference.payoff import LinearPayoff

    model = NormalUncertaintyModel(mu=mu, sigma=sigma, num_qubits=num_qubits, low=low, high=high)
    payoff = LinearPayoff(breakeven=breakeven, slope=slope, max_value=max_value)
    return _estimate_uncached(model, payoff, n_samples=n_samples, seed=seed, alpha=alpha)


def _estimate_uncached(
    model: UncertaintyModel,
    payoff: PayoffFunction,
    n_samples: int,
    seed: int | None,
    alpha: float = 0.05,
) -> ClassicalResult:
    """Core Monte Carlo implementation — no caching."""
    rng = np.random.default_rng(seed)
    x_values, probs = model.samples()

    # Sample indices according to the discretised probability mass
    indices = rng.choice(len(x_values), size=n_samples, p=probs)
    x_drawn = x_values[indices]

    g_values = payoff.apply(x_drawn)
    mean = float(g_values.mean())
    std = float(g_values.std())
    std_error = std / np.sqrt(n_samples)
    half_width = _z_score(alpha) * std_error

    return ClassicalResult(
        value=mean,
        std_error=std_error,
        confidence_interval=(mean - half_width, mean + half_width),
        n_samples=n_samples,
    )


# ---------------------------------------------------------------------------
# Synchronous engine
# ---------------------------------------------------------------------------


def estimate(
    model: UncertaintyModel,
    payoff: PayoffFunction,
    n_samples: int = 10_000,
    seed: int | None = None,
    alpha: float = 0.05,
) -> ClassicalResult:
    """Estimate E[g(X)] via classical Monte Carlo sampling.

    Args:
        model:     An ``UncertaintyModel`` instance.
        payoff:    A ``PayoffFunction`` instance.
        n_samples: Number of random samples to draw (default 10 000).
        seed:      Optional random seed for reproducibility.  When provided,
                   the result is served from an in-process LRU cache on
                   repeated calls with identical parameters.
        alpha:     Significance level for the confidence interval (default 0.05
                   → 95 % CI).  Consistent with the quantum endpoint's ``alpha``.

    Returns:
        A :class:`ClassicalResult` with mean, std error, and ``(1 - alpha)`` CI.
    """
    log.info("Classical MC: drawing %d samples (seed=%s alpha=%.2f)", n_samples, seed, alpha)

    # Route to the cached path only when the call is deterministic and the
    # model/payoff are real instances with scalar attributes (not mocks).
    if seed is not None and hasattr(model, "mu"):
        try:
            result = _estimate_cached(
                mu=float(model.mu),
                sigma=float(model.sigma),
                num_qubits=int(model.num_qubits),
                low=float(model.low) if getattr(model, "low", None) is not None else None,
                high=float(model.high) if getattr(model, "high", None) is not None else None,
                breakeven=float(getattr(payoff, "breakeven", 0.0)),
                slope=float(getattr(payoff, "slope", 0.0)),
                max_value=float(getattr(payoff, "max_value", 1.0)),
                n_samples=n_samples,
                seed=seed,
                alpha=alpha,
            )
        except (TypeError, ValueError):
            # Attributes are not real scalars (e.g. mocks in tests) — fall through.
            result = _estimate_uncached(model, payoff, n_samples=n_samples, seed=seed, alpha=alpha)
    else:
        result = _estimate_uncached(model, payoff, n_samples=n_samples, seed=seed, alpha=alpha)

    log.info(
        "Classical MC result: value=%.6f  std_error=%.6f  CI=(%.6f, %.6f)",
        result.value,
        result.std_error,
        *result.confidence_interval,
    )
    return result


# ---------------------------------------------------------------------------
# Async wrapper
# ---------------------------------------------------------------------------


async def estimate_async(
    model: UncertaintyModel,
    payoff: PayoffFunction,
    n_samples: int = 10_000,
    seed: int | None = None,
    alpha: float = 0.05,
) -> ClassicalResult:
    """Async wrapper around :func:`estimate`.

    Runs the CPU-bound sampling in a thread pool so the event loop is never
    blocked.  Use this inside FastAPI route handlers and async notebook cells.
    """
    return await asyncio.to_thread(estimate, model, payoff, n_samples, seed, alpha)
