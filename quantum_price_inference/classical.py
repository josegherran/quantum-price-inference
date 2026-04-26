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
import logging
from dataclasses import dataclass

import numpy as np

log = logging.getLogger(__name__)


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
# Synchronous engine
# ---------------------------------------------------------------------------


def estimate(
    model,
    payoff,
    n_samples: int = 10_000,
    seed: int | None = None,
) -> ClassicalResult:
    """Estimate E[g(X)] via classical Monte Carlo sampling.

    Args:
        model:     An ``UncertaintyModel`` instance.
        payoff:    A ``PayoffFunction`` instance.
        n_samples: Number of random samples to draw (default 10 000).
        seed:      Optional random seed for reproducibility.

    Returns:
        A :class:`ClassicalResult` with mean, std error, and 95 % CI.
    """
    log.info("Classical MC: drawing %d samples (seed=%s)", n_samples, seed)

    rng = np.random.default_rng(seed)
    x_values, probs = model.samples()

    # Sample indices according to the discretised probability mass
    indices = rng.choice(len(x_values), size=n_samples, p=probs)
    x_drawn = x_values[indices]

    g_values = payoff.apply(x_drawn)
    mean = float(g_values.mean())
    std = float(g_values.std())
    std_error = std / np.sqrt(n_samples)
    half_width = 1.96 * std_error  # 95 % CI

    result = ClassicalResult(
        value=mean,
        std_error=std_error,
        confidence_interval=(mean - half_width, mean + half_width),
        n_samples=n_samples,
    )
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
    model,
    payoff,
    n_samples: int = 10_000,
    seed: int | None = None,
) -> ClassicalResult:
    """Async wrapper around :func:`estimate`.

    Runs the CPU-bound sampling in a thread pool so the event loop is never
    blocked.  Use this inside FastAPI route handlers and async notebook cells.
    """
    return await asyncio.to_thread(estimate, model, payoff, n_samples, seed)
