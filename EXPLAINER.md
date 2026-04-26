# What Does This Project Do? 🤔

## Imagine You're Running a Lemonade Stand

You want to sell lemonade tomorrow. But you don't know:

- 🌤️ Will it be hot or cold outside?
- 🧒 How many kids will walk by?
- 🍋 How much will lemons cost at the store?

You can't know for sure. But you can **make a smart guess**.

---

## The Big Idea: A Weighted Guess

Instead of picking one number and hoping for the best, a smart guess looks like this:

> "There's a 30% chance it'll be really hot and I'll sell 50 cups.
> There's a 50% chance it'll be warm and I'll sell 20 cups.
> There's a 20% chance it rains and I'll sell 5 cups."

Then you **average all those possibilities** — each one weighted by how likely it is.

That average is called the **Expected Value**, and it's the fairest price you could set.

---

## Two Ways to Make That Guess

Imagine you have a magic bag full of little futures — each one is a possible tomorrow.

### 🎲 The Classical Way (like rolling dice many times)

You reach into the bag and pull out **thousands of futures**, one by one.
You check each one: "Did I make money? How much?"
Then you average all the answers.

This works, but it's **slow** — the more accurate you want to be, the more futures you have to check.

### ⚛️ The Quantum Way (like checking all futures at once)

Quantum computers are special. Instead of checking futures one by one, they can look at **all of them at the same time** — like spreading them all on the table at once.

This is called **Quantum Amplitude Estimation**.

It gets to a good answer **much faster** than the classical way.

---

## The Recipe (Always 4 Steps)

No matter what you're pricing — lemonade, cloud software, or a space rocket — the recipe is always the same:

| Step | Name | What it means |
|---|---|---|
| 1 | **Uncertainty Model** | What things might change? (weather, demand, cost) |
| 2 | **Payoff Function** | If that happens, how much do I earn or lose? |
| 3 | **Encoding** | Load all those possibilities into the computer |
| 4 | **Estimation** | Ask: "What's the average outcome?" |

---

## What This Program Actually Does

This program is a **simulator**. It lets you:

1. Describe what's uncertain (like "demand might be anywhere between 10 and 100 cups")
2. Describe your payoff (like "I earn €0.50 for every cup above my cost")
3. Run the **classical method** — try thousands of random futures
4. Run the **quantum method** — estimate the answer with a quantum algorithm
5. **Compare both answers side by side** to see they agree — just one gets there faster

It also lets you **draw the quantum circuit** and see it in [IBM Quantum Composer](https://quantum.cloud.ibm.com/composer) — a visual tool that shows exactly what the quantum computer does, step by step, like sheet music for a quantum song.

---

## So Why Does This Matter?

Everything in business has uncertainty:

- 📦 Will customers buy my product?
- ☁️ How much will my cloud bill be next month?
- 📉 What if a key supplier raises prices?

This project shows that **quantum computers could one day help companies make smarter pricing decisions** — faster and more accurately than classical computers can.

We're not there yet with real quantum hardware. But the math already works. And this project proves it. 🚀

---

## Who Made This?

**Jose Giori Herran Escobar** — built this as part of a hands-on workshop to teach business leaders how quantum computing works in the real world.

> *"Even before quantum computers are fast enough to beat classical ones, learning to think this way makes us better at understanding value under uncertainty."*
