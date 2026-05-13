"""Tests for quantum_price_inference.composer.

Tests that require a real Qiskit circuit (QASM export, URL generation) are
skipped automatically when ``qiskit-finance`` is absent, since building a
meaningful circuit requires the full notebook extra.

Import-safety and error-path tests run without any extras.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from quantum_price_inference.composer import COMPOSER_BASE_URL, circuit_to_qasm2, composer_url


# ---------------------------------------------------------------------------
# Import-safety tests — no qiskit required
# ---------------------------------------------------------------------------


class TestComposerImportSafety:
    def test_module_imports_without_qiskit(self):
        """composer.py must be importable even when qiskit is not installed."""
        # If we got here, the import at the top of this file already succeeded.
        import quantum_price_inference.composer  # noqa: F401

    def test_circuit_to_qasm2_raises_without_qiskit(self):
        """circuit_to_qasm2() raises ImportError with a helpful message."""
        mock_circuit = MagicMock()
        with patch.dict(sys.modules, {"qiskit": None, "qiskit.qasm2": None}):
            with pytest.raises(ImportError, match="qiskit"):
                circuit_to_qasm2(mock_circuit)

    def test_composer_url_raises_without_qiskit(self):
        """composer_url() raises ImportError with a helpful message."""
        mock_circuit = MagicMock()
        with patch.dict(sys.modules, {"qiskit": None, "qiskit.qasm2": None}):
            with pytest.raises(ImportError, match="qiskit"):
                composer_url(mock_circuit)


# ---------------------------------------------------------------------------
# Integration tests — require qiskit-finance to build a real circuit
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def qiskit_finance():
    return pytest.importorskip("qiskit_finance", reason="qiskit-finance not installed")


class TestComposerIntegration:
    """Tests that build a real circuit and export it.  Skipped without qiskit-finance."""

    def _build_circuit(self, normal_model, linear_payoff):
        """Build a small combined circuit for export tests."""
        return linear_payoff.circuit(normal_model)

    def test_circuit_to_qasm2_returns_string(self, qiskit_finance, normal_model, linear_payoff):
        circuit = self._build_circuit(normal_model, linear_payoff)
        qasm = circuit_to_qasm2(circuit)
        assert isinstance(qasm, str)
        assert len(qasm) > 0

    def test_qasm2_starts_with_openqasm_header(self, qiskit_finance, normal_model, linear_payoff):
        circuit = self._build_circuit(normal_model, linear_payoff)
        qasm = circuit_to_qasm2(circuit)
        assert qasm.strip().startswith("OPENQASM 2.0")

    def test_qasm2_contains_qreg(self, qiskit_finance, normal_model, linear_payoff):
        circuit = self._build_circuit(normal_model, linear_payoff)
        qasm = circuit_to_qasm2(circuit)
        assert "qreg" in qasm

    def test_composer_url_starts_with_base(self, qiskit_finance, normal_model, linear_payoff):
        circuit = self._build_circuit(normal_model, linear_payoff)
        url = composer_url(circuit)
        assert url.startswith(COMPOSER_BASE_URL)

    def test_composer_url_contains_code_param(self, qiskit_finance, normal_model, linear_payoff):
        circuit = self._build_circuit(normal_model, linear_payoff)
        url = composer_url(circuit)
        assert "?code=" in url

    def test_composer_url_is_url_encoded(self, qiskit_finance, normal_model, linear_payoff):
        """The QASM code in the URL must be percent-encoded (no raw spaces or newlines)."""
        circuit = self._build_circuit(normal_model, linear_payoff)
        url = composer_url(circuit)
        code_part = url.split("?code=", 1)[1]
        assert " " not in code_part
        assert "\n" not in code_part
