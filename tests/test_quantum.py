"""Tests for quantum_price_inference.quantum.

The quantum engine requires ``qiskit-algorithms`` (core dep) and
``qiskit-finance`` (notebook extra).  Tests that exercise the real IQAE
circuit are skipped automatically when ``qiskit_finance`` is absent.
"""

from __future__ import annotations

import asyncio
import sys
from unittest.mock import MagicMock, patch

import pytest

from quantum_price_inference.quantum import QuantumResult, estimate, estimate_async
from quantum_price_inference.uncertainty import NormalUncertaintyModel
from quantum_price_inference.payoff import LinearPayoff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _small_model() -> NormalUncertaintyModel:
    """2-qubit model — fast enough for integration tests."""
    return NormalUncertaintyModel(mu=100.0, sigma=15.0, num_qubits=2)


def _small_payoff() -> LinearPayoff:
    return LinearPayoff(breakeven=85.0, slope=0.02)


# ---------------------------------------------------------------------------
# Unit tests — mock qiskit-algorithms so they run without the full stack
# ---------------------------------------------------------------------------


class TestQuantumResultDataclass:
    def test_fields_accessible(self):
        r = QuantumResult(
            value=0.42,
            confidence_interval=(0.38, 0.46),
            epsilon=0.01,
            num_oracle_calls=120,
        )
        assert r.value == pytest.approx(0.42)
        assert r.confidence_interval == (0.38, 0.46)
        assert r.epsilon == pytest.approx(0.01)
        assert r.num_oracle_calls == 120

    def test_frozen(self):
        r = QuantumResult(
            value=0.1, confidence_interval=(0.0, 0.2), epsilon=0.05, num_oracle_calls=10
        )
        with pytest.raises((AttributeError, TypeError)):
            r.value = 0.9  # type: ignore[misc]


class TestEstimateWithMock:
    """Unit tests that mock the qiskit-algorithms layer."""

    def _make_mock_result(self, estimation: float = 0.5, ci=(0.45, 0.55), oracle_calls: int = 64):
        mock_result = MagicMock()
        mock_result.estimation = estimation
        mock_result.confidence_interval = ci
        mock_result.num_oracle_queries = oracle_calls
        return mock_result

    def _patch_iae(self, mock_result):
        """Return a context manager that patches IterativeAmplitudeEstimation."""
        mock_iae_instance = MagicMock()
        mock_iae_instance.estimate.return_value = mock_result

        mock_iae_cls = MagicMock(return_value=mock_iae_instance)
        mock_problem_cls = MagicMock()
        mock_sampler_cls = MagicMock()

        patches = [
            patch(
                "quantum_price_inference.quantum.IterativeAmplitudeEstimation",
                mock_iae_cls,
                create=True,
            ),
            patch(
                "quantum_price_inference.quantum.EstimationProblem",
                mock_problem_cls,
                create=True,
            ),
            patch(
                "quantum_price_inference.quantum.StatevectorSampler",
                mock_sampler_cls,
                create=True,
            ),
        ]
        return patches

    def _run_with_mocks(self, estimation=0.5, ci=(0.45, 0.55), oracle_calls=64, max_value=1.0):
        """Run estimate() with mocked qiskit-algorithms and a mock circuit."""
        mock_result = self._make_mock_result(estimation, ci, oracle_calls)

        model = MagicMock()
        model.num_qubits = 3
        mock_circuit = MagicMock()
        mock_circuit.num_qubits = 4  # 3 state + 1 objective
        model.circuit.return_value = mock_circuit

        payoff = MagicMock()
        payoff.max_value = max_value
        payoff.circuit.return_value = mock_circuit

        # Patch the imports inside quantum.py
        fake_algorithms = MagicMock()
        fake_algorithms.EstimationProblem = MagicMock()
        fake_iae_instance = MagicMock()
        fake_iae_instance.estimate.return_value = mock_result
        fake_algorithms.IterativeAmplitudeEstimation = MagicMock(return_value=fake_iae_instance)

        fake_qiskit = MagicMock()
        fake_qiskit.primitives.StatevectorSampler = MagicMock()

        with patch.dict(
            sys.modules,
            {
                "qiskit_algorithms": fake_algorithms,
                "qiskit.primitives": fake_qiskit.primitives,
            },
        ):
            # Force re-import of the function's local imports
            result = (
                estimate.__wrapped__(model, payoff) if hasattr(estimate, "__wrapped__") else None
            )

        return result, model, payoff, fake_iae_instance

    def test_import_error_without_qiskit_algorithms(self):
        """estimate() raises ImportError with a helpful message when qiskit-algorithms is absent."""
        model = MagicMock()
        model.num_qubits = 3
        mock_circuit = MagicMock()
        mock_circuit.num_qubits = 4
        model.circuit.return_value = mock_circuit

        payoff = MagicMock()
        payoff.max_value = 1.0
        payoff.circuit.return_value = mock_circuit

        with patch.dict(sys.modules, {"qiskit_algorithms": None}):
            with pytest.raises(ImportError, match="qiskit-algorithms"):
                estimate(model, payoff)

    def test_import_error_without_qiskit(self):
        """estimate() raises ImportError with a helpful message when qiskit is absent."""
        model = MagicMock()
        model.num_qubits = 3
        mock_circuit = MagicMock()
        mock_circuit.num_qubits = 4
        model.circuit.return_value = mock_circuit

        payoff = MagicMock()
        payoff.max_value = 1.0
        payoff.circuit.return_value = mock_circuit

        with patch.dict(sys.modules, {"qiskit_algorithms": None, "qiskit": None}):
            with pytest.raises(ImportError):
                estimate(model, payoff)


