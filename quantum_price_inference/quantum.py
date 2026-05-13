"""
Quantum Amplitude Estimation (QAE) engine.

Implements block 3 (Encoding) + block 4 (Estimation) using Qiskit's
``IterativeAmplitudeEstimation`` algorithm from ``qiskit-algorithms``.

Algorithm summary
-----------------
1. Build the full circuit: ``uncertainty_circuit ⊗ payoff_circuit``.
2. Wrap it in an ``EstimationProblem`` that identifies the objective qubit.
3. Run ``IterativeAmplitudeEstimation`` (IQAE) — iteratively applies the
   Grover operator to converge on ``sin²(θ) ≈ E[g(X)] / max_value``.
4. De-normalise the result back to business units.

IQAE is preferred over standard QAE because it does not require phase
estimation ancilla qubits and converges with fewer circuit evaluations.

Caching
-------
IQAE on a ``StatevectorSampler`` is fully deterministic — the same parameters
always produce the same result.  Results are cached in an in-process LRU cache
(max 128 entries) keyed on all scalar parameters.  The cache is lost on process
restart; for multi-worker deployments use a shared cache (Wave 3).

Usage
-----
    from quantum_price_inference.quantum import estimate, estimate_async
    from quantum_price_inference.uncertainty import NormalUncertaintyModel
    from quantum_price_inference.payoff import LinearPayoff

    model = NormalUncertaintyModel(mu=100.0, sigma=15.0, num_qubits=3)
    payoff = LinearPayoff(breakeven=90.0, slope=0.02)

    result = estimate(model, payoff, epsilon=0.01, alpha=0.05)
    print(result.value, result.confidence_interval)

Notes
-----
- Requires ``qiskit-algorithms`` (core dep) and ``qiskit-finance`` (notebook extra).
- Simulation is run on ``StatevectorSampler`` by default — no IBM account needed.
- ``epsilon`` controls precision; smaller values require more circuit evaluations.
"""

from __future__ import annotations

import asyncio
import functools
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QuantumResult:
    """Output of a quantum amplitude estimation run.

    Attributes:
        value:               Estimated E[g(X)] in the payoff's original scale.
        confidence_interval: Confidence interval ``(lower, upper)`` at level
                             ``1 - alpha``.
        epsilon:             Target precision used for the run.
        num_oracle_calls:    Total number of Grover oracle evaluations.
    """

    value: float
    confidence_interval: tuple[float, float]
    epsilon: float
    num_oracle_calls: int


# ---------------------------------------------------------------------------
# Internal cached implementation
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=128)
def _estimate_cached(
    mu: float,
    sigma: float,
    num_qubits: int,
    low: float | None,
    high: float | None,
    breakeven: float,
    slope: float,
    max_value: float,
    epsilon: float,
    alpha: float,
) -> QuantumResult:
    """LRU-cached implementation for deterministic IQAE runs.

    IQAE on ``StatevectorSampler`` is fully deterministic — the same parameters
    always produce the same result.  All parameters are scalars so they are
    hashable and safe as cache keys.
    """
    from quantum_price_inference.uncertainty import NormalUncertaintyModel
    from quantum_price_inference.payoff import LinearPayoff

    model = NormalUncertaintyModel(mu=mu, sigma=sigma, num_qubits=num_qubits, low=low, high=high)
    payoff = LinearPayoff(breakeven=breakeven, slope=slope, max_value=max_value)
    return _estimate_uncached(model, payoff, epsilon=epsilon, alpha=alpha)


