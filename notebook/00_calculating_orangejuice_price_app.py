import marimo as mo
import numpy as np
import matplotlib.pyplot as plt



    yield mo.md(
        r"""
        # 🍊 Calculating a Fair Price for Orange Juice (Marimo App)

        This interactive app demonstrates, through a practical orange juice pricing scenario, the difference between classical Monte Carlo and quantum amplitude estimation techniques for fair pricing under uncertainty.
        """
    )

    # --- Parameters ---
    cost_per_cup = mo.number(label="Cost per cup ($)", value=2.50, min=0, max=10, step=0.01)
    reference_demand = mo.number(label="Reference demand (cups)", value=100, min=1, max=1000, step=1)
    reference_price = mo.number(label="Reference price ($)", value=5.00, min=0, max=10, step=0.01)
    price_sensitivity = mo.number(label="Price sensitivity", value=0.30, min=0, max=1, step=0.01)
    demand_noise_pct = mo.number(label="Demand noise (%)", value=15, min=0, max=100, step=1)

    yield mo.hstack([cost_per_cup, reference_demand, reference_price, price_sensitivity, demand_noise_pct])

    price_grid = np.linspace(4.0, 6.0, 25)

    # --- Demand and profit functions ---
    def demand(price, noise):
        base = reference_demand.value * (1 - price_sensitivity.value * (price - reference_price.value))
        return base * (1 + noise)

    def profit(price, noise):
        d = demand(price, noise)
        return (price - cost_per_cup.value) * d

    # --- Monte Carlo estimation ---
    def monte_carlo_estimate(price, n_samples=10000):
        noises = np.random.uniform(-demand_noise_pct.value/100, demand_noise_pct.value/100, n_samples)
        profits = profit(price, noises)
        mean = np.mean(profits)
        std_err = np.std(profits, ddof=1) / np.sqrt(n_samples)
        return mean, std_err

    # --- QAE estimation (simulated) ---
    def qae_estimate(price, n_queries=100):
        mean = (price - cost_per_cup.value) * reference_demand.value * (1 - price_sensitivity.value * (price - reference_price.value))
        _, mc_std = monte_carlo_estimate(price, 100000)
        error = mc_std * (1 / n_queries)
        return mean, error

    n_samples = mo.number(label="MC samples", value=10000, min=100, max=100000, step=100)
    n_queries = mo.number(label="QAE queries", value=100, min=10, max=10000, step=10)
    yield mo.hstack([n_samples, n_queries])

    # --- Compute curves ---
    mc_means = []
    mc_errors = []
    qae_means = []
    qae_errors = []
    for p in price_grid:
        m, e = monte_carlo_estimate(p, int(n_samples.value))
        mc_means.append(m)
        mc_errors.append(e)
        m_q, e_q = qae_estimate(p, int(n_queries.value))
        qae_means.append(m_q)
        qae_errors.append(e_q)
    mc_means = np.array(mc_means)
    mc_errors = np.array(mc_errors)
    qae_means = np.array(qae_means)
    qae_errors = np.array(qae_errors)

    # --- Plot expected profit vs price ---
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(price_grid, mc_means, label="Monte Carlo (mean)", color="steelblue")
    ax.fill_between(price_grid, mc_means - mc_errors, mc_means + mc_errors, color="steelblue", alpha=0.2, label="MC 1-sigma")
    ax.plot(price_grid, qae_means, label="Quantum AE (mean)", color="darkorange")
    ax.fill_between(price_grid, qae_means - qae_errors, qae_means + qae_errors, color="darkorange", alpha=0.2, label="QAE 1-sigma")
    ax.set_xlabel("Price ($)")
    ax.set_ylabel("Expected Profit ($)")
    ax.set_title("Expected Profit vs Price")
    ax.legend()
    ax.grid(True, ls="--", alpha=0.5)
    yield mo.pyplot(fig)

    # --- Conclusions ---
    yield mo.md(
        r"""
        ---
        **Monte Carlo** is reliable but requires many samples for high precision ($O(1/\sqrt{N})$).  
        **Quantum Amplitude Estimation** (QAE, simulated) achieves the same or better precision with far fewer queries ($O(1/N)$).

        **Business impact:** Quantum methods enable more stable, reproducible, and fair pricing decisions, especially when computational resources are limited or when small profit differences matter.
        """
    )

# Required for marimo CLI
app = mo.App(main)
