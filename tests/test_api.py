"""Tests for the FastAPI REST endpoints."""

import anyio
import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.fixture()
def estimate_payload():
    """Standard request payload for classical/quantum endpoints."""
    return {
        "uncertainty": {"mu": 100.0, "sigma": 15.0, "num_qubits": 3},
        "payoff": {"breakeven": 85.0, "slope": 0.02},
    }


def _run(coro):
    """Run a coroutine synchronously using anyio."""
    return anyio.run(coro)


async def _post(path, payload, params=""):
    url = f"{path}{('?' + params) if params else ''}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(url, json=payload)


async def _get(path):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(path)


# ---------------------------------------------------------------------------
# Legacy health check
# ---------------------------------------------------------------------------


def test_health():
    async def check():
        return await _get("/health")

    response = anyio.run(check)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# 2.4 — Liveness and readiness probes
# ---------------------------------------------------------------------------


def test_health_live_returns_200():
    async def check():
        return await _get("/health/live")

    response = anyio.run(check)
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_health_ready_returns_200():
    async def check():
        return await _get("/health/ready")

    response = anyio.run(check)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "checks" in data


def test_health_ready_reports_qiskit_status():
    async def check():
        return await _get("/health/ready")

    response = anyio.run(check)
    checks = response.json()["checks"]
    # qiskit is a core dependency — must always be present
    assert "qiskit" in checks
    assert checks["qiskit"] in ("ok", "missing")


# ---------------------------------------------------------------------------
# 2.1 — Request ID header
# ---------------------------------------------------------------------------


def test_response_includes_request_id_header():
    async def check():
        return await _get("/health/live")

    response = anyio.run(check)
    assert "x-request-id" in response.headers


def test_client_request_id_is_echoed():
    """If the client sends X-Request-ID, the same value is returned."""

    async def check():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get("/health/live", headers={"X-Request-ID": "test-id-123"})

    response = anyio.run(check)
    assert response.headers.get("x-request-id") == "test-id-123"


# ---------------------------------------------------------------------------
# Classical endpoint
# ---------------------------------------------------------------------------


def test_classical_estimate_returns_200(estimate_payload):
    async def check():
        return await _post("/estimate/classical", estimate_payload)

    response = anyio.run(check)
    assert response.status_code == 200


def test_classical_estimate_response_shape(estimate_payload):
    async def check():
        return await _post("/estimate/classical", estimate_payload)

    response = anyio.run(check)
    data = response.json()
    assert data["method"] == "classical_monte_carlo"
    assert "value" in data
    assert "std_error" in data
    assert "confidence_interval" in data
    assert "lower" in data["confidence_interval"]
    assert "upper" in data["confidence_interval"]
    assert data["n_samples"] == 10_000


def test_classical_estimate_value_in_range(estimate_payload):
    async def check():
        return await _post("/estimate/classical", estimate_payload)

    response = anyio.run(check)
    data = response.json()
    assert 0.0 <= data["value"] <= 1.0


def test_classical_estimate_custom_n_samples(estimate_payload):
    async def check():
        return await _post("/estimate/classical", estimate_payload, "n_samples=500&seed=42")

    response = anyio.run(check)
    assert response.status_code == 200
    assert response.json()["n_samples"] == 500


def test_classical_estimate_invalid_sigma(estimate_payload):
    bad_payload = dict(estimate_payload)
    bad_payload["uncertainty"] = {**estimate_payload["uncertainty"], "sigma": -1.0}

    async def check():
        return await _post("/estimate/classical", bad_payload)

    response = anyio.run(check)
    assert response.status_code == 422


def test_classical_estimate_invalid_slope(estimate_payload):
    bad_payload = dict(estimate_payload)
    bad_payload["payoff"] = {**estimate_payload["payoff"], "slope": 0.0}

    async def check():
        return await _post("/estimate/classical", bad_payload)

    response = anyio.run(check)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 2.3 — Classical cache: seeded calls return identical results
# ---------------------------------------------------------------------------


def test_classical_seeded_calls_are_identical(estimate_payload):
    """Two requests with the same seed must return bit-identical results (cache hit)."""

    async def check():
        r1 = await _post("/estimate/classical", estimate_payload, "n_samples=1000&seed=99")
        r2 = await _post("/estimate/classical", estimate_payload, "n_samples=1000&seed=99")
        return r1, r2

    r1, r2 = anyio.run(check)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["value"] == r2.json()["value"]
    assert r1.json()["std_error"] == r2.json()["std_error"]


def test_classical_different_seeds_may_differ(estimate_payload):
    """Two requests with different seeds should (almost certainly) differ."""

    async def check():
        r1 = await _post("/estimate/classical", estimate_payload, "n_samples=100&seed=1")
        r2 = await _post("/estimate/classical", estimate_payload, "n_samples=100&seed=2")
        return r1, r2

    r1, r2 = anyio.run(check)
    assert r1.status_code == 200
    assert r2.status_code == 200
    # With only 100 samples and different seeds, values are very unlikely to be identical
    assert r1.json()["value"] != r2.json()["value"]