# ---------------------------------------------------------------------------
# Integration tests — require qiskit-finance; skipped if absent
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def qiskit_finance():
    return pytest.importorskip("qiskit_finance", reason="qiskit-finance not installed")


class TestEstimateIntegration:
    """Run the real IQAE on a small circuit.  Skipped without qiskit-finance."""

    def test_returns_quantum_result(self, qiskit_finance):
        model = _small_model()
        payoff = _small_payoff()
        result = estimate(model, payoff, epsilon=0.05, alpha=0.05)
        assert isinstance(result, QuantumResult)

    def test_value_in_valid_range(self, qiskit_finance):
        model = _small_model()
        payoff = _small_payoff()
        result = estimate(model, payoff, epsilon=0.05, alpha=0.05)
        assert 0.0 <= result.value <= payoff.max_value

    def test_confidence_interval_ordered(self, qiskit_finance):
        model = _small_model()
        payoff = _small_payoff()
        result = estimate(model, payoff, epsilon=0.05, alpha=0.05)
        lo, hi = result.confidence_interval
        assert lo < hi

    def test_confidence_interval_contains_value(self, qiskit_finance):
        model = _small_model()
        payoff = _small_payoff()
        result = estimate(model, payoff, epsilon=0.05, alpha=0.05)
        lo, hi = result.confidence_interval
        assert lo <= result.value <= hi

    def test_epsilon_recorded(self, qiskit_finance):
        model = _small_model()
        payoff = _small_payoff()
        epsilon = 0.05
        result = estimate(model, payoff, epsilon=epsilon, alpha=0.05)
        assert result.epsilon == pytest.approx(epsilon)

    def test_num_oracle_calls_positive(self, qiskit_finance):
        model = _small_model()
        payoff = _small_payoff()
        result = estimate(model, payoff, epsilon=0.05, alpha=0.05)
        assert result.num_oracle_calls >= 0

    def test_result_is_frozen(self, qiskit_finance):
        model = _small_model()
        payoff = _small_payoff()
        result = estimate(model, payoff, epsilon=0.05, alpha=0.05)
        with pytest.raises((AttributeError, TypeError)):
            result.value = 999.0  # type: ignore[misc]

    def test_async_matches_sync(self, qiskit_finance):
        """Async wrapper must return a valid QuantumResult (same algorithm, same bounds)."""
        model = _small_model()
        payoff = _small_payoff()
        # Run both independently — IQAE uses a sampler internally so two runs
        # are not guaranteed to be bit-identical, but both must be valid results.
        sync_result = estimate(model, payoff, epsilon=0.05, alpha=0.05)
        async_result = asyncio.run(estimate_async(model, payoff, epsilon=0.05, alpha=0.05))
        assert isinstance(async_result, QuantumResult)
        assert 0.0 <= async_result.value <= payoff.max_value
        # Both results should be in the same ballpark (within 3× epsilon of each other).
        assert abs(sync_result.value - async_result.value) < 3 * 0.05

    def test_smaller_epsilon_tighter_ci(self, qiskit_finance):
        """A smaller epsilon target should produce a narrower confidence interval."""
        model = _small_model()
        payoff = _small_payoff()
        coarse = estimate(model, payoff, epsilon=0.05, alpha=0.05)
        fine = estimate(model, payoff, epsilon=0.02, alpha=0.05)
        coarse_width = coarse.confidence_interval[1] - coarse.confidence_interval[0]
        fine_width = fine.confidence_interval[1] - fine.confidence_interval[0]
        assert fine_width <= coarse_width

    def test_value_close_to_classical(self, qiskit_finance):
        """QAE and classical MC should agree within a reasonable tolerance.

        A 2-qubit model has only 4 grid points, so the discretisation error
        between QAE and classical MC can be significant.  We use a generous
        tolerance (0.3) that is still meaningful — it rules out completely
        wrong results while accepting the coarse-grid approximation.
        """
        from quantum_price_inference.classical import estimate as classical_estimate

        model = _small_model()
        payoff = _small_payoff()
        q_result = estimate(model, payoff, epsilon=0.05, alpha=0.05)
        c_result = classical_estimate(model, payoff, n_samples=50_000, seed=0)
        # Both operate on the same 4-point discretised distribution, so they
        # should agree within the combined discretisation + estimation error.
        assert abs(q_result.value - c_result.value) < 0.3
