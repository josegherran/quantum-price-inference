"""Tests for quantum_price_inference.uncertainty."""

import numpy as np
import pytest

from quantum_price_inference.uncertainty import NormalUncertaintyModel, LogNormalUncertaintyModel


class TestNormalUncertaintyModel:
    def test_samples_shape(self, normal_model):
        x, probs = normal_model.samples()
        assert len(x) == 2**normal_model.num_qubits
        assert len(probs) == len(x)

    def test_probabilities_sum_to_one(self, normal_model):
        _, probs = normal_model.samples()
        assert abs(probs.sum() - 1.0) < 1e-10

    def test_probabilities_non_negative(self, normal_model):
        _, probs = normal_model.samples()
        assert (probs >= 0).all()

    def test_support_within_bounds(self, normal_model):
        x, _ = normal_model.samples()
        assert x.min() >= normal_model.low
        assert x.max() <= normal_model.high

    def test_default_bounds_three_sigma(self):
        model = NormalUncertaintyModel(mu=50.0, sigma=10.0)
        assert model.low == pytest.approx(50.0 - 3 * 10.0)
        assert model.high == pytest.approx(50.0 + 3 * 10.0)

    def test_custom_bounds(self):
        model = NormalUncertaintyModel(mu=50.0, sigma=10.0, low=30.0, high=70.0)
        assert model.low == 30.0
        assert model.high == 70.0

    def test_num_qubits_resolution(self):
        for q in [2, 3, 4]:
            model = NormalUncertaintyModel(mu=100.0, sigma=10.0, num_qubits=q)
            x, probs = model.samples()
            assert len(x) == 2**q

    def test_mean_near_mu(self, normal_model):
        x, probs = normal_model.samples()
        weighted_mean = (x * probs).sum()
        assert abs(weighted_mean - normal_model.mu) < normal_model.sigma


class TestLogNormalUncertaintyModel:
    def test_samples_shape(self, lognormal_model):
        x, probs = lognormal_model.samples()
        assert len(x) == 2**lognormal_model.num_qubits

    def test_probabilities_sum_to_one(self, lognormal_model):
        _, probs = lognormal_model.samples()
        assert abs(probs.sum() - 1.0) < 1e-10

    def test_support_strictly_positive(self, lognormal_model):
        x, _ = lognormal_model.samples()
        assert (x > 0).all()

    def test_default_low_is_positive(self):
        model = LogNormalUncertaintyModel(mu=1.0, sigma=1.0)
        assert model.low > 0