# ---------------------------------------------------------------------------
# Quantum endpoint — skipped without qiskit-finance
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def qiskit_finance():
    return pytest.importorskip("qiskit_finance", reason="qiskit-finance not installed")


def test_quantum_estimate_returns_200(qiskit_finance, estimate_payload):
    async def check():
        return await _post("/estimate/quantum", estimate_payload, "epsilon=0.05")

    response = anyio.run(check)
    assert response.status_code == 200


def test_quantum_estimate_response_shape(qiskit_finance, estimate_payload):
    async def check():
        return await _post("/estimate/quantum", estimate_payload, "epsilon=0.05")

    response = anyio.run(check)
    data = response.json()
    assert data["method"] == "quantum_amplitude_estimation"
    assert "value" in data
    assert "confidence_interval" in data
    assert "lower" in data["confidence_interval"]
    assert "upper" in data["confidence_interval"]
    assert "epsilon" in data
    assert "num_oracle_calls" in data


def test_quantum_estimate_value_in_range(qiskit_finance, estimate_payload):
    async def check():
        return await _post("/estimate/quantum", estimate_payload, "epsilon=0.05")

    response = anyio.run(check)
    data = response.json()
    assert 0.0 <= data["value"] <= 1.0


def test_quantum_estimate_ci_ordered(qiskit_finance, estimate_payload):
    async def check():
        return await _post("/estimate/quantum", estimate_payload, "epsilon=0.05")

    response = anyio.run(check)
    ci = response.json()["confidence_interval"]
    assert ci["lower"] < ci["upper"]


def test_quantum_estimate_invalid_epsilon(estimate_payload):
    """epsilon outside [0.001, 0.1] must return 422."""

    async def check():
        return await _post("/estimate/quantum", estimate_payload, "epsilon=0.5")

    response = anyio.run(check)
    assert response.status_code == 422


def test_quantum_estimate_invalid_alpha(estimate_payload):
    """alpha outside [0.01, 0.5] must return 422."""

    async def check():
        return await _post("/estimate/quantum", estimate_payload, "epsilon=0.05&alpha=0.001")

    response = anyio.run(check)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 2.3 — Quantum cache: repeated calls return identical results
# ---------------------------------------------------------------------------


def test_quantum_repeated_calls_are_identical(qiskit_finance, estimate_payload):
    """IQAE on StatevectorSampler is deterministic — repeated calls must match."""

    async def check():
        r1 = await _post("/estimate/quantum", estimate_payload, "epsilon=0.05")
        r2 = await _post("/estimate/quantum", estimate_payload, "epsilon=0.05")
        return r1, r2

    r1, r2 = anyio.run(check)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["value"] == r2.json()["value"]
    assert r1.json()["num_oracle_calls"] == r2.json()["num_oracle_calls"]


# ---------------------------------------------------------------------------
# Prometheus metrics endpoint
# ---------------------------------------------------------------------------


def test_metrics_endpoint_returns_200():
    async def check():
        return await _get("/metrics")

    response = anyio.run(check)
    assert response.status_code == 200


def test_metrics_endpoint_contains_http_requests():
    async def check():
        return await _get("/metrics")

    response = anyio.run(check)
    assert "http_requests_total" in response.text or "http_request" in response.text


# ---------------------------------------------------------------------------
# 4.4 — /v1 versioning prefix
# ---------------------------------------------------------------------------


def test_v1_classical_endpoint_returns_200(estimate_payload):
    async def check():
        return await _post("/v1/estimate/classical", estimate_payload)

    response = anyio.run(check)
    assert response.status_code == 200


def test_v1_quantum_endpoint_returns_200(estimate_payload):
    qiskit_finance = pytest.importorskip("qiskit_finance")  # noqa: F841

    async def check():
        return await _post("/v1/estimate/quantum", estimate_payload, "epsilon=0.05")

    response = anyio.run(check)
    assert response.status_code == 200


def test_legacy_classical_endpoint_still_works(estimate_payload):
    """Un-prefixed legacy route must remain available for one release cycle."""

    async def check():
        return await _post("/estimate/classical", estimate_payload)

    response = anyio.run(check)
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 4.1 — LogNormal distribution type via API
# ---------------------------------------------------------------------------


def test_classical_lognormal_distribution_returns_200():
    payload = {
        "uncertainty": {"distribution_type": "lognormal", "mu": 4.6, "sigma": 0.3, "num_qubits": 3},
        "payoff": {"breakeven": 80.0, "slope": 0.02},
    }

    async def check():
        return await _post("/v1/estimate/classical", payload, "n_samples=1000&seed=0")

    response = anyio.run(check)
    assert response.status_code == 200
    assert 0.0 <= response.json()["value"] <= 1.0


