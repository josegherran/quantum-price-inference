"""
Uncertainty models for the quantum price inference 4-block pipeline.

An uncertainty model describes *what is uncertain* — demand, cost, usage, FX, etc. —
as a probability distribution encoded into a quantum circuit.

Two concrete models are provided:

- ``NormalUncertaintyModel``   — symmetric bell-curve uncertainty (cost, FX)
- ``LogNormalUncertaintyModel`` — right-skewed, always-positive variable (demand, usage)

Both wrap the corresponding ``qiskit-finance`` distribution loaders, which are
optional dependencies.  If ``qiskit-finance`` is not installed the models raise a
clear ``ImportError`` only when instantiated, not at import time.

Usage
-----
    from quantum_price_inference.uncertainty import NormalUncertaintyModel

    model = NormalUncertaintyModel(mu=100.0, sigma=15.0, num_qubits=3)
    circuit = model.circuit()        # QuantumCircuit ready for encoding
    x, probs = model.samples()       # discretised support + probabilities
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Protocol — any uncertainty model must satisfy this interface
# ---------------------------------------------------------------------------


class UncertaintyModel(Protocol):
    """Structural interface for all uncertainty models."""

    @property
    def num_qubits(self) -> int:
        """Number of qubits used to discretise the distribution."""
        ...

    @property
    def low(self) -> float:
        """Lower bound of the discretised support."""
        ...

    @property
    def high(self) -> float:
        """Upper bound of the discretised support."""
        ...

    def circuit(self):  # -> QuantumCircuit
        """Return the Qiskit circuit that loads the distribution."""
        ...

    def samples(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return ``(x_values, probabilities)`` over the discretised support."""
        ...


# ---------------------------------------------------------------------------
# Normal distribution
# ---------------------------------------------------------------------------


@dataclass
class NormalUncertaintyModel:
    """Uncertainty model based on a discretised Normal distribution.

    Args:
        mu:         Mean of the distribution (e.g. expected demand or cost).
        sigma:      Standard deviation.
        num_qubits: Number of qubits; resolution = 2**num_qubits grid points.
                    Typical values: 3 (coarse demo), 5 (moderate accuracy).
        low:        Lower bound of the discretised support (default: mu - 3σ).
        high:       Upper bound of the discretised support (default: mu + 3σ).
    """

    mu: float
    sigma: float
    num_qubits: int = 3
    low: float = field(init=False)
    high: float = field(init=False)
    _low_init: float | None = field(default=None, repr=False)
    _high_init: float | None = field(default=None, repr=False)

    def __init__(
        self,
        mu: float,
        sigma: float,
        num_qubits: int = 3,
        low: float | None = None,
        high: float | None = None,
    ) -> None:
        self.mu = mu
        self.sigma = sigma
        self.num_qubits = num_qubits
        self.low = low if low is not None else mu - 3 * sigma
        self.high = high if high is not None else mu + 3 * sigma
        log.debug(
            "NormalUncertaintyModel(mu=%s, sigma=%s, qubits=%d, low=%s, high=%s)",
            mu,
            sigma,
            num_qubits,
            self.low,
            self.high,
        )

    # ------------------------------------------------------------------
    # Circuit encoding (requires qiskit-finance)
    # ------------------------------------------------------------------

    def circuit(self):
        """Return a Qiskit circuit that loads the Normal distribution.

        Requires the ``notebook`` extra (``qiskit-finance``).

        Returns:
            A ``QuantumCircuit`` with ``num_qubits`` qubits prepared in the
            state representing the discretised Normal distribution.

        Raises:
            ImportError: if ``qiskit-finance`` is not installed.
        """
        try:
            from qiskit_finance.circuit.library import NormalDistribution  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "qiskit-finance is required for circuit encoding. "
                "Install it with: uv sync --extra notebook"
            ) from exc

        dist = NormalDistribution(
            num_qubits=self.num_qubits,
            mu=self.mu,
            sigma=self.sigma**2,
            bounds=(self.low, self.high),
        )
        log.debug("Built NormalDistribution circuit with %d qubits", self.num_qubits)
        return dist

    # ------------------------------------------------------------------
    # Classical discretisation (no qiskit-finance needed)
    # ------------------------------------------------------------------

    def samples(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return the discretised support and probability mass.

        Returns:
            Tuple ``(x, probs)`` where ``x`` has shape ``(2**num_qubits,)`` and
            ``probs`` sums to 1.
        """
        n = 2**self.num_qubits
        x = np.linspace(self.low, self.high, n)
        # Unnormalised Gaussian evaluated at grid points
        raw = np.exp(-0.5 * ((x - self.mu) / self.sigma) ** 2)
        probs = raw / raw.sum()
        return x, probs


# ---------------------------------------------------------------------------
# Log-Normal distribution
# ---------------------------------------------------------------------------


@dataclass
class LogNormalUncertaintyModel:
    """Uncertainty model based on a discretised Log-Normal distribution.

    Suitable for strictly positive, right-skewed variables such as demand
    volume or usage counts.

    Args:
        mu:         Mean of the underlying Normal (log-space mean).
        sigma:      Standard deviation of the underlying Normal (log-space std).
        num_qubits: Number of qubits; resolution = 2**num_qubits grid points.
        low:        Lower bound of the discretised support (must be > 0).
        high:       Upper bound of the discretised support.
    """

    mu: float
    sigma: float
    num_qubits: int
    low: float
    high: float

    def __init__(
        self,
        mu: float,
        sigma: float,
        num_qubits: int = 3,
        low: float | None = None,
        high: float | None = None,
    ) -> None:
        self.mu = mu
        self.sigma = sigma
        self.num_qubits = num_qubits
        # Sensible defaults: exp(mu ± 3σ) clipped to positive domain
        self.low = low if low is not None else max(0.01, np.exp(mu - 3 * sigma))
        self.high = high if high is not None else np.exp(mu + 3 * sigma)
        log.debug(
            "LogNormalUncertaintyModel(mu=%s, sigma=%s, qubits=%d, low=%s, high=%s)",
            mu,
            sigma,
            num_qubits,
            self.low,
            self.high,
        )

    def circuit(self):
        """Return a Qiskit circuit that loads the Log-Normal distribution.

        Requires the ``notebook`` extra (``qiskit-finance``).

        Raises:
            ImportError: if ``qiskit-finance`` is not installed.
        """
        try:
            from qiskit_finance.circuit.library import LogNormalDistribution  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "qiskit-finance is required for circuit encoding. "
                "Install it with: uv sync --extra notebook"
            ) from exc

        dist = LogNormalDistribution(
            num_qubits=self.num_qubits,
            mu=self.mu,
            sigma=self.sigma**2,
            bounds=(self.low, self.high),
        )
        log.debug("Built LogNormalDistribution circuit with %d qubits", self.num_qubits)
        return dist

    def samples(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return the discretised support and probability mass."""
        n = 2**self.num_qubits
        x = np.linspace(self.low, self.high, n)
        # Log-normal PDF evaluated at grid points
        raw = np.exp(-0.5 * ((np.log(x) - self.mu) / self.sigma) ** 2) / x
        probs = raw / raw.sum()
        return x, probs
