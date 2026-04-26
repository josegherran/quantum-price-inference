# quantum-price-inference

A quantum price inference simulation system that uses quantum algorithms for inferring asset prices using amplitude estimation and quantum Monte Carlo methods, with two interfaces:

- **Jupyter Notebook** — researcher interface with circuit visualizations, price simulations, and full physics derivations
- **REST API** — FastAPI service for programmatic access to quantum simulations.

## general approach

Pricing a product or service is fundamentally a **probability problem**. Instead of computing a fixed number, we estimate an expected value over uncertain outcomes:

```
Fair Price = E[g(X)]
```

- `X` — uncertain input (demand, cost, usage, FX, incidents)
- `g(X)` — business payoff (revenue, margin, penalty, benefit)

This system implements two estimation paths side-by-side:

| Approach | Method | Notes |
|---|---|---|
| Classical | Monte Carlo simulation | Accuracy improves as O(1/√N) |
| Quantum | Amplitude Estimation (QAE) | Extracts expected value directly from quantum state |

Both paths share the same **4-block model**:

1. **Uncertainty Model** — define what is uncertain (variable demand, cost, usage)
2. **Payoff Function** — map outcomes to business value (margin, loss, penalty)
3. **Encoding** — load probability distributions into the quantum circuit
4. **Estimation** — extract the expected value via amplitude estimation

The quantum approach does not change *what* is calculated — only *how efficiently* the expectation is estimated. The same model applies across business domains: API pricing with variable usage, services with SLA penalties, subscriptions with churn uncertainty.

See [Quantum_Workshop_Facilitator_Script.md](Quantum_Workshop_Facilitator_Script.md) for the full 90-minute workshop guide designed for non-technical stakeholders.

## features

- simulate the price of a product or service using quantum amplitude estimation
- model uncertainty over demand, cost, usage, or any continuous business variable
- define custom payoff functions (margin, penalty, benefit) applied to simulated outcomes
- run classical Monte Carlo and quantum QAE side-by-side for direct comparison
- visualize quantum circuits and probability distributions in the notebook interface
- expose all simulations via a REST API for programmatic and integration use

## requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) — fast Python package and project manager

All other dependencies are declared in [pyproject.toml](pyproject.toml):

| Package | Purpose |
|---|---|
| `qiskit` | quantum circuit construction and simulation |
| `qiskit-algorithms` | amplitude estimation (QAE) |
| `numpy` | classical Monte Carlo and numerical computation |
| `matplotlib` | circuit and distribution visualizations |
| `fastapi` | REST API server |
| `uvicorn[standard]` | ASGI server for FastAPI |
| `jupyter`, `ipykernel` | interactive notebook interface *(optional)* |
| `qiskit-finance` | pre-built uncertainty distributions and payoff circuits *(optional)* |

## circuit visualization

Circuits can be visualized locally (via Matplotlib) or interactively in **IBM Quantum Composer** — no IBM account needed to open a circuit in the visual editor.

```python
from qiskit import QuantumCircuit
from quantum_price_inference.composer import open_in_composer, composer_url

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)

# open directly in the default browser
open_in_composer(qc)

# or just get the URL (useful in notebooks / CI)
url = composer_url(qc)
print(url)
```

The utility exports the circuit to **OpenQASM 2.0** and encodes it as a `?code=` query parameter in the Composer URL. No upload, no credentials.

> Composer: <https://quantum.cloud.ibm.com/composer>

## installation

```bash
# clone the repository
git clone https://github.com/your-org/quantum-price-inference.git
cd quantum-price-inference

# create virtual environment and install core dependencies
uv sync

# also install notebook extras (Jupyter + circuit drawing)
uv sync --extra notebook

# also install dev tools (pytest, ruff, httpx)
uv sync --extra dev
```

Activate the environment when running commands directly:

```bash
source .venv/bin/activate
```

Or prefix any command with `uv run` to use the project environment without activating:

```bash
uv run jupyter notebook
uv run uvicorn api.main:app --reload
```

### run the notebook

```bash
uv run jupyter notebook
```

Open `notebook/quantum_price_inference.ipynb`.

### run the REST API

```bash
uv run uvicorn api.main:app --reload
```

API available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## License and documentation in this repository are licensed under the MIT License. See [LICENSE](LICENSE) for details.

License is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Author

@ 2026
Jose Giori Herran Escobar -  [GitHub](https://github.com/josegherran) - [LinkedIn](https://www.linkedin.com/in/joseherran/)
