"""Tests for the FastAPI REST endpoints."""

import pytest
import anyio
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.fixture()
def estimate_payload():
    return {
        "uncertainty": {"mu": 100.0, "sigma": 15.0, "num_qubits": 3},
        "payoff": {"breakeven": 85.0, "slope": 0.02},
    }


def _run(coro):
    """Run a coroutine synchronously using anyio."""
    return anyio.from_thread.run_sync(lambda: None) or anyio.run(coro)


async def _post(path, payload, params=""):
    url = f"{path}{('?' + params) if params else ''}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(url, json=payload)


async def _get(path):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(path)


def test_health():
    response = anyio.run(_get, "/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_classical_estimate_returns_200(estimate_payload):
    response = anyio.run(_post, "/estimate/classical", estimate_payload)
    assert response.status_code == 200


def test_classical_estimate_response_shape(estimate_payload):
    response = anyio.run(_post, "/estimate/classical", estimate_payload)
    data = response.json()
    assert data["method"] == "classical_monte_carlo"
    assert "value" in data
    assert "std_error" in data
    assert "confidence_interval" in data
    assert "lower" in data["confidence_interval"]
    assert "upper" in data["confidence_interval"]
    assert data["n_samples"] == 10_000


def test_classical_estimate_value_in_range(estimate_payload):
    response = anyio.run(_post, "/estimate/classical", estimate_payload)
    data = response.json()
    assert 0.0 <= data["value"] <= 1.0


def test_classical_estimate_custom_n_samples(estimate_payload):
    response = anyio.run(_post, "/estimate/classical", estimate_payload, "n_samples=500&seed=42")
    assert response.status_code == 200
    assert response.json()["n_samples"] == 500


def test_classical_estimate_invalid_sigma(estimate_payload):
    bad_payload = dict(estimate_payload)
    bad_payload["uncertainty"] = {**estimate_payload["uncertainty"], "sigma": -1.0}
    response = anyio.run(_post, "/estimate/classical", bad_payload)
    assert response.status_code == 422


def test_classical_estimate_invalid_slope(estimate_payload):
    bad_payload = dict(estimate_payload)
    bad_payload["payoff"] = {**estimate_payload["payoff"], "slope": 0.0}
    response = anyio.run(_post, "/estimate/classical", bad_payload)
    assert response.status_code == 422