def test_classical_lognormal_value_differs_from_normal():
    """LogNormal and Normal with domain-appropriate params produce different estimates."""
    payoff = {"breakeven": 80.0, "slope": 0.02}

    async def check():
        # Normal: mu=100, sigma=15 — typical cost distribution
        r_normal = await _post(
            "/v1/estimate/classical",
            {
                "uncertainty": {
                    "distribution_type": "normal",
                    "mu": 100.0,
                    "sigma": 15.0,
                    "num_qubits": 3,
                },
                "payoff": payoff,
            },
            "n_samples=5000&seed=7",
        )
        # LogNormal: same domain (support ~55–200) but right-skewed
        r_lognormal = await _post(
            "/v1/estimate/classical",
            {
                "uncertainty": {
                    "distribution_type": "lognormal",
                    "mu": 4.6,
                    "sigma": 0.3,
                    "num_qubits": 3,
                },
                "payoff": payoff,
            },
            "n_samples=5000&seed=7",
        )
        return r_normal, r_lognormal

    r_normal, r_lognormal = anyio.run(check)
    assert r_normal.status_code == 200
    assert r_lognormal.status_code == 200
    assert r_normal.json()["value"] != r_lognormal.json()["value"]


def test_classical_invalid_distribution_type_returns_422(estimate_payload):
    bad = {
        **estimate_payload,
        "uncertainty": {**estimate_payload["uncertainty"], "distribution_type": "uniform"},
    }

    async def check():
        return await _post("/v1/estimate/classical", bad)

    response = anyio.run(check)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 4.2 — Threshold payoff type via API
# ---------------------------------------------------------------------------


def test_classical_threshold_payoff_returns_200():
    payload = {
        "uncertainty": {"mu": 100.0, "sigma": 15.0, "num_qubits": 3},
        "payoff": {"payoff_type": "threshold", "breakeven": 85.0, "threshold": 100.0},
    }

    async def check():
        return await _post("/v1/estimate/classical", payload, "n_samples=5000&seed=0")

    response = anyio.run(check)
    assert response.status_code == 200
    # Threshold payoff returns a probability in [0, 1]
    assert 0.0 <= response.json()["value"] <= 1.0


def test_classical_threshold_payoff_missing_threshold_returns_422():
    payload = {
        "uncertainty": {"mu": 100.0, "sigma": 15.0, "num_qubits": 3},
        "payoff": {"payoff_type": "threshold", "breakeven": 85.0},
    }

    async def check():
        return await _post("/v1/estimate/classical", payload)

    response = anyio.run(check)
    assert response.status_code == 422


def test_classical_threshold_differs_from_linear():
    """Threshold payoff estimate should differ from linear payoff estimate."""
    uncertainty = {"mu": 100.0, "sigma": 15.0, "num_qubits": 3}

    async def check():
        r_linear = await _post(
            "/v1/estimate/classical",
            {
                "uncertainty": uncertainty,
                "payoff": {"payoff_type": "linear", "breakeven": 85.0, "slope": 0.02},
            },
            "n_samples=5000&seed=42",
        )
        r_threshold = await _post(
            "/v1/estimate/classical",
            {
                "uncertainty": uncertainty,
                "payoff": {"payoff_type": "threshold", "breakeven": 85.0, "threshold": 100.0},
            },
            "n_samples=5000&seed=42",
        )
        return r_linear, r_threshold

    r_linear, r_threshold = anyio.run(check)
    assert r_linear.status_code == 200
    assert r_threshold.status_code == 200
    assert r_linear.json()["value"] != r_threshold.json()["value"]


# ---------------------------------------------------------------------------
# 4.3 — Consistent alpha parameter on classical endpoint
# ---------------------------------------------------------------------------


def test_classical_alpha_widens_ci_at_lower_confidence(estimate_payload):
    """Lower confidence (higher alpha) should produce a narrower CI."""

    async def check():
        r_95 = await _post(
            "/v1/estimate/classical", estimate_payload, "n_samples=5000&seed=1&alpha=0.05"
        )
        r_50 = await _post(
            "/v1/estimate/classical", estimate_payload, "n_samples=5000&seed=1&alpha=0.50"
        )
        return r_95, r_50

    r_95, r_50 = anyio.run(check)
    assert r_95.status_code == 200
    assert r_50.status_code == 200
    ci_95 = r_95.json()["confidence_interval"]
    ci_50 = r_50.json()["confidence_interval"]
    width_95 = ci_95["upper"] - ci_95["lower"]
    width_50 = ci_50["upper"] - ci_50["lower"]
    assert width_95 > width_50


def test_classical_invalid_alpha_returns_422(estimate_payload):
    async def check():
        return await _post("/v1/estimate/classical", estimate_payload, "alpha=0.99")

    response = anyio.run(check)
    assert response.status_code == 422


def test_quantum_endpoint_also_accepts_alpha(estimate_payload):
    """Verify quantum endpoint still accepts alpha (regression guard for 4.3)."""
    qiskit_finance = pytest.importorskip("qiskit_finance")  # noqa: F841

    async def check():
        return await _post("/v1/estimate/quantum", estimate_payload, "epsilon=0.05&alpha=0.10")

    response = anyio.run(check)
    assert response.status_code == 200