def _estimate_uncached(model, payoff, epsilon: float, alpha: float) -> QuantumResult:
    """Core IQAE implementation — no caching."""
    try:
        from qiskit_algorithms import EstimationProblem, IterativeAmplitudeEstimation  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "qiskit-algorithms is required for quantum estimation. Install it with: uv sync"
        ) from exc

    try:
        from qiskit.primitives import StatevectorSampler  # type: ignore[import]
    except ImportError as exc:
        raise ImportError("qiskit is required. Install it with: uv sync") from exc

    # Build the full circuit (uncertainty + payoff)
    full_circuit = payoff.circuit(model)
    objective_qubit = full_circuit.num_qubits - 1

    problem = EstimationProblem(
        state_preparation=full_circuit,
        objective_qubits=[objective_qubit],
    )

    sampler = StatevectorSampler()
    iae = IterativeAmplitudeEstimation(
        epsilon_target=epsilon,
        alpha=alpha,
        sampler=sampler,
    )

    result_raw = iae.estimate(problem)

    max_value = getattr(payoff, "max_value", 1.0)
    value = result_raw.estimation * max_value
    ci_raw = result_raw.confidence_interval
    ci = (ci_raw[0] * max_value, ci_raw[1] * max_value)
    num_oracle_calls = getattr(
        result_raw,
        "num_oracle_queries",
        getattr(result_raw, "num_oracle_calls", 0),
    )

    return QuantumResult(
        value=value,
        confidence_interval=ci,
        epsilon=epsilon,
        num_oracle_calls=num_oracle_calls,
    )


# ---------------------------------------------------------------------------
# Synchronous engine
# ---------------------------------------------------------------------------


def estimate(
    model,
    payoff,
    epsilon: float = 0.01,
    alpha: float = 0.05,
) -> QuantumResult:
    """Estimate E[g(X)] via Iterative Quantum Amplitude Estimation.

    Args:
        model:   An ``UncertaintyModel`` instance. Must have a ``circuit()``
                 method (requires ``qiskit-finance``).
        payoff:  A ``PayoffFunction`` instance with a ``circuit(model)`` method.
        epsilon: Target precision for the amplitude estimate (default 0.01).
                 Smaller values → more accurate, more oracle calls.
        alpha:   Significance level for the confidence interval (default 0.05
                 → 95 % CI).

    Returns:
        A :class:`QuantumResult` with the estimated value and CI.  Results are
        served from an in-process LRU cache on repeated calls with identical
        parameters (IQAE on StatevectorSampler is fully deterministic).

    Raises:
        ImportError: if ``qiskit-algorithms`` or ``qiskit-finance`` is not installed.
    """
    log.info("Quantum QAE: epsilon=%.4f  alpha=%.4f", epsilon, alpha)

    # Route to the cached path when the model exposes real scalar attributes
    # (i.e., it is a NormalUncertaintyModel + LinearPayoff, not a mock).
    if hasattr(model, "mu") and hasattr(payoff, "breakeven"):
        try:
            result = _estimate_cached(
                mu=float(model.mu),
                sigma=float(model.sigma),
                num_qubits=int(model.num_qubits),
                low=float(model.low) if getattr(model, "low", None) is not None else None,
                high=float(model.high) if getattr(model, "high", None) is not None else None,
                breakeven=float(payoff.breakeven),
                slope=float(payoff.slope),
                max_value=float(getattr(payoff, "max_value", 1.0)),
                epsilon=epsilon,
                alpha=alpha,
            )
        except (TypeError, ValueError):
            # Attributes are not real scalars (e.g. mocks in tests) — fall through.
            result = _estimate_uncached(model, payoff, epsilon=epsilon, alpha=alpha)
    else:
        result = _estimate_uncached(model, payoff, epsilon=epsilon, alpha=alpha)

    log.info(
        "QAE result: value=%.6f  CI=(%.6f, %.6f)  oracle_calls=%d",
        result.value,
        *result.confidence_interval,
        result.num_oracle_calls,
    )
    return result


# ---------------------------------------------------------------------------
# Async wrapper
# ---------------------------------------------------------------------------


async def estimate_async(
    model,
    payoff,
    epsilon: float = 0.01,
    alpha: float = 0.05,
) -> QuantumResult:
    """Async wrapper around :func:`estimate`.

    Runs the CPU-bound QAE in a thread pool so the event loop is never
    blocked.  Use this inside FastAPI route handlers and async notebook cells.
    """
    return await asyncio.to_thread(estimate, model, payoff, epsilon, alpha)
