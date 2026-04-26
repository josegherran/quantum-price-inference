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
        A :class:`QuantumResult` with the estimated value and CI.

    Raises:
        ImportError: if ``qiskit-algorithms`` or ``qiskit-finance`` is not installed.
    """
    try:
        from qiskit_algorithms import EstimationProblem, IterativeAmplitudeEstimation  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "qiskit-algorithms is required for quantum estimation. "
            "Install it with: uv sync"
        ) from exc

    try:
        from qiskit.primitives import StatevectorSampler  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "qiskit is required. Install it with: uv sync"
        ) from exc

    log.info("Quantum QAE: epsilon=%.4f  alpha=%.4f", epsilon, alpha)

    # Build the full circuit (uncertainty + payoff)
    full_circuit = payoff.circuit(model)

    # The objective qubit is always the last qubit in the combined circuit
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

    # QAE returns the amplitude in [0, 1]; de-normalise by max_value
    max_value = getattr(payoff, "max_value", 1.0)
    value = result_raw.estimation * max_value
    ci_raw = result_raw.confidence_interval
    ci = (ci_raw[0] * max_value, ci_raw[1] * max_value)
    num_oracle_calls = result_raw.num_oracle_calls

    result = QuantumResult(
        value=value,
        confidence_interval=ci,
        epsilon=epsilon,
        num_oracle_calls=num_oracle_calls,
    )
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
