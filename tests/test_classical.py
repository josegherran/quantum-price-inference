"""Tests for quantum_price_inference.classical."""

import asyncio

from quantum_price_inference.classical import estimate, estimate_async, ClassicalResult


class TestClassicalEstimate:
    def test_returns_classical_result(self, normal_model, linear_payoff):
        result = estimate(normal_model, linear_payoff, n_samples=1_000, seed=0)
        assert isinstance(result, ClassicalResult)

    def test_value_in_valid_range(self, normal_model, linear_payoff):
        result = estimate(normal_model, linear_payoff, n_samples=1_000, seed=0)
        assert 0.0 <= result.value <= linear_payoff.max_value

    def test_std_error_positive(self, normal_model, linear_payoff):
        result = estimate(normal_model, linear_payoff, n_samples=1_000, seed=0)
        assert result.std_error >= 0.0

    def test_confidence_interval_contains_value(self, normal_model, linear_payoff):
        result = estimate(normal_model, linear_payoff, n_samples=1_000, seed=0)
        lo, hi = result.confidence_interval
        assert lo <= result.value <= hi

    def test_confidence_interval_ordered(self, normal_model, linear_payoff):
        result = estimate(normal_model, linear_payoff, n_samples=1_000, seed=0)
        assert result.confidence_interval[0] < result.confidence_interval[1]

    def test_n_samples_recorded(self, normal_model, linear_payoff):
        result = estimate(normal_model, linear_payoff, n_samples=500, seed=0)
        assert result.n_samples == 500

    def test_seed_reproducibility(self, normal_model, linear_payoff):
        r1 = estimate(normal_model, linear_payoff, n_samples=1_000, seed=42)
        r2 = estimate(normal_model, linear_payoff, n_samples=1_000, seed=42)
        assert r1.value == r2.value

    def test_different_seeds_differ(self, normal_model, linear_payoff):
        r1 = estimate(normal_model, linear_payoff, n_samples=1_000, seed=1)
        r2 = estimate(normal_model, linear_payoff, n_samples=1_000, seed=2)
        # Extremely unlikely to be identical
        assert r1.value != r2.value

    def test_more_samples_reduces_std_error(self, normal_model, linear_payoff):
        small = estimate(normal_model, linear_payoff, n_samples=100, seed=0)
        large = estimate(normal_model, linear_payoff, n_samples=10_000, seed=0)
        assert large.std_error < small.std_error

    def test_threshold_payoff_value_is_probability(self, normal_model, threshold_payoff):
        result = estimate(normal_model, threshold_payoff, n_samples=5_000, seed=0)
        assert 0.0 <= result.value <= 1.0


class TestClassicalEstimateAsync:
    def test_async_matches_sync(self, normal_model, linear_payoff):
        sync_result = estimate(normal_model, linear_payoff, n_samples=500, seed=7)
        async_result = asyncio.run(
            estimate_async(normal_model, linear_payoff, n_samples=500, seed=7)
        )
        assert sync_result.value == async_result.value
