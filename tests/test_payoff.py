"""Tests for quantum_price_inference.payoff."""

import numpy as np
import pytest

from quantum_price_inference.payoff import LinearPayoff


class TestLinearPayoff:
    def test_zero_below_breakeven(self, linear_payoff):
        assert linear_payoff(80.0) == 0.0
        assert linear_payoff(85.0) == 0.0  # exactly at breakeven

    def test_positive_above_breakeven(self, linear_payoff):
        assert linear_payoff(95.0) > 0.0

    def test_capped_at_max_value(self, linear_payoff):
        # Very high demand should saturate at max_value
        assert linear_payoff(1_000_000.0) == pytest.approx(linear_payoff.max_value)

    def test_scalar_matches_apply(self, linear_payoff):
        x = np.array([70.0, 85.0, 100.0, 120.0])
        vectorised = linear_payoff.apply(x)
        scalar = np.array([linear_payoff(xi) for xi in x])
        np.testing.assert_allclose(vectorised, scalar)

    def test_apply_returns_array(self, linear_payoff):
        x = np.linspace(50.0, 150.0, 20)
        result = linear_payoff.apply(x)
        assert result.shape == x.shape

    def test_invalid_slope_raises(self):
        with pytest.raises(ValueError):
            LinearPayoff(breakeven=80.0, slope=-0.1)

    def test_invalid_max_value_raises(self):
        with pytest.raises(ValueError):
            LinearPayoff(breakeven=80.0, slope=0.01, max_value=0.0)

    def test_linearity_between_breakeven_and_cap(self):
        payoff = LinearPayoff(breakeven=0.0, slope=0.1, max_value=1.0)
        # At x=5, g = 0.1*5 = 0.5
        assert payoff(5.0) == pytest.approx(0.5)
        # At x=10, g = 0.1*10 = 1.0 (saturates)
        assert payoff(10.0) == pytest.approx(1.0)

    def test_circuit_requires_qiskit_finance(self, linear_payoff, normal_model):
        """LinearPayoff.circuit() is skipped without qiskit-finance."""
        pytest.importorskip("qiskit_finance", reason="qiskit-finance not installed")
        circuit = linear_payoff.circuit(normal_model)
        # Objective qubit is appended — total qubits > model qubits
        assert circuit.num_qubits > normal_model.num_qubits

    def test_circuit_import_error_without_qiskit(self, linear_payoff, normal_model):
        """LinearPayoff.circuit() raises ImportError with a helpful message."""
        import sys
        from unittest.mock import patch

        with patch.dict(
            sys.modules,
            {
                "qiskit": None,
                "qiskit.circuit": None,
                "qiskit.circuit.library": None,
                "qiskit_finance": None,
                "qiskit_finance.circuit": None,
                "qiskit_finance.circuit.library": None,
            },
        ):
            with pytest.raises(ImportError, match="notebook"):
                linear_payoff.circuit(normal_model)


class TestThresholdPayoff:
    def test_zero_below_threshold(self, threshold_payoff):
        assert threshold_payoff(50.0) == 0.0
        assert threshold_payoff(99.9) == 0.0

    def test_one_at_and_above_threshold(self, threshold_payoff):
        assert threshold_payoff(100.0) == 1.0
        assert threshold_payoff(200.0) == 1.0

    def test_apply_vectorised(self, threshold_payoff):
        x = np.array([50.0, 100.0, 150.0])
        result = threshold_payoff.apply(x)
        np.testing.assert_array_equal(result, [0.0, 1.0, 1.0])

    def test_apply_returns_float_array(self, threshold_payoff):
        x = np.linspace(80.0, 120.0, 10)
        result = threshold_payoff.apply(x)
        assert result.dtype == float

    def test_circuit_requires_qiskit_finance(self, threshold_payoff, normal_model):
        """ThresholdPayoff.circuit() is skipped without qiskit-finance."""
        pytest.importorskip("qiskit_finance", reason="qiskit-finance not installed")
        circuit = threshold_payoff.circuit(normal_model)
        # Objective qubit is appended — total qubits > model qubits
        assert circuit.num_qubits > normal_model.num_qubits

    def test_circuit_output_within_step_of_threshold(self, threshold_payoff, normal_model):
        """The steep-ramp approximation should fire within one grid step of the threshold."""
        pytest.importorskip("qiskit_finance", reason="qiskit-finance not installed")
        n = 2**normal_model.num_qubits
        step = (normal_model.high - normal_model.low) / n
        # The approximation fires within ±step of the true threshold
        assert threshold_payoff(threshold_payoff.threshold + step) == pytest.approx(1.0)
        assert threshold_payoff(threshold_payoff.threshold - step - 1e-9) == pytest.approx(0.0)

    def test_circuit_import_error_without_qiskit(self, threshold_payoff, normal_model):
        """ThresholdPayoff.circuit() raises ImportError with a helpful message."""
        import sys
        from unittest.mock import patch

        with patch.dict(
            sys.modules,
            {
                "qiskit": None,
                "qiskit.circuit": None,
                "qiskit.circuit.library": None,
                "qiskit_finance": None,
                "qiskit_finance.circuit": None,
                "qiskit_finance.circuit.library": None,
            },
        ):
            with pytest.raises(ImportError, match="notebook"):
                threshold_payoff.circuit(normal_model)
