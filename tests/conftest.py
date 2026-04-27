"""Shared pytest fixtures for the quantum-price-inference test suite."""

import pytest

from quantum_price_inference.uncertainty import NormalUncertaintyModel, LogNormalUncertaintyModel
from quantum_price_inference.payoff import LinearPayoff, ThresholdPayoff


@pytest.fixture()
def normal_model():
    """Standard normal uncertainty model used across tests."""
    return NormalUncertaintyModel(mu=100.0, sigma=15.0, num_qubits=3)


@pytest.fixture()
def lognormal_model():
    """Log-normal uncertainty model."""
    return LogNormalUncertaintyModel(mu=4.6, sigma=0.3, num_qubits=3)


@pytest.fixture()
def linear_payoff():
    """Linear payoff with breakeven=85, slope=0.02."""
    return LinearPayoff(breakeven=85.0, slope=0.02)


@pytest.fixture()
def threshold_payoff():
    """Threshold payoff that fires at x >= 100."""
    return ThresholdPayoff(threshold=100.0)
