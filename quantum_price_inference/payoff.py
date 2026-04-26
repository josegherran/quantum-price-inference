"""
Payoff functions for the quantum price inference 4-block pipeline.

A payoff function maps an uncertain outcome ``x`` to a business value ``g(x)``.
It is the second block in the 4-block model and is agnostic to whether the
estimation is classical (applied element-wise to samples) or quantum (encoded
as a ``LinearAmplitudeFunction`` circuit appended to the uncertainty circuit).

Two concrete payoffs are provided:

- ``LinearPayoff``    — ``g(x) = slope * (x - breakeven)`` clipped to ``[0, 1]``
                        Represents margin or benefit linear in the outcome.
- ``ThresholdPayoff`` — ``g(x) = 1  if x >= threshold  else  0``
                        Represents a binary event: SLA breach, churn, etc.

Usage
-----
    from quantum_price_inference.payoff import LinearPayoff

    payoff = LinearPayoff(
        breakeven=80.0,
        slope=0.01,
        max_value=1.0,
    )
    value = payoff(95.0)             # scalar evaluation
    values = payoff.apply(x_array)   # vectorised evaluation
    circuit = payoff.circuit(model)  # quantum circuit (needs qiskit-finance)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Protocol — any payoff must satisfy this interface
# ---------------------------------------------------------------------------


class PayoffFunction(Protocol):
    """Structural interface for all payoff functions."""

    def __call__(self, x: float) -> float:
        """Evaluate the payoff at a single outcome value."""
        ...

    def apply(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """Vectorised evaluation over an array of outcome values."""
        ...

    def circuit(self, model):  # model: UncertaintyModel -> QuantumCircuit
        """Return a Qiskit circuit that appends this payoff to ``model.circuit()``."""
        ...


# ---------------------------------------------------------------------------
# Linear payoff  g(x) = clip(slope * (x - breakeven), 0, max_value)
# ---------------------------------------------------------------------------


@dataclass
class LinearPayoff:
    """Linear business payoff clipped to ``[0, max_value]``.

    Suitable for margin, revenue-above-cost, or any value that grows linearly
    once a threshold is crossed and saturates at a maximum.

    Args:
        breakeven:  The outcome value at which payoff becomes positive.
        slope:      Rate of value growth per unit of outcome above breakeven.
        max_value:  Saturation cap (also used to normalise the quantum circuit).
                    Defaults to 1.0 so the payoff is in [0, 1] for QAE.
    """

    breakeven: float
    slope: float
    max_value: float = 1.0

    def __post_init__(self) -> None:
        if self.slope <= 0:
            raise ValueError("slope must be positive")
        if self.max_value <= 0:
            raise ValueError("max_value must be positive")
        log.debug(
            "LinearPayoff(breakeven=%s, slope=%s, max_value=%s)",
            self.breakeven,
            self.slope,
            self.max_value,
        )

    def __call__(self, x: float) -> float:
        return float(np.clip(self.slope * (x - self.breakeven), 0.0, self.max_value))

    def apply(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """Vectorised evaluation — returns array of same shape as ``x``."""
        return np.clip(self.slope * (x - self.breakeven), 0.0, self.max_value)

    def circuit(self, model):
        """Return a Qiskit circuit combining ``model.circuit()`` + this payoff.

        The payoff is expressed as a ``LinearAmplitudeFunction`` from
        ``qiskit-finance``, which appends an objective qubit encoding
        ``sin²(θ) ≈ g(x) / max_value`` for use by QAE.

        Args:
            model: An ``UncertaintyModel`` instance (provides ``num_qubits``,
                   ``low``, ``high``).

        Raises:
            ImportError: if ``qiskit-finance`` is not installed.
        """
        try:
            from qiskit_finance.circuit.library import LinearAmplitudeFunction  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "qiskit-finance is required for circuit payoff encoding. "
                "Install it with: uv sync --extra notebook"
            ) from exc

        # Slope and intercept normalised so the function lives in [0, 1]
        slope_norm = self.slope / self.max_value
        intercept_norm = -self.slope * self.breakeven / self.max_value

        payoff_fn = LinearAmplitudeFunction(
            num_state_qubits=model.num_qubits,
            slope=slope_norm,
            offset=intercept_norm,
            domain=(model.low, model.high),
            image=(0, 1),
            rescaling_factor=0.25,
        )
        log.debug("Built LinearAmplitudeFunction circuit")

        # Compose: uncertainty circuit → payoff circuit
        from qiskit import QuantumCircuit

        num_qubits = model.num_qubits + payoff_fn.num_ancillas + 1
        circuit = QuantumCircuit(num_qubits)
        circuit.append(model.circuit(), range(model.num_qubits))
        circuit.append(payoff_fn, range(num_qubits))
        return circuit


# ---------------------------------------------------------------------------
# Threshold payoff  g(x) = 1 if x >= threshold else 0
# ---------------------------------------------------------------------------


@dataclass
class ThresholdPayoff:
    """Binary payoff — 1 if outcome reaches or exceeds a threshold.

    Models binary business events: SLA breach, churn, subscription renewal,
    cost overrun, etc.

    Args:
        threshold:  The outcome value above which the event occurs (payoff = 1).
    """

    threshold: float

    def __post_init__(self) -> None:
        log.debug("ThresholdPayoff(threshold=%s)", self.threshold)

    def __call__(self, x: float) -> float:
        return 1.0 if x >= self.threshold else 0.0

    def apply(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        return (x >= self.threshold).astype(float)

    def circuit(self, model):
        """Quantum encoding of a step function via ``LinearAmplitudeFunction``.

        Approximated as a very steep linear ramp across one grid interval.

        Raises:
            ImportError: if ``qiskit-finance`` is not installed.
        """
        try:
            from qiskit_finance.circuit.library import LinearAmplitudeFunction  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "qiskit-finance is required for circuit payoff encoding. "
                "Install it with: uv sync --extra notebook"
            ) from exc

        n = 2**model.num_qubits
        step = (model.high - model.low) / n  # one grid interval
        slope_approx = 1.0 / step

        payoff_fn = LinearAmplitudeFunction(
            num_state_qubits=model.num_qubits,
            slope=slope_approx,
            offset=-slope_approx * self.threshold,
            domain=(model.low, model.high),
            image=(0, 1),
            rescaling_factor=0.25,
        )
        log.debug("Built ThresholdPayoff LinearAmplitudeFunction circuit")

        from qiskit import QuantumCircuit

        num_qubits = model.num_qubits + payoff_fn.num_ancillas + 1
        circuit = QuantumCircuit(num_qubits)
        circuit.append(model.circuit(), range(model.num_qubits))
        circuit.append(payoff_fn, range(num_qubits))
        return circuit
