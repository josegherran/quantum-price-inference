
# Quantum Workshop Facilitator Script (90 min)

## Pricing Under Uncertainty – A Quantum Perspective (for Non-Financial Stakeholders)

---

## Audience

Business, IT, Architecture, Innovation, Data, Product leaders (no finance or quantum prerequisites).

---

## Facilitator Note: Interactive Demo

For the live demo section, you may use either the Jupyter notebook ([notebook/quantum_price_inference.ipynb](../notebook/quantum_price_inference.ipynb)) or the marimo app ([notebook/00_calculating_orangejuice_price_app.py](../notebook/00_calculating_orangejuice_price_app.py)) for a more interactive, real-time experience. The marimo app allows you to adjust parameters and instantly show the impact on classical and quantum price estimates.

---

> *Today we will see how pricing a product or service is really a probability problem – and how quantum computing offers a new way to estimate value under uncertainty.*

Participants will:

- Understand pricing as an **expected value**, not a fixed number
- Compare **classical vs quantum Monte Carlo** conceptually
- Walk away with a **business-ready mental model**, not math or physics

---

## Agenda (90 min)

1. Why pricing is a probability problem (10 min)
2. Classical Monte Carlo – intuition only (15 min)
3. What quantum Monte Carlo changes (10 min)
4. How quantum pricing works (conceptual model) (10 min)
5. Live demo (Qiskit – observe & interpret) (25 min)
6. Translate to product/service pricing (15 min)
7. Wrap-up & takeaways (5 min)

---

## 1. Why Pricing Is About Probability (10 min)

**Facilitator says:**
> We don't price based on what will happen – we price based on what *might* happen.

Key idea:

```code
Fair Price = Expected Value = E[g(X)]
```

- `X`: uncertain future outcome (demand, cost, incidents, FX, usage)
- `g(X)`: business impact (revenue, margin, penalty)

**Example (non-financial):**

- Tomorrow's cloud cost varies
- SLA penalties may or may not occur
- Usage volume is uncertain

Pricing = weighted average across possibilities.

---

## 2. Classical Monte Carlo (15 min)

**Facilitator explanation:**
> Monte Carlo means: simulate many futures, average the results.

Steps:

1. Generate many scenarios
2. Compute business outcome for each
3. Average

Key intuition:

- Accuracy improves slowly
- To double precision → ~4× more simulations

This becomes expensive when:

- Scenarios are complex
- Confidence must be tight
- Decisions are near real-time

---

## 3. What Quantum Monte Carlo Changes (10 min)

**Important clarification:**
> Quantum does not change *what* we calculate – only *how* efficiently we estimate it.

Comparison:

- Classical MC: counts frequencies
- Quantum MC: estimates probabilities directly (amplitudes)

Key message (no math):
> Quantum algorithms reduce estimation error faster *in theory*.

This is about **future capability and modeling discipline**, not speed today.

---

## 4. Quantum Pricing – The Mental Model (10 min)

Pricing with quantum computers always has **4 building blocks**:

1. **Uncertainty Model**
   - What is uncertain?
   - Can be demand, cost, usage, FX

2. **Business Payoff Function**
   - How does value change with outcomes?
   - Margin, loss, penalty, benefit

3. **Encoding**
   - Probabilities are loaded into the model

4. **Estimation**
   - The expected value is extracted

> This structure applies to *any* business problem under uncertainty.

---

## 5. Live Demo – Observe, Don't Code (25 min)

**Facilitator runs prepared notebook** (participants watch & interpret).

### Pre-flight check (do this before the session starts)

Run the following in the project directory to ensure all notebook dependencies are installed and the correct kernel is available:

```bash
uv sync --extra notebook --extra dev
uv run jupyter notebook
```

In the notebook UI, confirm the kernel shown in the top-right corner is **`python3`** (the project venv). If it shows a different kernel, switch via *Kernel → Change kernel → python3*. Skipping this step causes `ModuleNotFoundError: No module named 'matplotlib'` on the first cell.

### What to emphasize

- We model uncertainty (example: variable outcome)
- We define a payoff (value or profit)
- We estimate an expected value

### Show side-by-side

- Classical Monte Carlo result
- Quantum amplitude estimation result

**Important framing:**
> Same question. Same value. Different estimation technique.

Do **not** discuss hardware, qubits, or performance benchmarks.

---

## 6. Translate to Product & Service Pricing (15 min)

**Facilitator says:**
> Forget finance. This applies directly to our products and services.

### Mapping Template

| Finance Term | Business Meaning |
| ------------- | ------------------ |
| Underlying price | Demand / cost / usage |
| Payoff | Margin / penalty / benefit |
| Option price | Fair price |

### Business Examples

- API pricing with variable usage
- Service with SLA penalties
- Subscription with churn uncertainty

Key insight:
> Quantum Monte Carlo is a **value estimation engine for uncertainty**.

---

## 7. Wrap-Up – Key Takeaways (5 min)

Reinforce:

1. Pricing is probabilistic
2. Monte Carlo estimates value
3. Quantum improves estimation, not logic
4. The same model applies across business domains

**Closing line:**
> Even before quantum advantage, this approach improves how we reason about value.

---

## Deliverables

- This facilitator script
- One demo notebook
- One reusable mental model

---
